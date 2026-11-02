# The mountains theme's background: looking out from a rocky ledge across a misty valley,
# rows of forested ridges stepping away toward a great range of snowy peaks

import math

import random

from partials.config import s
from partials.backgrounds.base import LayeredBackground
from partials.backgrounds.perspective import Perspective
from partials.backgrounds.peaks import PeakSky, GreatPeaks, Ridge, MistBank, Ledge, PrayerFlags
from partials.backgrounds.peaks_weather import SummitPlume, CloudShadows, Avalanche, MistFall
from partials.backgrounds.peaks_light import SunBeams, Monastery
from partials.backgrounds.peaks_life import Choughs, Eagle, Ibex, Marmot, Climbers, YakCaravan, Paraglider, SnowLeopard
from partials.backgrounds.brook_life import Visits, VisitClock


class MistyBackground(LayeredBackground):

    # The far edge of the valley: the feet of the peaks, where the sea of cloud lies
    HORIZON = s(235)
    FAR_SCALE = 0.1

    # Things that wax and wane on their own
    WIND = (0.4, 1.5)
    WIND_TIME = (5000, 12000)
    LIGHT = (0.8, 1.15)
    LIGHT_TIME = (7000, 16000)

    # Gusts: now and then the wind picks up for a moment, more often when it's already windy
    GUST_WAIT = (9000, 26000)
    GUST_TIME = 2800
    GUST_STRENGTH = 1.3

    # The ridges, far to near: (height at the left, height at the right, distance, hilliness,
    # tree height), at the medium size
    RIDGES = (
        (246, 232, 1.0, 8, 3),
        (282, 330, 0.72, 14, 5),
        (408, 352, 0.45, 16, 7),
        (452, 512, 0.18, 14, 10),
    )
    # The mist banks, far to near: (height, depth, strength, speed), the first in front of the
    # peaks and each of the others in front of the ridge before it
    MIST = (
        (226, 34, 0.85, 3),
        (268, 34, 0.6, 4),
        (348, 44, 0.6, 5),
        (430, 50, 0.55, 6),
        (560, 70, 0.6, 7),
    )

    def __init__(self):
        super().__init__(Perspective(far_scale=self.FAR_SCALE, horizon=self.HORIZON))
        self.wind = self.swell(*self.WIND, self.WIND_TIME)
        self.light = self.swell(*self.LIGHT, self.LIGHT_TIME)
        self.gust_wait = random.randint(*self.GUST_WAIT)
        self.gust_age = None            # how far into a gust we are, or None between gusts
        self.update_weather()

        # Back to front: sky, the great peaks with cloud shadows sliding over them, the odd
        # avalanche and the snow plume off the summit, then each ridge with a bank of mist in
        # front of it: the monastery on the second ridge, the mist pouring over the third ridge
        # now and then, sunbeams slanting down through the mist by day, an eagle circling,
        # and last the ledge with its cairn and prayer flags (with the marmot and the ibex in
        # front of them), and the
        # choughs. Rare visitors (climbers, a yak caravan, a paraglider, a snow leopard) take turns
        self.sky = self.add(PeakSky(self))
        visits = Visits()                                               # rare visitors take turns
        self.add(VisitClock(self, visits))
        self.peaks = self.add(GreatPeaks(self))
        self.shadows = self.add(CloudShadows(self, self.peaks))       # by day
        self.avalanche = self.add(Avalanche(self, self.peaks))
        self.climbers = self.add(visits.join(Climbers(self, self.peaks)))
        self.plume = self.add(SummitPlume(self, self.peaks.summits[2]))
        self.mist = [MistBank(self, *mist) for mist in self.MIST]
        self.ridges = [Ridge(self, *ridge) for ridge in self.RIDGES]
        self.add(self.mist[0])
        self.add(self.ridges[0])
        self.add(self.mist[1])
        self.add(self.ridges[1])
        self.monastery = self.add(Monastery(self, self.ridges[1]))
        self.yaks = self.add(visits.join(YakCaravan(self, self.ridges[1], self.monastery)))     # by day
        self.add(self.mist[2])
        self.add(self.ridges[2])
        self.mistfall = self.add(MistFall(self, self.ridges[2]))
        self.beams = self.add(SunBeams(self, self.sky))               # by day
        self.add(self.mist[3])
        self.add(self.ridges[3])
        self.add(self.mist[4])
        self.eagle = self.add(Eagle(self))                              # by day
        self.paraglider = self.add(visits.join(Paraglider(self)))      # by day
        self.ledge = self.add(Ledge(self))
        self.flags = self.add(PrayerFlags(self, self.ledge))
        self.marmot = self.add(Marmot(self, self.ledge))                # by day
        self.ibex = self.add(Ibex(self, self.ledge))                    # by day
        self.leopard = self.add(visits.join(SnowLeopard(self, self.ledge, self.ibex)))
        self.ibex.blocked = lambda: self.leopard.active
        self.choughs = self.add(Choughs(self, self.ledge))              # by day

    def gust(self):
        # 0 between gusts; during one it swells up to 1 and back down
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

    def update_weather(self):
        gust = self.gust()
        self.weather["storm"] = 0
        self.weather["gust"] = gust
        self.weather["wind"] = self.wind.value * (1 + self.GUST_STRENGTH * gust)
        self.weather["light"] = self.light.value

    def update(self, dt):
        self.update_gusts(dt)
        self.update_weather()
        super().update(dt)
