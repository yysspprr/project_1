# Light in the mountains: beams of sunlight slanting down through the mist by day, and a
# little monastery on a far ridge, a thread of smoke rising from it by day and its windows
# glowing warm at night

import math

import random

import pygame

from partials.config import WIDTH, s
from partials.backgrounds.base import Layer
from partials.backgrounds.brook_light import glow_sprite
from partials.backgrounds.peaks_weather import Puffs


class SunBeams(Layer):
    # Broad, faint shafts of sunlight fanning down and to the left from the sun, through the
    # mist over the far ridges. Each one brightens and fades on its own, and all of them dim
    # when a cloud crosses the sun. By day only (needs "beam")
    #
    # Palette colors it uses:
    #   "beam"                      the light (it's laid over the scene, see-through)

    COUNT = 4
    STRENGTH = 0.3                 # how strong a beam is at its brightest
    REACH = 430                     # how far down the beams go, at the medium size

    def __init__(self, scene, sky):
        super().__init__(scene)
        self.origin = (sky.body_x, sky.body_y)
        self.beams = []
        for i in range(self.COUNT):
            angle = math.radians(105 + i * 11 + random.uniform(-3, 3))    # from straight down, round to the lower left
            self.beams.append({"angle": angle, "spread": math.radians(random.uniform(2.5, 4.5)),
                               "glow": self.swell(0, 1, (5000, 12000))})
        self.images = None
        self.palette = None

    def paint(self, palette):
        color = pygame.Color(palette["beam"])
        reach = s(self.REACH)
        ox, oy = self.origin
        self.images = []
        for beam in self.beams:
            a, spread = beam["angle"], beam["spread"]
            # A long thin wedge, widening away from the sun, then blurred soft
            tip = (ox + math.cos(a) * s(20), oy + math.sin(a) * s(20))
            left = (ox + math.cos(a - spread) * reach * 1.4, oy + math.sin(a - spread) * reach * 1.4)
            right = (ox + math.cos(a + spread) * reach * 1.4, oy + math.sin(a + spread) * reach * 1.4)
            xs = [tip[0], left[0], right[0]]
            box = pygame.Rect(int(min(xs)) - s(20), int(oy) - s(10), int(max(xs) - min(xs)) + s(40), reach)
            image = pygame.Surface(box.size, pygame.SRCALPHA)
            image.fill((color.r, color.g, color.b, 0))
            paint = pygame.Color(color.r, color.g, color.b, 255)
            pygame.draw.polygon(image, paint, [(x - box.x, y - box.y) for x, y in (tip, left, right)])
            # Fading out toward its far end
            fade = pygame.Surface((1, box.h), pygame.SRCALPHA)
            for y in range(box.h):
                fade.set_at((0, y), (255, 255, 255, int(255 * (1 - y / box.h) ** 1.3)))
            image.blit(pygame.transform.scale(fade, box.size), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            small = pygame.transform.smoothscale(image, (max(1, box.w // 6), max(1, box.h // 6)))
            image = pygame.transform.smoothscale(small, box.size)
            self.images.append((image, box.topleft))
        self.palette = palette

    def draw(self, surface, palette):
        if "beam" not in palette:
            return
        if self.palette is not palette:
            self.paint(palette)
        light = max(0, min(1.2, self.scene.weather["light"]))
        sun = max(0, (light - 0.8) / 0.35)                  # they only show when the sun is out
        for (image, place), beam in zip(self.images, self.beams):
            strength = self.STRENGTH * sun * (0.25 + 0.75 * beam["glow"].value)
            if strength > 0.01:
                image.set_alpha(int(255 * strength))
                surface.blit(image, place)


class Monastery(Layer):
    # A little whitewashed monastery perched on a far ridge on the left: two tapering blocks
    # with a dark red band under the roofs and a golden spire. By day a thread of smoke rises
    # from it and drifts off on the wind; at night its windows glow warm
    #
    # Palette colors it uses:
    #   "wall", "wall_shade", "wall_band", "gold", "window"
    #   "smoke"                     by day (no smoke without it)
    #   "window_glow"               at night (no glow without it)

    X = 44                          # where it stands, at the medium size
    SMOKE_RATE = 1.6                # puffs a second

    def __init__(self, scene, ridge):
        super().__init__(scene)
        self.time = 0
        self.x = s(self.X)
        self.y = ridge.top_at(self.x) + s(3)
        self.k = max(1, s(1))
        self.smoke = []
        self.waiting = 0
        self.flicker = self.swell(0.8, 1.0, (300, 900))
        self.palette = None
        for i in range(40):
            self.update(200)

    def update(self, dt):
        self.time += dt
        self.waiting -= dt * self.SMOKE_RATE / 1000
        while self.waiting <= 0:
            self.waiting += 1
            self.smoke.append({"x": self.x + s(6), "y": self.y - s(19), "age": 0.0, "life": random.uniform(5000, 8000)})
        wind = self.scene.weather["wind"]
        for p in self.smoke:
            p["age"] += dt
            p["y"] -= s(4) * dt / 1000
            p["x"] -= s(3) * wind * (p["age"] / 3000) * dt / 1000      # rises, then leans off on the wind
        self.smoke = [p for p in self.smoke if p["age"] < p["life"]]

    def paint(self, palette):
        self.glow = None
        if "window_glow" in palette:
            self.glow = glow_sprite(s(9), pygame.Color(palette["window_glow"]), flatten=0.8)
        self.puffs = Puffs(palette["smoke"]) if "smoke" in palette else None
        self.palette = palette

    def draw(self, surface, palette):
        if self.palette is not palette:
            self.paint(palette)
        x, y, k = self.x, self.y, s(1)
        wall = pygame.Color(palette["wall"])
        shade = pygame.Color(palette["wall_shade"])
        band = pygame.Color(palette["wall_band"])
        window = pygame.Color(palette["window"])
        night = self.glow is not None
        if night:
            window = window.lerp(pygame.Color(palette["window_glow"]), self.flicker.value)

        if self.puffs is not None:
            for p in self.smoke:
                t = p["age"] / p["life"]
                self.puffs.draw(surface, p["x"], p["y"], s(2) + s(6) * t, 0.35 * min(1, t * 5) * (1 - t))

        # The smaller block on the right, then the main one in front, both tapering upward
        pygame.draw.polygon(surface, shade, [(x + 6 * k, y), (x + 17 * k, y), (x + 16 * k, y - 9 * k), (x + 7 * k, y - 9 * k)])
        pygame.draw.rect(surface, band, (x + 7 * k, y - 11 * k, 9 * k, 2 * k))
        pygame.draw.polygon(surface, wall, [(x - 10 * k, y), (x + 9 * k, y), (x + 8 * k, y - 13 * k), (x - 9 * k, y - 13 * k)])
        pygame.draw.polygon(surface, shade, [(x - 10 * k, y), (x - 6 * k, y), (x - 6 * k, y - 13 * k), (x - 9 * k, y - 13 * k)])
        pygame.draw.rect(surface, band, (x - 9 * k, y - 16 * k, 17 * k, 3 * k))
        pygame.draw.line(surface, shade.lerp((0, 0, 0), 0.3), (x - 10 * k, y - 16 * k), (x + 9 * k, y - 16 * k), 1)
        # The golden spire on the roof
        gold = pygame.Color(palette["gold"])
        pygame.draw.polygon(surface, gold, [(x - 2 * k, y - 16 * k), (x + 2 * k, y - 16 * k), (x, y - 21 * k)])
        # Windows: a row on the main block, one on the small one
        windows = [(x - 4 * k, y - 9 * k), (x, y - 9 * k), (x + 4 * k, y - 9 * k), (x + 11 * k, y - 6 * k)]
        for wx, wy in windows:
            pygame.draw.rect(surface, window, (wx - k, wy - k, max(1, 2 * k), max(1, 3 * k)))
        if night:
            strength = self.flicker.value
            glow = self.glow.copy()
            glow.fill([int(255 * strength)] * 3, special_flags=pygame.BLEND_RGB_MULT)
            surface.blit(glow, glow.get_rect(center=(x + 2 * k, y - 8 * k)), special_flags=pygame.BLEND_RGB_ADD)
