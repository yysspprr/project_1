# The underwater theme's background: a coral reef seen from just above the sea floor, the
# surface rippling overhead and light slanting down through the water

import math

import random

from partials.backgrounds.base import LayeredBackground
from partials.backgrounds.perspective import Perspective
from partials.backgrounds.reef import OpenWater, Surface, LightRays, ReefFloor, Kelp, Bubbles, MarineSnow
from partials.backgrounds.reef_light import Caustics, Plankton
from partials.backgrounds.reef_life import (FishSchool, Anemone, Crab, Octopus, Jellyfish, SeaTurtle, MantaRay, FarShark,
                                            WhaleShadow, TreasureChest)
from partials.backgrounds.brook_life import Visits, VisitClock
from partials.config import HEIGHT, s


class UnderwaterBackground(LayeredBackground):

    # The swell: the water rocks slowly back and forth, sometimes more, sometimes less
    SWELL = (0.3, 1.0)              # how far it rocks
    SWELL_TIME = (6000, 14000)
    SWELL_PERIOD = 5200             # milliseconds for one rock back and forth
    LIGHT = (0.7, 1.15)
    LIGHT_TIME = (6000, 14000)

    def __init__(self):
        super().__init__(Perspective())
        self.rock = self.swell(*self.SWELL, self.SWELL_TIME)
        self.light = self.swell(*self.LIGHT, self.LIGHT_TIME)
        self.time = 0
        self.update_weather()

        # Back to front: the water and far shapes (and a shark, far off, now and then), light
        # rays (and a manta overhead), the reef floor with the light dancing on it, the chest,
        # octopus, anemone and crab, kelp up the edges, schools of fish, jellyfish (and a turtle),
        # bubbles, drifting specks and glowing plankton, and the surface overhead (with a
        # whale's shadow passing). Rare visitors take turns (see Visits)
        visits = Visits()                                               # rare visitors take turns
        self.add(VisitClock(self, visits))
        self.water = self.add(OpenWater(self))
        self.bubbles = Bubbles(self, None)                              # made early: others stir and add to them
        self.plankton = Plankton(self, self.bubbles)
        self.floor = ReefFloor(self)
        self.bubbles.place_vents(self.floor)
        self.shark = self.add(visits.join(FarShark(self, self.floor)))   # far off in the blue
        self.rays = self.add(LightRays(self))
        self.manta = self.add(visits.join(MantaRay(self)))
        self.add(self.floor)
        self.caustics = self.add(Caustics(self, self.floor))          # by day
        self.chest = self.add(visits.join(TreasureChest(self, self.floor, self.bubbles)))
        self.octopus = self.add(Octopus(self, self.floor))
        self.anemone = self.add(Anemone(self, self.floor))
        self.crab = self.add(Crab(self, self.floor))
        self.kelp = self.add(Kelp(self, self.floor))
        self.schools = [self.add(FishSchool(self, "school_a", 8, (s(70), HEIGHT * 0.55), self.plankton)),
                        self.add(FishSchool(self, "school_b", 6, (HEIGHT * 0.35, HEIGHT * 0.7), self.plankton))]
        self.jellyfish = self.add(Jellyfish(self, self.plankton))
        self.turtle = self.add(visits.join(SeaTurtle(self, self.plankton)))
        self.add(self.bubbles)
        self.snow = self.add(MarineSnow(self))
        self.add(self.plankton)                                         # glowing, by night
        self.surface = self.add(Surface(self))
        self.whale = self.add(visits.join(WhaleShadow(self)))           # a shadow on the surface

    def update_weather(self):
        self.weather["storm"] = 0
        self.weather["wind"] = 1
        self.weather["surge"] = math.sin(self.time / self.SWELL_PERIOD * 2 * math.pi) * self.rock.value
        self.weather["light"] = self.light.value

    def update(self, dt):
        self.time += dt
        self.update_weather()
        super().update(dt)
