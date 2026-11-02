# The city theme's background: looking out from a rooftop over a big city's skyline,
# rows of buildings stepping away into the haze, with an elevated railway running across

import random

from partials.config import s
from partials.backgrounds.base import LayeredBackground
from partials.backgrounds.perspective import Perspective
from partials.backgrounds.skyline import CitySky, Skyline, Viaduct, Rooftop
from partials.backgrounds.city_lights import WindowLights, Beacons, NeonSign, BridgeTraffic, Fireworks
from partials.backgrounds.city_weather import Steam, Laundry
from partials.backgrounds.city_life import Pigeons, RoofCat, Trains, Planes, Starlings, Helicopter, Blimp, BalconyGardener
from partials.backgrounds.brook_life import Visits, VisitClock


class UrbanBackground(LayeredBackground):

    # Where the sky meets the haze behind the furthest towers
    HORIZON = s(300)
    FAR_SCALE = 0.1

    # Things that wax and wane on their own
    WIND = (0.4, 1.3)
    WIND_TIME = (5000, 12000)
    LIGHT = (0.8, 1.15)
    LIGHT_TIME = (7000, 16000)

    # How many windows are lit at night in each row, far to near
    LIT = (0.32, 0.28, 0.25, 0.22)

    # The rows of buildings, far to near: (tops, widths, distance, window, window spacing,
    # landmarks), at the medium size. Landmarks are (x, width, top, kind)
    ROWS = (
        ((128, 182), (16, 32), 0.62, (1.5, 2), (4, 5), ((70, 30, 112, "spire"), (300, 22, 132, "needle"))),
        ((212, 262), (26, 48), 0.38, (2.5, 3.5), (6, 8), ()),
        ((300, 360), (38, 66), 0.18, (3.5, 5), (8, 11), ()),
    )
    # Low rooftops below the railway, nearer still
    NEAR_ROW = ((482, 530), (44, 80), 0.04, (4, 6), (10, 13), ())

    def __init__(self):
        super().__init__(Perspective(far_scale=self.FAR_SCALE, horizon=self.HORIZON))
        self.wind = self.swell(*self.WIND, self.WIND_TIME)
        self.light = self.swell(*self.LIGHT, self.LIGHT_TIME)
        self.update_weather()

        # Back to front: sky, a plane passing high up, a blimp now and then, then each row of
        # buildings with its lit windows: fireworks (some nights) and starlings in front of the
        # furthest towers, the bridge and its traffic behind the second row, the neon sign and a
        # balcony gardener on the third, then the railway on its arches with its trains, the
        # low rooftops in front of it, warning lights on the masts, a helicopter, and the roof
        # we're standing on, with steam, a line of washing, pigeons and a cat. Rare visitors
        # (starlings, a helicopter, a blimp, the gardener) take turns
        self.sky = self.add(CitySky(self))
        visits = Visits()
        self.add(VisitClock(self, visits))
        self.planes = self.add(Planes(self))
        self.blimp = self.add(visits.join(Blimp(self)))
        self.rows = [Skyline(self, *row) for row in self.ROWS] + [Skyline(self, *self.NEAR_ROW)]
        self.lights = [WindowLights(self, row, lit) for row, lit in zip(self.rows, self.LIT)]
        self.add(self.rows[0])
        self.add(self.lights[0])
        self.fireworks = self.add(Fireworks(self))                    # some nights
        self.starlings = self.add(visits.join(Starlings(self)))       # by day
        self.bridge = self.add(BridgeTraffic(self))
        self.add(self.rows[1])
        self.add(self.lights[1])
        self.add(self.rows[2])
        self.add(self.lights[2])
        self.gardener = self.add(visits.join(BalconyGardener(self, self.rows[2])))     # by day
        self.sign = self.add(NeonSign(self))
        self.viaduct = self.add(Viaduct(self))
        self.trains = self.add(Trains(self, self.viaduct))
        self.add(self.rows[3])
        self.add(self.lights[3])
        self.beacons = self.add(Beacons(self, self.rows))
        self.helicopter = self.add(visits.join(Helicopter(self)))
        self.rooftop = self.add(Rooftop(self))
        self.steam = self.add(Steam(self, self.rooftop, self.rows[3]))
        self.laundry = self.add(Laundry(self))
        self.pigeons = self.add(Pigeons(self, self.rooftop))           # by day
        self.cat = self.add(RoofCat(self, self.rooftop))

    def update_weather(self):
        self.weather["storm"] = 0
        self.weather["wind"] = self.wind.value
        self.weather["light"] = self.light.value

    def update(self, dt):
        self.update_weather()
        super().update(dt)
