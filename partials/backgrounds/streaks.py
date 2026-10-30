# Things falling onto the surface: rain streaks here, but the same layer can drop
# anything that falls straight down and lands somewhere (snow, petals...) with other settings

import random

import pygame

from partials.config import s
from partials.backgrounds.base import Layer


class FallingStreaks(Layer):
    # Each streak is aimed at a spot on the surface. It falls toward it, slanted a
    # little by the wind, and when it gets there it calls on_land(x, y), which is how
    # the rain background turns a landing drop into a ripple.
    # Falling distance, length and thickness all follow the scene's perspective
    #
    # Palette colors it uses:
    #   "rain"          the streak's color (falls back to "ripple", then "text")

    FALL_TIME = (380, 520)          # milliseconds from appearing to landing
    FALL_HEIGHT = 520               # how far a drop falls on screen, up close, in pixels
    LENGTH = (45, 70)               # how long a streak is, up close, in pixels
    WIDTH = 2                       # up close, in pixels
    WIND = 0.12                     # sideways slant at a normal breeze: pixels to the side per pixel down
    STRENGTH = 0.85                 # how strongly a streak shows (0 = invisible, 1 = full "rain" color)
    TAIL = 0.45                     # the back half of a streak is this much as strong as the front

    def __init__(self, scene, on_land=None):
        super().__init__(scene)
        self.on_land = on_land
        self.wind = 1               # the background can change this; 1 is a normal breeze
        self.streaks = []

    def add(self, x, y):
        # Start a drop falling toward (x, y)
        size = self.scene.view.scale(y)
        self.streaks.append({
            "x": x,
            "y": y,
            "size": size,
            "fall": s(self.FALL_HEIGHT) * size,
            "length": s(random.randint(*self.LENGTH)) * size,
            "time": random.randint(*self.FALL_TIME),
            "slant": self.WIND * self.wind,     # the wind when it started falling
            "age": 0,
        })

    def update(self, dt):
        falling = []
        for streak in self.streaks:
            streak["age"] += dt
            if streak["age"] < streak["time"]:
                falling.append(streak)
            elif self.on_land is not None:
                self.on_land(streak["x"], streak["y"])
        self.streaks = falling

    def head(self, streak, left):
        # Where the front of the streak is when it still has left (0-1) of its fall to go
        drop = streak["fall"] * left
        return (streak["x"] - drop * streak["slant"], streak["y"] - drop)

    def draw(self, surface, palette):
        view = self.scene.view
        rain_color = pygame.Color(palette.get("rain", palette.get("ripple", palette["text"])))

        for streak in self.streaks:
            left = 1 - streak["age"] / streak["time"]           # 1 when it appears, 0 when it lands
            head_x, head_y = self.head(streak, left)
            # The streak trails back up along its path, but never above where it started
            trail = min(streak["length"], streak["fall"] * (1 - left))
            middle = (head_x - trail / 2 * streak["slant"], head_y - trail / 2)
            tail = (head_x - trail * streak["slant"], head_y - trail)

            # Fade into what's behind it, a little stronger close to us
            water = self.scene.color_at(palette, head_y)
            strength = self.STRENGTH * view.clarity(streak["y"])
            front_color = water.lerp(rain_color, strength)
            back_color = water.lerp(rain_color, strength * self.TAIL)
            line = max(1, round(s(self.WIDTH) * streak["size"]))

            pygame.draw.line(surface, back_color, tail, middle, line)
            pygame.draw.line(surface, front_color, middle, (head_x, head_y), line)
