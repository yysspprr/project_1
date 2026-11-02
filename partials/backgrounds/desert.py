# The desert theme's background: rolling dunes seen from the top of a dune, pyramids on
# the horizon, and an oasis of palms around a small pool in a dip between the dunes

import math

import random

from partials.config import ROUND_Y, s
from partials.backgrounds.base import LayeredBackground
from partials.backgrounds.perspective import Perspective
from partials.backgrounds.dunes import Pyramids, Dunes, DesertRocks, Oasis, Palms, SandWisps
from partials.backgrounds.desert_weather import HeatShimmer, PoolRipples, Tumbleweed, Sandstorm
from partials.backgrounds.desert_light import DesertSky, ShootingStars, PoolSky, Campfire
from partials.backgrounds.desert_life import Lizard, Scarab, Jerboas, Hawk, Fennec, Caravan, Mirage
from partials.backgrounds.brook_life import Visits, VisitClock


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

    # Sandstorms: every few minutes the wind rises, the air turns to dust, and it clears again
    STORM_WAIT = (80000, 180000)    # milliseconds between storms
    STORM_FIRST = (40000, 90000)
    STORM_RISE = 6000               # milliseconds it takes to blow up
    STORM_HOLD = (9000, 16000)      # how long it rages
    STORM_FALL = 8000               # how long it takes to clear
    STORM_PEAK = (0.6, 1.0)
    STORM_WIND = 1.6                # how much a full storm adds to the wind
    STORM_DIM = 0.55                # how much a full storm dims the light

    def __init__(self):
        super().__init__(Perspective(far_scale=self.FAR_SCALE, horizon=self.HORIZON))
        self.wind = self.swell(*self.WIND, self.WIND_TIME)
        self.light = self.swell(*self.LIGHT, self.LIGHT_TIME)
        self.gust_wait = random.randint(*self.GUST_WAIT)
        self.gust_age = None
        self.storm_wait = random.uniform(*self.STORM_FIRST)
        self.storm_age = None       # how far into a storm we are, or None between storms
        self.update_weather()

        # Back to front: sky (with the Milky Way at night) and shooting stars, pyramids on the
        # horizon, the dunes and near sand, the heat shimmering over them, rocks, the oasis
        # with the night sky mirrored in it, its ripples and palms, the campfire, the creatures
        # of the sand, tumbleweed, sand blowing off the dunes, and the dust of a sandstorm
        # when one blows. Rare visitors (a mirage, a caravan, a hawk, a fennec) take turns
        self.sky = self.add(DesertSky(self))
        self.shooting_stars = self.add(ShootingStars(self))            # some nights
        self.pyramids = self.add(Pyramids(self))
        self.dunes = self.add(Dunes(self))
        visits = Visits()                                               # rare visitors take turns
        self.add(VisitClock(self, visits))
        self.mirage = self.add(visits.join(Mirage(self)))              # by day
        self.caravan = self.add(visits.join(Caravan(self, self.dunes)))
        self.shimmer = self.add(HeatShimmer(self))                     # wavers what's behind it, by day
        self.rocks = self.add(DesertRocks(self))
        self.hawk = self.add(visits.join(Hawk(self)))                  # by day
        self.oasis = self.add(Oasis(self))
        self.pool_sky = self.add(PoolSky(self, self.oasis))            # stars in the water, at night
        self.ripples = self.add(PoolRipples(self, self.oasis))
        self.palms = self.add(Palms(self, self.oasis))
        self.campfire = self.add(Campfire(self, self.oasis))           # lit at night
        self.fennec = self.add(visits.join(Fennec(self, self.dunes)))  # by night
        self.lizard = self.add(Lizard(self))                           # by day
        self.scarab = self.add(Scarab(self))                           # by day
        self.jerboas = self.add(Jerboas(self))                         # by night
        self.tumbleweed = self.add(Tumbleweed(self))
        self.wisps = self.add(SandWisps(self, self.dunes))
        self.sandstorm = self.add(Sandstorm(self))

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

    def storm(self):
        # 0 between storms; during one it blows up to its peak, rages, and dies down
        if self.storm_age is None:
            return 0
        age = self.storm_age
        rise, hold = self.STORM_RISE, self.storm_hold
        if age < rise:
            t = age / rise
        elif age < rise + hold:
            t = 1
        else:
            t = 1 - (age - rise - hold) / self.STORM_FALL
        t = max(0.0, min(1.0, t))
        return self.storm_peak * t * t * (3 - 2 * t)

    def update_storm(self, dt):
        if self.storm_age is None:
            self.storm_wait -= dt
            if self.storm_wait <= 0:
                self.storm_age = 0
                self.storm_hold = random.uniform(*self.STORM_HOLD)
                self.storm_peak = random.uniform(*self.STORM_PEAK)
            return
        self.storm_age += dt
        if self.storm_age > self.STORM_RISE + self.storm_hold + self.STORM_FALL:
            self.storm_age = None
            self.storm_wait = random.uniform(*self.STORM_WAIT)

    def update_weather(self):
        gust = self.gust()
        storm = self.storm()
        self.weather["storm"] = storm
        self.weather["gust"] = gust
        self.weather["wind"] = self.wind.value * (1 + self.GUST_STRENGTH * gust) + self.STORM_WIND * storm
        self.weather["light"] = self.light.value * (1 - self.STORM_DIM * storm)

    def update(self, dt):
        self.update_storm(dt)
        self.update_gusts(dt)
        self.update_weather()
        super().update(dt)
