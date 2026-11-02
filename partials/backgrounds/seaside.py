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
        # at night), then the rocks and grass and the palm in front
        self.sky = self.add(Sky(self))
        self.sea = self.add(Sea(self))
        self.beam = self.add(LighthouseBeam(self, self.sea))          # at night
        self.glitter = self.add(GlitterPath(self, self.sky, self.sea))
        self.waves = self.add(Waves(self, self.sea))
        self.surf_glow = self.add(GlowingSurf(self, self.waves))      # at night
        self.front = self.add(BeachFront(self))
        self.palm = self.add(BeachPalm(self))

    def update_weather(self):
        self.weather["storm"] = 0
        self.weather["wind"] = self.breeze.value
        self.weather["light"] = self.light.value

    def update(self, dt):
        self.update_weather()
        super().update(dt)
