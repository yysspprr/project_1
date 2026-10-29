### =====================================================
### 1 - IMPORTS, COLORS & SETUP                         #
### 1 - IMPORTS, COLORS & SETUP                         #
### 1 - IMPORTS, COLORS & SETUP                         #
### =====================================================

# =======================================================
# 1.1 - Imports                                         #
# =======================================================

# Built-in modules
import math
import random
import subprocess
import sys

# Installed modules
import pygame

# My files
import game_logic as logic
from config import *
from themes import THEMES
from backgrounds import make_background

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
# 2.1 - Drawing functions                               #
# =======================================================

def make_letters(text, font, color, digit_font=None):
    letter_images = []
    for letter in text:
        if digit_font is not None and letter.isdigit():
            letter_images.append(render_digit(letter, font, digit_font, color))
        else:
            letter_images.append(font.render(letter, True, color))
    return letter_images

def render_digit(digit, font, digit_font, color):
    # A digit in the digit font, lined up with the main font's baseline
    image = digit_font.render(digit, True, color)
    lined_up = pygame.Surface((image.get_width(), font.get_height()), pygame.SRCALPHA)
    lined_up.blit(image, (0, font.get_ascent() - digit_font.get_ascent()))
    return lined_up

def make_poses(images, style="strong"):
    amount, tilt = WOBBLE_STYLES[style]
    poses = []
    for image in images:
        dx = random.randint(-amount, amount)
        dy = random.randint(-amount, amount)
        angle = random.randint(-tilt, tilt)
        poses.append((dx, dy, angle))
    return poses

# Cache for tilted images, so each one is only rotated once
tilted_cache = {}

def get_tilted(image, angle):
    key = (image, angle)
    if key not in tilted_cache:
        if len(tilted_cache) > 1000:
            tilted_cache.clear()
        tilted_cache[key] = pygame.transform.rotozoom(image, angle, 1)
    return tilted_cache[key]

def draw_wobbly(images, poses, anchor_x, y, align="center", gap=0):
    total_width = 0
    for image in images:
        total_width += image.get_width()
    total_width += gap * (len(images) - 1)

    if align == "left":
        left = anchor_x
    else:
        left = anchor_x - total_width // 2
    x = left

    for position in range(len(images)):
        dx, dy, angle = poses[position]
        tilted = get_tilted(images[position], angle)
        center = (x + images[position].get_width() // 2 + dx,
                  y + images[position].get_height() // 2 + dy)
        screen.blit(tilted, tilted.get_rect(center=center))
        x += images[position].get_width() + gap

    return pygame.Rect(left, y, total_width, images[0].get_height())

def draw_stacked(images, poses, center_x, y, gap, row_gap):
    split = len(images) // 2
    row_height = images[0].get_height()

    if split > 0:
        draw_wobbly(images[:split], poses[:split], center_x, y, gap=gap)
    draw_wobbly(images[split:], poses[split:], center_x, y + row_height + row_gap, gap=gap)

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

def make_label(text, font, color, style="subtle", digit_font=None, x=0, y=0):
    # A wobbly piece of text: its letter images, their poses and how strongly it wobbles
    letters = make_letters(text, font, color, digit_font)
    return {"letters": letters, "poses": make_poses(letters, style), "style": style, "x": x, "y": y}

def draw_label(label, x, y, align="center"):
    if len(label["letters"]) > 0:               # an empty label (like no message) draws nothing
        draw_wobbly(label["letters"], label["poses"], x, y, align=align)

def rewobble(label):
    # New poses in the label's own style; works for buttons too
    label["poses"] = make_poses(label["letters"], label["style"])

def make_sprite(slots, style="subtle"):
    # Wobbly images: each slot has a few frames to pick from, and a random one shows each tick
    sprite = {"slots": slots, "style": style}
    reanimate(sprite)
    return sprite

def reanimate(sprite):
    # Pick a new frame for every slot, and new poses
    images = []
    for frames in sprite["slots"]:
        images.append(random.choice(frames))
    sprite["letters"] = images
    sprite["poses"] = make_poses(images, sprite["style"])

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
        "frame": 0,                             # which of the three frames is showing
        "poses": make_poses([normal_frames[0]], "subtle"),
        "rect": pygame.Rect(0, 0, 0, 0),
    }

def draw_icon_button(icon, center_x, y):
    can_hover = not game.warning_modal_open and (not game.settings_open or icon is settings_icon)
    if can_hover and icon["rect"].collidepoint(pygame.mouse.get_pos()):
        image = icon["hover_frames"][icon["frame"]]
    else:
        image = icon["frames"][icon["frame"]]
    icon["rect"] = draw_wobbly([image], icon["poses"], center_x, y)

def rounded_box_points(rect, radius=s(14), corner_steps=6, edge_steps=8):
    # Points along a rounded rectangle: a curved arc at each corner,
    # with evenly spaced points along the straight edges in between
    corners = [
        (rect.right - radius, rect.top + radius, -90),
        (rect.right - radius, rect.bottom - radius, 0),
        (rect.left + radius, rect.bottom - radius, 90),
        (rect.left + radius, rect.top + radius, 180),
    ]
    arcs = []
    for cx, cy, start in corners:
        arc = []
        for i in range(corner_steps + 1):
            angle = math.radians(start + 90 * i / corner_steps)
            arc.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
        arcs.append(arc)

    points = []
    for i in range(4):
        points.extend(arcs[i])
        end = arcs[i][-1]
        next_start = arcs[(i + 1) % 4][0]
        for step in range(1, edge_steps):
            t = step / edge_steps
            points.append((end[0] + (next_start[0] - end[0]) * t,
                           end[1] + (next_start[1] - end[1]) * t))
    return points

def jitter_points(points, amount=BOX_WOBBLE):
    jittered = []
    for x, y in points:
        jittered.append((x + random.uniform(-amount, amount),
                         y + random.uniform(-amount, amount)))
    return jittered

def make_box_image(points, rect, fill_color, line_color):
    pad = s(6)
    width = rect.width + pad * 2
    height = rect.height + pad * 2
    big = pygame.Surface((width * BOX_SCALE, height * BOX_SCALE), pygame.SRCALPHA)

    big_points = []
    for x, y in points:
        big_points.append(((x - rect.left + pad) * BOX_SCALE,
                           (y - rect.top + pad) * BOX_SCALE))

    pygame.draw.polygon(big, fill_color, big_points)
    if line_color is not None:
        pygame.draw.lines(big, line_color, True, big_points, s(3) * BOX_SCALE)
        for point in big_points:
            pygame.draw.circle(big, line_color, point, s(3) / 2 * BOX_SCALE)

    return pygame.transform.smoothscale(big, (width, height))

def make_box(rect, fill_color, line_color, radius=s(14), edge_steps=8, wobble=BOX_WOBBLE):
    # A boiling box: its shape, colors and how much it wobbles, plus its current image
    box = {
        "rect": rect,
        "points": rounded_box_points(rect, radius=radius, edge_steps=edge_steps),
        "fill": fill_color,
        "line": line_color,
        "wobble": wobble,
    }
    rejitter(box)
    return box

def rejitter(box):
    # A new wobbly image of the box, in its own colors and wobble amount
    jittered = jitter_points(box["points"], box["wobble"])
    box["image"] = make_box_image(jittered, box["rect"], box["fill"], box["line"])

def draw_box(box):
    screen.blit(box["image"], box["image"].get_rect(center=box["rect"].center))

def tint_image(image, color):
    tinted = image.copy()
    tinted.fill(color, special_flags=pygame.BLEND_RGBA_MULT)
    return tinted

def tint_frames(frames, color):
    tinted = []
    for frame in frames:
        tinted.append(tint_image(frame, color))
    return tinted

def load_frames(folder, name, size):
    frames = []
    for number in range(1, FRAME_COUNT + 1):
        path = str(folder / f"{name}_{number}.png")
        image = pygame.image.load(path).convert_alpha()
        frames.append(pygame.transform.smoothscale(image, size))
    return frames

# =======================================================
# 2.2 - Game functions                                  #
# =======================================================

def start_game(difficulty):
    game.difficulty = difficulty
    game.screen = "game"

    game.range_lowest, game.range_highest, game.max_tries, game.tokens_needed = logic.difficulty_settings(difficulty)
    game.max_digits = logic.max_digits(game.range_lowest, game.range_highest)
    set_game_labels()

    make_entry_box(game.max_digits)
    make_history_box(game.max_tries, game.max_digits)

    game.lives = logic.STARTING_LIVES
    game.tokens = 0
    game.rounds_played = 0
    set_hearts()
    set_tokens()
    next_round()

def set_game_labels():
    labels["difficulty"] = make_label(f"{game.difficulty} mode", tiny_font, MUTED_COLOR, "subtle")
    labels["range"] = make_label(f"({game.range_lowest}-{game.range_highest})", small_heading_font, TEXT_COLOR,
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

def set_tries_label():
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
    images = []
    for position in range(game.max_tries):
        if position < len(game.guesses):
            text = str(game.guesses[position]).center(game.max_digits)
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

def make_history_box(max_tries, max_digits):
    global history_box
    columns = max_tries - max_tries // 2            # the bottom row is the widest
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
            range_labels.append(make_label(f"{below}-{above}", range_label_font, TEXT_COLOR,
                                           x=range_fill.centerx, y=above_y))
        else:
            range_labels.append(make_label(str(below), range_label_font, TEXT_COLOR, x=range_fill.left, y=above_y))
            range_labels.append(make_label(str(above), range_label_font, TEXT_COLOR, x=range_fill.right, y=above_y))
    elif below is not None:
        range_labels.append(make_label(str(below), range_label_font, TEXT_COLOR, x=range_fill.left, y=above_y))
    elif above is not None:
        range_labels.append(make_label(str(above), range_label_font, TEXT_COLOR, x=range_fill.right, y=above_y))

def bar_icons():
    # The icons on the left side of the bar, depending on the screen
    if game.screen == "game":
        return [home_icon, back_icon, restart_icon]
    elif game.screen == "difficulty":
        return [back_icon]
    else:
        return []

def settings_offset():
    # How many pixels the bar has slid up: 0 when closed, the panel height when open
    eased = 1 - (1 - game.settings_slide) ** 2          # fast at first, slowing down at the end
    return round(SETTINGS_PANEL_HEIGHT * eased)

def clicked_bar_icon(pos):
    # Which visible bar icon was clicked, or None
    for icon in bar_icons() + [settings_icon]:
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
    labels["play_again"] = make_label("play again", tiny_font, MUTED_COLOR)

    # See-through layers
    bar_surface.fill(BAR_COLOR)
    warning_modal_overlay.fill(OVERLAY_COLOR)
    settings_panel_surface.fill(BAR_COLOR)

    # Game screen: boxes and setters, rebuilt from the current game
    make_entry_box(game.max_digits)
    make_history_box(game.max_tries, game.max_digits)
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
# 2.4 - Game state class                                #
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

        # Game
        self.lives = logic.STARTING_LIVES
        self.tokens = 0
        self.rounds_played = 0

        # Current round
        self.secret = 0
        self.try_count = 0
        self.guesses = []
        self.round_over = False
        self.typed_guess = ""
        self.message = ""

    def result(self):
        return logic.game_result(self.lives, self.tokens, self.tokens_needed)

    def has_progress(self):
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
    warning_modal_yes_button, warning_modal_no_button,
]

# =======================================================
# 3.9 - Starting values                                 #
# =======================================================

background = None
background_theme = None         # which theme the background was made for
labels = {}                     # every wobbly text, by name; filled in by apply_theme and the setters
sprites = {}                    # every wobbly image, by name
boxes = {}                      # every boiling box, by name
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
    elif action == "difficulty":
        game.screen = "difficulty"
    elif action == "resize":
        restart_program()

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
        if game.screen == "difficulty":
            game.screen = "menu"
        elif game.has_progress():
            open_warning_modal("difficulty", "leave this game?")
        else:
            game.screen = "difficulty"
    elif icon is restart_icon:
        if game.has_progress():
            open_warning_modal("restart", "restart this game?")
        else:
            start_game(game.difficulty)

def click_menu(pos):
    if new_game_button["rect"].collidepoint(pos):
        game.screen = "difficulty"
    elif free_mode_button["rect"].collidepoint(pos):
        print("free mode clicked")
    elif exit_button["rect"].collidepoint(pos):
        game.running = False

def click_difficulty(pos):
    if easy_button["rect"].collidepoint(pos):
        start_game("easy")
    elif normal_button["rect"].collidepoint(pos):
        start_game("normal")
    elif hard_button["rect"].collidepoint(pos):
        start_game("hard")

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

def handle_typing(event):
    if event.unicode.isdigit() and len(game.typed_guess) < game.max_digits:
        set_typed(game.typed_guess + event.unicode)
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
        start_game(game.difficulty)

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
    elif game.screen == "game":
        draw_game()

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

def draw_game():
    # Status: what you're guessing, and how you're doing
    draw_label(labels["heading"], CENTER_X, HEADING_Y)
    draw_label(labels["range"], CENTER_X, RANGE_Y)
    draw_label(labels["difficulty"], CENTER_X, DIFFICULTY_LABEL_Y)
    draw_label(labels["round"], CENTER_X, ROUND_Y)
    draw_label(sprites["hearts"], CENTER_X, HEARTS_Y)
    draw_stacked(sprites["tokens"]["letters"], sprites["tokens"]["poses"], CENTER_X, TOKENS_Y,
                 TOKEN_GAP, TOKEN_ROW_GAP)

    # Play: range bar, message, entry box, space key
    if game.difficulty in RANGE_BAR_MODES:
        draw_range_bar()
    draw_label(labels["message"], CENTER_X, MESSAGE_Y)
    draw_entry()
    if game.round_over:
        draw_space_cue()

    # Record: tries left and the guess history
    draw_label(labels["tries"], CENTER_X, TRIES_Y)
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

    x = BAR_PADDING + BAR_ICON_SIZE // 2
    for icon in bar_icons():
        draw_icon_button(icon, x, icon_y)
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