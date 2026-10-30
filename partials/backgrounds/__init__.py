# Animated backgrounds, built from layers (see base.py)
# main.py only needs make_background(); everything else lives in this folder

from partials.backgrounds.rain import RainBackground


# Which background goes with which theme (themes without one use a plain color)
BACKGROUNDS = {
    "rain": RainBackground,
}

def make_background(theme):
    if theme in BACKGROUNDS:
        return BACKGROUNDS[theme]()
    return None
