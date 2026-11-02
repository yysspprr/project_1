# The city's weather: steam and smoke puffing from the chimney pots and rooftop vents and
# drifting off on the wind, and a line of washing on our roof flapping in the breeze

import math

import random

import pygame

from partials.config import WIDTH, UI_SCALE, s
from partials.backgrounds.base import Layer
from partials.backgrounds.peaks_weather import Puffs


class Steam(Layer):
    # Puffs of steam rising from the chimney pots on our roof and from vents on the roofs
    # below, swelling and thinning as they lean off on the wind (to the left)
    #
    # Palette colors it uses:
    #   "steam"

    RATE = 2.2                      # puffs a second from each source
    LIFE = (3500, 6000)

    def __init__(self, scene, rooftop, row):
        super().__init__(scene)
        k = s(1)
        cx, cy = s(rooftop.CHIMNEY[0]), s(rooftop.CHIMNEY[1])
        self.sources = [(cx - 5 * k, cy - 46 * k - s(12), 1.0), (cx + 5 * k, cy - 46 * k - s(12), 0.7)]
        # A couple of vents on the low rooftops below the railway, out at the sides
        sides = [b for b in row.buildings if (b["x"] + b["w"] * 0.6 < s(100) or b["x"] + b["w"] * 0.6 > WIDTH - s(100))]
        for b in random.sample(sides, min(2, len(sides))):
            self.sources.append((b["x"] + b["w"] * 0.6, b["top"] - s(3), 0.8))
        self.puffs = []
        self.waiting = [random.uniform(0, 1) for source in self.sources]
        self.palette = None
        for i in range(30):
            self.update(200)

    def update(self, dt):
        wind = self.scene.weather["wind"]
        for n, (x, y, size) in enumerate(self.sources):
            self.waiting[n] -= dt * self.RATE / 1000
            while self.waiting[n] <= 0:
                self.waiting[n] += random.uniform(0.7, 1.3)
                self.puffs.append({"x": x + random.uniform(-s(1), s(1)), "y": y, "age": 0.0, "life": random.uniform(*self.LIFE), "size": size})
        seconds = dt / 1000
        for p in self.puffs:
            p["age"] += dt
            t = p["age"] / p["life"]
            p["y"] -= s(12) * (1 - t * 0.6) * seconds
            p["x"] -= s(10) * wind * min(1, t * 2) * seconds
        self.puffs = [p for p in self.puffs if p["age"] < p["life"]]

    def draw(self, surface, palette):
        if self.palette is not palette:
            self.sprites = Puffs(palette["steam"])
            self.palette = palette
        for p in self.puffs:
            t = p["age"] / p["life"]
            radius = (s(2) + s(9) * t ** 0.8) * p["size"]
            self.sprites.draw(surface, p["x"], p["y"], radius, 0.45 * min(1, t * 6) * (1 - t) ** 1.3 * self.scene.keep(p["x"], 0.6))


class Laundry(Layer):
    # A washing line on our roof, from the chimney to a pole at the end of the parapet: a
    # shirt, a towel and a pair of socks, pegged on and flapping in the wind
    #
    # Palette colors it uses:
    #   "laundry"           a list of colors for the washing
    #   "line", "peg"       the line (and its pole), and the pegs

    FROM = (386, 532)               # the end tied to the chimney, at the medium size
    POLE = (328, 604)               # the foot of the pole on the parapet
    POLE_HEIGHT = 62
    SAG = 7

    def __init__(self, scene):
        super().__init__(scene)
        self.time = 0
        self.a = (s(self.FROM[0]), s(self.FROM[1]))
        self.pole = (s(self.POLE[0]), s(self.POLE[1]))
        self.b = (self.pole[0], self.pole[1] - s(self.POLE_HEIGHT))
        # (where along the line, width, height, kind)
        self.items = [(0.2, 13, 13, "shirt"), (0.5, 11, 15, "towel"), (0.72, 4, 8, "sock"), (0.82, 4, 8, "sock")]
        self.phases = [random.uniform(0, 6.3) for item in self.items]

    def point(self, t):
        (ax, ay), (bx, by) = self.a, self.b
        return ax + (bx - ax) * t, ay + (by - ay) * t + s(self.SAG) * math.sin(math.pi * t)

    def update(self, dt):
        self.time += dt

    def draw(self, surface, palette):
        k = UI_SCALE
        line = pygame.Color(palette["line"])
        peg = pygame.Color(palette["peg"])
        colors = [pygame.Color(c) for c in palette["laundry"]]
        wind = self.scene.weather["wind"] + self.scene.weather.get("gust", 0)
        pygame.draw.line(surface, line, self.pole, (self.b[0], self.b[1] - s(2)), max(1, s(2)))
        pygame.draw.lines(surface, line, False, [self.point(i / 12) for i in range(13)], 1)
        for n, (t, w, h, kind) in enumerate(self.items):
            x, y = self.point(t)
            w, h = w * k, h * k
            beat = math.sin(self.time / 180 + self.phases[n]) * 0.5 + math.sin(self.time / 77 + self.phases[n] * 2) * 0.25
            swing = -(0.4 + 0.5 * wind) * s(4) * (0.7 + 0.3 * beat)          # blown to the left
            ripple = beat * s(1.5) * wind
            color = colors[n % len(colors)]
            shade = color.lerp((0, 0, 0), 0.15)
            top_l, top_r = (x - w / 2, y), (x + w / 2, y)
            if kind == "shirt":
                body = [top_l, top_r, (x + w * 0.85 + swing * 0.5, y + h * 0.3), (x + w * 0.4 + swing * 0.6, y + h * 0.4),
                        (x + w * 0.35 + swing, y + h), (x - w * 0.35 + swing + ripple, y + h), (x - w * 0.4 + swing * 0.6, y + h * 0.4),
                        (x - w * 0.85 + swing * 0.5, y + h * 0.3)]
                pygame.draw.polygon(surface, color, body)
                pygame.draw.line(surface, shade, (x, y + s(1)), (x + swing * 0.9, y + h - s(1)), 1)
            elif kind == "sock":
                foot = 4 * k
                pygame.draw.polygon(surface, color, [top_l, top_r, (x + w / 2 + swing, y + h), (x + w / 2 + swing - foot, y + h + foot * 0.6),
                                                     (x - w / 2 + swing - foot, y + h), (x - w / 2 + swing, y + h * 0.7)])
            else:
                pygame.draw.polygon(surface, color, [top_l, top_r, (x + w / 2 + swing + ripple, y + h), (x + swing * 0.5, y + h - ripple * 0.5),
                                                     (x - w / 2 + swing - ripple, y + h)])
                if kind == "towel":                             # a stripe across it
                    pygame.draw.line(surface, shade, (x - w / 2 + swing * 0.75, y + h * 0.75), (x + w / 2 + swing * 0.75, y + h * 0.75), max(1, s(2)))
            for px in (x - w * 0.35, x + w * 0.35):
                pygame.draw.line(surface, peg, (px, y - s(2)), (px, y + s(2)), max(1, s(1)))
