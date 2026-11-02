# Light in the desert. The desert sky: a bigger, lower sun or a full moon with its grey
# seas, and on a clear night a dense starry sky with the Milky Way arching across it and
# now and then a shooting star. At the oasis: a campfire that glows and crackles at night
# (a cold ring of stones by day), and the night sky mirrored in the pool

import math

import random

import pygame

from partials.config import WIDTH, HEIGHT, s
from partials.backgrounds.base import Layer
from partials.backgrounds.helpers import Timer
from partials.backgrounds.sky import Sky
from partials.backgrounds.brook_light import glow_sprite


class DesertSky(Sky):
    # The shared sky, made for the desert: a bigger sun or moon sitting lower, the moon full
    # (with its darker seas), more stars, and at night the Milky Way: a soft pale band of
    # light thick with faint stars, painted into the sky once
    #
    # Palette colors it uses (besides the Sky's own):
    #   "milky_way"             the band's glow (night only: none without it)
    #   "moon_sea"              the darker patches on the moon (falls back to a darker "body")

    BODY_SIZE = 16
    BODY_HEIGHT = 0.5
    MOON_BITE = 3                   # far enough off that it doesn't bite: a full moon
    STARS = 70
    BAND_STARS = 420
    BAND = ((0.02, 1.0), (0.72, -0.1))     # the Milky Way's ends: (share across, share down to the horizon)
    BAND_WIDTH = 30                 # pixels at the medium size

    def paint(self, palette):
        super().paint(palette)
        if "milky_way" not in palette:
            return
        color = pygame.Color(palette["milky_way"])
        rng = random.Random(7)
        (u0, v0), (u1, v1) = self.BAND
        x0, y0, x1, y1 = u0 * WIDTH, v0 * self.horizon, u1 * WIDTH, v1 * self.horizon
        length = math.hypot(x1 - x0, y1 - y0)
        nx, ny = -(y1 - y0) / length, (x1 - x0) / length
        glow = pygame.Surface(self.sky_image.get_size())
        glow.fill((0, 0, 0))
        width = s(self.BAND_WIDTH)
        # The glow: overlapping soft blobs along the band, wider and brighter in its middle
        for k in range(40):
            t = k / 39
            swell = 0.6 + 0.4 * math.sin(math.pi * t)
            x = x0 + (x1 - x0) * t + nx * math.sin(t * 9) * width * 0.25
            y = y0 + (y1 - y0) * t + ny * math.sin(t * 9) * width * 0.25
            blob = glow_sprite(width * swell * rng.uniform(0.8, 1.2), (color.r * 0.22, color.g * 0.22, color.b * 0.22), 0.8, 5)
            glow.blit(blob, blob.get_rect(center=(int(x), int(y))), special_flags=pygame.BLEND_RGB_MAX)
        self.sky_image.blit(glow, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        # Faint stars crowded into it, thickest along its middle
        for k in range(self.BAND_STARS):
            t = rng.random()
            spread = rng.gauss(0, 0.45) * width
            x = x0 + (x1 - x0) * t + nx * spread
            y = y0 + (y1 - y0) * t + ny * spread
            if not (0 <= x < WIDTH and 0 <= y < self.horizon - 1):
                continue
            behind = pygame.Color(self.sky_image.get_at((int(x), int(y))))
            strength = rng.uniform(0.25, 0.7) * self.scene.keep(x, 0.5)
            self.sky_image.set_at((int(x), int(y)), behind.lerp(color, strength))

    def paint_disc(self, palette, light):
        super().paint_disc(palette, light)
        if palette.get("sky_body") != "moon":
            return
        # The moon's seas: a few soft darker patches
        radius = s(self.BODY_SIZE)
        middle = (radius + 1, radius + 1)
        body = pygame.Color(palette["body"])
        sea = pygame.Color(palette.get("moon_sea", body.lerp((0, 0, 0), 0.25)))
        for u, v, r in ((-0.3, -0.25, 0.32), (0.15, -0.35, 0.22), (0.25, 0.15, 0.28), (-0.15, 0.35, 0.18), (0.45, -0.05, 0.12)):
            pygame.draw.circle(self.disc, sea, (middle[0] + u * radius, middle[1] + v * radius), r * radius)


class ShootingStars(Layer):
    # Now and then on a night, a shooting star: a bright point streaking down across the sky
    # with a fading tail, gone in under a second. Night only: needs "star" in the palette

    EVERY = (14000, 40000)
    LIFE = 750
    LENGTH = 60                     # how far it travels, pixels at the medium size

    def __init__(self, scene):
        super().__init__(scene)
        self.timer = Timer(self.EVERY)
        self.timer.left = random.uniform(5000, self.EVERY[1])
        self.horizon = scene.view.horizon
        self.star = None
        self.night = False

    def update(self, dt):
        if self.night and self.star is None and self.timer.tick(dt):
            angle = random.uniform(0.25, 0.6) * random.choice((1, -1))
            x = self.scene.margin_x()
            self.star = {"x": x, "y": random.uniform(0.05, 0.4) * self.horizon, "angle": angle, "age": 0.0}
        if self.star is not None:
            self.star["age"] += dt
            if self.star["age"] > self.LIFE:
                self.star = None

    def draw(self, surface, palette):
        self.night = "star" in palette
        if self.star is None or not self.night:
            return
        star = pygame.Color(palette["star"])
        t = self.star["age"] / self.LIFE
        travel = s(self.LENGTH) * t
        direction = (math.cos(self.star["angle"]) * (1 if self.star["angle"] > 0 else -1), abs(math.sin(self.star["angle"])))
        hx, hy = self.star["x"] + direction[0] * travel, self.star["y"] + direction[1] * travel
        if hy > self.horizon:
            return
        fade = math.sin(math.pi * t)
        for k in range(6):
            share = k / 6
            ax = hx - direction[0] * s(18) * share
            ay = hy - direction[1] * s(18) * share
            bx = hx - direction[0] * s(18) * (share + 1 / 6)
            by = hy - direction[1] * s(18) * (share + 1 / 6)
            behind = self.scene.color_at(palette, ay)
            pygame.draw.line(surface, behind.lerp(star, fade * (1 - share)), (ax, ay), (bx, by), 1)
        pygame.draw.circle(surface, self.scene.color_at(palette, hy).lerp(star, fade), (hx, hy), max(1, s(1.2)))


class PoolSky(Layer):
    # At night, the pool mirrors the sky: stars twinkling in the dark water, and a soft
    # pale sheen on the side nearest the moon. Night only: needs "star" in the palette

    STARS = 26

    def __init__(self, scene, oasis):
        super().__init__(scene)
        self.oasis = oasis
        self.time = 0
        self.stars = []
        for i in range(self.STARS):
            x, y = oasis.point(random.uniform(0, 2 * math.pi), random.uniform(0, 0.85) ** 0.7)
            self.stars.append((x, y, random.uniform(1500, 4000), random.uniform(0, 2 * math.pi)))

    def update(self, dt):
        self.time += dt

    def draw(self, surface, palette):
        if "star" not in palette:
            return
        star = pygame.Color(palette["star"])
        wind = self.scene.weather.get("wind", 1)
        storm = self.scene.weather.get("storm", 0)
        for x, y, period, phase in self.stars:
            twinkle = 0.5 + 0.5 * math.sin(self.time / period * 2 * math.pi + phase)
            # Wind ripples break the reflection up
            strength = twinkle * 0.55 * (1 - storm) * max(0.2, 1.3 - wind * 0.5) * self.scene.keep(x, 0.5)
            if strength < 0.08:
                continue
            water = self.oasis.water_color(palette, y)
            wobble = math.sin(self.time / 300 + phase) * s(1) * wind
            pygame.draw.line(surface, water.lerp(star, strength), (x - s(1) + wobble, y), (x + s(1) + wobble, y), 1)


class Campfire(Layer):
    # A campfire at the oasis, on the sand at the front left of the pool. By day it's a cold
    # ring of stones round a few charred sticks, with a thin thread of smoke. At night it
    # burns: flickering tongues of flame over crossed logs, sparks drifting up, a warm glow
    # on the sand and the palms around it, and its light trembling on the water
    #
    # Palette colors it uses:
    #   "fire", "fire_core"                 the flames (unlit without "fire")
    #   "rock", "rock_dark"                 the stones round it
    #   "palm_trunk_dark"                   the logs
    #   "smoke"                             the smoke by day (optional)

    GLOW = 80                       # glow radius, pixels at the medium size
    SPARKS = 8
    SIZE = 1.7                      # how big it is, compared to its drawing at the medium size up close

    def __init__(self, scene, oasis):
        super().__init__(scene)
        self.oasis = oasis
        self.x, self.y = oasis.point(math.pi * 0.86, 1.32)
        self.k = scene.view.scale(self.y) * self.SIZE
        self.time = 0
        self.sparks = []
        self.smoke = []
        self.glow = None
        self.painted_palette = None
        stones = 9
        self.stones = [(math.cos(2 * math.pi * i / stones) * s(9) * self.k, math.sin(2 * math.pi * i / stones) * s(3.6) * self.k,
                        random.uniform(0.8, 1.2)) for i in range(stones)]

    def paint(self, palette):
        self.glow = None
        if "fire" in palette:
            color = pygame.Color(palette["fire"])
            r = s(self.GLOW) * self.k
            self.glow = glow_sprite(r, (color.r * 0.5, color.g * 0.35, color.b * 0.2), 0.75, 18)
            self.pool_glow = glow_sprite(r * 0.6, (color.r * 0.35, color.g * 0.25, color.b * 0.12), 0.25, 6)
        self.painted_palette = palette

    def update(self, dt):
        self.time += dt
        seconds = dt / 1000
        wind = self.scene.weather.get("wind", 1)
        lit = self.painted_palette is not None and "fire" in self.painted_palette
        if lit and len(self.sparks) < self.SPARKS and random.random() < dt / 180:
            self.sparks.append({"x": self.x + random.uniform(-s(3), s(3)), "y": self.y - s(6) * self.k, "age": 0.0,
                                "life": random.uniform(700, 1600), "drift": random.uniform(-1, 1)})
        for spark in self.sparks:
            spark["age"] += dt
            spark["y"] -= s(26) * seconds
            spark["x"] += (spark["drift"] * s(6) - wind * s(8)) * seconds
        self.sparks = [spark for spark in self.sparks if spark["age"] < spark["life"]]
        if not lit and "smoke" in (self.painted_palette or {}) and random.random() < dt / 500:
            self.smoke.append({"x": self.x, "y": self.y - s(3) * self.k, "age": 0.0, "life": random.uniform(2500, 4000)})
        for puff in self.smoke:
            puff["age"] += dt
            puff["y"] -= s(9) * seconds
            puff["x"] -= wind * s(6) * seconds
        self.smoke = [puff for puff in self.smoke if puff["age"] < puff["life"]]

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        k = self.k
        x, y = self.x, self.y
        lit = "fire" in palette
        flicker = 0.82 + 0.12 * math.sin(self.time / 70) * math.sin(self.time / 173) + 0.06 * math.sin(self.time / 41)
        if lit:
            level = int(255 * flicker)
            for sprite, at in ((self.glow, (x, y - s(6) * k)), (self.pool_glow, (x + s(40) * k, self.oasis.point(math.pi * 0.86, 0.85)[1]))):
                glow = sprite.copy()
                glow.fill((level, level, level), special_flags=pygame.BLEND_RGB_MULT)
                surface.blit(glow, glow.get_rect(center=(int(at[0]), int(at[1]))), special_flags=pygame.BLEND_RGB_ADD)
        # The ring of stones (back half), the logs, the flames, then the front stones
        rock = pygame.Color(palette.get("rock", palette["muted"]))
        dark = pygame.Color(palette.get("rock_dark", palette["muted"]))
        wood = pygame.Color(palette.get("palm_trunk_dark", palette["text"]))
        if lit:
            rock = rock.lerp(pygame.Color(palette["fire"]), 0.25)
        for dx, dy, size in self.stones:
            if dy < 0:
                pygame.draw.ellipse(surface, rock, (x + dx - s(2.6) * k * size, y + dy - s(1.8) * k * size, s(5.2) * k * size, s(3.4) * k * size))
        for a in (0.4, -0.4, 1.4):
            pygame.draw.line(surface, wood, (x - math.cos(a) * s(7) * k, y + math.sin(a) * s(1.5) * k),
                             (x + math.cos(a) * s(7) * k, y - math.sin(a) * s(1.5) * k), max(2, int(s(2.4) * k)))
        if lit:
            fire = pygame.Color(palette["fire"])
            core = pygame.Color(palette.get("fire_core", palette["fire"]))
            for n, (offset, height) in enumerate(((-0.45, 0.7), (0.4, 0.8), (0, 1.15))):
                sway = math.sin(self.time / (90 + n * 23) + n) * s(1.5) * k
                h = s(15) * k * height * flicker
                base_x = x + offset * s(5) * k
                tongue = [(base_x - s(3.2) * k, y - s(1) * k), (base_x + sway * 0.5 - s(1.6) * k, y - h * 0.55),
                          (base_x + sway, y - h), (base_x + sway * 0.5 + s(1.6) * k, y - h * 0.55), (base_x + s(3.2) * k, y - s(1) * k)]
                pygame.draw.polygon(surface, fire, tongue)
                inner = [((px - base_x) * 0.5 + base_x, y - (y - py) * 0.6) for px, py in tongue]
                pygame.draw.polygon(surface, core, inner)
            for spark in self.sparks:
                fade = 1 - spark["age"] / spark["life"]
                behind = self.scene.color_at(palette, spark["y"])
                pygame.draw.circle(surface, behind.lerp(core, fade), (spark["x"], spark["y"]), max(1, s(0.9)))
        else:
            smoke = palette.get("smoke")
            if smoke:
                smoke = pygame.Color(smoke)
                for puff in self.smoke:
                    t = puff["age"] / puff["life"]
                    behind = self.scene.color_at(palette, puff["y"])
                    pygame.draw.circle(surface, behind.lerp(smoke, 0.5 * math.sin(math.pi * t)), (puff["x"], puff["y"]), s(1.5 + 3 * t) * k)
        for dx, dy, size in self.stones:
            if dy >= 0:
                stone = pygame.Rect(0, 0, s(5.2) * k * size, s(3.4) * k * size)
                stone.center = (x + dx, y + dy)
                pygame.draw.ellipse(surface, dark, stone.move(0, 1))
                pygame.draw.ellipse(surface, rock, stone)
