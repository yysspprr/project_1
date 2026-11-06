# The space theme's background: drifting through deep space alongside the Voyager probe,
# past a great ringed planet, with the Sun far behind us. Light mode is a negative of it

import random

from partials.config import s
from partials.backgrounds.base import LayeredBackground
from partials.backgrounds.perspective import Perspective
from partials.backgrounds.cosmos import Backdrop, Starfield, Sun, GasGiant, Voyager
from partials.backgrounds.cosmos_light import Pulsar, PaleBlueDot, Signal, Comet, Supernova
from partials.backgrounds.cosmos_life import Asteroids, Rocket, Saucer, Astronaut, SolarSail
from partials.backgrounds.brook_life import Visits, VisitClock


class SpaceBackground(LayeredBackground):

    # No horizon out here: the whole window is sky
    HORIZON = 0

    # How fast we drift past the stars, waxing and waning a little
    DRIFT = (0.7, 1.3)
    DRIFT_TIME = (8000, 18000)

    def __init__(self):
        super().__init__(Perspective(horizon=self.HORIZON))
        self.drift = self.swell(*self.DRIFT, self.DRIFT_TIME)
        self.update_weather()

        # Back to front: the backdrop with its nebula and galaxy, the stars, a pulsar, a
        # supernova (very rarely), the Sun, the Earth in its ray of sunlight, a comet now and
        # then, the ringed planet and its moon, asteroids tumbling past, and Voyager with its
        # signal going home. Rare visitors (a solar sail, a rocket, a flying saucer, an
        # astronaut) take turns
        self.backdrop = self.add(Backdrop(self))
        visits = Visits()
        self.add(VisitClock(self, visits))
        self.stars = self.add(Starfield(self))
        self.pulsar = self.add(Pulsar(self))
        self.supernova = self.add(Supernova(self))
        self.sun = self.add(Sun(self))
        self.earth = self.add(PaleBlueDot(self))
        self.comet = self.add(Comet(self, self.sun))
        self.sail = self.add(visits.join(SolarSail(self)))
        self.planet = self.add(GasGiant(self))
        self.asteroids = self.add(Asteroids(self))
        self.voyager = self.add(Voyager(self))
        self.signal = self.add(Signal(self, self.voyager, self.earth))
        self.rocket = self.add(visits.join(Rocket(self)))
        self.saucer = self.add(visits.join(Saucer(self, self.planet)))
        self.astronaut = self.add(visits.join(Astronaut(self)))

    def update_weather(self):
        self.weather["storm"] = 0
        self.weather["wind"] = 0
        self.weather["light"] = 1
        self.weather["drift"] = self.drift.value

    def update(self, dt):
        self.update_weather()
        super().update(dt)
