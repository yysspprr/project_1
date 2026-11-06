# Light and motion in space: a pulsar flashing away on the left, the pale blue dot of the
# Earth hanging in a faint ray of sunlight, Voyager's radio signal pulsing home toward it,
# a comet sailing past now and then with its tails streaming away from the Sun, and very
# rarely a far star flaring up as a supernova
#
# Everything here glows, so it's drawn with shine() (see cosmos.py): added on in dark mode,
# taken away in the negative of light mode

import math

import random

import pygame

from partials.config import WIDTH, HEIGHT, UI_SCALE, s
from partials.backgrounds.base import Layer
from partials.backgrounds.helpers import Timer
from partials.backgrounds.brook_light import glow_sprite
from partials.backgrounds.cosmos import shine, blur


def scaled(color, strength):
    strength = max(0.0, min(1.0, strength))
    return (int(color[0] * strength), int(color[1] * strength), int(color[2] * strength))


class Pulsar(Layer):
    # A pulsar far off on the left: a dead star spinning fast, flashing twice a turn as its
    # two beams sweep past us, a thin cross of light flicking out with each flash
    #
    # Palette colors it uses:
    #   "pulsar"

    PLACE = (52, 318)
    PERIOD = 900                    # milliseconds for one turn

    def __init__(self, scene):
        super().__init__(scene)
        self.x, self.y = s(self.PLACE[0]), s(self.PLACE[1])
        self.time = 0
        self.palette = None

    def update(self, dt):
        self.time += dt

    def draw(self, surface, palette):
        if self.palette is not palette:
            self.color, self.blend = shine(palette, "pulsar")
            self.glow = glow_sprite(s(10), self.color)
            self.palette = palette
        t = (self.time % self.PERIOD) / self.PERIOD
        flash = max(math.exp(-((t - 0.25) * 18) ** 2), 0.6 * math.exp(-((t - 0.75) * 18) ** 2))   # a big flash and a smaller one
        x, y = self.x, self.y
        surface.fill(scaled(self.color, 0.35 + 0.65 * flash), (x - 1, y - 1, max(2, s(2)), max(2, s(2))), special_flags=self.blend)
        if flash > 0.05:
            glow = self.glow.copy()
            glow.fill([int(255 * flash)] * 3, special_flags=pygame.BLEND_RGB_MULT)
            surface.blit(glow, glow.get_rect(center=(x, y)), special_flags=self.blend)
            reach = s(14) * flash
            faint = scaled(self.color, flash * 0.6)
            surface.fill(faint, (x - reach, y, reach * 2, 1), special_flags=self.blend)
            surface.fill(faint, (x, y - reach * 0.6, 1, reach * 1.2), special_flags=self.blend)


class PaleBlueDot(Layer):
    # The Earth, seen from the edge of the solar system: a single pale blue pixel, hanging in a
    # faint ray of scattered sunlight, just as Voyager saw it looking back
    #
    # Palette colors it uses:
    #   "earth", "sunbeam"

    PLACE = (366, 168)

    def __init__(self, scene):
        super().__init__(scene)
        self.x, self.y = s(self.PLACE[0]), s(self.PLACE[1])
        self.time = 0
        self.palette = None

    def update(self, dt):
        self.time += dt

    def paint(self, palette):
        # The ray: a long, soft, slanting band of light passing through the dot
        color, self.blend = shine(palette, "sunbeam")
        w, h = s(40), s(240)
        ray = pygame.Surface((w, h))
        ray.fill((0, 0, 0))
        for y in range(h):
            fade = math.sin(math.pi * y / h) ** 1.5
            pygame.draw.line(ray, scaled(color, fade), (w / 2 - s(3), y), (w / 2 + s(3), y))
        ray = blur(ray, 4)
        self.ray = pygame.transform.rotate(ray, -7)
        self.dot, _ = shine(palette, "earth")
        self.palette = palette

    def draw(self, surface, palette):
        if self.palette is not palette:
            self.paint(palette)
        surface.blit(self.ray, self.ray.get_rect(center=(self.x, self.y)), special_flags=self.blend)
        pulse = 0.85 + 0.15 * math.sin(self.time / 1600)
        surface.fill(scaled(self.dot, pulse), (self.x, self.y, max(1, s(1.5)), max(1, s(1.5))), special_flags=self.blend)


class Signal(Layer):
    # Voyager calling home: every so often a burst of radio waves leaves its dish, a few arcs
    # rising one after another up toward the pale blue dot, widening and fading as they go
    #
    # Palette colors it uses:
    #   "signal"

    EVERY = (5000, 9000)
    ARCS = 3
    TRAVEL = 4200                   # milliseconds an arc takes to fade out on its way

    def __init__(self, scene, voyager, earth):
        super().__init__(scene)
        self.voyager = voyager
        self.earth = earth
        self.timer = Timer(self.EVERY)
        self.timer.left = 1500
        self.arcs = []
        self.palette = None

    def update(self, dt):
        if self.timer.tick(dt):
            for n in range(self.ARCS):
                self.arcs.append({"age": -n * 350.0})
        for arc in self.arcs:
            arc["age"] += dt
        self.arcs = [arc for arc in self.arcs if arc["age"] < self.TRAVEL]

    def draw(self, surface, palette):
        if not self.arcs:
            return
        if self.palette is not palette:
            self.color, self.blend = shine(palette, "signal")
            self.palette = palette
        start = self.voyager.at(1, -22)                         # the dish's feed
        end = (self.earth.x, self.earth.y)
        dx, dy = end[0] - start[0], end[1] - start[1]
        distance = math.hypot(dx, dy)
        heading = math.atan2(dy, dx)
        for arc in self.arcs:
            if arc["age"] < 0:
                continue
            t = arc["age"] / self.TRAVEL
            x, y = start[0] + dx * t * 0.8, start[1] + dy * t * 0.8
            radius = s(7) + s(16) * t
            strength = (1 - t) ** 1.3 * 0.9 * self.scene.keep(x, 0.5)
            points = []
            for i in range(9):
                a = heading + (i / 8 - 0.5) * 1.7
                points.append((x - math.cos(heading) * radius + math.cos(a) * radius, y - math.sin(heading) * radius + math.sin(a) * radius))
            arc_surface = pygame.Surface((s(60), s(60)))
            arc_surface.fill((0, 0, 0))
            ox, oy = x - s(30), y - s(30)
            pygame.draw.lines(arc_surface, scaled(self.color, strength), False, [(px - ox, py - oy) for px, py in points], max(1, s(1.5)))
            surface.blit(arc_surface, (ox, oy), special_flags=self.blend)


class Comet(Layer):
    # Every few minutes a comet sails slowly across the sky: a bright fuzzy head, a broad
    # curving dust tail and a thin straight blue ion tail, both streaming away from the Sun
    #
    # Palette colors it uses:
    #   "comet", "comet_dust", "comet_ion"

    WAIT = (90000, 200000)
    FIRST = (30000, 80000)
    TIME = 32000

    def __init__(self, scene, sun):
        super().__init__(scene)
        self.sun = sun
        self.timer = Timer(self.WAIT)
        self.timer.left = random.uniform(*self.FIRST)
        self.flight = None
        self.palette = None

    def start(self):
        y0 = s(random.uniform(60, 200))
        way = random.choice((-1, 1))
        self.flight = {"age": 0.0, "from": (-s(30) if way > 0 else WIDTH + s(30), y0),
                       "to": (WIDTH + s(30) if way < 0 else WIDTH + s(30), y0 + s(random.uniform(60, 140)))}
        if way < 0:
            self.flight["to"] = (-s(30), y0 + s(random.uniform(60, 140)))

    def update(self, dt):
        if self.flight is None:
            if self.timer.tick(dt):
                self.start()
            return
        self.flight["age"] += dt
        if self.flight["age"] > self.TIME:
            self.flight = None

    def draw(self, surface, palette):
        if self.flight is None:
            return
        if self.palette is not palette:
            self.head, self.blend = shine(palette, "comet")
            self.dust, _ = shine(palette, "comet_dust")
            self.ion, _ = shine(palette, "comet_ion")
            self.glow = glow_sprite(s(8), self.head)
            self.palette = palette
        t = self.flight["age"] / self.TIME
        (ax, ay), (bx, by) = self.flight["from"], self.flight["to"]
        x, y = ax + (bx - ax) * t, ay + (by - ay) * t
        show = min(1, t * 8, (1 - t) * 8) * self.scene.keep(x, 0.45)
        # The tails point away from the Sun
        away = math.atan2(y - self.sun.y, x - self.sun.x)
        length = s(95)
        for n in range(24):
            u = n / 24
            # Dust: broad, curving a little behind the comet's path
            bend = u * u * 0.35 * (1 if bx > ax else -1)
            dx = x + math.cos(away + bend) * length * u
            dy = y + math.sin(away + bend) * length * u
            strength = (1 - u) ** 1.4 * 0.55 * show
            size = max(1, s(1.5) + s(6) * u)
            surface.fill(scaled(self.dust, strength), (dx - size / 2, dy - size / 2, size, size), special_flags=self.blend)
            # Ion: thin and straight, a little longer
            ix = x + math.cos(away) * length * 1.2 * u
            iy = y + math.sin(away) * length * 1.2 * u
            surface.fill(scaled(self.ion, (1 - u) * 0.8 * show), (ix, iy, max(1, s(1.5)), max(1, s(1.5))), special_flags=self.blend)
        glow = self.glow.copy()
        glow.fill([int(255 * show)] * 3, special_flags=pygame.BLEND_RGB_MULT)
        surface.blit(glow, glow.get_rect(center=(x, y)), special_flags=self.blend)
        surface.fill(scaled(self.head, show), (x - 1, y - 1, max(2, s(2.5)), max(2, s(2.5))), special_flags=self.blend)


class Supernova(Layer):
    # Very rarely, a star somewhere off at the side flares up: over a few seconds it grows to
    # outshine everything, with long spikes of light, then slowly fades back to nothing
    #
    # Palette colors it uses:
    #   "supernova"

    WAIT = (240000, 480000)
    FIRST = (120000, 240000)
    RISE = 4000
    FADE = 30000

    def __init__(self, scene):
        super().__init__(scene)
        self.timer = Timer(self.WAIT)
        self.timer.left = random.uniform(*self.FIRST)
        self.flare = None
        self.palette = None

    def update(self, dt):
        if self.flare is None:
            if self.timer.tick(dt):
                self.flare = {"age": 0.0, "x": self.scene.margin_x(), "y": s(random.uniform(60, 380))}
            return
        self.flare["age"] += dt
        if self.flare["age"] > self.RISE + self.FADE:
            self.flare = None

    def draw(self, surface, palette):
        if self.flare is None:
            return
        if self.palette is not palette:
            self.color, self.blend = shine(palette, "supernova")
            self.glow = glow_sprite(s(28), self.color)
            self.palette = palette
        a = self.flare["age"]
        strength = (a / self.RISE) ** 2 if a < self.RISE else (1 - (a - self.RISE) / self.FADE) ** 2
        x, y = self.flare["x"], self.flare["y"]
        glow = self.glow.copy()
        glow.fill([int(255 * strength)] * 3, special_flags=pygame.BLEND_RGB_MULT)
        surface.blit(glow, glow.get_rect(center=(x, y)), special_flags=self.blend)
        reach = s(30) * strength
        for dx, dy in ((1, 0), (0, 1)):
            surface.fill(scaled(self.color, strength * 0.7), (x - reach * dx, y - reach * dy, max(1, reach * 2 * dx), max(1, reach * 2 * dy)),
                         special_flags=self.blend)
        surface.fill(scaled(self.color, strength), (x - 1, y - 1, max(2, s(2.5)), max(2, s(2.5))), special_flags=self.blend)
