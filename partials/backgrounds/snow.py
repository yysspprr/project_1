# The snow theme's background: a snowy landscape with a frozen pond, seen from an angle,
# under a winter sky with snow falling

import math

import random

from partials.config import ROUND_Y, HEIGHT, s
from partials.backgrounds.base import LayeredBackground
from partials.backgrounds.perspective import Perspective
from partials.backgrounds.sky import Sky
from partials.backgrounds.mountains import SnowyRange
from partials.backgrounds.snowfield import SnowField, FrozenPond, SnowSparkle, SnowGusts
from partials.backgrounds.flakes import Snowfall, DiamondDust
from partials.backgrounds.aurora import Aurora
from partials.backgrounds.village import Village
from partials.backgrounds.winterframe import FirBough
from partials.backgrounds.critters import Tracks, Fox, SleighRide


class SnowBackground(LayeredBackground):

    # The same horizon as the rain theme: in the gap below the game screen's heading lines
    HORIZON = ROUND_Y - s(5)
    FAR_SCALE = 0.12

    # Things that wax and wane on their own: (lowest, highest), and milliseconds to change
    SNOWFALL = (0, 1)               # 0 = a few lazy flakes, 1 = a flurry
    SNOWFALL_TIME = (8000, 18000)
    WIND = (0.2, 1.6)               # 1 is a normal breeze
    WIND_TIME = (5000, 12000)
    STORM_WIND = 0.6                # how much heavy snow drags the wind with it: 0 = not at all
    LIGHT = (0.45, 1.15)            # the sun or moon breaking through (high) or clouding over (low)
    LIGHT_TIME = (6000, 14000)
    STORM_DIM = 0.5                 # how much a flurry dims the light

    # Gusts: now and then the wind picks up for a moment, more often when it's already windy
    GUST_WAIT = (10000, 30000)      # milliseconds between gusts at a normal breeze
    GUST_TIME = 2600                # how long one lasts, rising and falling
    GUST_STRENGTH = 1.2             # how much a gust adds to the wind at its peak

    def __init__(self):
        super().__init__(Perspective(far_scale=self.FAR_SCALE, horizon=self.HORIZON))
        self.snowfall = self.swell(*self.SNOWFALL, self.SNOWFALL_TIME)
        self.wind = self.swell(*self.WIND, self.WIND_TIME)
        self.light = self.swell(*self.LIGHT, self.LIGHT_TIME)
        self.gust_wait = random.randint(*self.GUST_WAIT)
        self.gust_age = None        # how far into a gust we are, or None between gusts
        self.update_weather()

        # Back to front: sky, aurora (and a rare sleigh), the mountains on the horizon, the snowy
        # ground and its sparkle, the pond (reflecting the aurora), tracks in the snow, the village,
        # the fox, then falling snow and diamond dust
        self.sky = self.add(Sky(self))
        self.aurora = self.add(Aurora(self))
        self.sleigh = self.add(SleighRide(self, sky=self.sky))       # very rarely, on December nights
        self.range = self.add(SnowyRange(self))
        self.ground = self.add(SnowField(self))
        self.pond = self.add(FrozenPond(self, mirrors=[self.aurora]))
        self.sparkle = self.add(SnowSparkle(self, avoid=self.pond))
        self.gusts = self.add(SnowGusts(self.ground))
        self.tracks = self.add(Tracks(self))
        self.village = self.add(Village(self))
        self.fox = self.add(Fox(self, tracks=self.tracks))
        self.flakes = self.add(Snowfall(self))
        self.dust = self.add(DiamondDust(self))

        # Close to us: two boughs of a big fir standing just out of sight on the right,
        # one just below the sun or moon, one lower down with a bird on it
        self.upper_bough = self.add(FirBough(self, side="right", height=self.sky.body_y + s(32),
                                             reach=115, droop=45, bird=False))
        self.lower_bough = self.add(FirBough(self, side="right", height=HEIGHT * 0.6,
                                             reach=95, droop=40))

    def gust(self):
        # 0 between gusts; during one it swells up to 1 and back down
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
        # The weather report every layer reads: heavy snow is a storm, and a gust briefly
        # whips the wind up, so the snow, smoke, clouds and boughs all feel it at once
        storm = self.snowfall.value
        gust = self.gust()
        self.weather["storm"] = storm
        self.weather["gust"] = gust
        self.weather["wind"] = (self.wind.value * (1 - self.STORM_WIND / 2 + self.STORM_WIND * storm)
                                * (1 + self.GUST_STRENGTH * gust))
        self.weather["light"] = self.light.value * (1 - self.STORM_DIM * storm)

    def update(self, dt):
        self.update_gusts(dt)
        self.update_weather()
        super().update(dt)
