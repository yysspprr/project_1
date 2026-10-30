### =====================================================
### 1 - IMPORTS, COLORS & SETUP                         #
### 1 - IMPORTS, COLORS & SETUP                         #
### 1 - IMPORTS, COLORS & SETUP                         #
### =====================================================

# =======================================================
# 1.1 - Imports                                         #
# =======================================================

# Built-in modules
import random
import subprocess
import sys

# Installed modules
import pygame

# My files
import partials.game_logic as logic
from partials.drawing import *
from partials.themes import THEMES
from partials.backgrounds import make_background
from partials.config import *
from partials.stats import load_stats, record_game

# =======================================================
# 1.2 - Colors                                          #
# =======================================================

# Fall back to the defaults if the saved file names a theme or mode that doesn't exist
if settings["theme"] not in THEMES:
    settings["theme"] = "plain"
if settings["mode"] not in ("dark", "light"):
    settings["mode"] = "dark"

def set_palette(theme, mode):
    global palette, BG_COLOR, TEXT_COLOR, ACCENT_COLOR, FIELD_COLOR, MUTED_COLOR
    global OVERLAY_COLOR, HISTORY_BOX_COLOR, RANGE_FILL_COLOR, BAR_COLOR

    palette = THEMES[theme][mode]
    BG_COLOR = palette["bg"]
    TEXT_COLOR = palette["text"]
    ACCENT_COLOR = palette["accent"]
    FIELD_COLOR = palette["field"]
    MUTED_COLOR = palette["muted"]
    OVERLAY_COLOR = palette["overlay"]
    HISTORY_BOX_COLOR = palette["history_box"]
    RANGE_FILL_COLOR = palette["range_fill"]
    BAR_COLOR = palette["bar"]

set_palette(settings["theme"], settings["mode"])

# =======================================================
# 1.3 - Pygame setup                                    #
# =======================================================

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Guesstimate!")
clock = pygame.time.Clock()

### =====================================================
### 2 - FUNCTIONS & CLASSES                             #
### 2 - FUNCTIONS & CLASSES                             #
### 2 - FUNCTIONS & CLASSES                             #
### =====================================================

# =======================================================
# 2.1 - Buttons and icons                               #
# =======================================================

def make_button(text):
    letters = make_letters(text, menu_font, TEXT_COLOR)
    return {
        "text": text,
        "letters": letters,
        "hover_letters": make_letters(text, menu_font, ACCENT_COLOR),
        "poses": make_poses(letters),
        "rect": pygame.Rect(0, 0, 0, 0),
        "style": "strong",
    }

def draw_button(button, y, center_x=CENTER_X, layer="screen"):
    # Only buttons on the top layer react to the mouse: modal, then panel, then screen
    if game.warning_modal_open:
        can_hover = layer == "modal"
    elif game.settings_open:
        can_hover = layer == "panel"
    else:
        can_hover = layer == "screen"

    if can_hover and button["rect"].collidepoint(pygame.mouse.get_pos()):
        letters = button["hover_letters"]
    else:
        letters = button["letters"]
    button["rect"] = draw_wobbly(letters, button["poses"], center_x, y)

def faint_color():
    # The muted color, mostly see-through: for things that are there but not active
    color = pygame.Color(MUTED_COLOR)
    color.a = INACTIVE_ICON_ALPHA
    return color

def make_icon_button(name):
    frames = load_frames(SETTINGS_PANEL_ICONS_DIR / name, name, (BAR_ICON_SIZE, BAR_ICON_SIZE))
    normal_frames = []
    hover_frames = []

    for frame in frames:
        normal_frames.append(tint_image(frame, TEXT_COLOR))
        hover_frames.append(tint_image(frame, ACCENT_COLOR))
    
    return {
        "white_frames": frames,
        "frames": normal_frames,
        "hover_frames": hover_frames,
        "inactive_frames": tint_frames(frames, faint_color()),
        "frame": 0,                             # which of the three frames is showing
        "poses": make_poses([normal_frames[0]], "subtle"),
        "rect": pygame.Rect(0, 0, 0, 0),
    }

def draw_icon_button(icon, center_x, y, active=True):
    can_hover = active and not game.warning_modal_open and (not game.settings_open or icon is settings_icon)
    if not active:
        image = icon["inactive_frames"][icon["frame"]]
    elif can_hover and icon["rect"].collidepoint(pygame.mouse.get_pos()):
        image = icon["hover_frames"][icon["frame"]]
    else:
        image = icon["frames"][icon["frame"]]
    icon["rect"] = draw_wobbly([image], icon["poses"], center_x, y)

# =======================================================
# 2.2 - Game functions                                  #
# =======================================================

def start_game(difficulty):
    game.difficulty = difficulty
    game.screen = "game"

    if difficulty == "free":
        game.range_lowest = settings["free from"]
        game.range_highest = settings["free to"]
        game.max_tries = None                       # None: no limit
        game.tokens_needed = 0
        game.history_size = logic.FREE_HISTORY_SIZE
        game.show_range_bar = settings["free range bar"]
        game.show_history = settings["free history"]
    else:
        game.range_lowest, game.range_highest, game.max_tries, game.tokens_needed = logic.difficulty_settings(difficulty)
        game.history_size = game.max_tries
        game.show_range_bar = difficulty in RANGE_BAR_MODES
        game.show_history = True

    game.max_digits = logic.max_digits(game.range_lowest, game.range_highest)
    set_game_labels()

    make_entry_box(game.max_digits)
    make_history_box(game.history_size, game.max_digits)

    game.lives = logic.STARTING_LIVES
    game.tokens = 0
    game.rounds_played = 0
    game.rounds_won = 0
    game.total_tries = 0
    game.first_tries = 0
    set_hearts()
    set_tokens()
    next_round()

def set_game_labels():
    labels["difficulty"] = make_label(f"{game.difficulty} mode", tiny_font, MUTED_COLOR, "subtle")
    labels["range"] = make_label(f"({game.range_lowest} to {game.range_highest})", small_heading_font, TEXT_COLOR,
                                 "normal", small_heading_digit_font)

def next_round():
    game.secret = random.randint(game.range_lowest, game.range_highest)
    print(f"number = {game.secret}")

    game.try_count = 0
    set_typed("")
    game.guesses.clear()
    game.round_over = False
    set_game_message("")
    set_tries_label()
    set_history()
    make_range_fill()
    set_round_label()

def end_round(won_round):
    game.round_over = True
    game.rounds_played += 1
    make_range_fill()

    # Free mode: no lives or tokens to update
    if game.difficulty == "free":
        set_game_message(f"got it in {tries_text(game.try_count)}!")
        return

    if won_round:
        game.rounds_won += 1
        if game.try_count == 1:
            game.first_tries += 1
    
    game.lives, game.tokens = logic.after_round(game.lives, game.tokens, won_round, game.difficulty)
    set_hearts()
    set_tokens()

    result = game.result()
    if result == "game won":
        set_game_message("you won the game!")
    elif result == "game lost":
        set_game_message(f"game over! it was {game.secret}")

def set_game_message(text):
    game.message = text
    labels["message"] = make_label(text, small_font, TEXT_COLOR, "normal", small_digit_font)

def set_typed(text):
    game.typed_guess = text
    labels["typed"] = make_label(text, typed_font, ACCENT_COLOR, "typed")

def tries_text(count):
    if count == 1:
        return "1 try"
    return f"{count} tries"

def set_tries_label():
    if game.max_tries is None:
        text = tries_text(game.try_count)
    else:
        tries_left = game.max_tries - game.try_count
        if tries_left == 1:
            text = "1 try left"
        else:
            text = f"{tries_left} tries left"

    labels["tries"] = make_label(text, tiny_font, MUTED_COLOR, "subtle", tiny_digit_font)

def set_round_label():
    round_number = game.rounds_played + 1
    labels["round"] = make_label(f"round {round_number}", tiny_font, TEXT_COLOR, "subtle", tiny_digit_font)

def set_hearts():
    sprites["hearts"] = make_sprite(heart_slots(), "strong")

def heart_slots():
    slots = []
    for position in range(logic.STARTING_LIVES):
        if game.result() == "game won":
            slots.append(heart_frames_gold)
        elif position < game.lives:
            slots.append(heart_frames_red)
        else:
            slots.append(heart_frames_empty)
    return slots

def set_tokens():
    sprites["tokens"] = make_sprite(token_slots(), "strong")

def token_slots():
    slots = []
    for position in range(game.tokens_needed):
        if position < game.tokens:
            slots.append(token_frames_filled)
        else:
            slots.append(token_frames_empty)
    return slots

def set_history():
    slots = []
    for image in make_history_images():
        slots.append([image])           # one frame each: the numbers wobble but don't animate
    sprites["history"] = make_sprite(slots, "typed")

def make_history_images():
    shown = game.guesses[-game.history_size:]      # the last history_size guesses
    images = []
    for position in range(game.history_size):
        if position < len(shown):
            text = str(shown[position]).center(game.max_digits)
            color = TEXT_COLOR
        else:
            text = HISTORY_EMPTY_SYMBOL * game.max_digits
            color = MUTED_COLOR
        images.append(history_font.render(text, True, color))
    return images

def open_warning_modal(action, question):
    game.warning_modal_open = True
    game.warning_modal_action = action
    labels["warning"] = make_label(question, menu_font, TEXT_COLOR, "normal")
    boxes["warning"] = make_box(warning_modal_panel, FIELD_COLOR, TEXT_COLOR, radius=s(16), edge_steps=16)

def make_entry_box(max_digits):
    global entry_box
    width = (ENTRY_PADDING + max_digits * typed_char_width
             + ENTER_KEY_GAP + ENTER_KEY_SIZE[0] + ENTER_KEY_INSET)

    entry_box = pygame.Rect(0, 0, width, ENTRY_BOX_HEIGHT)
    entry_box.center = (CENTER_X, ENTRY_BOX_Y)
    boxes["entry"] = make_box(entry_box, FIELD_COLOR, TEXT_COLOR)

def make_history_box(history_size, max_digits):
    global history_box
    columns = history_size - history_size // 2      # the bottom row is the widest
    slot_width = history_font.size("0" * max_digits)[0]
    slot_height = history_font.get_height()

    width = columns * slot_width + (columns - 1) * HISTORY_GAP + HISTORY_PADDING * 2
    height = slot_height * 2 + HISTORY_ROW_GAP + HISTORY_PADDING * 2

    history_box = pygame.Rect(0, 0, width, height)
    history_box.midtop = (CENTER_X, HISTORY_Y - HISTORY_PADDING)
    boxes["history"] = make_box(history_box, HISTORY_BOX_COLOR, None)

def make_range_track():
    global range_track
    range_track = pygame.Rect((0, 0), RANGE_BAR_SIZE)
    range_track.midtop = (CENTER_X, RANGE_BAR_Y)
    boxes["range_track"] = make_box(range_track, (0, 0, 0, 0), MUTED_COLOR,
                                    radius=RANGE_BAR_SIZE[1] // 2, wobble=RANGE_BAR_WOBBLE)

def make_range_fill():
    global range_fill
    low, high = game.narrowed_range()
    total = game.range_highest - game.range_lowest + 1      # how many numbers the bar covers

    left = range_track.left + (low - game.range_lowest) * range_track.width / total
    right = range_track.left + (high - game.range_lowest + 1) * range_track.width / total

    width = max(round(right - left), 2)                     # never thinner than 2 px
    range_fill = pygame.Rect(round(left), range_track.top, width, range_track.height)
    radius = min(range_track.height // 2, width // 2)
    boxes["range_fill"] = make_box(range_fill, RANGE_FILL_COLOR, None, radius=radius, wobble=RANGE_BAR_WOBBLE)

    set_range_labels()

def set_range_labels():
    global range_labels
    below_y = range_track.bottom + RANGE_LABEL_GAP
    above_y = range_track.top - RANGE_LABEL_GAP - range_label_font.get_height()

    # Ends of the track
    range_labels = [
        make_label(str(game.range_lowest), range_label_font, MUTED_COLOR, x=range_track.left, y=below_y),
        make_label(str(game.range_highest), range_label_font, MUTED_COLOR, x=range_track.right, y=below_y),
    ]

    # Round over: the fill has shrunk to the secret, so show the answer
    if game.round_over:
        range_labels.append(make_label(str(game.secret), range_label_font, TEXT_COLOR,
                                       x=range_fill.centerx, y=above_y))
        return

    # The closest guesses on each side, at the edges of the fill
    below, above = game.closest_guesses()

    if below is not None and above is not None:
        below_width = range_label_font.size(str(below))[0]
        above_width = range_label_font.size(str(above))[0]
        needed = (below_width + above_width) / 2 + RANGE_LABEL_MIN_GAP

        if range_fill.width < needed:
            range_labels.append(make_label(f"{below} to {above}", range_label_font, TEXT_COLOR,
                                           x=range_fill.centerx, y=above_y))
        else:
            range_labels.append(make_label(str(below), range_label_font, TEXT_COLOR, x=range_fill.left, y=above_y))
            range_labels.append(make_label(str(above), range_label_font, TEXT_COLOR, x=range_fill.right, y=above_y))
    elif below is not None:
        range_labels.append(make_label(str(below), range_label_font, TEXT_COLOR, x=range_fill.left, y=above_y))
    elif above is not None:
        range_labels.append(make_label(str(above), range_label_font, TEXT_COLOR, x=range_fill.right, y=above_y))

def active_bar_icons():
    # The left icons that do something on this screen (never the same as a button on screen)
    if game.screen == "game":
        return [home_icon, back_icon, restart_icon]
    elif game.screen in ("difficulty", "free setup"):
        return [back_icon]
    else:
        return []                       # menu and results: their own buttons cover it

def settings_offset():
    # How many pixels the bar has slid up: 0 when closed, the panel height when open
    eased = 1 - (1 - game.settings_slide) ** 2          # fast at first, slowing down at the end
    return round(SETTINGS_PANEL_HEIGHT * eased)

def clicked_bar_icon(pos):
    # Which active bar icon was clicked, or None
    for icon in active_bar_icons() + [settings_icon]:
        if icon["rect"].collidepoint(pos):
            return icon
    return None

def apply_theme():
    # Use the theme and mode from settings, and remake everything that has a color
    global background, background_theme
    global cursor_on, cursor_off
    global token_frames_filled, token_frames_empty

    # A new background only when the theme changes, so a mode switch keeps the ripples
    if background_theme != settings["theme"]:
        background = make_background(settings["theme"])
        background_theme = settings["theme"]

    set_palette(settings["theme"], settings["mode"])

    # Titles and headings
    labels["title"] = make_label("guesstimate!", title_font, TEXT_COLOR, "strong")
    labels["difficulty_title"] = make_label("pick a difficulty", menu_font, TEXT_COLOR, "normal")
    labels["heading"] = make_label("guess a number", small_heading_font, TEXT_COLOR, "normal")

    # Buttons and bar icons
    for button in all_buttons:
        button["letters"] = make_letters(button["text"], menu_font, TEXT_COLOR)
        button["hover_letters"] = make_letters(button["text"], menu_font, ACCENT_COLOR)
    for icon in all_icons:
        icon["frames"] = tint_frames(icon["white_frames"], TEXT_COLOR)
        icon["hover_frames"] = tint_frames(icon["white_frames"], ACCENT_COLOR)
        icon["inactive_frames"] = tint_frames(icon["white_frames"], faint_color())

    # Tinted images
    token_frames_filled = tint_frames(token_frames_filled_white, ACCENT_COLOR)
    token_frames_empty = tint_frames(token_frames_empty_white, MUTED_COLOR)
    enter_frames = tint_frames(enter_frames_white, TEXT_COLOR)
    space_frames = tint_frames(space_frames_white, MUTED_COLOR)
    sprites["enter"] = make_sprite([enter_frames], "subtle")
    sprites["space"] = make_sprite([space_frames], "subtle")

    # Cursor and small labels
    cursor_on = typed_font.render(CURSOR_SYMBOL, True, MUTED_COLOR)
    cursor_off = pygame.Surface(cursor_on.get_size(), pygame.SRCALPHA)
    sprites["cursor"] = make_sprite([[cursor_on]], "typed")
    labels["continue"] = make_label("next round", tiny_font, MUTED_COLOR)
    labels["play_again"] = make_label("see results", tiny_font, MUTED_COLOR)

    # See-through layers
    bar_surface.fill(BAR_COLOR)
    warning_modal_overlay.fill(OVERLAY_COLOR)
    settings_panel_surface.fill(BAR_COLOR)

    # Free mode setup screen
    labels["free_title"] = make_label("free mode", menu_font, TEXT_COLOR, "normal")
    labels["free_from_label"] = make_label("from", tiny_font, MUTED_COLOR)
    labels["free_to_label"] = make_label("to", tiny_font, MUTED_COLOR)
    set_free_inputs()
    set_free_message(game.free_message)
    set_free_toggles()

    # Game screen: boxes and setters, rebuilt from the current game
    make_entry_box(game.max_digits)
    make_history_box(game.history_size, game.max_digits)
    make_range_track()
    make_range_fill()
    set_game_labels()
    set_game_message(game.message)
    set_typed(game.typed_guess)
    set_tries_label()
    set_round_label()
    set_hearts()
    set_tokens()
    set_history()
    set_results()
    set_settings_rows()

# =======================================================
# 2.3 - Settings functions                              #
# =======================================================

def setting_choices(name):
    # Everything a setting can be set to, in order
    if name == "theme":
        return list(THEMES)
    elif name == "mode":
        return ["dark", "light"]
    elif name == "window size":
        return ["auto", "small", "medium", "large"]

def change_setting(name, step):
    # Go to the next (step 1) or previous (step -1) choice, wrapping around, and save it
    choices = setting_choices(name)
    index = (choices.index(settings[name]) + step) % len(choices)
    settings[name] = choices[index]
    save_settings(settings)

    apply_theme()

def set_settings_rows():
    global settings_rows
    settings_rows = []
    for name in SETTINGS_ROWS:
        settings_rows.append({
            "name": name,
            "label": make_label(name, small_font, MUTED_COLOR),
            "value": make_label(settings[name], small_font, TEXT_COLOR),
            "left": make_button("<"),
            "right": make_button(">"),
        })

def restart_program():
    # Start a fresh copy of the game, then close this one
    pygame.quit()
    subprocess.Popen([sys.executable] + sys.argv)
    sys.exit()

def close_settings():
    game.settings_open = False

    # A different window size only takes effect after a restart
    if pick_window_size() != window_size:
        if game.screen == "game" and game.has_progress():
            open_warning_modal("resize", "restart to resize?")
        else:
            restart_program()

def toggle_settings():
    if game.settings_open:
        close_settings()
    else:
        game.settings_open = True

# =======================================================
# 2.4 - Free mode setup functions                       #
# =======================================================

def open_free_setup():
    # Show the setup screen, starting from the last range that was used
    game.screen = "free setup"
    game.free_text["from"] = str(settings["free from"])
    game.free_text["to"] = str(settings["free to"])
    game.free_focus = "from"
    set_free_message("")
    set_free_inputs()

def set_free_inputs():
    # The two number boxes; the one you're typing in gets a gold outline
    width = ENTRY_PADDING * 2 + FREE_BOX_CHARS * typed_char_width

    for field, center_x in (("from", CENTER_X - FREE_BOX_GAP), ("to", CENTER_X + FREE_BOX_GAP)):
        rect = pygame.Rect(0, 0, width, ENTRY_BOX_HEIGHT)
        rect.center = (center_x, FREE_BOX_Y)

        if field == game.free_focus:
            line_color = ACCENT_COLOR
        else:
            line_color = TEXT_COLOR

        boxes[f"free_{field}"] = make_box(rect, FIELD_COLOR, line_color)
        labels[f"free_{field}"] = make_label(game.free_text[field], typed_font, ACCENT_COLOR, "typed")

def set_free_message(text):
    game.free_message = text
    labels["free_message"] = make_label(text, small_font, TEXT_COLOR, "normal", small_digit_font)

def set_free_toggles():
    global free_toggles
    free_toggles = []
    for name, text in FREE_TOGGLES:
        if settings[name]:
            value = "on"
        else:
            value = "off"
        free_toggles.append({
            "name": name,
            "label": make_label(text, small_font, MUTED_COLOR),
            "value": make_button(value),
        })

def toggle_free_option(name):
    settings[name] = not settings[name]
    save_settings(settings)
    set_free_toggles()

def type_in_free_box(event):
    field = game.free_focus
    text = game.free_text[field]

    if event.key == pygame.K_TAB:
        if field == "from":
            game.free_focus = "to"
        else:
            game.free_focus = "from"
    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        start_free_game()
        return
    elif event.key == pygame.K_BACKSPACE:
        text = text[:-1]
    elif event.unicode.isdigit() and len(text.lstrip("-")) < 4:
        text = text + event.unicode
    elif event.unicode == "-" and text == "":
        text = "-"                              # a minus only as the very first character

    game.free_text[field] = text
    set_free_inputs()

def start_free_game():
    # Check the range; if it's fine, save it and start
    try:
        low = int(game.free_text["from"])
        high = int(game.free_text["to"])
    except ValueError:
        set_free_message("fill in both numbers!")
        return

    problem = logic.free_range_problem(low, high)
    if problem is not None:
        set_free_message(problem)
        return

    settings["free from"] = low
    settings["free to"] = high
    save_settings(settings)
    start_game("free")

# =======================================================
# 2.5 - Results screen functions                        #
# =======================================================

def open_results():
    game.screen = "results"
    if game.difficulty != "free":
        record_game(stats, game.difficulty, game.result() == "game won",
                    game.total_tries, game.rounds_played, game.first_tries)
    set_results()

def set_results():
    # The title and stats lines, depending on the mode and how the game ended
    global results_lines
    lines = []

    if game.difficulty == "free":
        title = "you got it!"
        lines.append(f"the number was {game.secret}")
        lines.append(f"free mode ({game.range_lowest} to {game.range_highest})")
        lines.append(tries_text(game.try_count))

        # Only mention the help that was turned off
        turned_off = []
        if not game.show_range_bar:
            turned_off.append("no range bar")
        if not game.show_history:
            turned_off.append("no history")
        if len(turned_off) > 0:
            lines.append(", ".join(turned_off))
    else:
        if game.result() == "game won":
            title = "you won!"
        else:
            title = "game over"
            lines.append(f"the last number was {game.secret}")
        lines.append(f"{game.difficulty} mode")
        lines.append(f"{game.rounds_won} of {game.rounds_played} rounds won")
        lines.append(f"{game.total_tries} guesses in total")

    labels["results_title"] = make_label(title, title_font, TEXT_COLOR, "strong")
    results_lines = []
    for text in lines:
        results_lines.append(make_label(text, small_font, TEXT_COLOR, "normal", small_digit_font))

def results_back_button():
    # "change range" after free mode, "difficulty" after the regular modes
    if game.difficulty == "free":
        return results_range_button
    return results_difficulty_button

# =======================================================
# 2.6 - Game state class                                #
# =======================================================

class GameState:
    def __init__(self):

        # Screen state
        self.screen = "menu"
        self.warning_modal_open = False
        self.warning_modal_action = ""
        self.settings_open = False
        self.running = True
        self.settings_slide = 0         # 0 = closed, 1 = fully open; changes a bit every frame

        # Difficulty
        self.difficulty = "normal"
        self.range_lowest, self.range_highest, self.max_tries, self.tokens_needed = logic.difficulty_settings(self.difficulty)
        self.max_digits = logic.max_digits(self.range_lowest, self.range_highest)

        self.history_size = self.max_tries         # how many guesses the history shows

        self.show_range_bar = True
        self.show_history = True

        # Free mode setup screen
        self.free_text = {"from": "", "to": ""}     # what's typed in each box
        self.free_focus = "from"                    # which box you're typing in
        self.free_message = ""

        # Game
        self.lives = logic.STARTING_LIVES
        self.tokens = 0
        self.rounds_played = 0
        self.rounds_won = 0
        self.total_tries = 0            # guesses over the whole game, all rounds together

        self.first_tries = 0            # rounds guessed on the very first try

        # Current round
        self.secret = 0
        self.try_count = 0
        self.guesses = []
        self.round_over = False
        self.typed_guess = ""
        self.message = ""

    def result(self):
        # Free mode has no lives or tokens: the game is won once the number is guessed
        if self.difficulty == "free":
            if self.round_over:
                return "game won"
            return "playing"
        return logic.game_result(self.lives, self.tokens, self.tokens_needed)

    def has_progress(self):
        if self.difficulty == "free":
            return self.try_count > 0 and not self.round_over
        return logic.has_progress(self.lives, self.tokens, self.tokens_needed, self.rounds_played, self.try_count)
    
    def narrowed_range(self):
        if self.round_over:
            return self.secret, self.secret
        return logic.narrowed_range(self.guesses, self.secret, self.range_lowest, self.range_highest)

    def closest_guesses(self):
        return logic.closest_guesses(self.guesses, self.secret)

### =====================================================
### 3 - SCREEN SETUP                                    #
### 3 - SCREEN SETUP                                    #
### 3 - SCREEN SETUP                                    #
### =====================================================

# =======================================================
# 3.1 - Font settings                                   #
# =======================================================

title_font = pygame.font.Font(FONT_PATH, s(40))
small_heading_font = pygame.font.Font(FONT_PATH, s(26))
small_heading_digit_font = pygame.font.Font(DIGIT_FONT_PATH, s(24))
menu_font = pygame.font.Font(FONT_PATH, s(24))
typed_font = pygame.font.Font(DIGIT_FONT_PATH, s(32))
small_font = pygame.font.Font(FONT_PATH, s(18))
small_digit_font = pygame.font.Font(DIGIT_FONT_PATH, s(17))
tiny_font = pygame.font.Font(FONT_PATH, s(16))
tiny_digit_font = pygame.font.Font(DIGIT_FONT_PATH, s(15))
history_font = pygame.font.Font(DIGIT_FONT_PATH, HISTORY_FONT_SIZE)
range_label_font = pygame.font.Font(DIGIT_FONT_PATH, RANGE_LABEL_FONT_SIZE)

# =======================================================
# 3.2 - Menu screen setup                               #
# =======================================================

new_game_button = make_button("new game")
free_mode_button = make_button("free mode")
exit_button = make_button("exit")

# =======================================================
# 3.3 - Difficulty screen setup                         #
# =======================================================

easy_button = make_button("easy")
normal_button = make_button("normal")
hard_button = make_button("hard")

free_start_button = make_button("start")

# Free mode toggles: (setting name, label shown)
FREE_TOGGLES = [
    ("free range bar", "range bar"),
    ("free history", "history"),
]

# Results screen
results_again_button = make_button("play again")
results_range_button = make_button("change range")
results_difficulty_button = make_button("difficulty")
results_menu_button = make_button("menu")

# =======================================================
# 3.4 - Game state                                      #
# =======================================================

game = GameState()

# =======================================================
# 3.5 - Game screen setup                               #
# =======================================================

heart_frames_red = load_frames(HEARTS_DIR / "red", "heart_red", HEART_SIZE)
heart_frames_gold = load_frames(HEARTS_DIR / "gold", "heart_gold", HEART_SIZE)
heart_frames_empty = load_frames(HEARTS_DIR / "empty", "heart_empty", HEART_SIZE)

token_frames_filled_white = load_frames(TOKENS_FILLED_DIR, "token_filled", TOKEN_SIZE)
token_frames_empty_white = load_frames(TOKENS_EMPTY_DIR, "token_empty", TOKEN_SIZE)
enter_frames_white = load_frames(ENTER_KEY_DIR, "enter_key", ENTER_KEY_SIZE)
space_frames_white = load_frames(SPACE_BAR_KEY_DIR, "space_key", SPACE_BAR_KEY_SIZE)

# Width of the widest character you can type, so the box always fits
typed_char_width = 0
for char in "0123456789-_":
    typed_char_width = max(typed_char_width, typed_font.size(char)[0])

# =======================================================
# 3.6 - Bottom bar setup                                #
# =======================================================

home_icon = make_icon_button("home")
back_icon = make_icon_button("back")
restart_icon = make_icon_button("restart")
settings_icon = make_icon_button("settings")

all_icons = [home_icon, back_icon, restart_icon, settings_icon]

bar_left_icons = [home_icon, back_icon, restart_icon]       # always drawn, in this order

bar_surface = pygame.Surface((WIDTH, BAR_HEIGHT), pygame.SRCALPHA)

# =======================================================
# 3.7 - Settings panel setup                            #
# =======================================================

SETTINGS_ROWS = ["theme", "mode", "window size"]

settings_panel_surface = pygame.Surface((WIDTH, SETTINGS_PANEL_HEIGHT), pygame.SRCALPHA)

# =======================================================
# 3.8 - Warning modal setup                             #
# =======================================================

warning_modal_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

warning_modal_panel = pygame.Rect((0, 0), WARNING_MODAL_SIZE)
warning_modal_panel.center = (CENTER_X, HEIGHT // 2)

warning_modal_yes_button = make_button("yes")
warning_modal_no_button = make_button("no")

all_buttons = [
    new_game_button, free_mode_button, exit_button,
    easy_button, normal_button, hard_button,
    free_start_button,
    warning_modal_yes_button, warning_modal_no_button,
    results_again_button, results_range_button, results_difficulty_button, results_menu_button,
]

# =======================================================
# 3.9 - Starting values                                 #
# =======================================================

background = None
background_theme = None         # which theme the background was made for
labels = {}                     # every wobbly text, by name; filled in by apply_theme and the setters
sprites = {}                    # every wobbly image, by name
boxes = {}                      # every boiling box, by name
stats = load_stats()            # the player's stats per regular mode, from stats.json
apply_theme()

### =====================================================
### 4 - MAIN LOOP                                       #
### 4 - MAIN LOOP                                       #
### 4 - MAIN LOOP                                       #
### =====================================================

# =======================================================
# 4.1 - Event handling                                  #
# =======================================================

def handle_event(event):
    if event.type == pygame.QUIT:
        handle_quit()
    elif event.type == pygame.MOUSEBUTTONDOWN:
        handle_click(event.pos)
    elif event.type == pygame.KEYDOWN:
        handle_key(event)

def handle_quit():
    # The window's close button: ask first if there's a game to lose
    if game.screen == "game" and game.has_progress() and not game.warning_modal_open:
        open_warning_modal("quit", "quit the game?")
    else:
        game.running = False

# --- Mouse ---

def handle_click(pos):
    # Whatever is on top gets the click: modal, then the gear, then the panel, then the rest
    clicked_icon = clicked_bar_icon(pos)

    if game.warning_modal_open:
        click_warning_modal(pos)
    elif clicked_icon is settings_icon:
        toggle_settings()
    elif game.settings_open:
        click_settings_panel(pos)
    elif clicked_icon is not None:
        click_bar_icon(clicked_icon)
    elif game.screen == "menu":
        click_menu(pos)
    elif game.screen == "difficulty":
        click_difficulty(pos)
    elif game.screen == "free setup":
        click_free_setup(pos)
    elif game.screen == "results":
        click_results(pos)

def click_warning_modal(pos):
    if warning_modal_yes_button["rect"].collidepoint(pos):
        game.warning_modal_open = False
        confirm_warning(game.warning_modal_action)
    elif warning_modal_no_button["rect"].collidepoint(pos):
        game.warning_modal_open = False

def confirm_warning(action):
    # The player clicked "yes": do what the modal asked about
    if action == "menu":
        game.screen = "menu"
    elif action == "quit":
        game.running = False
    elif action == "restart":
        start_game(game.difficulty)
    elif action == "back":
        leave_game()
    elif action == "resize":
        restart_program()

def leave_game():
    # Back from a game: to the free mode setup or the difficulty screen
    if game.difficulty == "free":
        open_free_setup()
    else:
        game.screen = "difficulty"

def click_settings_panel(pos):
    if pos[1] < HEIGHT - BAR_HEIGHT - settings_offset():
        close_settings()                        # a click above the bar closes the panel
        return

    for row in settings_rows:
        if row["left"]["rect"].collidepoint(pos):
            change_setting(row["name"], -1)
            break
        elif row["right"]["rect"].collidepoint(pos):
            change_setting(row["name"], 1)
            break

def click_bar_icon(icon):
    if icon is home_icon:
        if game.has_progress():
            open_warning_modal("menu", "leave this game?")
        else:
            game.screen = "menu"
    elif icon is back_icon:
        if game.screen in ("difficulty", "free setup"):
            game.screen = "menu"
        elif game.has_progress():
            open_warning_modal("back", "leave this game?")
        else:
            leave_game()
    elif icon is restart_icon:
        if game.has_progress():
            open_warning_modal("restart", "restart this game?")
        else:
            start_game(game.difficulty)

def click_menu(pos):
    if new_game_button["rect"].collidepoint(pos):
        game.screen = "difficulty"
    elif free_mode_button["rect"].collidepoint(pos):
        open_free_setup()
    elif exit_button["rect"].collidepoint(pos):
        game.running = False

def click_difficulty(pos):
    if easy_button["rect"].collidepoint(pos):
        start_game("easy")
    elif normal_button["rect"].collidepoint(pos):
        start_game("normal")
    elif hard_button["rect"].collidepoint(pos):
        start_game("hard")

def click_free_setup(pos):
    if boxes["free_from"]["rect"].collidepoint(pos):
        game.free_focus = "from"
        set_free_inputs()
    elif boxes["free_to"]["rect"].collidepoint(pos):
        game.free_focus = "to"
        set_free_inputs()
    elif free_start_button["rect"].collidepoint(pos):
        start_free_game()
    else:
        for row in free_toggles:
            if row["value"]["rect"].collidepoint(pos):
                toggle_free_option(row["name"])
                break

def click_results(pos):
    if results_again_button["rect"].collidepoint(pos):
        start_game(game.difficulty)
    elif results_back_button()["rect"].collidepoint(pos):
        leave_game()
    elif results_menu_button["rect"].collidepoint(pos):
        game.screen = "menu"

# --- Keyboard ---

def handle_key(event):
    if game.warning_modal_open:
        return                                  # the modal only listens to the mouse

    if event.key == pygame.K_ESCAPE:
        toggle_settings()
    elif event.key == pygame.K_l:
        change_setting("mode", 1)
    elif event.key == pygame.K_t:
        change_setting("theme", 1)
    elif game.screen == "game" and not game.settings_open:
        if game.round_over:
            if event.key == pygame.K_SPACE:
                continue_after_round()
        else:
            handle_typing(event)
    elif game.screen == "free setup" and not game.settings_open:
        type_in_free_box(event)
    elif game.screen == "results" and not game.settings_open:
        if event.key == pygame.K_SPACE:
            start_game(game.difficulty)

def handle_typing(event):
    if event.unicode.isdigit() and len(game.typed_guess) < game.max_digits:
        set_typed(game.typed_guess + event.unicode)
    elif event.unicode == "-" and game.typed_guess == "" and game.range_lowest < 0:
        set_typed("-")                          # a minus only first, and only if the range goes below 0
    elif event.key == pygame.K_BACKSPACE:
        set_typed(game.typed_guess[:-1])
    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        submit_guess()

# What the game says after each kind of guess
GUESS_MESSAGES = {
    "invalid": "type a number first!",
    "out of range": "out of range!",
    "repeat": "already guessed!",
    "too high": "too high!",
    "too low": "too low!",
    "correct": "correct!",
}

def submit_guess():
    guess = game.typed_guess
    result = logic.check_guess(guess, game.secret, game.range_lowest, game.range_highest, game.guesses)
    set_typed("")
    set_game_message(GUESS_MESSAGES[result])

    if result in ("too high", "too low", "correct"):
        game.guesses.append(int(guess))
        game.try_count += 1
        game.total_tries += 1
        set_tries_label()
        set_history()
        make_range_fill()

    if result == "correct":
        end_round(True)
    elif game.try_count == game.max_tries:
        set_game_message(f"out of tries! it was {game.secret}...")
        end_round(False)

def continue_after_round():
    # Space after a round: the next round, or a new game if this one is over
    if game.result() == "playing":
        next_round()
    else:
        open_results()

# =======================================================
# 4.2 - Update                                          #
# =======================================================

def update(dt):
    # Everything that moves on its own: the background, the settings bar and the wobble
    global last_wobble

    if background is not None and not game.warning_modal_open:
        background.update(dt)
    slide_settings_bar(dt)

    now = pygame.time.get_ticks()
    if now - last_wobble >= WOBBLE_INTERVAL and not game.warning_modal_open:
        wobble_everything()
        last_wobble = now

def slide_settings_bar(dt):
    # Move the bar a little toward open or closed
    step = dt / SETTINGS_SLIDE_TIME
    if game.settings_open:
        game.settings_slide = min(game.settings_slide + step, 1)
    else:
        game.settings_slide = max(game.settings_slide - step, 0)

def wobble_everything():
    # New poses, frames and box outlines for everything that boils
    for label in labels.values():
        rewobble(label)
    for sprite in sprites.values():
        reanimate(sprite)
    for box in boxes.values():
        rejitter(box)
    for button in all_buttons:
        rewobble(button)

    for icon in all_icons:
        icon["frame"] = random.randrange(FRAME_COUNT)
        icon["poses"] = make_poses([icon["frames"][0]], "subtle")

    for label in range_labels:
        rewobble(label)

    for row in settings_rows:
        rewobble(row["label"])
        rewobble(row["value"])
        rewobble(row["left"])
        rewobble(row["right"])

    for row in free_toggles:
        rewobble(row["label"])
        rewobble(row["value"])

    for label in results_lines:
        rewobble(label)

    if background is not None:
        background.wobble()

# =======================================================
# 4.3 - Drawing                                         #
# =======================================================

def draw_screen():
    # Back to front: background, the current screen, the bar and panel, then the modal on top
    if background is None:
        screen.fill(BG_COLOR)
    else:
        background.draw(screen, palette)

    if game.screen == "menu":
        draw_menu()
    elif game.screen == "difficulty":
        draw_difficulty()
    elif game.screen == "free setup":
        draw_free_setup()
    elif game.screen == "game":
        draw_game()
    elif game.screen == "results":
        draw_results()

    draw_bar()
    draw_settings_panel()

    if game.warning_modal_open:
        draw_warning_modal()

# --- Screens ---

def draw_menu():
    draw_label(labels["title"], CENTER_X, TITLE_Y)
    draw_button(new_game_button, NEW_GAME_Y)
    draw_button(free_mode_button, FREE_MODE_Y)
    draw_button(exit_button, EXIT_Y)

def draw_difficulty():
    draw_label(labels["difficulty_title"], CENTER_X, TITLE_Y)
    draw_button(easy_button, EASY_Y)
    draw_button(normal_button, NORMAL_Y)
    draw_button(hard_button, HARD_Y)

def draw_free_setup():
    draw_label(labels["free_title"], CENTER_X, TITLE_Y)

    for field in ("from", "to"):
        rect = boxes[f"free_{field}"]["rect"]
        label_y = rect.top - FREE_LABEL_GAP - tiny_font.get_height()
        draw_label(labels[f"free_{field}_label"], rect.centerx, label_y)
        draw_box(boxes[f"free_{field}"])

        # The typed number, plus a blinking cursor in the box you're typing in
        line_letters = labels[f"free_{field}"]["letters"]
        line_poses = labels[f"free_{field}"]["poses"]
        typing_here = field == game.free_focus and not game.settings_open
        if typing_here and (pygame.time.get_ticks() // CURSOR_BLINK) % 2 == 0:
            line_letters = line_letters + [cursor_on]
            line_poses = line_poses + sprites["cursor"]["poses"]

        if len(line_letters) > 0:
            draw_wobbly(line_letters, line_poses, rect.left + ENTRY_PADDING,
                        rect.centery - typed_font.get_height() // 2, align="left")

    draw_label(labels["free_message"], CENTER_X, FREE_MESSAGE_Y)

    # The toggles; the values use the bigger menu font, so move them up to line up
    value_shift = (small_font.get_height() - menu_font.get_height()) // 2
    for position in range(len(free_toggles)):
        row = free_toggles[position]
        y = FREE_TOGGLE_Y + position * FREE_TOGGLE_GAP
        draw_label(row["label"], FREE_TOGGLE_LABEL_X, y, align="left")
        draw_button(row["value"], y + value_shift, center_x=FREE_TOGGLE_VALUE_X)

    draw_button(free_start_button, FREE_START_Y)

def draw_results():
    draw_label(labels["results_title"], CENTER_X, RESULTS_TITLE_Y)
    for position in range(len(results_lines)):
        draw_label(results_lines[position], CENTER_X, RESULTS_LINES_Y + position * RESULTS_LINE_GAP)

    draw_button(results_again_button, RESULTS_AGAIN_Y)
    draw_button(results_back_button(), RESULTS_BACK_Y)
    draw_button(results_menu_button, RESULTS_MENU_Y)

def draw_game():
    # Status: what you're guessing, and how you're doing
    draw_label(labels["heading"], CENTER_X, HEADING_Y)
    draw_label(labels["range"], CENTER_X, RANGE_Y)
    draw_label(labels["difficulty"], CENTER_X, DIFFICULTY_LABEL_Y)

    if game.difficulty != "free":
        draw_label(labels["round"], CENTER_X, ROUND_Y)
        draw_label(sprites["hearts"], CENTER_X, HEARTS_Y)
        draw_stacked(sprites["tokens"]["letters"], sprites["tokens"]["poses"], CENTER_X, TOKENS_Y,
                     TOKEN_GAP, TOKEN_ROW_GAP)

    # Play: range bar, message, entry box, space key
    if game.show_range_bar:
        draw_range_bar()
    draw_label(labels["message"], CENTER_X, MESSAGE_Y)
    draw_entry()
    if game.round_over:
        draw_space_cue()

    # Record: tries and the guess history
    draw_label(labels["tries"], CENTER_X, TRIES_Y)
    if game.show_history:
        draw_box(boxes["history"])
        draw_stacked(sprites["history"]["letters"], sprites["history"]["poses"], CENTER_X, HISTORY_Y,
                     HISTORY_GAP, HISTORY_ROW_GAP)

# --- Parts of the game screen ---

def draw_range_bar():
    draw_box(boxes["range_fill"])
    draw_box(boxes["range_track"])
    for label in range_labels:
        draw_label(label, label["x"], label["y"])

def draw_entry():
    draw_box(boxes["entry"])

    # The typed digits, plus a blinking cursor while you can type
    can_type = (not game.round_over and not game.warning_modal_open
                and not game.settings_open and len(game.typed_guess) < game.max_digits)

    line_letters = labels["typed"]["letters"]
    line_poses = labels["typed"]["poses"]
    if can_type:
        if (pygame.time.get_ticks() // CURSOR_BLINK) % 2 == 0:
            cursor_image = cursor_on
        else:
            cursor_image = cursor_off
        line_letters = labels["typed"]["letters"] + [cursor_image]
        line_poses = labels["typed"]["poses"] + sprites["cursor"]["poses"]

    if len(line_letters) > 0:
        draw_wobbly(line_letters, line_poses, entry_box.left + ENTRY_PADDING,
                    entry_box.centery - typed_font.get_height() // 2, align="left")

    # The enter key, once there's something to submit
    if game.typed_guess != "" and not game.round_over:
        enter_x = entry_box.right - ENTER_KEY_INSET - ENTER_KEY_SIZE[0] // 2
        enter_y = entry_box.centery - ENTER_KEY_SIZE[1] // 2
        draw_label(sprites["enter"], enter_x, enter_y)

def draw_space_cue():
    # After a round: the space key, with "next round" or "play again" under it
    if game.result() == "playing":
        next_label = labels["continue"]
    else:
        next_label = labels["play_again"]

    space_y = entry_box.bottom + SPACE_BAR_KEY_GAP
    draw_label(sprites["space"], CENTER_X, space_y)
    draw_label(next_label, CENTER_X, space_y + SPACE_BAR_KEY_SIZE[1] + SPACE_BAR_KEY_LABEL_GAP)

# --- On every screen ---

def draw_bar():
    bar_top = HEIGHT - BAR_HEIGHT - settings_offset()
    icon_y = bar_top + (BAR_HEIGHT - BAR_ICON_SIZE) // 2
    screen.blit(bar_surface, (0, bar_top))

    active = active_bar_icons()
    x = BAR_PADDING + BAR_ICON_SIZE // 2
    for icon in bar_left_icons:
        draw_icon_button(icon, x, icon_y, icon in active)
        x += BAR_ICON_SIZE + BAR_ICON_GAP

    draw_icon_button(settings_icon, WIDTH - BAR_PADDING - BAR_ICON_SIZE // 2, icon_y)

def draw_settings_panel():
    # Revealed below the bar as it slides up
    if settings_offset() == 0:
        return

    panel_top = HEIGHT - settings_offset()
    pygame.draw.rect(screen, BG_COLOR, (0, panel_top, WIDTH, SETTINGS_PANEL_HEIGHT))
    screen.blit(settings_panel_surface, (0, panel_top))

    # Arrows use the bigger menu font, so move them up to line up with the rows
    arrow_shift = (small_font.get_height() - menu_font.get_height()) // 2

    for position in range(len(settings_rows)):
        row = settings_rows[position]
        y = panel_top + SETTINGS_ROW_TOP + position * SETTINGS_ROW_GAP

        draw_label(row["label"], SETTINGS_LABEL_X, y, align="left")
        draw_label(row["value"], SETTINGS_VALUE_X, y)
        draw_button(row["left"], y + arrow_shift, center_x=SETTINGS_VALUE_X - SETTINGS_ARROW_GAP, layer="panel")
        draw_button(row["right"], y + arrow_shift, center_x=SETTINGS_VALUE_X + SETTINGS_ARROW_GAP, layer="panel")

def draw_warning_modal():
    screen.blit(warning_modal_overlay, (0, 0))
    draw_box(boxes["warning"])
    draw_label(labels["warning"], CENTER_X, warning_modal_panel.top + WARNING_QUESTION_OFFSET)
    draw_button(warning_modal_yes_button, warning_modal_panel.top + WARNING_YES_OFFSET, layer="modal")
    draw_button(warning_modal_no_button, warning_modal_panel.top + WARNING_NO_OFFSET, layer="modal")

# =======================================================
# 4.4 - Main loop                                       #
# =======================================================

last_wobble = 0
dt = 0

while game.running:

    for event in pygame.event.get():
        handle_event(event)

    update(dt)
    draw_screen()

    pygame.display.flip()
    dt = clock.tick(FPS)            # milliseconds since the last frame

pygame.quit()