# Settings that stay the same while the game runs:
# window size, file paths, sizes, positions and wobble styles


# =======================================================
# 1.1 - Imports                                         #
# =======================================================

import json

from pathlib import Path

import pygame

# =======================================================
# 1.2 - Saved settings                                    #
# =======================================================

BASE_DIR = Path(__file__).parent.parent     # the project folder: one up from game/
SETTINGS_PATH = BASE_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "theme": "plain",
    "mode": "dark",
    "window size": "auto",
    "free from": 1,
    "free to": 100,
    "free range bar": True,
    "free history": True,
}

def load_settings():
    settings = dict(DEFAULT_SETTINGS)           # a copy, so the defaults stay untouched
    try:
        with open(SETTINGS_PATH) as file:
            settings.update(json.load(file))
    except (FileNotFoundError, json.JSONDecodeError):
        pass                                    # no file yet, or a broken one: keep the defaults
    return settings

def save_settings(settings):
    with open(SETTINGS_PATH, "w") as file:
        json.dump(settings, file, indent=4)

settings = load_settings()

# =======================================================
# 1.3 - Window                                          #
# =======================================================

pygame.init()

WINDOW_SIZES = {
    "small": (400, 600),
    "medium": (440, 660),
    "large": (520, 780),
}

BASE_WIDTH = 440                # the layout is designed at the medium size
FORCE_WINDOW_SIZE = None        # set to "small", "medium" or "large" to test a size
SCREEN_MARGIN = 120             # room for the taskbar and the window's title bar

def pick_window_size():
    if FORCE_WINDOW_SIZE is not None:
        return FORCE_WINDOW_SIZE

    if settings["window size"] in WINDOW_SIZES:
        return settings["window size"]
    
    desktop_height = pygame.display.get_desktop_sizes()[0][1]
    chosen = "small"
    for name in ("small", "medium", "large"):
        if WINDOW_SIZES[name][1] <= desktop_height - SCREEN_MARGIN:
            chosen = name
    return chosen

window_size = pick_window_size()
WIDTH, HEIGHT = WINDOW_SIZES[window_size]
CENTER_X = WIDTH // 2
FPS = 60

UI_SCALE = WIDTH / BASE_WIDTH   # 1.0 at medium, smaller or larger otherwise

def s(value):
    # Scale a size or position from the medium layout to the current window
    return round(value * UI_SCALE)

# =======================================================
# 1.4 - Paths                                           #
# =======================================================

FONT_PATH = str(BASE_DIR / "assets" / "font" / "ShortStack.ttf")
DIGIT_FONT_PATH = str(BASE_DIR / "assets" / "font" / "SometypeMono.ttf")

ENTER_KEY_DIR = BASE_DIR / "assets" / "img" / "keys" / "enter_key"
SPACE_BAR_KEY_DIR = BASE_DIR / "assets" / "img" / "keys" / "space_bar_key"

HEARTS_DIR = BASE_DIR / "assets" / "img" / "hearts"
TOKENS_FILLED_DIR = BASE_DIR / "assets" / "img" / "tokens" / "filled"
TOKENS_EMPTY_DIR = BASE_DIR / "assets" / "img" / "tokens" / "empty"

SETTINGS_PANEL_ICONS_DIR = BASE_DIR / "assets" / "img" / "settings_panel"

# =======================================================
# 1.5 - Sizing                                          #
# =======================================================

WARNING_MODAL_SIZE = (s(300), s(180))
SPACE_BAR_KEY_SIZE = (s(50), s(20))
HEART_SIZE = (s(26), s(26))
TOKEN_SIZE = (s(30), s(30))

# Range bar
RANGE_BAR_SIZE = (s(300), s(14))
RANGE_LABEL_FONT_SIZE = s(14)

# Entry box
ENTER_KEY_SIZE = (s(24), s(30))
ENTRY_BOX_HEIGHT = s(56)

# Guess history
HISTORY_FONT_SIZE = s(20)
HISTORY_PADDING = s(10)                 # space between the box edge and the slots

# Bottom bar
BAR_HEIGHT = s(44)
BAR_ICON_SIZE = s(26)

SETTINGS_PANEL_HEIGHT = s(200)

# =======================================================
# 1.6 - Layout (positions)                              #
# =======================================================

# Menu screen
TITLE_Y = s(60)

NEW_GAME_Y = s(200)
FREE_MODE_Y = s(275)
EXIT_Y = s(350)

# Difficulty screen
EASY_Y = s(160)
NORMAL_Y = s(220)
HARD_Y = s(280)

# Free mode setup screen
FREE_BOX_Y = s(170)                     # center of the two number boxes
FREE_BOX_GAP = s(85)                    # from the middle of the window to each box's center
FREE_BOX_CHARS = 6                      # room inside a box: a minus, 4 digits and the cursor
FREE_LABEL_GAP = s(6)                   # space between a box and its label above it
FREE_MESSAGE_Y = s(230)
FREE_START_Y = s(420)
FREE_TOGGLE_Y = s(280)                  # top of the first toggle row
FREE_TOGGLE_GAP = s(40)                 # from one toggle row to the next
FREE_TOGGLE_LABEL_X = CENTER_X - s(110) # left edge of the toggle labels
FREE_TOGGLE_VALUE_X = CENTER_X + s(90)  # center of the on/off values

# Game screen
HEADING_Y = s(10)
RANGE_Y = s(40)
DIFFICULTY_LABEL_Y = s(70)

ROUND_Y = s(125)
HEARTS_Y = s(140)
TOKENS_Y = s(170)
TOKEN_GAP = s(6)                        # space between tokens in a row
TOKEN_ROW_GAP = s(4)                    # space between the two rows

RANGE_BAR_Y = s(260)
RANGE_BAR_MODES = ("easy", "normal")    # difficulties that show the range bar
RANGE_LABEL_GAP = s(3)                  # space between the bar and its labels
RANGE_LABEL_MIN_GAP = s(6)              # merge the bound labels if they'd get closer than this

MESSAGE_Y = s(285)
ENTRY_BOX_Y = s(345)                    # center of the entry box
ENTER_KEY_INSET = s(10)                 # space between the enter key icon and the entry box's right edge
ENTER_KEY_GAP = s(6)                    # space between the last possible digit and the enter key icon
ENTRY_PADDING = s(10)                   # space between the entry box's left edge and the first digit
SPACE_BAR_KEY_GAP = s(14)               # space between the entry box and the space key
SPACE_BAR_KEY_LABEL_GAP = s(4)          # space between the space key and its label

TRIES_Y = s(475)                        # small label just above the guess history

HISTORY_Y = s(510)                      # top of the guess history
HISTORY_GAP = s(12)                     # space between slots in a row
HISTORY_ROW_GAP = s(6)                  # space between the two rows

# Results screen
RESULTS_TITLE_Y = s(70)
RESULTS_LINES_Y = s(150)                # top of the first stats line
RESULTS_LINE_GAP = s(32)                # from one stats line to the next
RESULTS_AGAIN_Y = s(370)
RESULTS_BACK_Y = s(425)
RESULTS_MENU_Y = s(480)

# Bottom bar
BAR_PADDING = s(16)                     # space between the window edge and the outer icons
BAR_ICON_GAP = s(12)                    # space between icons

SETTINGS_SLIDE_TIME = 250               # milliseconds for the bar to slide fully open or closed
SETTINGS_ROW_TOP = s(24)                # from the panel's top edge to the first row
SETTINGS_ROW_GAP = s(40)                # from one row to the next
SETTINGS_LABEL_X = s(30)                # left edge of the labels
SETTINGS_VALUE_X = WIDTH - s(110)       # center of the values
SETTINGS_ARROW_GAP = s(65)              # from a value's center to each of its arrows

# Warning modal offsets (measured down from the panel's top edge)
WARNING_QUESTION_OFFSET = s(30)
WARNING_YES_OFFSET = s(90)
WARNING_NO_OFFSET = s(130)

# =======================================================
# 1.7 - Wobble effect                                   #
# =======================================================

WOBBLE_INTERVAL = 300           # milliseconds per pose
FRAME_COUNT = 3                 # how many drawn frames each animated image has

# Wobble styles: (max pixels a letter can move, max degrees it can tilt)
WOBBLE_STYLES = {
    "strong": (1, 6),
    "normal": (1, 4),
    "subtle": (0, 3),
    "typed": (0, 2),
}

BOX_WOBBLE = 1.5 * UI_SCALE     # max pixels the box outline can shift
BOX_SCALE = 3                   # how much bigger boxes are drawn before smoothing

RANGE_BAR_WOBBLE = 0.6 * UI_SCALE   # the thin range bar boils more gently

# =======================================================
# 1.8 - Input cursor                                    #
# =======================================================

CURSOR_SYMBOL = "_"
CURSOR_BLINK = 500

HISTORY_EMPTY_SYMBOL = "_"          # repeated to fill an empty slot