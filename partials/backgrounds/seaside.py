# The seaside theme's background: a tropical beach looking out to sea, waves washing up
# the sand, a palm leaning in overhead

import math

import random

from partials.config import ROUND_Y, s
from partials.backgrounds.base import LayeredBackground
from partials.backgrounds.perspective import Perspective
from partials.backgrounds.sky import Sky
from partials.backgrounds.beach import Sea, Waves, BeachPalm, BeachFront
from partials.backgrounds.seaside_light import GlitterPath, LighthouseBeam, GlowingSurf
from partials.backgrounds.seaside_life import (Gulls, Crabs, Sandpipers, Footprints, Dolphins, Sailboat, Bottle, WhaleSpout,
                                               Kite, Hatchlings)
from partials.backgrounds.brook_life import Visits, VisitClock


class SeasideBackground(LayeredBackground):

    # The same horizon as the rain, snow, blossom and desert themes
    HORIZON = ROUND_Y - s(5)
    FAR_SCALE = 0.15

    # Things that wax and wane on their own
    BREEZE = (0.5, 1.4)
    BREEZE_TIME = (5000, 12000)
    LIGHT = (0.75, 1.15)
    LIGHT_TIME = (7000, 16000)

    def __init__(self):
        super().__init__(Perspective(far_scale=self.FAR_SCALE, horizon=self.HORIZON))
        self.breeze = self.swell(*self.BREEZE, self.BREEZE_TIME)
        self.light = self.swell(*self.LIGHT, self.LIGHT_TIME)
        self.update_weather()

        # Back to front: sky, the sea and the beach (with the far cay and the lighthouse, its
        # beam sweeping at night), glitter on the water, the waves washing up the sand (glowing
        # at night) with footprints on the sand, crabs and sandpipers at the water's edge,
        # the rocks and grass, gulls overhead, and the palm in front. Rare visitors (a sailboat,
        # a whale, dolphins, a bottle, a kite, hatchlings) take turns
        self.sky = self.add(Sky(self))
        visits = Visits()                                               # rare visitors take turns
        self.add(VisitClock(self, visits))
        self.sea = self.add(Sea(self))
        self.beam = self.add(LighthouseBeam(self, self.sea))          # at night
        self.sailboat = self.add(visits.join(Sailboat(self)))
        self.spout = self.add(visits.join(WhaleSpout(self)))
        self.dolphins = self.add(visits.join(Dolphins(self)))
        self.glitter = self.add(GlitterPath(self, self.sky, self.sea))
        self.waves = Waves(self, self.sea)
        self.footprints = self.add(Footprints(self, self.sea, self.waves))
        self.add(self.waves)
        self.surf_glow = self.add(GlowingSurf(self, self.waves))      # at night
        self.bottle = self.add(visits.join(Bottle(self, self.waves)))
        self.crabs = self.add(Crabs(self, self.waves))
        self.sandpipers = self.add(Sandpipers(self, self.waves))
        self.hatchlings = self.add(visits.join(Hatchlings(self, self.waves)))   # at night
        self.front = self.add(BeachFront(self))
        self.gulls = self.add(Gulls(self))                              # by day
        self.kite = self.add(visits.join(Kite(self)))                  # by day
        self.palm = self.add(BeachPalm(self))

    def update_weather(self):
        self.weather["storm"] = 0
        self.weather["wind"] = self.breeze.value
        self.weather["light"] = self.light.value

    def update(self, dt):
        self.update_weather()
        super().update(dt)
