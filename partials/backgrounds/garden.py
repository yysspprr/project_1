# A spring garden in the East-Asian style, seen from a low veranda: misty hills on the
# horizon with a pagoda on the nearest one, a garden of moss and raked gravel around a still
# pond, a stone lantern, blossoming trees, and a blossom branch reaching in from the side

import math

import random

import pygame

from partials.config import WIDTH, HEIGHT, CENTER_X, s
from partials.backgrounds.base import Layer
from partials.backgrounds.helpers import make_jitter


def blend(palette, key, fallback, haze=0.0, haze_key="mist"):
    # A palette color, pulled toward the mist by haze (things far away fade into it)
    color = pygame.Color(palette.get(key, fallback))
    if haze and haze_key in palette:
        color = color.lerp(pygame.Color(palette[haze_key]), haze)
    return color


class MistyHills(Layer):
    # Three ridges of soft hills along the horizon, each further one paler and bluer, with
    # bands of mist lying in the valleys between them. They rise toward the sides of the
    # window and dip low in the middle, so they frame the title rather than sit behind it.
    # Painted once
    #
    # Palette colors it uses:
    #   "hill_far", "hill_mid", "hill_near"     the three ridges
    #   "mist"                                  the mist between them (no mist without it)

    RIDGES = (("hill_far", 66, 0.35), ("hill_mid", 46, 0.55), ("hill_near", 26, 0.8))   # color, rise at the sides, mist
    MIDDLE = 0.18                   # how much of that rise is left in the middle of the window

    def __init__(self, scene):
        super().__init__(scene)
        self.horizon = scene.view.horizon
        self.waves = [[(random.uniform(0.6, 1.0), random.uniform(18, 34), random.uniform(0, 2 * math.pi)),
                       (random.uniform(0.2, 0.4), random.uniform(7, 12), random.uniform(0, 2 * math.pi))]
                      for ridge in self.RIDGES]
        self.image = None
        self.painted_palette = None

    def ridge_y(self, index, x):
        rise = s(self.RIDGES[index][1])
        side = abs(x - CENTER_X) / CENTER_X
        shape = self.MIDDLE + (1 - self.MIDDLE) * side ** 1.4
        roll = sum(amount * math.sin(x / s(length) + phase) for amount, length, phase in self.waves[index])
        return self.horizon - rise * shape * (0.75 + 0.25 * roll)

    def paint(self, palette):
        image = pygame.Surface((WIDTH, int(self.horizon) + 2), pygame.SRCALPHA)
        mist = pygame.Color(palette["mist"]) if "mist" in palette else None
        for index, (key, rise, mist_amount) in enumerate(self.RIDGES):
            color = pygame.Color(palette.get(key, palette["muted"]))
            line = [(x, self.ridge_y(index, x)) for x in range(-4, WIDTH + 5, 4)]
            pygame.draw.polygon(image, color, line + [(WIDTH + 4, self.horizon + 2), (-4, self.horizon + 2)])
            # Mist lying along the foot of this ridge, fading upward
            if mist is not None:
                depth = s(14)
                for k in range(depth):
                    share = (1 - k / depth) ** 2 * mist_amount
                    y = int(self.horizon - k * 1.2)
                    band = pygame.Surface((WIDTH, 1), pygame.SRCALPHA)
                    band.fill((mist.r, mist.g, mist.b, int(255 * share * 0.55)))
                    image.blit(band, (0, y - (2 - index) * s(6)))
        self.image = image
        self.painted_palette = palette

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.image, (0, 0))


class Pagoda(Layer):
    # A tiered pagoda standing on the nearest hill, at the right of the window, its spire
    # rising against the sky (the moon or sun peeks out from behind it). Sweeping roofs with
    # upturned eaves, a pale band under each, and at night a few lit windows. A few trees
    # stand around its foot. Slightly hazy with distance. Painted once
    #
    # Palette colors it uses:
    #   "pagoda_wall", "pagoda_roof", "pagoda_trim"     its walls, roofs and the pale bands
    #   "window"                        lit windows (night only: none without it)
    #   "pine", "blossom", "tree_trunk" the trees around it
    #   "mist"                          what distance fades it toward

    TIERS = 5
    WIDTH_AT_BASE = 30              # the bottom tier's walls, pixels at the medium size
    TIER_HEIGHT = 13
    NARROWING = 0.84                # each tier's width, compared to the one below
    EAVES = 1.75                    # how far the roofs reach out, compared to the walls
    UPTURN = 4                      # how far the eave tips curl up
    SPIRE = 20
    HAZE = 0.22

    def __init__(self, scene, hills):
        super().__init__(scene)
        self.x = WIDTH - s(60)
        self.base = hills.ridge_y(2, self.x) + s(6)
        self.trees = []
        for i in range(7):
            side = -1 if i % 2 else 1
            tx = self.x + side * random.uniform(s(22), s(55))
            self.trees.append((tx, hills.ridge_y(2, tx) + s(random.uniform(6, 12)), random.choice(("pine", "blossom", "blossom")),
                               s(random.uniform(9, 15))))
        self.trees.sort(key=lambda tree: tree[1])
        self.image = None
        self.painted_palette = None

    def roof(self, x, y, half, thickness):
        # A roof seen from the front: a sweeping band whose ends curl up
        up = s(self.UPTURN)
        top = [(x - half * 0.55, y - thickness * 1.6), (x + half * 0.55, y - thickness * 1.6)]
        right = [(x + half * 0.85, y - thickness * 0.4), (x + half, y - up), (x + half * 0.95, y + thickness * 0.2)]
        left = [(x - half * 0.95, y + thickness * 0.2), (x - half, y - up), (x - half * 0.85, y - thickness * 0.4)]
        bottom = [(x + half * 0.5, y + thickness * 0.55), (x - half * 0.5, y + thickness * 0.55)]
        return top + right + bottom + left

    def tree(self, image, palette, x, y, kind, size):
        if kind == "pine":
            color = blend(palette, "pine", palette["muted"], self.HAZE)
            for k in range(3):
                w = size * (1 - k * 0.25)
                ty = y - size * 0.5 - k * size * 0.55
                pygame.draw.polygon(image, color, [(x - w, ty + size * 0.35), (x, ty - size * 0.5), (x + w, ty + size * 0.35)])
        else:
            trunk = blend(palette, "tree_trunk", palette["muted"], self.HAZE)
            pygame.draw.line(image, trunk, (x, y), (x, y - size * 0.8), max(1, s(2)))
            colors = palette.get("blossom", [palette["muted"]])
            for k in range(6):
                angle = k * 1.1
                color = blend(palette, None, colors[k % len(colors)], self.HAZE)
                pygame.draw.circle(image, color, (x + math.cos(angle) * size * 0.5, y - size * 1.1 + math.sin(angle) * size * 0.35),
                                   size * 0.55)

    def paint(self, palette):
        image = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        wall = blend(palette, "pagoda_wall", palette["muted"], self.HAZE)
        roof = blend(palette, "pagoda_roof", palette["text"], self.HAZE)
        trim = blend(palette, "pagoda_trim", palette["muted"], self.HAZE)
        window = pygame.Color(palette["window"]) if "window" in palette else None
        for tree in self.trees:
            if tree[1] < self.base:
                self.tree(image, palette, *tree)

        x, y = self.x, self.base
        width = s(self.WIDTH_AT_BASE)
        height = s(self.TIER_HEIGHT)
        # A stone plinth, then the tiers from the bottom up
        pygame.draw.rect(image, trim.lerp(roof, 0.4), (x - width * 0.7, y - s(4), width * 1.4, s(4)))
        y -= s(4)
        for tier in range(self.TIERS):
            half = width / 2
            pygame.draw.rect(image, wall, (x - half, y - height, width, height))
            pygame.draw.rect(image, trim, (x - half, y - height, width, height * 0.22))
            # Posts dividing the front into bays, and the windows between them
            for k in (-1, 1):
                pygame.draw.line(image, wall.lerp(roof, 0.5), (x + k * half * 0.34, y - height * 0.78), (x + k * half * 0.34, y), 1)
            if window is not None and tier < self.TIERS - 1:
                for k in (-0.67, 0, 0.67):
                    if (tier + int(k * 3)) % 2 == 0:
                        pygame.draw.rect(image, window, (x + k * half - s(1.5), y - height * 0.6, s(3), height * 0.35))
            y -= height
            self.roof_points = self.roof(x, y, half * self.EAVES, s(3))
            pygame.draw.polygon(image, roof, self.roof_points)
            y -= s(4)
            width *= self.NARROWING
            height *= 0.93
        # The spire: a pole hung with rings, and a little jewel on top
        top = y - s(self.SPIRE)
        pygame.draw.line(image, roof, (x, y + s(2)), (x, top), max(1, s(2)))
        for k in range(5):
            ry = y - s(4) - k * s(2.6)
            pygame.draw.line(image, roof, (x - s(3.5) + k * 0.3, ry), (x + s(3.5) - k * 0.3, ry), 1)
        pygame.draw.circle(image, roof, (x, top), max(1, s(2)))

        for tree in self.trees:
            if tree[1] >= self.base:
                self.tree(image, palette, *tree)
        self.image = image
        self.painted_palette = palette

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.image, (0, 0))


class GardenPond(Layer):
    # The garden itself: moss from the horizon down, an oval of pale raked gravel, and in
    # it a still pond with stones around its rim. The water mirrors the sky: pale near its
    # far edge, deeper toward us. Painted once. Others ask inside(x, y) to know whether a
    # point is on the water
    #
    # Palette colors it uses:
    #   "ground_far", "ground_near"     the moss, far away and up close
    #   "gravel", "gravel_line"         the gravel and the lines raked into it
    #   "pond_far", "pond_near"         the water at its far and near edge
    #   "pond_edge"                     the dark line where water meets stone
    #   "rim_stone", "rim_stone_dark"   the stones around the rim

    CENTER_Y = 335                  # the pond's middle, pixels at the medium size: behind the entry box
    HALF = (160, 72)                # half its width and height
    GRAVEL = (46, 24)               # how far the gravel reaches past the water
    RAKED = 4                       # lines raked around the pond
    RIM_STONES = 30
    SPECKLE = 2600                  # flecks of texture in the moss
    HEDGE = 34                      # round clipped bushes along the far edge of the garden
    PATH = 7                        # stepping stones leading up to the pond
    SHRUBS = ((-0.06, 1.02, 70), (0.98, 0.93, 85), (0.83, 0.62, 40), (0.12, 0.66, 34))   # (share across, share down, size)

    def __init__(self, scene):
        super().__init__(scene)
        self.horizon = scene.view.horizon
        view = scene.view
        self.specks = [(random.uniform(0, WIDTH), view.random_y(0.3), random.random()) for i in range(self.SPECKLE)]
        self.hedge = []
        for i in range(self.HEDGE):
            x = WIDTH * (i + random.uniform(0, 1)) / self.HEDGE
            self.hedge.append((x, self.horizon + s(random.uniform(1, 4)), s(random.uniform(5, 9))))
        # The path: stepping stones from the bottom left of the window up to the pond's edge
        self.path = []
        for i in range(self.PATH):
            t = i / (self.PATH - 1)
            x = s(70) + (s(150) - s(70)) * t + math.sin(t * 3.2) * s(22)
            y = HEIGHT + s(10) - (HEIGHT + s(10) - s(self.CENTER_Y + self.HALF[1] + 18)) * t
            self.path.append((x + random.uniform(-s(4), s(4)), y, random.uniform(0.85, 1.15), random.uniform(-0.3, 0.3)))
        self.shrubs = [(WIDTH * u, HEIGHT * v, s(size)) for u, v, size in self.SHRUBS]
        self.cx, self.cy = CENTER_X, s(self.CENTER_Y)
        self.wave = [(random.uniform(0.02, 0.05), k, random.uniform(0, 2 * math.pi)) for k in (2, 3)]
        self.rim = []
        for i in range(self.RIM_STONES):
            angle = 2 * math.pi * i / self.RIM_STONES + random.uniform(-0.06, 0.06)
            self.rim.append((angle, random.uniform(0.8, 1.25), random.uniform(0.7, 1.0)))
        self.image = None
        self.painted_palette = None

    def reach(self, angle):
        # How far the pond's edge is from its middle in a direction, as a share of HALF
        return 1 + sum(amount * math.sin(k * angle + phase) for amount, k, phase in self.wave)

    def outline(self, grow=(0, 0), count=72):
        points = []
        for i in range(count):
            angle = 2 * math.pi * i / count
            r = self.reach(angle)
            points.append((self.cx + math.cos(angle) * (s(self.HALF[0]) * r + grow[0]),
                           self.cy + math.sin(angle) * (s(self.HALF[1]) * r + grow[1])))
        return points

    def water_color(self, palette, y):
        far = pygame.Color(palette.get("pond_far", palette["bg"]))
        near = pygame.Color(palette.get("pond_near", palette["bg"]))
        y0, y1 = self.cy - s(self.HALF[1]) * 1.2, self.cy + s(self.HALF[1]) * 1.2
        return far.lerp(near, max(0, min(1, (y - y0) / (y1 - y0))) ** 0.8)

    def point(self, angle, share):
        # A point share of the way from the pond's middle to its edge, in a direction
        r = self.reach(angle) * share
        return (self.cx + math.cos(angle) * s(self.HALF[0]) * r, self.cy + math.sin(angle) * s(self.HALF[1]) * r)

    def inside(self, x, y, margin=1.0):
        dx, dy = (x - self.cx) / s(self.HALF[0]), (y - self.cy) / s(self.HALF[1])
        return dx * dx + dy * dy < (self.reach(math.atan2(dy, dx)) * margin) ** 2

    def ground_color(self, palette, y):
        far = pygame.Color(palette.get("ground_far", palette["bg"]))
        near = pygame.Color(palette.get("ground_near", palette["bg"]))
        return far.lerp(near, self.scene.view.nearness(y))

    def paint(self, palette):
        image = pygame.Surface((WIDTH, HEIGHT - int(self.horizon)))
        for row in range(image.get_height()):
            pygame.draw.line(image, self.ground_color(palette, self.horizon + row), (0, row), (WIDTH, row))
        top = self.horizon

        def shift(points):
            return [(x, y - top) for x, y in points]

        # Texture in the moss: flecks a little lighter and darker than the ground
        for x, y, pick in self.specks:
            base = self.ground_color(palette, y)
            fleck = base.lerp((255, 255, 255), 0.12) if pick < 0.5 else base.lerp((0, 0, 0), 0.1)
            size = max(1, s(1.6) * self.scene.view.scale(y))
            pygame.draw.circle(image, fleck, (x, y - top), size)

        # A hedge of round clipped bushes along the far edge, where the garden meets the hills
        bush = pygame.Color(palette.get("shrub", palette["muted"]))
        bush_dark = pygame.Color(palette.get("shrub_dark", palette["muted"]))
        bush_light = pygame.Color(palette.get("shrub_light", palette.get("shrub", palette["muted"])))
        haze = pygame.Color(palette.get("mist", palette.get("shrub", palette["muted"])))
        for x, y, r in self.hedge:
            pygame.draw.ellipse(image, bush_dark.lerp(haze, 0.25), (x - r, y - r * 0.9 - top, r * 2, r * 1.5))
            pygame.draw.ellipse(image, bush.lerp(haze, 0.25), (x - r * 0.9, y - r * 1.1 - top, r * 1.7, r * 1.3))

        # Raked gravel around the pond, the rake lines following its shape
        gravel = pygame.Color(palette.get("gravel", palette["muted"]))
        line = pygame.Color(palette.get("gravel_line", palette["muted"]))
        gx, gy = s(self.GRAVEL[0]), s(self.GRAVEL[1])
        pygame.draw.polygon(image, gravel, shift(self.outline((gx, gy))))
        for k in range(1, self.RAKED + 1):
            share = k / (self.RAKED + 1)
            pygame.draw.lines(image, line, True, shift(self.outline((gx * share, gy * share))), 1)

        # The water: the sky mirrored, pale at its far edge, deeper near us
        far = pygame.Color(palette.get("pond_far", palette["bg"]))
        near = pygame.Color(palette.get("pond_near", palette["bg"]))
        water = pygame.Surface(image.get_size(), pygame.SRCALPHA)
        y0, y1 = self.cy - s(self.HALF[1]) * 1.2, self.cy + s(self.HALF[1]) * 1.2
        for y in range(int(y0), int(y1) + 1):
            share = max(0, min(1, (y - y0) / (y1 - y0)))
            pygame.draw.line(water, far.lerp(near, share ** 0.8), (0, y - top), (WIDTH, y - top))
        mask = pygame.Surface(image.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(mask, (255, 255, 255, 255), shift(self.outline()))
        water.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        image.blit(water, (0, 0))
        pygame.draw.lines(image, pygame.Color(palette.get("pond_edge", palette["muted"])), True, shift(self.outline()), max(1, s(2)))

        # Stones along the rim, bigger toward us
        stone = pygame.Color(palette.get("rim_stone", palette["muted"]))
        dark = pygame.Color(palette.get("rim_stone_dark", palette["muted"]))
        for angle, size, squash in sorted(self.rim, key=lambda r: math.sin(r[0])):
            r = self.reach(angle)
            x = self.cx + math.cos(angle) * s(self.HALF[0]) * r
            y = self.cy + math.sin(angle) * s(self.HALF[1]) * r
            w = s(12) * size * self.scene.view.scale(y)
            h = w * 0.55 * squash
            pygame.draw.ellipse(image, dark, (x - w, y - h * 0.6 - top, w * 2, h * 1.9))
            pygame.draw.ellipse(image, stone, (x - w * 0.95, y - h - top, w * 1.9, h * 1.7))
        # Stepping stones up to the pond
        for x, y, size, turn in self.path:
            scale = self.scene.view.scale(y)
            w, h = s(17) * size * scale, s(17) * size * scale * self.scene.view.flatten(y) * 1.2
            pygame.draw.ellipse(image, dark, (x - w, y - h * 0.8 - top, w * 2, h * 2))
            pygame.draw.ellipse(image, stone, (x - w * 0.97, y - h - top, w * 1.94, h * 1.85))
            pygame.draw.ellipse(image, stone.lerp((255, 255, 255), 0.15), (x - w * 0.7, y - h * 0.9 - top, w * 1.1, h * 0.9))

        # Clipped shrubs, round and low, a few with azalea flowers
        flowers = palette.get("azalea")
        for k, (x, y, r) in enumerate(self.shrubs):
            r *= self.scene.view.scale(y)
            mounds = [(-0.45, 0.1, 0.62), (0.4, 0.12, 0.6), (0, -0.15, 0.72)]
            for u, v, m in mounds:
                pygame.draw.ellipse(image, bush_dark, (x + u * r - m * r, y + v * r - m * r * 0.7 - top + r * 0.12, m * r * 2, m * r * 1.4))
            for u, v, m in mounds:
                pygame.draw.ellipse(image, bush, (x + u * r - m * r * 0.95, y + v * r - m * r * 0.75 - top, m * r * 1.9, m * r * 1.3))
                pygame.draw.ellipse(image, bush_light, (x + u * r - m * r * 0.6, y + v * r - m * r * 0.7 - top, m * r * 0.9, m * r * 0.55))
            if flowers and k % 2 == 0:
                rng = random.Random(k)
                for f in range(int(r / s(2.2))):
                    fx = x + rng.uniform(-0.85, 0.85) * r
                    fy = y + rng.uniform(-0.6, 0.25) * r
                    pygame.draw.circle(image, pygame.Color(flowers[f % len(flowers)]), (fx, fy - top), max(1, s(1.6)))
        self.image = image
        self.painted_palette = palette

    def color_at(self, palette, y):
        if y < self.horizon:
            return None
        return self.ground_color(palette, y)

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.image, (0, self.horizon))


class StoneLantern(Layer):
    # A stone lantern standing in the moss at the left of the pond: a base, a post, a
    # firebox with an opening, a wide curved cap and a knob on top. At night a flame glows
    # inside and lights the ground around it. Painted once
    #
    # Palette colors it uses:
    #   "lantern", "lantern_light", "lantern_dark"  the stone, its lit side, its shaded side
    #   "lantern_glow"                              the flame at night (unlit without it)

    HEIGHT_TALL = 64                # pixels at the medium size
    X = 40
    BASE_Y = 408

    def __init__(self, scene):
        super().__init__(scene)
        self.x, self.y = s(self.X), s(self.BASE_Y)
        self.image = None
        self.glow = None
        self.painted_palette = None
        self.time = 0

    def parts(self):
        # (half width, height) of each part from the bottom up, in shares of the full height
        return [("base", 0.36, 0.1), ("post", 0.13, 0.3), ("table", 0.32, 0.07), ("box", 0.24, 0.2),
                ("cap", 0.5, 0.12), ("knob", 0.09, 0.12)]

    def paint(self, palette):
        tall = s(self.HEIGHT_TALL)
        stone = pygame.Color(palette.get("lantern", palette["muted"]))
        light = pygame.Color(palette.get("lantern_light", palette["muted"]))
        dark = pygame.Color(palette.get("lantern_dark", palette["muted"]))
        image = pygame.Surface((int(tall * 1.4), int(tall * 1.3)), pygame.SRCALPHA)
        x, y = image.get_width() / 2, image.get_height() - tall * 0.08
        self.offset = (self.x - x, self.y - y)
        pygame.draw.ellipse(image, (0, 0, 0, 60), (x - tall * 0.45, y - tall * 0.06, tall * 0.9, tall * 0.14))
        flame_at = None
        for name, half, height in self.parts():
            w, h = half * tall, height * tall
            if name == "cap":
                # A wide roof with curled-up corners
                cap = [(x - w, y - h * 0.15), (x - w * 0.92, y - h * 0.55), (x - w * 0.35, y - h), (x + w * 0.35, y - h),
                       (x + w * 0.92, y - h * 0.55), (x + w, y - h * 0.15), (x + w * 0.6, y + h * 0.1), (x - w * 0.6, y + h * 0.1)]
                pygame.draw.polygon(image, stone, cap)
                pygame.draw.polygon(image, light, [(x - w * 0.92, y - h * 0.55), (x - w * 0.35, y - h), (x, y - h), (x - w * 0.2, y - h * 0.4)])
                pygame.draw.lines(image, dark, True, cap, 1)
            elif name == "knob":
                pygame.draw.circle(image, stone, (x, y - h * 0.5), w * 1.2)
                pygame.draw.circle(image, dark, (x, y - h * 0.5), w * 1.2, 1)
            else:
                rect = pygame.Rect(x - w, y - h, w * 2, h)
                pygame.draw.rect(image, stone, rect)
                pygame.draw.rect(image, light, (x - w, y - h, w * 0.45, h))
                pygame.draw.rect(image, dark, (x + w * 0.55, y - h, w * 0.45, h))
                pygame.draw.rect(image, dark, rect, 1)
                if name == "box":
                    # The opening the light shines out of
                    opening = pygame.Rect(0, 0, w * 0.9, h * 0.62)
                    opening.center = (x, y - h * 0.5)
                    lit = "lantern_glow" in palette
                    pygame.draw.rect(image, pygame.Color(palette["lantern_glow"]) if lit else dark.lerp((0, 0, 0), 0.3), opening)
                    flame_at = (self.offset[0] + opening.centerx, self.offset[1] + opening.centery)
            y -= h
        self.image = image
        self.glow = None
        if "lantern_glow" in palette and flame_at:
            color = pygame.Color(palette["lantern_glow"])
            radius = int(tall * 0.9)
            glow = pygame.Surface((radius * 2, radius * 2))
            glow.fill((0, 0, 0))
            for ring in range(7):
                share = 1 - ring / 7
                strength = ((ring + 1) / 7) ** 1.8 * 0.4
                pygame.draw.circle(glow, (int(color.r * strength), int(color.g * strength), int(color.b * strength)),
                                   (radius, radius), radius * share)
            self.glow = glow
            self.flame_at = flame_at
        self.painted_palette = palette

    def update(self, dt):
        self.time += dt

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.image, self.offset)
        if self.glow is not None:
            # The flame flickers a little
            flicker = 0.85 + 0.15 * math.sin(self.time / 90) * math.sin(self.time / 237)
            glow = self.glow.copy()
            level = int(255 * flicker)
            glow.fill((level, level, level), special_flags=pygame.BLEND_RGB_MULT)
            surface.blit(glow, glow.get_rect(center=self.flame_at), special_flags=pygame.BLEND_RGB_ADD)


class BlossomTree(Layer):
    # A cherry tree in full bloom standing at one side of the garden: a dark crooked trunk
    # and a cloud of blossom made of many overlapping round clusters, lighter on top and
    # deeper underneath. Painted once
    #
    # Palette colors it uses:
    #   "tree_trunk", "blossom" (a list, light to deep), "blossom_dark"

    def __init__(self, scene, x, base_y, size):
        super().__init__(scene)
        self.x, self.base_y, self.size = x, base_y, size
        self.limbs = []
        # A trunk that leans and forks into a few limbs
        lean = random.uniform(-0.25, 0.25)
        self.fork = (x + lean * size * 0.6, base_y - size * 0.9)
        for k in range(4):
            angle = -math.pi / 2 + (k - 1.5) * 0.45 + random.uniform(-0.15, 0.15)
            length = size * random.uniform(0.55, 0.85)
            self.limbs.append((self.fork, (self.fork[0] + math.cos(angle) * length, self.fork[1] + math.sin(angle) * length)))
        self.clusters = []
        for k in range(26):
            angle = random.uniform(0, 2 * math.pi)
            reach = random.uniform(0, 1) ** 0.6
            cx = self.fork[0] + math.cos(angle) * size * 0.95 * reach
            cy = self.fork[1] - size * 0.55 + math.sin(angle) * size * 0.5 * reach
            self.clusters.append((cx, cy, size * random.uniform(0.22, 0.34)))
        self.clusters.sort(key=lambda c: c[1])
        self.image = None
        self.painted_palette = None

    def paint(self, palette):
        image = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        trunk = pygame.Color(palette.get("tree_trunk", palette["muted"]))
        colors = [pygame.Color(c) for c in palette.get("blossom", [palette["muted"]])]
        deep = pygame.Color(palette.get("blossom_dark", palette["muted"]))
        width = max(2, int(self.size * 0.09))
        pygame.draw.line(image, trunk, (self.x, self.base_y), self.fork, width)
        for start, end in self.limbs:
            pygame.draw.line(image, trunk, start, end, max(1, width // 2))
        # Clusters: a deep shade underneath each, then the blossom, then a light top
        for cx, cy, r in self.clusters:
            pygame.draw.circle(image, deep, (cx, cy + r * 0.25), r)
        for i, (cx, cy, r) in enumerate(self.clusters):
            color = colors[(i * 7) % len(colors)]
            pygame.draw.circle(image, color, (cx, cy), r * 0.92)
            pygame.draw.circle(image, colors[0].lerp((255, 255, 255), 0.25) if i % 3 == 0 else colors[0], (cx - r * 0.25, cy - r * 0.3), r * 0.4)
        self.image = image
        self.painted_palette = palette

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.image, (0, 0))


class BlossomBranch(Layer):
    # A cherry branch reaching in from the left edge of the window, just above the game's
    # tokens, crooked and dark, hung with clusters of five-petalled blossoms and buds. It
    # sways in the breeze; each pose it takes is painted once and reused. Others ask
    # flower_spots() for where petals can come loose from
    #
    # Palette colors it uses:
    #   "branch"                the wood
    #   "blossom" (a list), "blossom_dark", "blossom_middle"    the flowers

    Y = 110                         # where it comes in at the edge, pixels at the medium size
    REACH = 100
    DROOP = 40
    SWAY = 1.6                      # degrees it rocks at a normal breeze
    SWAY_TIME = 3800
    FLOWERS = 22

    def __init__(self, scene):
        super().__init__(scene)
        self.root = (-s(6), s(self.Y))
        self.time = 0
        # The limb: a crooked line of points, and a couple of twigs off it
        self.limb = []
        for k in range(7):
            t = k / 6
            self.limb.append((t * s(self.REACH), t * t * s(self.DROOP) + math.sin(t * 5) * s(3)))
        self.twigs = []
        for t in (0.35, 0.6, 0.85):
            k = int(t * 6)
            base = self.limb[k]
            up = random.choice((-1, 1))
            self.twigs.append([base, (base[0] + s(random.uniform(10, 18)), base[1] + up * s(random.uniform(8, 14)))])
        self.flowers = []
        spots = self.limb[2:] + [twig[1] for twig in self.twigs]
        for i in range(self.FLOWERS):
            bx, by = random.choice(spots)
            self.flowers.append((bx + random.uniform(-s(9), s(9)), by + random.uniform(-s(6), s(9)),
                                 s(random.uniform(5.5, 7.5)), random.uniform(0, 2 * math.pi), random.random() < 0.2))
        self.flowers.sort(key=lambda f: f[1])
        self.poses = {}
        self.painted_palette = None

    def angle(self):
        wind = self.scene.weather.get("wind", 1)
        return math.sin(self.time / self.SWAY_TIME * 2 * math.pi) * self.SWAY * wind + (wind - 1) * 1.2

    def turn(self, point, angle):
        a = math.radians(angle)
        return (self.root[0] + point[0] * math.cos(a) - point[1] * math.sin(a),
                self.root[1] + point[0] * math.sin(a) + point[1] * math.cos(a))

    def flower_spots(self):
        angle = self.angle()
        return [self.turn((x, y), angle) for x, y, size, spin, bud in self.flowers]

    def paint_pose(self, palette, angle):
        size = (int(s(self.REACH) * 1.4), int(s(self.REACH)))
        image = pygame.Surface(size, pygame.SRCALPHA)
        origin = (0, size[1] / 2)

        def at(point):
            x, y = self.turn(point, angle)
            return (x - self.root[0], y - self.root[1] + origin[1])

        wood = pygame.Color(palette.get("branch", palette["text"]))
        limb = [at(p) for p in self.limb]
        for k in range(len(limb) - 1):
            pygame.draw.line(image, wood, limb[k], limb[k + 1], max(2, int(s(9) * (1 - k / 7))))
            pygame.draw.circle(image, wood, limb[k + 1], max(1, int(s(9) * (1 - k / 7)) / 2))
        for twig in self.twigs:
            pygame.draw.line(image, wood, at(twig[0]), at(twig[1]), max(1, s(2)))
        colors = [pygame.Color(c) for c in palette.get("blossom", [palette["muted"]])]
        deep = pygame.Color(palette.get("blossom_dark", palette["muted"]))
        middle = pygame.Color(palette.get("blossom_middle", palette.get("blossom_dark", palette["muted"])))
        for i, (x, y, r, spin, bud) in enumerate(self.flowers):
            cx, cy = at((x, y))
            if bud:
                pygame.draw.circle(image, deep, (cx, cy), r * 0.55)
                continue
            color = colors[i % len(colors)]
            for p in range(5):
                a = spin + p * 2 * math.pi / 5
                pygame.draw.circle(image, deep, (cx + math.cos(a) * r * 0.62, cy + math.sin(a) * r * 0.62 + 0.6), r * 0.52)
            for p in range(5):
                a = spin + p * 2 * math.pi / 5
                pygame.draw.circle(image, color, (cx + math.cos(a) * r * 0.6, cy + math.sin(a) * r * 0.6), r * 0.48)
            pygame.draw.circle(image, middle, (cx, cy), max(1, r * 0.28))
        return image, (self.root[0], self.root[1] - origin[1])

    def update(self, dt):
        self.time += dt

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.poses = {}
            self.painted_palette = palette
        key = round(self.angle() * 4) / 4
        if key not in self.poses:
            if len(self.poses) > 60:
                self.poses = {}
            self.poses[key] = self.paint_pose(palette, key)
        image, where = self.poses[key]
        surface.blit(image, where)


class Petals(Layer):
    # Cherry petals drifting down over the whole scene: each one tumbles as it falls (it
    # narrows and widens as it turns), swings from side to side and is carried by the wind.
    # Some come loose from the branch. Where one lands on the ground it lies a moment and
    # fades. Where it lands on the pond it sends out a tiny ring, then floats, drifting
    # slowly downwind until it joins one of the little rafts of petals gathering along the
    # pond's edge. In a gust (the scene's weather "gust") the branch lets go of a flurry,
    # petals lying on the ground are swept back up, and everything in the air swirls.
    # Fewer and softer behind the middle of the game
    #
    # Palette colors it uses:
    #   "petal"                 a list of petal colors
    #   "petal_edge"            an outline, so pale petals show against a pale sky (optional)
    #   "pond_ripple"           the rings where petals land on the pond (falls back to "petal")

    COUNT = 50                      # at the fullest petal fall
    FALL = (16, 30)                 # pixels per second, at the medium size up close
    DRIFT = 20                      # sideways pixels per second at a normal breeze
    SIZE = (3.0, 4.6)
    FROM_BRANCH = 0.25              # share that come loose from the branch
    LIE = (2500, 6000)              # milliseconds one lies on the ground before it's gone
    FLOAT = (60000, 120000)         # milliseconds one floats on the pond
    TO_POND = 0.22                  # share of petals headed for the pond (it's where they last)
    MOST_AFLOAT = 70                # more than this, and the oldest fade sooner
    QUIET = 0.7

    # Gusts
    FLURRY = 30                     # petals the branch lets go of in a gust
    SWEEP = 0.6                     # share of the petals lying on the ground a gust sweeps back up
    SWIRL = 40                      # how hard petals loop in a gust, pixels per second at the medium size

    # Rafts: where floating petals gather, as (direction from the pond's middle, share of the way to its edge)
    RAFTS = ((0.25, 0.86), (-0.45, 0.84), (2.6, 0.88))
    RAFT_SIZE = 16                  # pixels at the medium size
    PADDLE = 5                      # how fast a floating petal drifts toward its raft, pixels per second
    RING_LIFE = 1100

    def __init__(self, scene, pond, branch):
        super().__init__(scene)
        self.pond = pond
        self.branch = branch
        self.falling = [self.new_petal(random.uniform(-s(10), HEIGHT)) for i in range(self.COUNT)]
        self.resting = []
        self.rings = []
        self.rafts = [pond.point(angle, share) for angle, share in self.RAFTS]
        self.flurried = False

    def new_petal(self, y=None, x=None):
        view = self.scene.view
        land = view.random_y(0.4)
        from_branch = y is None and x is None and random.random() < self.FROM_BRANCH
        if from_branch:
            x, start = random.choice(self.branch.flower_spots())
        elif x is not None:
            start = y
        else:
            start = -s(10) if y is None else y
            x = None
        size = view.scale(land)
        land = max(land, start + s(10))
        speed = s(random.uniform(*self.FALL)) * (0.6 + 0.4 * size)
        if x is None:
            # Start it upwind of where it will land, so petals land all across the garden
            drift = s(self.DRIFT) * self.scene.weather.get("wind", 1) * (land - start) / speed * 0.8
            target = random.uniform(-s(20), WIDTH + s(20))
            if random.random() < self.TO_POND:
                target, land = self.pond.point(random.uniform(0, 2 * math.pi), random.uniform(0.2, 0.9))
                land = max(land, start + s(10))
                drift = s(self.DRIFT) * self.scene.weather.get("wind", 1) * (land - start) / speed * 0.8
            x = target - drift
        return {"x": x, "y": start, "land": land, "size": s(random.uniform(*self.SIZE)) * (0.5 + 0.5 * size),
                "speed": speed, "spin": random.uniform(0, 2 * math.pi),
                "spin_speed": random.uniform(2, 5), "swing": random.uniform(0, 2 * math.pi), "pick": random.random(),
                "show": random.random()}

    def flurry(self):
        # A gust: the branch lets go of a handful, and petals on the ground lift off again
        for k in range(self.FLURRY):
            x, y = random.choice(self.branch.flower_spots())
            self.falling.append(self.new_petal(y, x))
        lifted = []
        for petal in self.resting:
            if not petal["water"] and random.random() < self.SWEEP:
                again = self.new_petal(petal["y"] - s(4), petal["x"])
                again["land"] = petal["y"] + s(random.uniform(10, 90)) * self.scene.view.scale(petal["y"])
                again["speed"] *= 0.5
                lifted.append(petal)
                self.falling.append(again)
        self.resting = [petal for petal in self.resting if petal not in lifted]

    def update(self, dt):
        weather = self.scene.weather
        wind = weather.get("wind", 1)
        fall = weather.get("petalfall", 1)
        gust = weather.get("gust", 0)
        seconds = dt / 1000
        if gust > 0.2 and not self.flurried:
            self.flurried = True
            self.flurry()
        elif gust == 0:
            self.flurried = False

        for i, petal in enumerate(self.falling):
            loop = math.sin(petal["swing"] * 1.3)
            petal["y"] += (petal["speed"] - gust * s(self.SWIRL) * (0.4 + loop)) * seconds
            petal["x"] += (s(self.DRIFT) * wind + math.sin(petal["swing"]) * s(14)) * seconds * (0.5 + 0.5 * petal["size"] / s(3))
            petal["swing"] += seconds * (2.2 + gust * 3)
            petal["spin"] += seconds * petal["spin_speed"] * (1 + gust * 2)
            if petal["y"] >= petal["land"]:
                on_water = self.pond.inside(petal["x"], petal["y"], 0.92)
                life = random.uniform(*(self.FLOAT if on_water else self.LIE))
                rest = {**petal, "water": on_water, "life": life, "age": 0.0}
                if on_water:
                    rest["raft"] = min(self.rafts, key=lambda r: (r[0] - petal["x"]) ** 2 + (r[1] - petal["y"]) ** 2
                                       + random.uniform(0, s(80)) ** 2)
                    rest["spot"] = (random.uniform(-1, 1), random.uniform(-1, 1))
                    self.rings.append({"x": petal["x"], "y": petal["y"], "age": 0.0})
                self.resting.append(rest)
                self.falling[i] = self.new_petal() if random.random() < fall else None
            elif petal["x"] > WIDTH + s(60):
                self.falling[i] = None
        self.falling = [petal for petal in self.falling if petal is not None]
        while len(self.falling) < self.COUNT * fall:
            self.falling.append(self.new_petal())

        afloat = [petal for petal in self.resting if petal["water"]]
        crowd = max(0, len(afloat) - self.MOST_AFLOAT)
        for petal in self.resting:
            petal["age"] += dt
            if not petal["water"]:
                continue
            if crowd > 0 and petal["age"] < petal["life"] - 3000:
                petal["age"] = petal["life"] - 3000           # too many afloat: the oldest start fading
                crowd -= 1
            # Drift toward its raft, slowing as it gets there and settling in among the others
            rx, ry = petal["raft"]
            spread = s(self.RAFT_SIZE)
            tx, ty = rx + petal["spot"][0] * spread, ry + petal["spot"][1] * spread * 0.45
            dx, dy = tx - petal["x"], ty - petal["y"]
            distance = math.hypot(dx, dy) or 1
            pull = s(self.PADDLE) * min(1, distance / s(20)) * (0.7 + 0.3 * wind)
            petal["x"] += dx / distance * pull * seconds
            petal["y"] += dy / distance * pull * seconds * 0.6
            petal["spin"] += seconds * 0.15
        self.resting = [petal for petal in self.resting if petal["age"] < petal["life"]]
        for ring in self.rings:
            ring["age"] += dt
        self.rings = [ring for ring in self.rings if ring["age"] < self.RING_LIFE]

    def draw_petal(self, surface, color, edge, x, y, size, turn):
        width = size * (0.35 + 0.65 * abs(math.cos(turn)))
        rect = (x - width, y - size * 0.6, width * 2, size * 1.2)
        if edge is not None and size > s(2.6):
            pygame.draw.ellipse(surface, edge, (rect[0] - 1, rect[1] - 1, rect[2] + 2, rect[3] + 2))
        pygame.draw.ellipse(surface, color, rect)

    def draw(self, surface, palette):
        colors = [pygame.Color(c) for c in palette.get("petal", [palette["text"]])]
        edge = pygame.Color(palette["petal_edge"]) if "petal_edge" in palette else None
        ripple = pygame.Color(palette.get("pond_ripple", colors[0]))
        for ring in self.rings:
            t = ring["age"] / self.RING_LIFE
            r = s(2) + s(9) * t
            color = self.pond.water_color(palette, ring["y"]).lerp(ripple, (1 - t) * 0.8)
            pygame.draw.ellipse(surface, color, (ring["x"] - r, ring["y"] - r * 0.4, r * 2, r * 0.8), 1)
        for petal in self.resting:
            fade = 1 - petal["age"] / petal["life"]
            quiet = self.QUIET * (0.5 if petal["water"] else 1)        # rafts are calm: they can stay
            if fade < 0.15 or petal["show"] > self.scene.keep(petal["x"], quiet):
                continue
            color = colors[int(petal["pick"] * len(colors)) % len(colors)]
            behind = self.pond.water_color(palette, petal["y"]) if petal["water"] else self.scene.color_at(palette, petal["y"])
            if petal["water"]:
                # Wet petals afloat look a touch deeper than dry ones, so rafts show on pale water
                if edge is not None:
                    color = color.lerp(edge, 0.3)
                color = behind.lerp(color, min(1, fade * 2.5))
                self.draw_petal(surface, color, None, petal["x"], petal["y"], petal["size"] * 1.05, petal["spin"])
            else:
                self.draw_petal(surface, behind.lerp(color, fade), None, petal["x"], petal["y"], petal["size"] * 0.9, 0.3)
        for petal in self.falling:
            if petal["show"] > self.scene.keep(petal["x"], self.QUIET):
                continue
            color = colors[int(petal["pick"] * len(colors)) % len(colors)]
            self.draw_petal(surface, color, edge, petal["x"], petal["y"], petal["size"], petal["spin"])
