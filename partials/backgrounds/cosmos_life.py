# Visitors in space. Regulars: now and then a few small asteroids come tumbling past at
# the sides. Rare visitors, one at a time: a little rocket blasting off up the side, a
# flying saucer zipping in to hover and shine its beam on the moon, an astronaut drifting
# by, slowly tumbling and waving, and a great shimmering solar sail gliding across the top
#
# Anything that glows (flames, lights, glints) is drawn with shine(), so it darkens the
# negative of light mode instead

import math

import random

import pygame

from partials.config import WIDTH, HEIGHT, UI_SCALE, s
from partials.backgrounds.base import Layer
from partials.backgrounds.helpers import Timer
from partials.backgrounds.brook_life import Visitor
from partials.backgrounds.brook_light import glow_sprite
from partials.backgrounds.cosmos import shine
from partials.backgrounds.cosmos_light import scaled


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def turned(x, y, angle, k):
    # A function placing points given in an object's own units (u right, v down) on the
    # screen, turned by angle and sized by k
    cos, sin = math.cos(angle), math.sin(angle)
    return lambda u, v: (x + (u * cos - v * sin) * k, y + (u * sin + v * cos) * k)


class Asteroids(Layer):
    # Every so often a few lumpy little asteroids come tumbling past at one side, each turning
    # at its own pace, lit on the side toward the Sun, with a crater or two
    #
    # Palette colors it uses:
    #   "rock", "rock_light", "rock_dark"

    WAIT = (18000, 40000)
    COUNT = (2, 4)

    def __init__(self, scene):
        super().__init__(scene)
        self.timer = Timer(self.WAIT)
        self.timer.left = random.uniform(4000, 15000)
        self.rocks = []

    def launch(self):
        side = random.choice((-1, 1))
        y = s(random.uniform(150, 400))
        for i in range(random.randint(*self.COUNT)):
            size = random.uniform(3, 9)
            corners = random.randint(7, 10)
            self.rocks.append({
                "x": -s(20) - random.uniform(0, s(60)) if side > 0 else WIDTH + s(20) + random.uniform(0, s(60)),
                "y": y + random.uniform(-s(50), s(50)),
                "vx": side * s(random.uniform(10, 22)), "vy": random.uniform(-s(4), s(4)),
                "angle": random.uniform(0, 6.3), "spin": random.uniform(-1.2, 1.2),
                "size": size, "shape": [random.uniform(0.7, 1.15) for c in range(corners)],
                "craters": [(random.uniform(-0.4, 0.4), random.uniform(-0.4, 0.4), random.uniform(0.15, 0.3)) for c in range(random.randint(1, 2))],
            })

    def update(self, dt):
        if self.timer.tick(dt):
            self.launch()
        seconds = dt / 1000
        for r in self.rocks:
            r["x"] += r["vx"] * seconds
            r["y"] += r["vy"] * seconds
            r["angle"] += r["spin"] * seconds
        self.rocks = [r for r in self.rocks if -s(100) < r["x"] < WIDTH + s(100)]

    def draw(self, surface, palette):
        rock = pygame.Color(palette["rock"])
        light = pygame.Color(palette["rock_light"])
        dark = pygame.Color(palette["rock_dark"])
        for r in self.rocks:
            at = turned(r["x"], r["y"], r["angle"], r["size"] * UI_SCALE)
            count = len(r["shape"])
            outline = [at(math.cos(2 * math.pi * c / count) * push, math.sin(2 * math.pi * c / count) * push) for c, push in enumerate(r["shape"])]
            fade = self.scene.keep(r["x"], 0.6)
            behind = pygame.Color(palette["space_low"])
            pygame.draw.polygon(surface, behind.lerp(rock, fade), outline)
            # The sunlit side: the same shape, smaller and shifted toward the Sun (up and right)
            k = r["size"] * UI_SCALE
            lit = [(x + (r["x"] - x) * 0.35 + k * 0.3, y + (r["y"] - y) * 0.35 - k * 0.3) for x, y in outline]
            pygame.draw.polygon(surface, behind.lerp(light, fade), lit)
            for cu, cv, cr in r["craters"]:
                pygame.draw.circle(surface, behind.lerp(dark, fade * 0.8), at(cu, cv), max(1, cr * k))


class Rocket(Visitor):
    # A little rocket blasting past up one side: white with red fins and a round window,
    # a flickering flame behind it and a trail of glowing exhaust fading away
    #
    # Palette colors it uses:
    #   "rocket", "rocket_trim", "porthole"
    #   "flame", "flame_core"       (they glow)

    TIME = 9000

    def start(self):
        super().start()
        self.age = 0.0
        self.side = random.choice((-1, 1))
        self.trail = []
        self.palette = None

    def place(self, age):
        t = age / self.TIME
        x0 = s(46) if self.side < 0 else WIDTH - s(46)
        x = x0 + math.sin(t * 2.2) * s(22) * self.side
        y = HEIGHT + s(30) - (HEIGHT + s(80)) * t
        return x, y

    def update(self, dt):
        if not self.active:
            return
        self.age += dt
        x, y = self.place(self.age)
        self.trail.append({"x": x + random.uniform(-s(1), s(1)), "y": y + s(14), "age": 0.0})
        for p in self.trail:
            p["age"] += dt
        self.trail = [p for p in self.trail if p["age"] < 1200]
        if self.age > self.TIME:
            self.active = False

    def draw(self, surface, palette):
        if not self.active:
            return
        if self.palette is not palette:
            self.flame, self.blend = shine(palette, "flame")
            self.core, _ = shine(palette, "flame_core")
            self.glow = glow_sprite(s(9), self.flame)
            self.palette = palette
        for p in self.trail:
            t = p["age"] / 1200
            size = max(1, s(2) + s(4) * t)
            surface.fill(scaled(self.flame, (1 - t) * 0.5), (p["x"] - size / 2, p["y"] + t * s(6), size, size), special_flags=self.blend)
        x, y = self.place(self.age)
        nx, ny = self.place(self.age + 100)
        angle = math.atan2(ny - y, nx - x) + math.pi / 2          # nose along its path
        k = 1.4 * UI_SCALE
        at = turned(x, y, angle, k)
        body = pygame.Color(palette["rocket"])
        trim = pygame.Color(palette["rocket_trim"])
        # The flame, flickering
        flick = 1 + 0.3 * math.sin(self.age / 30) + 0.2 * math.sin(self.age / 13)
        surface.blit(self.glow, self.glow.get_rect(center=at(0, 12)), special_flags=self.blend)
        flame = pygame.Surface((s(20), s(30)))
        flame.fill((0, 0, 0))
        local = turned(s(10), s(4), angle, k)
        pygame.draw.polygon(flame, self.flame, [local(-3, 8), local(3, 8), local(0, 8 + 9 * flick)])
        pygame.draw.polygon(flame, self.core, [local(-1.5, 8), local(1.5, 8), local(0, 8 + 5 * flick)])
        ox, oy = at(0, 0)
        surface.blit(flame, (ox - s(10), oy - s(4)), special_flags=self.blend)
        # The fins, the body and its nose, and the porthole
        for side in (-1, 1):
            pygame.draw.polygon(surface, trim, [at(side * 3, 3), at(side * 7, 9), at(side * 3, 8)])
        pygame.draw.polygon(surface, body, [at(-3, 8), at(-3.5, -2), at(-2, -8), at(0, -11), at(2, -8), at(3.5, -2), at(3, 8)])
        pygame.draw.polygon(surface, trim, [at(-2, -8), at(0, -11), at(2, -8)])
        pygame.draw.circle(surface, trim, at(0, -2), max(1, 2.2 * k))
        pygame.draw.circle(surface, pygame.Color(palette["porthole"]), at(0, -2), max(1, 1.5 * k))


class Saucer(Visitor):
    # A flying saucer: it zips in from the side, stops dead above the little moon and hovers
    # there, wobbling, the lights round its rim chasing each other, shining a beam down on the
    # moon for a while, then shoots off again
    #
    # Palette colors it uses:
    #   "saucer", "saucer_dark", "dome"
    #   "saucer_lights"             a list of colors for the lights round the rim (they glow)
    #   "saucer_beam"               its beam (glows)

    TIME = 16000

    def __init__(self, scene, planet):
        super().__init__(scene)
        self.moon = (s(planet.MOON[0]), s(planet.MOON[1]))
        self.palette = None

    def start(self):
        super().start()
        self.age = 0.0
        self.side = random.choice((-1, 1))

    def update(self, dt):
        if not self.active:
            return
        self.age += dt
        if self.age > self.TIME:
            self.active = False

    def place(self):
        hx, hy = self.moon[0] + s(18), self.moon[1] - s(46)
        a = self.age
        if a < 1200:                                            # in fast
            u = ease(a / 1200)
            sx = -s(40) if self.side > 0 else WIDTH + s(40)
            return sx + (hx - sx) * u, hy - (1 - u) * s(60)
        if a > self.TIME - 900:                                 # and gone
            u = ease((a - self.TIME + 900) / 900)
            return hx + u * (WIDTH + s(80)) * self.side, hy - u * s(120)
        return hx + math.sin(a / 700) * s(2), hy + math.sin(a / 450) * s(2)

    def draw(self, surface, palette):
        if not self.active:
            return
        if self.palette is not palette:
            self.lights = [shine({"c": c, "negative": palette.get("negative")}, "c") for c in palette["saucer_lights"]]
            self.beam, self.blend = shine(palette, "saucer_beam")
            self.palette = palette
        x, y = self.place()
        k = 1.3 * UI_SCALE
        tilt = math.sin(self.age / 600) * 0.12
        at = turned(x, y, tilt, k)
        if 2500 < self.age < self.TIME - 2000:
            # The beam: a widening cone of light down onto the moon, flickering
            strength = min(1, (self.age - 2500) / 800, (self.TIME - 2000 - self.age) / 800) * (0.8 + 0.2 * math.sin(self.age / 60))
            cone = pygame.Surface((s(50), s(52)))
            cone.fill((0, 0, 0))
            for row in range(s(50)):                            # brightest near the saucer, fading as it spreads
                share = row / s(50)
                half = 3 * k + (s(14) - 3 * k) * share
                pygame.draw.line(cone, scaled(self.beam, strength * (1 - share * 0.75)), (s(25) - half, row), (s(25) + half, row))
            surface.blit(cone, (x - s(25), y + 2 * k), special_flags=self.blend)
        pygame.draw.ellipse(surface, pygame.Color(palette["dome"]), pygame.Rect(0, 0, 9 * k, 8 * k).move(at(-4.5, -6.5)))
        rim = [at(math.cos(a) * 12, math.sin(a) * 3) for a in [i / 16 * 2 * math.pi for i in range(16)]]
        pygame.draw.polygon(surface, pygame.Color(palette["saucer"]), rim)
        pygame.draw.polygon(surface, pygame.Color(palette["saucer_dark"]), [at(-12, 0), at(12, 0), at(6, 3.5), at(-6, 3.5)])
        # Lights round the rim, chasing each other round
        for n in range(6):
            u = -10 + n * 4
            color, blend = self.lights[(n + int(self.age / 150)) % len(self.lights)]
            px, py = at(u, 1)
            surface.fill(color, (px - 1, py - 1, max(2, s(2)), max(2, s(2))), special_flags=blend)


class Astronaut(Visitor):
    # An astronaut drifting slowly past on the right, turning gently head over heels, waving
    # now and then, with a little puff from their jet pack to steady themselves
    #
    # Palette colors it uses:
    #   "suit", "suit_shade", "visor", "jet"
    #   "visor_glint"               a gleam on the visor (glows)

    TIME = 42000

    def start(self):
        super().start()
        self.age = 0.0
        self.side = random.choice((-1, 1))
        self.y0 = s(random.uniform(160, 300))
        self.puffs = []
        self.palette = None

    def update(self, dt):
        if not self.active:
            return
        self.age += dt
        if random.random() < dt / 3500:
            self.puffs.append({"age": 0.0, "angle": self.angle()})
        for p in self.puffs:
            p["age"] += dt
        self.puffs = [p for p in self.puffs if p["age"] < 900]
        if self.age > self.TIME:
            self.active = False

    def angle(self):
        return self.age / 9000 * self.side + 0.4

    def draw(self, surface, palette):
        if not self.active:
            return
        if self.palette is not palette:
            self.glint, self.blend = shine(palette, "visor_glint")
            self.palette = palette
        t = self.age / self.TIME
        x = WIDTH + s(30) - (WIDTH + s(60)) * t if self.side < 0 else -s(30) + (WIDTH + s(60)) * t
        y = self.y0 + math.sin(self.age / 4000) * s(10) - t * s(40)
        k = 1.4 * UI_SCALE
        angle = self.angle()
        at = turned(x, y, angle, k)
        suit = pygame.Color(palette["suit"])
        shade = pygame.Color(palette["suit_shade"])
        fade = self.scene.keep(x, 0.4)
        behind = pygame.Color(palette["space_low"])
        suit, shade = behind.lerp(suit, fade), behind.lerp(shade, fade)
        for p in self.puffs:
            u = p["age"] / 900
            px, py = turned(x, y, p["angle"], k)(-5 - u * 8, 2)
            pygame.draw.circle(surface, behind.lerp(pygame.Color(palette["jet"]), (1 - u) * fade), (px, py), max(1, (1 + u * 3) * k))
        wave = math.sin(self.age / 250) * 0.6 if math.sin(self.age / 3000) > 0.5 else 0
        # Back pack, legs, body, arms (one waving), helmet with its visor
        pygame.draw.polygon(surface, shade, [at(-6, -5), at(-3, -5), at(-3, 5), at(-6, 5)])
        for side in (-1, 1):
            pygame.draw.line(surface, suit, at(side * 1.5, 5), at(side * 2.5 + side * 0.5, 12), max(2, int(2.6 * k)))
            pygame.draw.circle(surface, shade, at(side * 3, 12.5), max(1, 1.5 * k))
        pygame.draw.polygon(surface, suit, [at(-3.5, -4), at(3.5, -4), at(3, 6), at(-3, 6)])
        pygame.draw.line(surface, shade, at(-2, 1), at(2, 1), 1)
        pygame.draw.line(surface, suit, at(-3, -3), at(-7, 2), max(2, int(2.2 * k)))
        hand = (6 + math.cos(wave) * 1, -8 - math.sin(wave) * 3)
        pygame.draw.line(surface, suit, at(3, -3), at(*hand), max(2, int(2.2 * k)))
        pygame.draw.circle(surface, suit, at(0, -7.5), max(2, 4 * k))
        pygame.draw.ellipse(surface, behind.lerp(pygame.Color(palette["visor"]), fade), pygame.Rect(0, 0, 5.5 * k, 4 * k).move(at(-2, -9.5)))
        gx, gy = at(1.5, -8.5)
        surface.fill(scaled(self.glint, 0.6 + 0.4 * math.sin(self.age / 900)), (gx, gy, max(1, s(1.5)), max(1, s(1.5))), special_flags=self.blend)


class SolarSail(Visitor):
    # A solar sail: a great square of mirror-thin film on four long booms, a tiny craft at its
    # middle, gliding slowly across the top of the sky on sunlight alone and turning gently;
    # now and then it catches the Sun and flashes
    #
    # Palette colors it uses:
    #   "sail", "sail_light", "boom"
    #   "sail_glint"                its flash (glows)

    TIME = 60000

    def start(self):
        super().start()
        self.age = 0.0
        self.side = random.choice((-1, 1))
        self.y = s(random.uniform(250, 330))
        self.palette = None

    def update(self, dt):
        if not self.active:
            return
        self.age += dt
        if self.age > self.TIME:
            self.active = False

    def draw(self, surface, palette):
        if not self.active:
            return
        if self.palette is not palette:
            self.glint, self.blend = shine(palette, "sail_glint")
            self.glow = glow_sprite(s(16), self.glint)
            self.palette = palette
        t = self.age / self.TIME
        x = -s(40) + (WIDTH + s(80)) * t if self.side > 0 else WIDTH + s(40) - (WIDTH + s(80)) * t
        y = self.y + math.sin(self.age / 7000) * s(6)
        turn = self.age / 15000
        k = 1.5 * UI_SCALE
        fade = self.scene.keep(x, 0.45)
        behind = pygame.Color(palette["space_low"])
        sail = behind.lerp(pygame.Color(palette["sail"]), fade)
        light = behind.lerp(pygame.Color(palette["sail_light"]), fade)
        boom = behind.lerp(pygame.Color(palette["boom"]), fade)
        # Seen at a slant: a squashed square, turning
        squash = 0.35 + 0.15 * math.sin(turn * 0.7)

        def corner(n):
            a = turn + n * math.pi / 2
            return (x + math.cos(a) * 16 * k, y + math.sin(a) * 16 * k * squash)

        corners = [corner(n) for n in range(4)]
        for n in range(4):
            # Each quarter of the sail its own shade, as they catch the light differently
            pygame.draw.polygon(surface, light if n % 2 else sail, [(x, y), corners[n], corners[(n + 1) % 4]])
        for c in corners:
            pygame.draw.line(surface, boom, (x, y), c, 1)
        pygame.draw.lines(surface, boom, True, corners, 1)
        pygame.draw.circle(surface, boom, (x, y), max(1, 1.5 * k))
        flash = max(0, math.sin(turn * 2.3)) ** 12                 # it catches the Sun now and then
        if flash > 0.02:
            glow = self.glow.copy()
            glow.fill([int(255 * flash * fade)] * 3, special_flags=pygame.BLEND_RGB_MULT)
            surface.blit(glow, glow.get_rect(center=(x, y)), special_flags=self.blend)
