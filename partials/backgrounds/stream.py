# The stream theme's background: a quiet woodland brook seen from just above, its water
# meandering down through a stony bed between mossy banks. No horizon, no sky

from partials.backgrounds.base import LayeredBackground
from partials.backgrounds.perspective import Perspective
from partials.backgrounds.brook import BrookCourse, BrookBed, BrookWater, BrookRocks, BrookLeaves


class StreamBackground(LayeredBackground):

    # Looking down at the brook from just above: the top of the window is only a little
    # further away than the bottom
    FAR_SCALE = 0.75

    # Things that wax and wane on their own: (lowest, highest), and milliseconds to change.
    # A serene scene: just a breeze that comes and goes, and the light, never a storm
    BREEZE = (0.2, 1.1)
    BREEZE_TIME = (6000, 15000)
    LIGHT = (0.6, 1.15)
    LIGHT_TIME = (7000, 16000)

    def __init__(self):
        super().__init__(Perspective(far_scale=self.FAR_SCALE))
        self.breeze = self.swell(*self.BREEZE, self.BREEZE_TIME)
        self.light = self.swell(*self.LIGHT, self.LIGHT_TIME)
        self.update_weather()

        # Back to front: the bed and banks, the water, the rocks, then fallen leaves
        self.course = BrookCourse(self.view)
        self.bed = self.add(BrookBed(self, self.course))
        self.water = self.add(BrookWater(self, self.course))
        self.rocks = self.add(BrookRocks(self, self.course))
        self.leaves = self.add(BrookLeaves(self, self.course))

    def update_weather(self):
        self.weather["storm"] = 0
        self.weather["wind"] = self.breeze.value
        self.weather["light"] = self.light.value

    def update(self, dt):
        self.update_weather()
        super().update(dt)
