# The stream theme's background: a quiet woodland brook seen from just above, its water
# meandering down through a stony bed between mossy banks. No horizon, no sky

from partials.backgrounds.base import LayeredBackground
from partials.backgrounds.perspective import Perspective
from partials.backgrounds.brook import BrookCourse, BrookBed, BrookWater, BrookRocks, BrookLeaves, BrookHaze, FallenLog
from partials.backgrounds.brook_flow import BrookCurrent, BrookWakes, DriftingLeaves
from partials.backgrounds.brook_light import SunDapples, WaterGlints, Fireflies
from partials.backgrounds.brook_life import (BrookRings, Dragonflies, Butterflies, Frog, Visits, VisitClock,
                                             Kingfisher, PaperBoat, Deer)


class StreamBackground(LayeredBackground):

    # Looking down at the brook at a slant: the top of the window is further away than the
    # bottom, so things there look smaller and a little more squashed
    FAR_SCALE = 0.6
    NEAR_FLATTEN = 0.75
    FAR_FLATTEN = 0.55

    # Things that wax and wane on their own: (lowest, highest), and milliseconds to change.
    # A serene scene: just a breeze that comes and goes, and the light, never a storm
    BREEZE = (0.2, 1.1)
    BREEZE_TIME = (6000, 15000)
    LIGHT = (0.6, 1.15)
    LIGHT_TIME = (7000, 16000)

    def __init__(self):
        super().__init__(Perspective(far_scale=self.FAR_SCALE, near_flatten=self.NEAR_FLATTEN, far_flatten=self.FAR_FLATTEN))
        self.breeze = self.swell(*self.BREEZE, self.BREEZE_TIME)
        self.light = self.swell(*self.LIGHT, self.LIGHT_TIME)
        self.update_weather()

        # Back to front: the bed and banks, the water and its current, the stones and the
        # ripples behind them, leaves (drifting on the water, lying on the banks), and the
        # fallen log on games when that's how the brook is crossed (stepping stones otherwise),
        # the frog, things flying low over the brook, sunlight through the leaves, the far
        # end's haze, and fireflies. Rare visitors take turns (see Visits)
        self.course = BrookCourse(self.view)
        self.bed = self.add(BrookBed(self, self.course))
        self.water = self.add(BrookWater(self, self.course))
        self.current = self.add(BrookCurrent(self, self.course, self.water))
        self.dapples = SunDapples(self)                                 # drawn later, over everything
        self.glints = self.add(WaterGlints(self, self.course, self.water, self.dapples))
        self.rings = self.add(BrookRings(self, self.water))             # where things touch the water
        self.rocks = BrookRocks(self, self.course)
        self.wakes = self.add(BrookWakes(self, self.course, self.water, self.rocks))
        self.add(self.rocks)
        self.drifting = self.add(DriftingLeaves(self, self.course, self.water, self.rocks))
        visits = Visits()
        self.add(VisitClock(self, visits))
        self.boat = self.add(visits.join(PaperBoat(self, self.course, self.rocks)))
        self.leaves = self.add(BrookLeaves(self, self.course))
        self.log = self.add(FallenLog(self, self.course))            # only on some games
        self.frog = self.add(Frog(self, self.course, self.rocks, self.log, self.rings))
        self.deer = self.add(visits.join(Deer(self, self.course, self.rings, self.rocks)))
        self.dragonflies = self.add(Dragonflies(self, self.course))   # by day
        self.butterflies = self.add(Butterflies(self, self.course))   # by day
        self.kingfisher = self.add(visits.join(Kingfisher(self, self.course, self.rings)))
        self.add(self.dapples)                                          # sunlight by day
        self.haze = self.add(BrookHaze(self))
        self.fireflies = self.add(Fireflies(self, self.course))         # at night

    def update_weather(self):
        self.weather["storm"] = 0
        self.weather["wind"] = self.breeze.value
        self.weather["light"] = self.light.value

    def update(self, dt):
        self.update_weather()
        super().update(dt)
