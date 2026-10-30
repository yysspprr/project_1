# The rain theme's background: rain falling onto water, seen from an angle

import random

from partials.config import WIDTH
from partials.backgrounds.base import LayeredBackground
from partials.backgrounds.helpers import Timer
from partials.backgrounds.water import WaterSurface
from partials.backgrounds.ripples import Ripples
from partials.backgrounds.debris import FloatingDebris
from partials.backgrounds.streaks import FallingStreaks


class RainBackground(LayeredBackground):

    SPAWN_TIME = (25, 90)           # milliseconds between drops in a normal shower (shortest, longest)
    DROP_SPREAD = 0.5               # how much drops crowd toward the back (see Perspective.random_y)

    # Things that wax and wane on their own: (lowest, highest), and milliseconds to change
    INTENSITY = (0.2, 1.3)          # how hard it rains: 0.2 is a drizzle, 1 a normal shower, more is a downpour
    INTENSITY_TIME = (6000, 15000)
    WIND = (0.3, 2.0)               # 1 is a normal breeze: slants the rain and pushes the debris along
    WIND_TIME = (4000, 10000)

    def __init__(self):
        super().__init__()
        self.intensity = self.swell(*self.INTENSITY, self.INTENSITY_TIME)
        self.wind = self.swell(*self.WIND, self.WIND_TIME)

        # Back to front: debris floats on the water, the rain falls in front of it all
        self.water = self.add(WaterSurface(self))
        self.ripples = self.add(Ripples(self))
        self.debris = self.add(FloatingDebris(self))
        self.rain = self.add(FallingStreaks(self, on_land=self.drop_landed))

        self.drop_timer = Timer(self.SPAWN_TIME)

    def drop_landed(self, x, y):
        self.ripples.add(x, y)
        self.debris.nudge(x, y)

    def update(self, dt):
        # Share the wind before anything moves
        self.rain.wind = self.wind.value
        self.debris.wind = self.wind.value

        super().update(dt)

        # Aim a new drop at a random spot on the water; heavier rain counts down faster
        if self.drop_timer.tick(dt, self.intensity.value):
            self.rain.add(random.uniform(0, WIDTH), self.view.random_y(self.DROP_SPREAD))
