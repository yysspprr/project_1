# The building blocks every background is made of
#
# A background is a stack of layers, drawn back to front.
# Each layer looks after one thing (the water, the ripples, the rain...)
# and has the same three methods the game already calls on a background:
#   update(dt)                  move things along; dt is milliseconds since the last frame
#   wobble()                    called on every wobble tick, for the hand-drawn boil
#   draw(surface, palette)      paint itself
#
# The background keeps a shared weather report (self.weather), so layers can react
# to the same conditions without knowing about each other:
#   "storm"     0 = calm, 1 = as wild as it gets
#   "wind"      1 = a normal breeze
#   "light"     1 = normal daylight or moonlight; lower when it clouds over
#
# There's also a quiet zone: the column in the middle where the game's text and boxes sit.
# Busy things fade there, so the game stays easy to read. Layers ask the background
#   keep(x)             how much of something at x survives: 1 at the sides, QUIET in the middle
#   keep(x, gentle)     the same, but only part of the way (gentle 0-1), for solid things
#   margin_x()          a random spot at the sides, for things that should stay out of the way
#
# Layers and backgrounds can also own swells: numbers that slowly wax and wane
# on their own (see Swell in helpers.py). Make them with self.swell(...);
# they're kept moving for you, so just read .value when you need it

import random

import pygame

from partials.config import WIDTH, CENTER_X, RANGE_BAR_SIZE, s
from partials.backgrounds.perspective import Perspective
from partials.backgrounds.helpers import Swell


class SwellOwner:
    # Shared by layers and backgrounds: a list of swells, all moved along together

    def swell(self, low, high, glide_time, start=None):
        if not hasattr(self, "swells"):
            self.swells = []
        new = Swell(low, high, glide_time, start)
        self.swells.append(new)
        return new

    def update_swells(self, dt):
        for swell in getattr(self, "swells", []):
            swell.update(dt)


class Layer(SwellOwner):
    # A layer that does nothing: real layers replace the methods they need

    def __init__(self, scene):
        self.scene = scene          # the background this layer belongs to, so layers can reach each other

    def update(self, dt):
        pass

    def wobble(self):
        pass

    def draw(self, surface, palette):
        pass


class LayeredBackground(SwellOwner):
    # Runs a list of layers: the first one added is drawn first (at the back).
    # All layers share one perspective (self.view), so they agree on what's near and far

    QUIET = 0.3                         # how much busy detail survives behind the game's text (0-1)
    QUIET_WIDTH = RANGE_BAR_SIZE[0] // 2  # half the quiet column's width: the widest thing in the game
    QUIET_FEATHER = s(40)               # its soft edges, so you can't see where it starts

    def __init__(self, view=None):
        self.layers = []
        self.view = view if view is not None else Perspective()
        self.weather = {"storm": 0, "wind": 1, "light": 1}

    def add(self, layer):
        self.layers.append(layer)
        return layer                # handy: self.ripples = self.add(Ripples(self))

    def update(self, dt):
        self.update_swells(dt)
        for layer in self.layers:
            layer.update_swells(dt)
            layer.update(dt)

    def wobble(self):
        for layer in self.layers:
            layer.wobble()

    def draw(self, surface, palette):
        for layer in self.layers:
            layer.draw(surface, palette)

    def keep(self, x, gentle=1):
        # How much of something at x survives the quiet zone
        inside = (self.QUIET_WIDTH + self.QUIET_FEATHER - abs(x - CENTER_X)) / self.QUIET_FEATHER
        inside = max(0, min(1, inside))
        return 1 - (1 - self.QUIET) * inside * gentle

    def margin_x(self):
        # A random x in the left or right margin, outside the quiet zone
        edge = CENTER_X - self.QUIET_WIDTH
        x = random.uniform(0, max(edge, 1))
        return x if random.random() < 0.5 else WIDTH - x

    def color_at(self, palette, y):
        # The color behind things at height y, so fading things can fade into it.
        # Layers that paint a backdrop (water, sky...) have a color_at of their own and
        # answer None for heights they don't cover; the front-most one that answers wins
        for layer in reversed(self.layers):
            if hasattr(layer, "color_at"):
                color = layer.color_at(palette, y)
                if color is not None:
                    return color
        return pygame.Color(palette["bg"])
