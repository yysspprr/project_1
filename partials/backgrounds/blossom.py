# The blossom theme's background: a spring garden in the East-Asian style under cherry
# blossom, seen from a low veranda, with a pagoda on the misty hills beyond

import math

import random

from partials.config import ROUND_Y, WIDTH, s
from partials.backgrounds.base import LayeredBackground
from partials.backgrounds.perspective import Perspective
from partials.backgrounds.sky import Sky
from partials.backgrounds.garden import MistyHills, Pagoda, GardenPond, StoneLantern, BlossomTree, BlossomBranch, Petals


class BlossomBackground(LayeredBackground):

    # The same horizon as the rain and snow themes, but a shallower garden: it doesn't
    # stretch as far away
    HORIZON = ROUND_Y - s(5)
    FAR_SCALE = 0.3

    # Things that wax and wane on their own: (lowest, highest), and milliseconds to change
    BREEZE = (0.3, 1.3)
    BREEZE_TIME = (6000, 14000)
    PETALFALL = (0.35, 1)           # share of the most petals that are falling
    PETALFALL_TIME = (8000, 18000)
    LIGHT = (0.7, 1.15)
    LIGHT_TIME = (7000, 16000)

    # Gusts: now and then the wind picks up for a moment and sends the petals swirling
    GUST_WAIT = (12000, 30000)      # milliseconds between gusts at a normal breeze
    GUST_TIME = 3200                # how long one lasts, rising and falling
    GUST_STRENGTH = 1.6             # how much a gust adds to the wind at its peak

    def __init__(self):
        super().__init__(Perspective(far_scale=self.FAR_SCALE, horizon=self.HORIZON))
        self.breeze = self.swell(*self.BREEZE, self.BREEZE_TIME)
        self.petalfall = self.swell(*self.PETALFALL, self.PETALFALL_TIME)
        self.light = self.swell(*self.LIGHT, self.LIGHT_TIME)
        self.gust_wait = random.randint(*self.GUST_WAIT)
        self.gust_age = None        # how far into a gust we are, or None between gusts
        self.update_weather()

        # Back to front: sky, hills, the pagoda, the garden and its pond, trees at the sides,
        # the stone lantern, the branch, then falling petals
        self.sky = self.add(Sky(self))
        self.hills = self.add(MistyHills(self))
        self.pagoda = self.add(Pagoda(self, self.hills))
        self.garden = self.add(GardenPond(self))
        self.trees = [self.add(BlossomTree(self, WIDTH - s(4), s(262), s(70)))]
        self.lantern = self.add(StoneLantern(self))
        self.branch = self.add(BlossomBranch(self))
        self.petals = self.add(Petals(self, self.garden, self.branch))

    def gust(self):
        # 0 between gusts; during one it swells up to 1 and back down
        if self.gust_age is None:
            return 0
        return math.sin(math.pi * self.gust_age / self.GUST_TIME)

    def update_gusts(self, dt):
        if self.gust_age is None:
            self.gust_wait -= dt * self.breeze.value
            if self.gust_wait <= 0:
                self.gust_age = 0
            return
        self.gust_age += dt
        if self.gust_age >= self.GUST_TIME:
            self.gust_age = None
            self.gust_wait = random.randint(*self.GUST_WAIT)

    def update_weather(self):
        gust = self.gust()
        self.weather["storm"] = 0
        self.weather["gust"] = gust
        self.weather["wind"] = self.breeze.value * (1 + self.GUST_STRENGTH * gust)
        self.weather["light"] = self.light.value
        self.weather["petalfall"] = self.petalfall.value

    def update(self, dt):
        self.update_gusts(dt)
        self.update_weather()
        super().update(dt)
