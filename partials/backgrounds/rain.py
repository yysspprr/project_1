# The rain theme's background: rain falling onto water, seen from an angle,
# with the sky above the far shore

import random

from partials.config import WIDTH, ROUND_Y, s
from partials.backgrounds.base import LayeredBackground
from partials.backgrounds.helpers import Timer
from partials.backgrounds.perspective import Perspective
from partials.backgrounds.sky import Sky
from partials.backgrounds.water import WaterSurface
from partials.backgrounds.ripples import Ripples
from partials.backgrounds.debris import FloatingDebris
from partials.backgrounds.wildlife import WaterStriders, RisingFish
from partials.backgrounds.streaks import FallingStreaks


class RainBackground(LayeredBackground):

    # The horizon sits just above the round label: in the gap below the game screen's
    # heading lines, so the far shore doesn't run behind them
    HORIZON = ROUND_Y - s(5)
    FAR_SCALE = 0.12                # how small things are at the horizon, compared to up close

    SPAWN_TIME = (25, 90)           # milliseconds between drops in a normal shower (shortest, longest)
    DROP_SPREAD = 0.5               # how much drops crowd toward the back (see Perspective.random_y)

    # Things that wax and wane on their own: (lowest, highest), and milliseconds to change
    INTENSITY = (0.2, 1.3)          # how hard it rains: 0.2 is a drizzle, 1 a normal shower, more is a downpour
    INTENSITY_TIME = (6000, 15000)
    WIND = (0.3, 2.0)               # 1 is a normal breeze: slants the rain and pushes the debris along
    WIND_TIME = (4000, 10000)
    STORM_WIND = 0.6                # how much the rain drags the wind with it: 0 = not at all
    LIGHT = (0.35, 1.2)             # the sun or moon breaking through (high) or clouding over (low)
    LIGHT_TIME = (5000, 12000)
    STORM_DIM = 0.55                # how much a full storm dims the light (0 = not at all, 1 = dark)

    def __init__(self):
        super().__init__(Perspective(far_scale=self.FAR_SCALE, horizon=self.HORIZON))
        self.intensity = self.swell(*self.INTENSITY, self.INTENSITY_TIME)
        self.wind = self.swell(*self.WIND, self.WIND_TIME)
        self.light = self.swell(*self.LIGHT, self.LIGHT_TIME)

        # Back to front: the sky, the water and what happens on it, then the rain in front of it all
        self.sky = self.add(Sky(self))
        self.water = self.add(WaterSurface(self))
        self.ripples = self.add(Ripples(self))
        self.fish = self.add(RisingFish(self, on_ripple=self.ripples.add))
        self.debris = self.add(FloatingDebris(self, on_ripple=self.ripples.add))
        self.striders = self.add(WaterStriders(self, on_ripple=self.ripples.add))
        self.rain = self.add(FallingStreaks(self, on_land=self.drop_landed))

        self.drop_timer = Timer(self.SPAWN_TIME)

    def drop_landed(self, x, y):
        # A drop on a leaf or twig makes it ripple instead; otherwise the water ripples
        if not self.debris.nudge(x, y):
            self.ripples.add(x, y)

    def update(self, dt):
        # The weather report every layer reads: heavy rain is a storm, and drags the wind up with it
        storm = self.intensity.share()
        self.weather["storm"] = storm
        self.weather["wind"] = self.wind.value * (1 - self.STORM_WIND / 2 + self.STORM_WIND * storm)
        self.weather["light"] = self.light.value * (1 - self.STORM_DIM * storm)

        super().update(dt)

        # Aim a new drop at a random spot on the water; heavier rain counts down faster
        if self.drop_timer.tick(dt, self.intensity.value):
            self.rain.add(random.uniform(0, WIDTH), self.view.random_y(self.DROP_SPREAD))
