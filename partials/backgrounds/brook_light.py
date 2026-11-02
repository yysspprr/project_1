# Light on the brook. By day: patches of sunlight falling through gaps in the leaves
# overhead, swaying with the breeze, and sparkles on the water where the sun hits it.
# By night: moonlight glinting on the water, and fireflies drifting and blinking over the
# brook, their glow reflected in the water below them.
# Each only appears when the palette has its color, so day and night follow the mode

import math

import random

import pygame

from partials.config import WIDTH, HEIGHT, CENTER_X, s
from partials.backgrounds.base import Layer


def glow_sprite(radius, color, flatten=1.0, rings=6):
    # A soft round glow, brightest in the middle, for adding onto the scene
    # (blit with BLEND_RGB_ADD): black adds nothing, so its edges vanish
    width, height = max(2, int(radius * 2)), max(2, int(radius * 2 * flatten))
    sprite = pygame.Surface((width, height))
    sprite.fill((0, 0, 0))
    for ring in range(rings):
        share = 1 - ring / rings                            # 1 for the outermost ring, smaller inward
        strength = ((ring + 1) / rings) ** 1.6
        rect = pygame.Rect(0, 0, width * share, height * share)
        rect.center = (width // 2, height // 2)
        pygame.draw.ellipse(sprite, [int(c * strength) for c in color[:3]], rect)
    return sprite


class SunDapples(Layer):
    # Patches of sunlight on the ground and the water, each a cluster of overlapping soft
    # spots (the gap in the leaves it shines through). They sway with the breeze, and now
    # and then one fades out while another fades in somewhere else, as the leaves above
    # shift. Daytime only: needs "sunlight" in the palette
    #
    # Palette colors it uses:
    #   "sunlight"              how much light a patch adds at its brightest, as a color

    COUNT = 14
    SIZE = (40, 70)                 # a patch's spots, pixels at the medium size
    LIFE = (9000, 20000)            # milliseconds a patch lasts, fading in and out
    SWAY = 5                        # how far they sway in the breeze, pixels at the medium size
    LEVELS = 8                      # brightness steps painted ahead of time

    def __init__(self, scene):
        super().__init__(scene)
        self.time = 0
        self.patches = [self.new_patch(random.random()) for i in range(self.COUNT)]
        self.sprites = None
        self.painted_palette = None

    def new_patch(self, age=0.0):
        view = self.scene.view
        y = random.uniform(-s(20), HEIGHT + s(20))
        x = random.uniform(0, WIDTH)
        if random.random() < 0.6:
            x = self.scene.margin_x()                       # mostly in the margins, away from the text
        life = random.uniform(*self.LIFE)
        return {"x": x, "y": y, "shape": random.randrange(4), "life": life, "age": age * life,
                "size": view.scale(y), "phase": random.uniform(0, 2 * math.pi)}

    def paint(self, palette):
        # Four patch shapes, each at a few brightness levels
        color = palette["sunlight"]
        view = self.scene.view
        flatten = view.near_flatten
        self.sprites = []
        for shape in range(4):
            spots = [(random.uniform(-0.6, 0.6), random.uniform(-0.35, 0.35), random.uniform(0.45, 0.8))
                     for k in range(random.randint(2, 4))]
            size = s(self.SIZE[1])
            levels = []
            for level in range(1, self.LEVELS + 1):
                share = level / self.LEVELS
                tint = [int(c * share) for c in color]
                patch = pygame.Surface((int(size * 3), int(size * 3 * flatten)))
                patch.fill((0, 0, 0))
                for u, v, r in spots:
                    spot = glow_sprite(size * r, tint, flatten, 4)
                    patch.blit(spot, (size * 1.5 + u * size - spot.get_width() / 2,
                                      size * 1.5 * flatten + v * size * flatten - spot.get_height() / 2),
                               special_flags=pygame.BLEND_RGB_MAX)
                levels.append(patch)
            self.sprites.append(levels)
        self.scaled = {}
        self.painted_palette = palette

    def update(self, dt):
        self.time += dt
        for i, patch in enumerate(self.patches):
            patch["age"] += dt
            if patch["age"] > patch["life"]:
                self.patches[i] = self.new_patch()

    def draw(self, surface, palette):
        if "sunlight" not in palette:
            return
        if self.painted_palette is not palette:
            self.paint(palette)
        light = self.scene.weather.get("light", 1)
        wind = self.scene.weather.get("wind", 1)
        for patch in self.patches:
            fade = math.sin(math.pi * patch["age"] / patch["life"]) ** 0.7
            level = int(fade * min(1, light) * self.LEVELS * self.scene.keep(patch["x"], 0.5))
            if level <= 0:
                continue
            sprite = self.sprites[patch["shape"]][min(level, self.LEVELS) - 1]
            # Further away, the patch looks smaller: scale once per patch and level, then reuse
            key = (patch["shape"], level, round(patch["size"] * 10))
            if key not in self.scaled:
                self.scaled[key] = pygame.transform.smoothscale(
                    sprite, (int(sprite.get_width() * patch["size"]), int(sprite.get_height() * patch["size"])))
            sprite = self.scaled[key]
            sway = math.sin(self.time / 1600 + patch["phase"]) * s(self.SWAY) * wind * patch["size"]
            surface.blit(sprite, (patch["x"] + sway - sprite.get_width() / 2, patch["y"] - sprite.get_height() / 2),
                         special_flags=pygame.BLEND_RGB_ADD)
        if len(self.scaled) > 400:
            self.scaled.clear()                             # keep the cache from growing forever


class WaterGlints(Layer):
    # Tiny sparkles winking on the water: by day where a patch of sunlight lands on it, by
    # night along the path of moonlight down the brook (the moon itself is off above the
    # trees). Each one flashes briefly now and then
    #
    # Palette colors it uses:
    #   "glint"                 the sparkles at their brightest
    #   "moonlight"             night only: present means the moon's path is drawn
    #   "moonlight_sheen"       night only: the faint pale streak the path adds to the water

    COUNT = 110
    FLASH = (1200, 3200)            # milliseconds between one sparkle's flashes
    MOON_PATH = 0.35                # how far right of the middle of the water the moon's path runs, as a share of its width
    MOON_WIDTH = 0.28               # how wide the path is, as a share of the water's width

    def __init__(self, scene, course, water, dapples):
        super().__init__(scene)
        self.course = course
        self.water = water
        self.dapples = dapples
        self.time = 0
        self.sheen = None
        self.painted_palette = None
        self.glints = []
        for i in range(self.COUNT):
            y = random.uniform(0, HEIGHT)
            self.glints.append({"across": random.uniform(-0.9, 0.9), "y": y, "period": random.uniform(*self.FLASH),
                                "phase": random.random(), "length": s(random.uniform(2, 4.5)) * scene.view.scale(y)})

    def paint_sheen(self, palette):
        # The moon's path on the water: a faint pale streak down the brook, added onto it
        course = self.course
        color = pygame.Color(palette["moonlight_sheen"])
        strip = pygame.Surface((65, 1))
        for i in range(65):
            fade = max(0.0, 1 - abs(i / 32 - 1)) ** 2
            strip.set_at((i, 0), (int(color.r * fade), int(color.g * fade), int(color.b * fade)))
        sheen = pygame.Surface((WIDTH, HEIGHT))
        sheen.fill((0, 0, 0))
        left, right = WIDTH, 0
        for y in range(HEIGHT):
            half = course.half_width(y)
            width = self.MOON_WIDTH * half * 2.4
            x = course.center(y) + self.MOON_PATH * half + math.sin(y / s(23)) * width * 0.1
            sheen.blit(pygame.transform.smoothscale(strip, (max(2, int(width)), 1)), (x - width / 2, y))
            left, right = min(left, x - width / 2), max(right, x + width / 2)
        # Only on the water
        mask = pygame.Surface((WIDTH, HEIGHT))
        mask.fill((0, 0, 0))
        pygame.draw.polygon(mask, (255, 255, 255), self.water.outline(0.97))
        sheen.blit(mask, (0, 0), special_flags=pygame.BLEND_RGB_MIN)
        # Only the strip it covers needs adding each frame, not the whole window
        self.sheen_area = pygame.Rect(int(max(0, left)), 0, int(min(WIDTH, right + 1) - max(0, left)), HEIGHT)
        self.sheen = sheen.subsurface(self.sheen_area).copy()
        self.painted_palette = palette

    def update(self, dt):
        self.time += dt

    def lit(self, palette, x, y, across):
        # How much light falls on the water here: sunlight patches by day, the moon's path by night
        if "moonlight" in palette:
            off = abs(across - self.MOON_PATH) / self.MOON_WIDTH
            return max(0.0, 1 - off * off)
        if "sunlight" not in palette:
            return 0.0
        best = 0.0
        for patch in self.dapples.patches:
            reach = s(SunDapples.SIZE[1]) * 1.3 * patch["size"]
            dx, dy = (x - patch["x"]) / reach, (y - patch["y"]) / (reach * 0.6)
            near = 1 - (dx * dx + dy * dy)
            if near > best:
                best = near * math.sin(math.pi * patch["age"] / patch["life"])
        return best

    def draw(self, surface, palette):
        if "glint" not in palette:
            return
        if "moonlight_sheen" in palette:
            if self.painted_palette is not palette:
                self.paint_sheen(palette)
            surface.blit(self.sheen, self.sheen_area.topleft, special_flags=pygame.BLEND_RGB_ADD)
        course = self.course
        glint = pygame.Color(palette["glint"])
        light = min(1.2, self.scene.weather.get("light", 1))
        for spark in self.glints:
            t = (self.time / spark["period"] + spark["phase"]) % 1
            flash = max(0.0, 1 - abs(t - 0.5) * 5)            # a short flash in the middle of each period
            if flash <= 0:
                continue
            y = spark["y"]
            x = course.center(y) + spark["across"] * course.half_width(y)
            strength = flash * self.lit(palette, x, y, spark["across"]) * light * self.scene.keep(x, 0.6)
            if strength <= 0.05:
                continue
            color = self.water.water_color(palette, x, y).lerp(glint, min(1, strength))
            half = spark["length"] * (0.5 + 0.5 * flash)
            pygame.draw.line(surface, color, (x - half, y), (x + half, y), max(1, s(1)))
            if strength > 0.6:
                pygame.draw.line(surface, color, (x, y - half * 0.5), (x, y + half * 0.5), 1)


class Fireflies(Layer):
    # Fireflies drifting over the brook at night, wandering slowly and blinking on and off
    # out of step with each other. Over the water, each one's glow shows in it too, a little
    # below the firefly (it hovers above its reflection). Night only: needs "firefly" in the palette
    #
    # Palette colors it uses:
    #   "firefly"               their glow

    COUNT = 18
    SPEED = 12                      # pixels per second, at the medium size
    HOVER = (8, 26)                 # how high above the ground or water they fly
    BLINK = (2200, 5500)            # milliseconds from one blink to the next
    LIT = 0.4                       # share of that time they're glowing
    GLOW = 9                        # glow radius, pixels at the medium size

    def __init__(self, scene, course):
        super().__init__(scene)
        self.course = course
        self.flies = [self.new_fly() for i in range(self.COUNT)]
        self.sprite = None
        self.painted_palette = None

    def new_fly(self):
        return {"x": random.uniform(0, WIDTH), "y": random.uniform(0, HEIGHT), "heading": random.uniform(0, 2 * math.pi),
                "hover": s(random.uniform(*self.HOVER)), "period": random.uniform(*self.BLINK),
                "clock": random.uniform(0, self.BLINK[1])}

    def paint(self, palette):
        color = pygame.Color(palette["firefly"])
        self.sprite = glow_sprite(s(self.GLOW), (color.r, color.g, color.b), 1.0, 6)
        self.reflection = glow_sprite(s(self.GLOW) * 0.7, (color.r // 3, color.g // 3, color.b // 3), 0.5, 4)
        self.core = color
        self.painted_palette = palette

    def update(self, dt):
        for fly in self.flies:
            fly["heading"] += random.uniform(-1.8, 1.8) * dt / 1000
            step = s(self.SPEED) * self.scene.view.scale(fly["y"]) * dt / 1000
            fly["x"] += math.cos(fly["heading"]) * step
            fly["y"] += math.sin(fly["heading"]) * step * 0.7
            # Wander back in if one drifts off the edge
            if not (-s(10) < fly["x"] < WIDTH + s(10)) or not (-s(10) < fly["y"] < HEIGHT + s(10)):
                fly["heading"] = math.atan2(HEIGHT / 2 - fly["y"], CENTER_X - fly["x"])
            fly["clock"] += dt

    def draw(self, surface, palette):
        if "firefly" not in palette:
            return
        if self.painted_palette is not palette:
            self.paint(palette)
        for fly in self.flies:
            t = (fly["clock"] % fly["period"]) / fly["period"]
            if t > self.LIT:
                continue
            glow = math.sin(math.pi * t / self.LIT) * self.scene.keep(fly["x"], 0.5)
            if glow < 0.08:
                continue
            x, y = fly["x"], fly["y"] - fly["hover"] * self.scene.view.scale(fly["y"])
            # Its reflection, if it's over the water
            if self.course.inside(fly["x"], fly["y"], 0.95):
                sprite = self.reflection
                ry = fly["y"] + fly["hover"] * self.scene.view.scale(fly["y"]) * 0.4
                self.blit_glow(surface, sprite, fly["x"], ry, glow)
            self.blit_glow(surface, self.sprite, x, y, glow)
            pygame.draw.circle(surface, self.core, (x, y), max(1, s(1.3)))

    def blit_glow(self, surface, sprite, x, y, glow):
        if glow < 0.99:
            sprite = sprite.copy()
            level = int(255 * glow)
            sprite.fill((level, level, level), special_flags=pygame.BLEND_RGB_MULT)
        surface.blit(sprite, (x - sprite.get_width() / 2, y - sprite.get_height() / 2), special_flags=pygame.BLEND_RGB_ADD)
