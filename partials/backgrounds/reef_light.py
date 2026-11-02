# Light under the sea. By day: caustics, the dancing net of light that sunlight focused by
# the ripples above throws over the sand and the coral. By night: plankton that lights up
# blue-green when the water around it is stirred (a bubble rising, a fish darting by),
# swirling and fading again

import math

import random

import pygame

from partials.config import WIDTH, HEIGHT, s
from partials.backgrounds.base import Layer
from partials.backgrounds.brook_light import glow_sprite


def caustic_tile(width, height, cells, seed):
    # A seamless tile of the caustic net: bright lines along the edges between irregular
    # cells (where the distances to the two nearest cell centers are nearly equal)
    rng = random.Random(seed)
    points = [(rng.uniform(0, width), rng.uniform(0, height)) for i in range(cells)]
    # Copies of the points around the tile, so the pattern wraps at the edges
    wrapped = [(x + dx * width, y + dy * height) for x, y in points for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
    tile = pygame.Surface((width, height))
    for py in range(height):
        for px in range(width):
            d1 = d2 = 1e9
            for x, y in wrapped:
                d = (x - px) ** 2 + (y - py) ** 2
                if d < d1:
                    d1, d2 = d, d1
                elif d < d2:
                    d2 = d
            gap = math.sqrt(d2) - math.sqrt(d1)
            v = max(0.0, 1 - gap / 3.2) ** 2.2
            tile.set_at((px, py), (int(255 * v),) * 3)
    return tile


class Caustics(Layer):
    # Two nets of light drifting over the sea floor in different directions, so where they
    # cross the light seems to dance. Laid flat on the floor (squashed with distance), added
    # onto the sand and coral, gentler behind the middle of the game. Daytime only: needs
    # "caustic" in the palette
    #
    # Palette colors it uses:
    #   "caustic"               the light (added onto the floor)
    #   "caustic_strength"      how bright, 0 to 1

    TILE = (48, 30)                 # the pattern's tile, in its own small pixels
    SCALE = 3.2                     # how much bigger it's drawn, at the medium size
    CELLS = 9

    def __init__(self, scene, floor):
        super().__init__(scene)
        self.floor = floor
        self.time = 0
        self.top = int(min(floor.floor_y(x) for x in range(0, WIDTH, 4))) - s(30)
        size = (int(self.TILE[0] * s(self.SCALE)), int(self.TILE[1] * s(self.SCALE)))
        self.tiles = [pygame.transform.smoothscale(caustic_tile(*self.TILE, self.CELLS, seed), size) for seed in (1, 2)]
        self.mask = None
        self.painted_palette = None

    def paint(self, palette):
        # Where the light can fall: the floor (and what grows on it), fading in from its top
        # edge, and softer in the middle; tinted with the light's color and strength
        color = pygame.Color(palette["caustic"])
        strength = palette.get("caustic_strength", 0.3)
        height = HEIGHT - self.top
        mask = pygame.Surface((WIDTH, height))
        mask.fill((0, 0, 0))
        for x in range(0, WIDTH, 2):
            edge = self.floor.floor_y(x) - s(26) - self.top
            quiet = self.scene.keep(x, 0.55)
            for y in range(max(0, int(edge)), height, 2):
                fade = max(0.0, min(1.0, (y - edge) / s(30))) * strength * quiet
                mask.fill((int(color.r * fade), int(color.g * fade), int(color.b * fade)), (x, y, 2, 2))
        self.mask = mask
        self.layer = pygame.Surface((WIDTH, height))
        self.painted_palette = palette

    def update(self, dt):
        self.time += dt

    def draw(self, surface, palette):
        if "caustic" not in palette:
            return
        if self.painted_palette is not palette:
            self.paint(palette)
        light = min(1.2, self.scene.weather.get("light", 1))
        layer = self.layer
        layer.fill((0, 0, 0))
        t = self.time / 1000
        # Each net tiled across the floor, scrolling its own way
        for k, tile in enumerate(self.tiles):
            w, h = tile.get_size()
            ox = (t * s(9) * (1 if k == 0 else -0.7)) % w
            oy = (t * s(4) * (1 if k == 0 else 1.3)) % h
            for x in range(-w, WIDTH + w, w):
                for y in range(-h, layer.get_height() + h, h):
                    layer.blit(tile, (x + ox, y + oy), special_flags=pygame.BLEND_RGB_MAX if k else 0)
        layer.blit(self.mask, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        if light < 0.99:
            level = int(255 * light)
            layer.fill((level, level, level), special_flags=pygame.BLEND_RGB_MULT)
        surface.blit(layer, (0, self.top), special_flags=pygame.BLEND_RGB_ADD)


class Plankton(Layer):
    # At night the water is full of tiny plankton that glow blue-green when stirred. Others
    # call stir(x, y, radius) when something moves through the water (a fish, a jellyfish);
    # rising bubbles stir it too. Each speck flares up, then fades over a second or two,
    # drifting with the swell. Night only: needs "glow" in the palette
    #
    # Palette colors it uses:
    #   "glow"                  the plankton's light

    COUNT = 140
    FADE = 1600                     # milliseconds to fade from full glow
    TWINKLE = 0.004                 # chance a second that a speck glows on its own

    def __init__(self, scene, bubbles=None):
        super().__init__(scene)
        self.bubbles = bubbles
        self.time = 0
        self.specks = [{"x": random.uniform(0, WIDTH), "y": random.uniform(s(30), HEIGHT), "glow": 0.0,
                        "phase": random.uniform(0, 6)} for i in range(self.COUNT)]
        self.sprites = None
        self.painted_palette = None

    def stir(self, x, y, radius):
        for p in self.specks:
            d = math.hypot(p["x"] - x, p["y"] - y)
            if d < radius:
                p["glow"] = max(p["glow"], 1 - d / radius * 0.6)

    def update(self, dt):
        self.time += dt
        swell = self.scene.weather.get("surge", 0)
        for p in self.specks:
            p["glow"] = max(0.0, p["glow"] - dt / self.FADE)
            if random.random() < self.TWINKLE * dt / 1000 * 60:
                p["glow"] = max(p["glow"], random.uniform(0.3, 0.7))
            p["x"] = (p["x"] + (swell * s(10) + math.sin(self.time / 1700 + p["phase"]) * s(3)) * dt / 1000) % WIDTH
            p["y"] += math.cos(self.time / 2100 + p["phase"]) * s(2) * dt / 1000
        if self.bubbles is not None and self.painted_palette is not None and "glow" in self.painted_palette:
            for b in self.bubbles.bubbles:
                if random.random() < dt / 120:
                    self.stir(b["x"], b["y"], s(14))

    def paint(self, palette):
        color = pygame.Color(palette["glow"])
        self.sprites = [glow_sprite(s(7) * (0.5 + 0.5 * k / 5), (color.r * k / 5, color.g * k / 5, color.b * k / 5), 1.0, 5) for k in range(1, 6)]
        self.core = color
        self.painted_palette = palette

    def draw(self, surface, palette):
        if "glow" not in palette:
            self.painted_palette = palette
            return
        if self.painted_palette is not palette or self.sprites is None:
            self.paint(palette)
        for p in self.specks:
            glow = p["glow"] * self.scene.keep(p["x"], 0.5)
            if glow < 0.1:
                continue
            sprite = self.sprites[min(4, int(glow * 5))]
            surface.blit(sprite, sprite.get_rect(center=(int(p["x"]), int(p["y"]))), special_flags=pygame.BLEND_RGB_ADD)
            behind = self.scene.color_at(palette, p["y"])
            surface.set_at((int(p["x"]), int(p["y"])), behind.lerp(self.core, min(1.0, glow)))
