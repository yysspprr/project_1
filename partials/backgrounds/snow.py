# The snow theme's background: a snowy landscape with a frozen pond, seen from an angle,
# under a winter sky with snow falling

from partials.config import ROUND_Y, s
from partials.backgrounds.base import LayeredBackground
from partials.backgrounds.perspective import Perspective
from partials.backgrounds.sky import Sky
from partials.backgrounds.mountains import SnowyRange
from partials.backgrounds.snowfield import SnowField, FrozenPond, SnowSparkle
from partials.backgrounds.flakes import Snowfall, DiamondDust
from partials.backgrounds.aurora import Aurora


class SnowBackground(LayeredBackground):

    # The same horizon as the rain theme: in the gap below the game screen's heading lines
    HORIZON = ROUND_Y - s(5)
    FAR_SCALE = 0.12

    # Things that wax and wane on their own: (lowest, highest), and milliseconds to change
    SNOWFALL = (0, 1)               # 0 = a few lazy flakes, 1 = a flurry
    SNOWFALL_TIME = (8000, 18000)
    WIND = (0.2, 1.6)               # 1 is a normal breeze
    WIND_TIME = (5000, 12000)
    STORM_WIND = 0.6                # how much heavy snow drags the wind with it: 0 = not at all
    LIGHT = (0.45, 1.15)            # the sun or moon breaking through (high) or clouding over (low)
    LIGHT_TIME = (6000, 14000)
    STORM_DIM = 0.5                 # how much a flurry dims the light

    def __init__(self):
        super().__init__(Perspective(far_scale=self.FAR_SCALE, horizon=self.HORIZON))
        self.snowfall = self.swell(*self.SNOWFALL, self.SNOWFALL_TIME)
        self.wind = self.swell(*self.WIND, self.WIND_TIME)
        self.light = self.swell(*self.LIGHT, self.LIGHT_TIME)
        self.update_weather()

        # Back to front: sky and aurora, the mountains on the horizon, the snowy ground and
        # its sparkle, the pond (reflecting the aurora), then falling snow and diamond dust
        self.sky = self.add(Sky(self))
        self.aurora = self.add(Aurora(self))
        self.range = self.add(SnowyRange(self))
        self.ground = self.add(SnowField(self))
        self.pond = self.add(FrozenPond(self, mirrors=[self.aurora]))
        self.sparkle = self.add(SnowSparkle(self, avoid=self.pond))
        self.flakes = self.add(Snowfall(self))
        self.dust = self.add(DiamondDust(self))

    def update_weather(self):
        # The weather report every layer reads: heavy snow is a storm
        storm = self.snowfall.value
        self.weather["storm"] = storm
        self.weather["wind"] = self.wind.value * (1 - self.STORM_WIND / 2 + self.STORM_WIND * storm)
        self.weather["light"] = self.light.value * (1 - self.STORM_DIM * storm)

    def update(self, dt):
        self.update_weather()
        super().update(dt)
