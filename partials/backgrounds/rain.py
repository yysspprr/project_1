# The rain theme's background: raindrops landing on still water

import random

from partials.config import WIDTH, HEIGHT
from partials.backgrounds.base import LayeredBackground
from partials.backgrounds.helpers import Timer
from partials.backgrounds.water import WaterSurface
from partials.backgrounds.ripples import Ripples


class RainBackground(LayeredBackground):

    SPAWN_TIME = (150, 500)         # milliseconds between drops (shortest, longest)

    def __init__(self):
        super().__init__()
        # Back to front
        self.water = self.add(WaterSurface(self))
        self.ripples = self.add(Ripples(self))

        self.drop_timer = Timer(self.SPAWN_TIME)

    def update(self, dt):
        super().update(dt)

        # Drops land anywhere for now; later the falling streaks decide where
        if self.drop_timer.tick(dt):
            self.ripples.add(random.randint(0, WIDTH), random.randint(0, HEIGHT))
