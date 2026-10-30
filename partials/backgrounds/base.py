# The building blocks every background is made of
#
# A background is a stack of layers, drawn back to front.
# Each layer looks after one thing (the water, the ripples, the rain...)
# and has the same three methods the game already calls on a background:
#   update(dt)                  move things along; dt is milliseconds since the last frame
#   wobble()                    called on every wobble tick, for the hand-drawn boil
#   draw(surface, palette)      paint itself
#
# Layers and backgrounds can also own swells: numbers that slowly wax and wane
# on their own (see Swell in helpers.py). Make them with self.swell(...);
# they're kept moving for you, so just read .value when you need it

import pygame

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

    def __init__(self, view=None):
        self.layers = []
        self.view = view if view is not None else Perspective()

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

    def color_at(self, palette, y):
        # The color behind things at height y, so fading things can fade into it.
        # The back layer decides if it knows how; otherwise it's the plain background color
        if self.layers and hasattr(self.layers[0], "color_at"):
            return self.layers[0].color_at(palette, y)
        return pygame.Color(palette["bg"])
