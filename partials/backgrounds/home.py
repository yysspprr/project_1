# The home theme's background: a cozy room seen from a comfy chair, a window on one side
# and a fire crackling in the hearth on the other

import random

from partials.backgrounds.base import LayeredBackground
from partials.backgrounds.perspective import Perspective
from partials.backgrounds.hearth import Room, Window, Fireplace, Firelight, Nook
from partials.backgrounds.window_weather import WindowWeather
from partials.backgrounds.home_life import Cat, SillBird, Passerby


class HomeBackground(LayeredBackground):

    # Things that wax and wane on their own: a draft that stirs the curtains, and the light
    DRAFT = (0.3, 1.1)
    DRAFT_TIME = (6000, 14000)
    LIGHT = (0.8, 1.1)
    LIGHT_TIME = (8000, 16000)

    def __init__(self):
        super().__init__(Perspective())
        self.draft = self.swell(*self.DRAFT, self.DRAFT_TIME)
        self.light = self.swell(*self.LIGHT, self.LIGHT_TIME)
        self.update_weather()

        # Back to front: the room, the window (with the weather, a bird on the sill and the odd
        # passer-by seen through it), the fireplace, the cat asleep before it, the firelight
        # over it all, then the chair and the table in front of us
        self.room = self.add(Room(self))
        self.window = self.add(Window(self))
        self.outside = self.add(WindowWeather(self, self.window))     # drawn by the window, on its glass
        self.bird = self.add(SillBird(self, self.window, self.outside))   # seen through the glass, by day
        self.passerby = self.add(Passerby(self, self.window, self.outside))
        self.fireplace = self.add(Fireplace(self))
        self.cat = self.add(Cat(self, self.fireplace))
        self.firelight = self.add(Firelight(self, self.fireplace))
        self.nook = self.add(Nook(self))

    def update_weather(self):
        self.weather["storm"] = 0
        self.weather["wind"] = self.draft.value
        cover = self.outside.cover() if hasattr(self, "outside") else 0
        self.weather["light"] = self.light.value * (1 - 0.5 * cover)

    def update(self, dt):
        self.update_weather()
        super().update(dt)
