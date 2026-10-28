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

# Installed modules
import pygame

# My files
import game_logic as logic
from config import *
from themes import THEMES

# =======================================================
# 1.2 - Colors                                          #
# =======================================================

theme = "plain"
mode = "dark"           # "dark" or "light"

def set_palette(theme, mode):
    global BG_COLOR, TEXT_COLOR, ACCENT_COLOR, FIELD_COLOR, MUTED_COLOR
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

set_palette(theme, mode)

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
    }

def make_label(text, font, color, x, y, style="subtle"):
    letters = make_letters(text, font, color)
    return {"letters": letters, "poses": make_poses(letters, style), "x": x, "y": y, "style": style}

def draw_button(button, y, center_x=CENTER_X, in_modal=False):
    can_hover = game.warning_modal_open == False or in_modal == True
    if can_hover == True and button["rect"].collidepoint(pygame.mouse.get_pos()):
        letters = button["hover_letters"]
    else:
        letters = button["letters"]
    button["rect"] = draw_wobbly(letters, button["poses"], center_x, y)

def make_icon_button(name):
    frames = load_frames(SETTINGS_ICONS_DIR / name, name, (BAR_ICON_SIZE, BAR_ICON_SIZE))
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
    can_hover = game.warning_modal_open == False
    if can_hover == True and icon["rect"].collidepoint(pygame.mouse.get_pos()):
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

def tint_image(image, color):
    tinted = image.copy()
    tinted.fill(color, special_flags=pygame.BLEND_RGBA_MULT)
    return tinted

def tint_frames(frames, color):
    tinted = []
    for frame in frames:
        tinted.append(tint_image(frame, color))
    return tinted

def load_heart_frames(state):
    frames = []
    for number in range(1, 4):
        path = str(HEARTS_DIR / state / f"heart_{state}_{number}.png")
        image = pygame.image.load(path).convert_alpha()
        frames.append(pygame.transform.smoothscale(image, (HEART_SIZE, HEART_SIZE)))
    return frames

def load_frames(folder, name, size):
    frames = []
    for number in range(1, 4):
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
    global difficulty_label_letters, difficulty_label_poses, range_letters, range_poses

    difficulty_label_letters = make_letters(f"{game.difficulty} mode", tiny_font, MUTED_COLOR)
    difficulty_label_poses = make_poses(difficulty_label_letters, "subtle")

    range_letters = make_letters(f"({game.range_lowest}-{game.range_highest})", small_heading_font, TEXT_COLOR,
                                 small_heading_digit_font)
    range_poses = make_poses(range_letters, "normal")

def next_round():
    game.secret = random.randint(game.range_lowest, game.range_highest)
    print(f"number = {game.secret}")

    game.try_count = 0
    set_typed("")
    game.guessed_list.clear()
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
    if result == "game_won":
        set_game_message("you won the game!")
    elif result == "game_lost":
        set_game_message(f"game over! it was {game.secret}")

    print(f"lives: {game.lives}, tokens: {game.tokens}/{game.tokens_needed}")

def set_game_message(text):
    game.message = text
    global message_letters, message_poses
    message_letters = make_letters(text, small_font, TEXT_COLOR, small_digit_font)
    message_poses = make_poses(message_letters, "normal")

def set_typed(text):
    global typed_letters, typed_poses
    game.typed_guess = text
    typed_letters = make_letters(text, typed_font, ACCENT_COLOR)
    typed_poses = make_poses(typed_letters, "typed")

def set_tries_label():
    global tries_letters, tries_poses
    tries_left = game.max_tries - game.try_count

    if tries_left == 1:
        text = "1 try left"
    else:
        text = f"{tries_left} tries left"

    tries_letters = make_letters(text, tiny_font, MUTED_COLOR, tiny_digit_font)
    tries_poses = make_poses(tries_letters, "subtle")

def set_round_label():
    global round_letters, round_poses
    round_number = game.rounds_played + 1
    round_letters = make_letters(f"round {round_number}", tiny_font, TEXT_COLOR, tiny_digit_font)
    round_poses = make_poses(round_letters, "subtle")

def set_hearts():
    global heart_images, heart_poses
    heart_images = make_heart_images()
    heart_poses = make_poses(heart_images)

def make_heart_images():
    images = []
    for position in range(logic.STARTING_LIVES):
        if game.result() == "game_won":
            frames = heart_frames_gold
        elif position < game.lives:
            frames = heart_frames_red
        else:
            frames = heart_frames_empty
        images.append(random.choice(frames))
    return images

def set_tokens():
    global token_images, token_poses
    token_images = make_token_images()
    token_poses = make_poses(token_images)

def make_token_images():
    images = []
    for position in range(game.tokens_needed):
        if position < game.tokens:
            frames = token_frames_filled
        else:
            frames = token_frames_empty
        images.append(random.choice(frames))
    return images

def set_history():
    global history_images, history_poses
    history_images = make_history_images()
    history_poses = make_poses(history_images, "typed")

def make_history_images():
    images = []
    for position in range(game.max_tries):
        if position < len(game.guessed_list):
            text = str(game.guessed_list[position]).center(game.max_digits)
            color = TEXT_COLOR
        else:
            text = HISTORY_EMPTY_SYMBOL * game.max_digits
            color = MUTED_COLOR
        images.append(history_font.render(text, True, color))
    return images

def open_warning_modal(action, question):
    global warning_modal_letters, warning_modal_poses, warning_modal_image

    game.warning_modal_open = True
    game.warning_modal_action = action
    warning_modal_letters = make_letters(question, menu_font, TEXT_COLOR)
    warning_modal_poses = make_poses(warning_modal_letters, "normal")

    warning_modal_image = make_box_image(jitter_points(warning_modal_base_points), warning_modal_panel,
                                        FIELD_COLOR, TEXT_COLOR)

def make_entry_box(max_digits):
    global entry_box, entry_base_points, entry_image
    width = (ENTRY_PADDING + max_digits * typed_char_width
             + ENTER_KEY_GAP + ENTER_KEY_SIZE[0] + ENTER_KEY_INSET)

    entry_box = pygame.Rect(0, 0, width, ENTRY_BOX_HEIGHT)
    entry_box.center = (CENTER_X, ENTRY_BOX_Y)
    entry_base_points = rounded_box_points(entry_box)
    entry_image = make_box_image(jitter_points(entry_base_points), entry_box, FIELD_COLOR, TEXT_COLOR)

def make_history_box(max_tries, max_digits):
    global history_box, history_base_points, history_image
    columns = max_tries - max_tries // 2            # the bottom row is the widest
    slot_width = history_font.size("0" * max_digits)[0]
    slot_height = history_font.get_height()

    width = columns * slot_width + (columns - 1) * HISTORY_GAP + HISTORY_PADDING * 2
    height = slot_height * 2 + HISTORY_ROW_GAP + HISTORY_PADDING * 2

    history_box = pygame.Rect(0, 0, width, height)
    history_box.midtop = (CENTER_X, HISTORY_Y - HISTORY_PADDING)
    history_base_points = rounded_box_points(history_box)
    history_image = make_box_image(jitter_points(history_base_points), history_box,
                                   HISTORY_BOX_COLOR, None)

def make_range_track():
    global range_track, range_track_points, range_track_image
    range_track = pygame.Rect((0, 0), RANGE_BAR_SIZE)
    range_track.midtop = (CENTER_X, RANGE_BAR_Y)
    range_track_points = rounded_box_points(range_track, radius=RANGE_BAR_SIZE[1] // 2)
    range_track_image = make_box_image(jitter_points(range_track_points, RANGE_BAR_WOBBLE), range_track,
                                       (0, 0, 0, 0), MUTED_COLOR)

def make_range_fill():
    global range_fill, range_fill_points, range_fill_image
    low, high = game.narrowed_range()
    total = game.range_highest - game.range_lowest + 1      # how many numbers the bar covers

    left = range_track.left + (low - game.range_lowest) * range_track.width / total
    right = range_track.left + (high - game.range_lowest + 1) * range_track.width / total

    width = max(round(right - left), 2)                     # never thinner than 2 px
    range_fill = pygame.Rect(round(left), range_track.top, width, range_track.height)
    radius = min(range_track.height // 2, width // 2)
    range_fill_points = rounded_box_points(range_fill, radius=radius)
    range_fill_image = make_box_image(jitter_points(range_fill_points, RANGE_BAR_WOBBLE), range_fill,
                                      RANGE_FILL_COLOR, None)

    set_range_labels()

def set_range_labels():
    global range_labels
    below_y = range_track.bottom + RANGE_LABEL_GAP
    above_y = range_track.top - RANGE_LABEL_GAP - range_label_font.get_height()

    # Ends of the track
    range_labels = [
        make_label(str(game.range_lowest), range_label_font, MUTED_COLOR, range_track.left, below_y),
        make_label(str(game.range_highest), range_label_font, MUTED_COLOR, range_track.right, below_y),
    ]

    # Round over: the fill has shrunk to the secret, so show the answer
    if game.round_over == True:
        range_labels.append(make_label(str(game.secret), range_label_font, TEXT_COLOR, range_fill.centerx, above_y))
        return

    # The closest guesses on each side, at the edges of the fill
    below, above = game.closest_guesses()

    if below is not None and above is not None:
        below_width = range_label_font.size(str(below))[0]
        above_width = range_label_font.size(str(above))[0]
        needed = (below_width + above_width) / 2 + RANGE_LABEL_MIN_GAP

        if range_fill.width < needed:
            range_labels.append(make_label(f"{below}-{above}", range_label_font, TEXT_COLOR, range_fill.centerx, above_y))
        else:
            range_labels.append(make_label(str(below), range_label_font, TEXT_COLOR, range_fill.left, above_y))
            range_labels.append(make_label(str(above), range_label_font, TEXT_COLOR, range_fill.right, above_y))
    elif below is not None:
        range_labels.append(make_label(str(below), range_label_font, TEXT_COLOR, range_fill.left, above_y))
    elif above is not None:
        range_labels.append(make_label(str(above), range_label_font, TEXT_COLOR, range_fill.right, above_y))

def bar_icons():
    # The icons on the left side of the bar, depending on the screen
    if game.screen == "game":
        return [home_icon, back_icon, restart_icon]
    elif game.screen == "difficulty":
        return [back_icon]
    else:
        return []

def clicked_bar_icon(pos):
    # Which visible bar icon was clicked, or None
    for icon in bar_icons() + [settings_icon]:
        if icon["rect"].collidepoint(pos):
            return icon
    return None

def apply_theme(new_theme, new_mode):
    # Switch to a theme and remake everything that has a color
    global theme, mode
    global title_letters, title_poses, difficulty_title_letters, difficulty_title_poses
    global heading_letters, heading_poses, cursor_on, cursor_off, cursor_poses
    global continue_letters, continue_poses, play_again_letters, play_again_poses
    global token_frames_filled, token_frames_empty, enter_frames, space_frames, enter_image, space_image
    global enter_poses, space_poses

    theme = new_theme
    mode = new_mode
    set_palette(theme, mode)

    # Titles and headings
    title_letters = make_letters("guesstimate!", title_font, TEXT_COLOR)
    title_poses = make_poses(title_letters)
    difficulty_title_letters = make_letters("pick a difficulty", menu_font, TEXT_COLOR)
    difficulty_title_poses = make_poses(difficulty_title_letters, "normal")
    heading_letters = make_letters("guess a number", small_heading_font, TEXT_COLOR)
    heading_poses = make_poses(heading_letters, "normal")

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
    enter_image = random.choice(enter_frames)
    space_image = random.choice(space_frames)
    enter_poses = make_poses([enter_image], "subtle")
    space_poses = make_poses([space_image], "subtle")

    # Cursor and small labels
    cursor_on = typed_font.render(CURSOR_SYMBOL, True, MUTED_COLOR)
    cursor_off = pygame.Surface(cursor_on.get_size(), pygame.SRCALPHA)
    cursor_poses = make_poses([cursor_on], "typed")
    continue_letters = make_letters("next round", tiny_font, MUTED_COLOR)
    continue_poses = make_poses(continue_letters, "subtle")
    play_again_letters = make_letters("play again", tiny_font, MUTED_COLOR)
    play_again_poses = make_poses(play_again_letters, "subtle")

    # See-through layers
    bar_surface.fill(BAR_COLOR)
    warning_modal_overlay.fill(OVERLAY_COLOR)

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

# =======================================================
# 2.3 - Game state class                                #
# =======================================================

class GameState:
    def __init__(self):

        # Screen state
        self.screen = "menu"
        self.warning_modal_open = False
        self.warning_modal_action = ""

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
        self.guessed_list = []
        self.round_over = False
        self.typed_guess = ""
        self.message = ""

    def result(self):
        return logic.game_result(self.lives, self.tokens, self.tokens_needed)

    def has_progress(self):
        return logic.has_progress(self.lives, self.tokens, self.tokens_needed, self.rounds_played, self.try_count)

    def narrowed_range(self):
        if self.round_over == True:
            return self.secret, self.secret
        return logic.narrowed_range(self.guessed_list, self.secret, self.range_lowest, self.range_highest)

    def closest_guesses(self):
        return logic.closest_guesses(self.guessed_list, self.secret)

### =====================================================
### 3 - SCREEN SETUP                                    #
### 3 - SCREEN SETUP                                    #
### 3 - SCREEN SETUP                                    #
### =====================================================

# =======================================================
# 3.1 - Font settings                                   #
# =======================================================

title_font = pygame.font.Font(FONT_PATH, s(40))
# heading_font = pygame.font.Font(FONT_PATH, s(30))      # unused for now
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

heart_frames_red = load_heart_frames("red")
heart_frames_gold = load_heart_frames("gold")
heart_frames_empty = load_heart_frames("empty")

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
# 3.7 - Warning modal setup                             #
# =======================================================

warning_modal_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

warning_modal_panel = pygame.Rect((0, 0), WARNING_MODAL_SIZE)
warning_modal_panel.center = (CENTER_X, HEIGHT // 2)
warning_modal_base_points = rounded_box_points(warning_modal_panel, radius=s(16), edge_steps=16)
warning_modal_image = make_box_image(jitter_points(warning_modal_base_points), warning_modal_panel,
                                        FIELD_COLOR, TEXT_COLOR)

# Filled in by open_warning_modal
warning_modal_letters = []
warning_modal_poses = []

warning_modal_yes_button = make_button("yes")
warning_modal_no_button = make_button("no")

all_buttons = [
    new_game_button, free_mode_button, exit_button,
    easy_button, normal_button, hard_button,
    warning_modal_yes_button, warning_modal_no_button,
]

# =======================================================
# 3.8 - Starting values                                 #
# =======================================================

apply_theme(theme, mode)

### =====================================================
### 4 - MAIN LOOP                                       #
### 4 - MAIN LOOP                                       #
### 4 - MAIN LOOP                                       #
### =====================================================

# =======================================================
# 4.1 - Loop setup                                      #
# =======================================================

last_wobble = 0
running = True

while running:

    # ===================================================
    # 4.2 - Handle events                               #
    # ===================================================

    for event in pygame.event.get():

        # Window close
        if event.type == pygame.QUIT:
            if game.screen == "game" and game.has_progress() == True and game.warning_modal_open == False:
                open_warning_modal("quit", "quit the game?")
            else:
                running = False

        # Mouse clicks
        if event.type == pygame.MOUSEBUTTONDOWN:
            clicked_icon = clicked_bar_icon(event.pos)

            if game.warning_modal_open == True:
                if warning_modal_yes_button["rect"].collidepoint(event.pos):
                    game.warning_modal_open = False
                    if game.warning_modal_action == "menu":
                        game.screen = "menu"
                    elif game.warning_modal_action == "quit":
                        running = False
                    elif game.warning_modal_action == "restart":
                        start_game(game.difficulty)
                    elif game.warning_modal_action == "difficulty":
                        game.screen = "difficulty"
                elif warning_modal_no_button["rect"].collidepoint(event.pos):
                    game.warning_modal_open = False

            elif clicked_icon is settings_icon:
                print("settings clicked")              # the panel comes later
            elif clicked_icon is home_icon:
                if game.has_progress() == True:
                    open_warning_modal("menu", "leave this game?")
                else:
                    game.screen = "menu"
            elif clicked_icon is back_icon:
                if game.screen == "difficulty":
                    game.screen = "menu"
                elif game.has_progress() == True:
                    open_warning_modal("difficulty", "leave this game?")
                else:
                    game.screen = "difficulty"
            elif clicked_icon is restart_icon:
                if game.has_progress() == True:
                    open_warning_modal("restart", "restart this game?")
                else:
                    start_game(game.difficulty)

            elif game.screen == "menu":
                if new_game_button["rect"].collidepoint(event.pos):
                    game.screen = "difficulty"
                elif free_mode_button["rect"].collidepoint(event.pos):
                    print("free mode clicked")
                elif exit_button["rect"].collidepoint(event.pos):
                    running = False
            elif game.screen == "difficulty":
                if easy_button["rect"].collidepoint(event.pos):
                    start_game("easy")
                elif normal_button["rect"].collidepoint(event.pos):
                    start_game("normal")
                elif hard_button["rect"].collidepoint(event.pos):
                    start_game("hard")

        # Keyboard
        if event.type == pygame.KEYDOWN and game.screen == "game" and game.round_over == False and game.warning_modal_open == False:
            if event.unicode.isdigit() and len(game.typed_guess) < game.max_digits:
                set_typed(game.typed_guess + event.unicode)
            elif event.key == pygame.K_BACKSPACE:
                set_typed(game.typed_guess[:-1])
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                result = logic.check_guess(game.typed_guess, game.secret, game.range_lowest, game.range_highest, game.guessed_list)
                set_typed("")

                if result in ("too high", "too low", "correct"):
                    game.try_count += 1
                    set_tries_label()
                    set_history()
                    make_range_fill()

                if result == "invalid":
                    set_game_message("type a number first!")
                elif result == "out of range":
                    set_game_message("out of range!")
                elif result == "repeat":
                    set_game_message("already guessed!")
                elif result == "too high":
                    set_game_message("too high!")
                elif result == "too low":
                    set_game_message("too low!")
                else:
                    set_game_message("correct!")
                    end_round(True)

                if result != "correct" and game.try_count == game.max_tries:
                    set_game_message(f"out of tries! it was {game.secret}...")
                    end_round(False)

        # Space: move on once a round is over
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and game.screen == "game" and game.round_over == True and game.warning_modal_open == False:
            if game.result() == "playing":
                next_round()
            else:
                start_game(game.difficulty)

        # L switches between light and dark mode
        if event.type == pygame.KEYDOWN and event.key == pygame.K_l and game.warning_modal_open == False:
            if mode == "dark":
                apply_theme(theme, "light")
            else:
                apply_theme(theme, "dark")

    # ===================================================
    # 4.3 - Update                                      #
    # ===================================================

    now = pygame.time.get_ticks()
    if now - last_wobble >= WOBBLE_INTERVAL and game.warning_modal_open == False:

        # Buttons
        for button in all_buttons:
            button["poses"] = make_poses(button["letters"])

        # Bottom bar icons
        for icon in all_icons:
            icon["frame"] = random.randrange(3)
            icon["poses"] = make_poses([icon["frames"][0]], "subtle")

        # Menu
        title_poses = make_poses(title_letters)

        # Difficulty screen
        difficulty_title_poses = make_poses(difficulty_title_letters, "normal")

        # Game screen
        heading_poses = make_poses(heading_letters, "normal")
        range_poses = make_poses(range_letters, "normal")
        difficulty_label_poses = make_poses(difficulty_label_letters, "subtle")
        round_poses = make_poses(round_letters, "subtle")

        heart_images = make_heart_images()
        heart_poses = make_poses(heart_images)

        token_images = make_token_images()
        token_poses = make_poses(token_images)

        history_poses = make_poses(history_images, "typed")

        tries_poses = make_poses(tries_letters, "subtle")

        entry_points = jitter_points(entry_base_points)
        entry_image = make_box_image(entry_points, entry_box, FIELD_COLOR, TEXT_COLOR)

        history_image = make_box_image(jitter_points(history_base_points), history_box,
                                       HISTORY_BOX_COLOR, None)

        range_track_image = make_box_image(jitter_points(range_track_points, RANGE_BAR_WOBBLE), range_track,
                                           (0, 0, 0, 0), MUTED_COLOR)

        range_fill_image = make_box_image(jitter_points(range_fill_points, RANGE_BAR_WOBBLE), range_fill,
                                          RANGE_FILL_COLOR, None)

        for label in range_labels:
            label["poses"] = make_poses(label["letters"], label["style"])

        typed_poses = make_poses(typed_letters, "typed")
        cursor_poses = make_poses([cursor_on], "typed")

        enter_image = random.choice(enter_frames)
        enter_poses = make_poses([enter_image], "subtle")

        space_image = random.choice(space_frames)
        space_poses = make_poses([space_image], "subtle")
        continue_poses = make_poses(continue_letters, "subtle")
        play_again_poses = make_poses(play_again_letters, "subtle")

        message_poses = make_poses(message_letters, "normal")

        # Warning modal
        warning_modal_poses = make_poses(warning_modal_letters, "normal")

        last_wobble = now

    # ===================================================
    # 4.4 - Draw                                        #
    # ===================================================

    screen.fill(BG_COLOR)

    if game.screen == "menu":
        draw_wobbly(title_letters, title_poses, CENTER_X, TITLE_Y)

        draw_button(new_game_button, NEW_GAME_Y)
        draw_button(free_mode_button, FREE_MODE_Y)
        draw_button(exit_button, EXIT_Y)

    if game.screen == "difficulty":
        draw_wobbly(difficulty_title_letters, difficulty_title_poses, CENTER_X, TITLE_Y)

        draw_button(easy_button, EASY_Y)
        draw_button(normal_button, NORMAL_Y)
        draw_button(hard_button, HARD_Y)

    if game.screen == "game":
        draw_wobbly(heading_letters, heading_poses, CENTER_X, HEADING_Y)
        draw_wobbly(range_letters, range_poses, CENTER_X, RANGE_Y)
        draw_wobbly(difficulty_label_letters, difficulty_label_poses, CENTER_X, DIFFICULTY_LABEL_Y)
        draw_wobbly(round_letters, round_poses, CENTER_X, ROUND_Y)
        draw_wobbly(heart_images, heart_poses, CENTER_X, HEARTS_Y)
        draw_stacked(token_images, token_poses, CENTER_X, TOKENS_Y, TOKEN_GAP, TOKEN_ROW_GAP)

        if game.difficulty in RANGE_BAR_MODES:
            screen.blit(range_fill_image, range_fill_image.get_rect(center=range_fill.center))
            screen.blit(range_track_image, range_track_image.get_rect(center=range_track.center))
            for label in range_labels:
                draw_wobbly(label["letters"], label["poses"], label["x"], label["y"])

        screen.blit(entry_image, entry_image.get_rect(center=entry_box.center))

        can_type = game.round_over == False and game.warning_modal_open == False and len(game.typed_guess) < game.max_digits

        line_letters = typed_letters
        line_poses = typed_poses
        if can_type == True:
            if (now // CURSOR_BLINK) % 2 == 0:
                cursor_image = cursor_on
            else:
                cursor_image = cursor_off
            line_letters = typed_letters + [cursor_image]
            line_poses = typed_poses + cursor_poses

        if len(line_letters) > 0:
            draw_wobbly(line_letters, line_poses, entry_box.left + ENTRY_PADDING,
                    entry_box.centery - typed_font.get_height() // 2, align="left")

        if game.typed_guess != "" and game.round_over == False:
            enter_x = entry_box.right - ENTER_KEY_INSET - ENTER_KEY_SIZE[0] // 2
            enter_y = entry_box.centery - ENTER_KEY_SIZE[1] // 2
            draw_wobbly([enter_image], enter_poses, enter_x, enter_y)

        if game.round_over == True:
            if game.result() == "playing":
                label_letters, label_poses = continue_letters, continue_poses
            else:
                label_letters, label_poses = play_again_letters, play_again_poses

            space_y = entry_box.bottom + SPACE_BAR_KEY_GAP
            draw_wobbly([space_image], space_poses, CENTER_X, space_y)
            draw_wobbly(label_letters, label_poses, CENTER_X, space_y + SPACE_BAR_KEY_SIZE[1] + SPACE_BAR_KEY_LABEL_GAP)

        if len(message_letters) > 0:
            draw_wobbly(message_letters, message_poses, CENTER_X, MESSAGE_Y)

        draw_wobbly(tries_letters, tries_poses, CENTER_X, TRIES_Y)
        screen.blit(history_image, history_image.get_rect(center=history_box.center))
        draw_stacked(history_images, history_poses, CENTER_X, HISTORY_Y, HISTORY_GAP, HISTORY_ROW_GAP)

    # Bottom bar, on every screen
    bar_top = HEIGHT - BAR_HEIGHT
    icon_y = bar_top + (BAR_HEIGHT - BAR_ICON_SIZE) // 2
    screen.blit(bar_surface, (0, bar_top))

    x = BAR_PADDING + BAR_ICON_SIZE // 2
    for icon in bar_icons():
        draw_icon_button(icon, x, icon_y)
        x += BAR_ICON_SIZE + BAR_ICON_GAP

    draw_icon_button(settings_icon, WIDTH - BAR_PADDING - BAR_ICON_SIZE // 2, icon_y)

    # Warning modal drawn last so it sits on top of everything
    if game.warning_modal_open == True:
        screen.blit(warning_modal_overlay, (0, 0))
        screen.blit(warning_modal_image, warning_modal_image.get_rect(center=warning_modal_panel.center))

        draw_wobbly(warning_modal_letters, warning_modal_poses, CENTER_X, warning_modal_panel.top + WARNING_QUESTION_OFFSET)

        draw_button(warning_modal_yes_button, warning_modal_panel.top + WARNING_YES_OFFSET, in_modal=True)
        draw_button(warning_modal_no_button, warning_modal_panel.top + WARNING_NO_OFFSET, in_modal=True)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()