# Animated backgrounds, built from layers (see base.py)
# main.py only needs make_background(); everything else lives in this folder

from partials.backgrounds.rain import RainBackground
from partials.backgrounds.snow import SnowBackground
from partials.backgrounds.stream import StreamBackground
from partials.backgrounds.blossom import BlossomBackground
from partials.backgrounds.desert import DesertBackground
from partials.backgrounds.home import HomeBackground
from partials.backgrounds.underwater import UnderwaterBackground
from partials.backgrounds.seaside import SeasideBackground
from partials.backgrounds.misty import MistyBackground


# Which background goes with which theme (themes without one use a plain color)
BACKGROUNDS = {
    "rain": RainBackground,
    "snow": SnowBackground,
    "stream": StreamBackground,
    "blossom": BlossomBackground,
    "desert": DesertBackground,
    "home": HomeBackground,
    "underwater": UnderwaterBackground,
    "seaside": SeasideBackground,
    "mountains": MistyBackground,
}

def make_background(theme):
    if theme in BACKGROUNDS:
        return BACKGROUNDS[theme]()
    return None
