# The desert theme's background: rolling dunes seen from the top of a dune, pyramids on
# the horizon, and an oasis of palms around a small pool in a dip between the dunes

import math

import random

from partials.config import ROUND_Y, s
from partials.backgrounds.base import LayeredBackground
from partials.backgrounds.perspective import Perspective
from partials.backgrounds.sky import Sky
from partials.backgrounds.dunes import Pyramids, Dunes, DesertRocks, Oasis, Palms, SandWisps


class DesertBackground(LayeredBackground):

    # The same horizon as the rain, snow and blossom themes; the desert stretches far away
    HORIZON = ROUND_Y - s(5)
    FAR_SCALE = 0.2

    # Things that wax and wane on their own: (lowest, highest), and milliseconds to change
    WIND = (0.3, 1.4)
    WIND_TIME = (5000, 13000)
    LIGHT = (0.8, 1.15)
    LIGHT_TIME = (7000, 16000)

    # Gusts: now and then the wind picks up and lifts sand off every crest
    GUST_WAIT = (10000, 26000)
    GUST_TIME = 3000
    GUST_STRENGTH = 1.5

    def __init__(self):
        super().__init__(Perspective(far_scale=self.FAR_SCALE, horizon=self.HORIZON))
        self.wind = self.swell(*self.WIND, self.WIND_TIME)
        self.light = self.swell(*self.LIGHT, self.LIGHT_TIME)
        self.gust_wait = random.randint(*self.GUST_WAIT)
        self.gust_age = None
        self.update_weather()

        # Back to front: sky, pyramids on the horizon, the dunes and near sand, rocks, the
        # oasis and its palms, then sand blowing
        self.sky = self.add(Sky(self))
        self.pyramids = self.add(Pyramids(self))
        self.dunes = self.add(Dunes(self))
        self.rocks = self.add(DesertRocks(self))
        self.oasis = self.add(Oasis(self))
        self.palms = self.add(Palms(self, self.oasis))
        self.wisps = self.add(SandWisps(self, self.dunes))

    def gust(self):
        if self.gust_age is None:
            return 0
        return math.sin(math.pi * self.gust_age / self.GUST_TIME)

    def update_gusts(self, dt):
        if self.gust_age is None:
            self.gust_wait -= dt * self.wind.value
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
        self.weather["wind"] = self.wind.value * (1 + self.GUST_STRENGTH * gust)
        self.weather["light"] = self.light.value

    def update(self, dt):
        self.update_gusts(dt)
        self.update_weather()
        super().update(dt)
