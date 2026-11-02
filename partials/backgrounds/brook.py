# A woodland brook seen from just above: a stony bed, mossy banks, and a channel of water
# meandering down through them, with rocks, ferns and fallen leaves. No horizon: the whole
# window is the brook

import math

import random

import pygame

from partials.config import WIDTH, HEIGHT, CENTER_X, ENTRY_BOX_Y, ENTRY_BOX_HEIGHT, TRIES_Y, TOKENS_Y, HISTORY_Y, s
from partials.backgrounds.base import Layer
from partials.backgrounds.helpers import make_jitter


class BrookCourse:
    # Where the water runs: a meander down the window that widens into a calm pool behind
    # the middle of the game (around the entry box), straightening out there so the pool
    # sits right behind the text. Not a layer: the layers that draw the brook all ask it
    #   center(y), half_width(y)    the middle of the water and half its width at height y
    #   edge(y, side)               where the water's edge is on one side (-1 left, 1 right)
    #   bank(y, side)               where the dry gravel ends and the moss begins
    #   inside(x, y)                whether (x, y) is on the water
    #   direction(y)                which way the water flows there, as a small (x, y) step
    #   crossing, crossing_y        how the brook is crossed this game ("stones" or "log"),
    #                               and at what height: in the gap between the entry box
    #                               and the guess count, so it never sits behind text

    WIDTH = 66                      # half the channel's width, in pixels at the medium size
    POOL_WIDTH = 50                 # how much wider the pool is
    POOL_SPAN = 95                  # how far up and down the pool reaches
    MEANDER = (62, 22)              # how far the two bends swing sideways
    LOOP = (125, 52)                # how long each bend is
    RAGGED = 0.14                   # how uneven each edge is, as a share of the width
    GRAVEL = (30, 58)               # how wide the dry gravel strip beside the water is

    def __init__(self, view):
        self.view = view
        self.pool_y = ENTRY_BOX_Y - s(15)
        self.crossing = random.choice(("stones", "log"))
        gap_top, gap_bottom = ENTRY_BOX_Y + ENTRY_BOX_HEIGHT / 2, TRIES_Y - s(10)
        self.crossing_y = (gap_top + gap_bottom) / 2 + random.uniform(-s(5), s(5))
        self.phases = [random.uniform(0, 2 * math.pi) for i in range(6)]
        # How far each height is along the ground, measured up from the bottom of the window:
        # a pixel near the top covers more ground than one near the bottom, so the brook's
        # bends and ragged edges come closer together the further away they are
        self.top = -s(60)
        self.ground_at = []
        distance = 0.0
        for y in range(HEIGHT + s(60), self.top - 1, -1):
            self.ground_at.append(distance)
            distance += 1 / view.scale(y)
        self.ground_at.reverse()

    def ground(self, y):
        i = int(y) - self.top
        i = max(0, min(len(self.ground_at) - 1, i))
        return -self.ground_at[i]

    def pool(self, y):
        # 1 in the middle of the pool, fading to 0 above and below it
        return math.exp(-((y - self.pool_y) / s(self.POOL_SPAN)) ** 2)

    def center(self, y):
        a, b = self.phases[0], self.phases[1]
        g = self.ground(y)
        bend = (s(self.MEANDER[0]) * math.sin(g / s(self.LOOP[0]) + a)
                + s(self.MEANDER[1]) * math.sin(g / s(self.LOOP[1]) + b))
        return CENTER_X + bend * self.view.scale(y) * (1 - 0.85 * self.pool(y))

    def half_width(self, y):
        return (s(self.WIDTH) + s(self.POOL_WIDTH) * self.pool(y)) * self.view.scale(y)

    def ragged(self, y, side, phase):
        a, b = self.phases[phase], self.phases[phase + 1]
        g = self.ground(y)
        return 0.6 * math.sin(g / s(37) + a + side) + 0.4 * math.sin(g / s(15) + b * side)

    def edge(self, y, side):
        half = self.half_width(y) * (1 + self.RAGGED * self.ragged(y, side, 2))
        return self.center(y) + side * half

    def bank(self, y, side):
        low, high = self.GRAVEL
        gravel = s(low + (high - low) * (0.5 + 0.5 * self.ragged(y, -side, 4))) * self.view.scale(y)
        return self.edge(y, side) + side * gravel

    def inside(self, x, y, margin=1):
        center = self.center(y)
        return abs(x - center) < self.half_width(y) * margin

    def direction(self, y):
        step = s(4)
        return (self.center(y + step) - self.center(y), step)


class BrookBed(Layer):
    # The stony bed and the banks: gravel everywhere, a little darker and damper right
    # next to the water, and mossy banks covering it from the dry strip outward: a fine
    # speckle of greens, low cushions of moss and the odd sprig of clover. Painted once
    #
    # Palette colors it uses:
    #   "bed"                   the bed under the gravel
    #   "gravel"                a list of gravel colors
    #   "damp"                  the wet gravel right next to the water (falls back to "bed")
    #   "bank", "bank_dark"     the moss, and its shade under cushions and along the edge
    #   "bank_speckle"          a list of greens for the moss's fine texture
    #   "bank_light"            the tops of the moss cushions
    #   "clover"                little three-leafed sprigs

    GRAVEL = 1800                   # specks of gravel
    SPECKLE = 4000                  # specks of texture in the moss
    CUSHIONS = 26                   # low rounded cushions of moss
    CUSHION_SIZE = (9, 20)          # pixels at the medium size
    CLOVER = 40
    STEP = 6                        # pixels between points along the bank edges
    DAMP_STEPS = 5                  # steps the damp gravel fades in over

    def __init__(self, scene, course):
        super().__init__(scene)
        self.course = course
        # Gravel only where it shows: on the dry strips between the water and the moss
        self.specks = []
        while len(self.specks) < self.GRAVEL:
            y = random.uniform(-s(4), HEIGHT + s(4))
            side = random.choice((-1, 1))
            x = course.edge(y, side) + random.uniform(-0.3, 1.1) * (course.bank(y, side) - course.edge(y, side))
            self.specks.append((x, y, random.uniform(0.8, 2.3) * scene.view.scale(y), random.random()))
        # The moss: a speckle, cushions made of overlapping rounded bumps, sprigs of clover
        self.speckle = [self.on_bank(s(2), s(240)) + (random.uniform(0.7, 1.6), random.random())
                        for i in range(self.SPECKLE)]
        self.cushions = []
        for i in range(self.CUSHIONS):
            x, y = self.on_bank(s(14), s(200))
            size = s(random.uniform(*self.CUSHION_SIZE)) * scene.view.scale(y)
            bumps = [(random.uniform(-0.6, 0.6), random.uniform(-0.3, 0.3), random.uniform(0.45, 0.7))
                     for k in range(random.randint(4, 7))]
            self.cushions.append((x, y, size, bumps))
        self.clover = [self.on_bank(s(6), s(200)) + (random.uniform(0, 2 * math.pi),) for i in range(self.CLOVER)]
        self.image = None
        self.painted_palette = None

    def on_bank(self, low, high):
        # A random spot on one of the banks, between low and high pixels out from its edge
        y = random.uniform(-s(6), HEIGHT + s(6))
        side = random.choice((-1, 1))
        return (self.course.bank(y, side) + side * random.uniform(low, high), y)

    def paint(self, palette):
        course = self.course
        image = pygame.Surface((WIDTH, HEIGHT))
        image.fill(pygame.Color(palette.get("bed", palette["bg"])))

        # Damp, darker gravel along the water, fading in over a few steps toward it
        bed = pygame.Color(palette.get("bed", palette["bg"]))
        damp = pygame.Color(palette.get("damp", palette.get("bed", palette["bg"])))
        for step in range(1, self.DAMP_STEPS + 1):
            share = step / self.DAMP_STEPS
            reach = 0.75 - 0.5 * share                     # how far out toward the moss
            left, right = [], []
            for y in range(-self.STEP, HEIGHT + self.STEP * 2, self.STEP):
                left.append((course.edge(y, -1) + (course.bank(y, -1) - course.edge(y, -1)) * reach, y))
                right.append((course.edge(y, 1) + (course.bank(y, 1) - course.edge(y, 1)) * reach, y))
            pygame.draw.polygon(image, bed.lerp(damp, share), left + right[::-1])

        # Gravel
        colors = [pygame.Color(color) for color in palette.get("gravel", [palette["muted"]])]
        for x, y, size, pick in self.specks:
            color = colors[int(pick * len(colors)) % len(colors)]
            if course.inside(x, y, 1.0):
                continue                                    # under the water: not worth drawing
            pygame.draw.ellipse(image, color, (x - size, y - size * 0.8, size * 2, size * 1.6))

        # The mossy banks, from each side of the window in to the edge of the gravel
        bank = pygame.Color(palette.get("bank", palette["muted"]))
        dark = pygame.Color(palette.get("bank_dark", palette["muted"]))
        for side in (-1, 1):
            edge = [(course.bank(y, side), y) for y in range(-self.STEP, HEIGHT + self.STEP * 2, self.STEP)]
            outer = -s(20) if side < 0 else WIDTH + s(20)
            pygame.draw.polygon(image, bank, edge + [(outer, HEIGHT + s(20)), (outer, -s(20))])
        greens = [pygame.Color(color) for color in palette.get("bank_speckle", [palette.get("bank", palette["muted"])])]
        for x, y, size, pick in self.speckle:
            pygame.draw.circle(image, greens[int(pick * len(greens)) % len(greens)], (x, y), size)
        light = pygame.Color(palette.get("bank_light", palette.get("bank", palette["muted"])))
        top = bank.lerp(light, 0.5)
        for x, y, size, bumps in self.cushions:
            # Shade under it, then its bumps, each lit a little more toward the top left
            for u, v, r in bumps:
                pygame.draw.circle(image, dark, (x + (u + 0.1) * size, y + (v + 0.12) * size), r * size)
            for u, v, r in bumps:
                pygame.draw.circle(image, top, (x + u * size, y + v * size), r * size * 0.92)
            for u, v, r in bumps:
                pygame.draw.circle(image, light, (x + (u - 0.1) * size, y + (v - 0.1) * size), r * size * 0.5)
        clover = pygame.Color(palette.get("clover", palette.get("bank_dark", palette["muted"])))
        leaf = max(1.5, s(2.3))
        for x, y, turn in self.clover:
            for k in range(3):
                angle = turn + k * 2 * math.pi / 3
                pygame.draw.circle(image, clover, (x + math.cos(angle) * leaf, y + math.sin(angle) * leaf * 0.8), leaf)
        # ... but the moss never covers the gravel strip: paint the strip's edge line over it
        for side in (-1, 1):
            edge = [(course.bank(y, side), y) for y in range(-self.STEP, HEIGHT + self.STEP * 2, self.STEP)]
            pygame.draw.lines(image, dark, False, edge, max(1, s(2)))

        self.image = image
        self.painted_palette = palette

    def color_at(self, palette, y):
        return pygame.Color(palette.get("bed", palette["bg"]))

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.image, (0, 0))


class BrookWater(Layer):
    # The water in the channel: lighter shallows at its edges, deepening smoothly toward the
    # middle. The color is painted once per palette; on each wobble tick only the outline
    # it's cut to changes, so the edges boil gently
    #
    # Palette colors it uses:
    #   "water", "water_deep"   the water at its edges and in its deepest middle
    #   "shallows"              the light band along the edges (falls back to "water")

    STEP = 6
    ROW = 2                         # pixels per row when painting the color
    REACH = 1.3                     # how far out the color is painted, past the middle width
    SHALLOWS = 0.2                  # how far in the shallows fade, as a share of the width
    DEEPEST = 0.75                  # how far in (as a share) the water reaches its deepest
    JITTER = 0.8                    # how far the edges wobble, in pixels

    def __init__(self, scene, course):
        super().__init__(scene)
        self.course = course
        self.rows = list(range(-self.STEP, HEIGHT + self.STEP * 2, self.STEP))
        self.jitter = make_jitter(len(self.rows) * 2, self.JITTER)
        self.color = None
        self.image = None
        self.painted_palette = None

    def outline(self, share):
        # The water's outline pulled toward its middle: 1 is the real edge, 0 the middle line
        course = self.course
        left, right = [], []
        for i, y in enumerate(self.rows):
            center = course.center(y)
            wobble = self.jitter[i] * share, self.jitter[len(self.rows) + i] * share
            left.append((center + (course.edge(y, -1) - center) * share + wobble[0], y))
            right.append((center + (course.edge(y, 1) - center) * share + wobble[1], y))
        return left + right[::-1]

    def profile(self, palette, across):
        # The water's color at a share of the way across: 0 the middle, 1 the edge
        water = pygame.Color(palette.get("water", palette["bg"]))
        deep = pygame.Color(palette.get("water_deep", palette.get("water", palette["bg"])))
        shallows = pygame.Color(palette.get("shallows", palette.get("water", palette["bg"])))
        inward = max(0.0, min(1.0, (1 - across) / self.DEEPEST))
        depth = inward * inward * (3 - 2 * inward)                  # eases in and out
        color = water.lerp(deep, depth)
        fade = max(0.0, min(1.0, 1 - (1 - across) / self.SHALLOWS))
        return color.lerp(shallows, fade * fade * 0.7)

    def paint_color(self, palette):
        # A strip of the color across the water, stretched onto each row of the channel
        strip = pygame.Surface((129, 1))
        for i in range(129):
            strip.set_at((i, 0), self.profile(palette, abs(i / 64 - 1) * self.REACH))
        image = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        course = self.course
        for y in range(-self.ROW, HEIGHT + self.ROW, self.ROW):
            middle = y + self.ROW / 2
            half = course.half_width(middle) * self.REACH
            row = pygame.transform.smoothscale(strip, (max(2, round(half * 2)), self.ROW))
            image.blit(row, (round(course.center(middle) - half), y))
        self.color = image

    def paint(self, palette):
        if self.color is None or self.painted_palette is not palette:
            self.paint_color(palette)
        # Cut the color to the wobbling outline
        mask = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(mask, (255, 255, 255, 255), self.outline(1))
        image = self.color.copy()
        image.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        self.image = image
        self.painted_palette = palette

    def water_color(self, palette, x, y):
        # The water's color at (x, y), so things in it can fade into it
        course = self.course
        across = abs(x - course.center(y)) / max(course.half_width(y), 1)
        return self.profile(palette, min(across, self.REACH))

    def wobble(self):
        self.jitter = make_jitter(len(self.rows) * 2, self.JITTER)
        self.image = None

    def draw(self, surface, palette):
        if self.image is None or self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.image, (0, 0))


def hull(points):
    # The outline around a set of points (the smallest convex shape holding them all)
    points = sorted(set(points))
    if len(points) < 3:
        return points
    def turn(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for point in points:
        while len(lower) >= 2 and turn(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    for point in reversed(points):
        while len(upper) >= 2 and turn(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    return lower[:-1] + upper[:-1]


def rock_shape(points=7):
    # A creek stone: a flattish, irregular polygon with a few straight-ish edges, in its own
    # units around (0, 0). Not an egg: some corners are clipped off where it once cracked
    shape = []
    start = random.uniform(0, 2 * math.pi)
    for i in range(points):
        angle = start + 2 * math.pi * i / points + random.uniform(-0.25, 0.25)
        radius = random.uniform(0.78, 1.08)
        shape.append((math.cos(angle) * radius, math.sin(angle) * radius * 0.72))
    return shape


class BrookRocks(Layer):
    # Stones in and along the water: big ones out in the channel, smaller ones on the gravel
    # by the edges. Each is a faceted, flattish polygon with a shadow on its downstream side,
    # a lighter top face, sometimes a cap of moss, and a little scatter of pebbles. They keep
    # out from behind the game's tokens, entry box and guess history. Painted once, and
    # again on each wobble tick so their outlines boil like the rest
    #
    # Palette colors it uses:
    #   "rock", "rock_light", "rock_dark"   the stone, its top face, its shadow and outline
    #   "moss"                              moss growing on top
    #   "foam"                              the little white bulge of water above a stone in the stream

    IN_WATER = 18
    ON_EDGES = 34
    SIZE_WATER = (12, 25)           # pixels at the medium size
    SIZE_EDGE = (6, 15)
    MOSSY = 0.5                     # share of stones with moss on top
    SIDE = 0.32                     # how tall a stone's side face looks, as a share of its size
    SIDE_WET = 0.2                  # ... less of it for stones standing in the water
    STEPPING_SIZE = (17, 20)        # stepping stones, pixels at the medium size
    STEPPING_GAP = 42               # roughly how far apart their middles are
    CROSSING_CLEAR = 44             # how far above and below the crossing other stones keep away
    SPACING = 1.25                  # how far apart stones keep, as a share of their sizes
    PEBBLES = 3                     # pebbles scattered around each stone
    JITTER = 0.05

    def __init__(self, scene, course):
        super().__init__(scene)
        self.course = course
        self.rocks = []
        # Rows the game's busiest bits sit on: keep the middle of those clear
        self.clear_rows = [(TOKENS_Y - s(14), TOKENS_Y + s(70)), (ENTRY_BOX_Y - s(45), ENTRY_BOX_Y + s(45)),
                           (HISTORY_Y - s(20), HISTORY_Y + s(85))]
        if course.crossing == "stones":
            self.lay_stepping_stones()
        for count, sizes, where in ((self.IN_WATER, self.SIZE_WATER, "water"), (self.ON_EDGES, self.SIZE_EDGE, "edge")):
            made = 0
            for attempt in range(count * 10):
                if made >= count:
                    break
                y = random.uniform(-s(10), HEIGHT + s(10))
                if where == "water":
                    if course.pool(y) > 0.35:
                        continue                            # the pool stays open and calm
                    x = course.center(y) + random.uniform(-0.8, 0.8) * course.half_width(y)
                else:
                    side = random.choice((-1, 1))
                    x = course.edge(y, side) + random.uniform(-0.15, 0.9) * (course.bank(y, side) - course.edge(y, side))
                if self.in_the_way(x, y) or abs(y - course.crossing_y) < s(self.CROSSING_CLEAR):
                    continue
                size = s(random.uniform(*sizes)) * scene.view.scale(y)
                if self.crowded(x, y, size):
                    continue
                self.add_stone(x, y, size, where == "water")
                made += 1
        self.rocks.sort(key=lambda rock: rock["y"])
        self.image = None
        self.painted_palette = None

    def add_stone(self, x, y, size, wet, mossy=None, pebbles=None, shape=None):
        view = self.scene.view
        if pebbles is None:
            pebbles = self.PEBBLES
        self.rocks.append({"x": x, "y": y, "size": size, "shape": shape or rock_shape(random.randint(6, 8)),
                           "squash": view.flatten(y) / view.near_flatten, "side": self.SIDE_WET if wet else self.SIDE,
                           "mossy": random.random() < self.MOSSY if mossy is None else mossy, "wet": wet,
                           "pebbles": [(random.uniform(-1.7, 1.7), random.uniform(0.2, 1.3), random.uniform(0.12, 0.25))
                                       for k in range(pebbles)],
                           "jitter": make_jitter(8, self.JITTER)})

    def lay_stepping_stones(self):
        # A wobbly row of flat-topped stones from one edge of the water to the other, a
        # comfortable stride apart, the row leaning a little
        course, view = self.course, self.scene.view
        y = course.crossing_y
        left, right = course.edge(y, -1), course.edge(y, 1)
        count = max(3, round((right - left) / (s(self.STEPPING_GAP) * view.scale(y))))
        lean = random.uniform(-0.12, 0.12)
        for i in range(count):
            share = (i + 0.5) / count
            x = left + (right - left) * (share + random.uniform(-0.05, 0.05))
            stone_y = y + (x - CENTER_X) * lean + random.uniform(-s(3), s(3))
            size = s(random.uniform(*self.STEPPING_SIZE)) * view.scale(stone_y)
            # Flatter on top than an ordinary stone: worn smooth by feet and water
            shape = [(u * 1.05, v * 0.85) for u, v in rock_shape(random.randint(7, 8))]
            self.add_stone(x, stone_y, size, True, mossy=random.random() < 0.25, pebbles=1, shape=shape)

    def crowded(self, x, y, size):
        # Too close to a stone already placed? Neighbours may nearly touch, but not pile up
        for other in self.rocks:
            gap = (size + other["size"]) * self.SPACING
            if (x - other["x"]) ** 2 + ((y - other["y"]) * 1.3) ** 2 < gap * gap:
                return True
        return False

    def in_the_way(self, x, y):
        # Behind the middle of the game's busiest rows?
        if self.scene.keep(x) > 0.85:
            return False
        return any(top < y < bottom for top, bottom in self.clear_rows)

    def place(self, rock, points, scale=1, shift=(0, 0)):
        placed = []
        for i, (u, v) in enumerate(points):
            push = (1 + rock["jitter"][i % len(rock["jitter"])]) * scale
            placed.append((rock["x"] + (u * push + shift[0]) * rock["size"],
                           rock["y"] + (v * push * rock["squash"] + shift[1]) * rock["size"]))
        return placed

    def paint(self, palette):
        image = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        rock = pygame.Color(palette.get("rock", palette["muted"]))
        light = pygame.Color(palette.get("rock_light", palette["muted"]))
        dark = pygame.Color(palette.get("rock_dark", palette["muted"]))
        moss = pygame.Color(palette.get("moss", palette["muted"]))
        foam = pygame.Color(palette.get("foam", palette["text"]))
        wash = pygame.Color(palette.get("water", palette["bg"])).lerp(foam, 0.45)
        side = rock.lerp(dark, 0.55)
        for stone in self.rocks:
            size = stone["size"]
            # Pebbles around it
            for px, py, ps in stone["pebbles"]:
                cx, cy = stone["x"] + px * size, stone["y"] + (py * stone["squash"] + stone["side"]) * size
                r = ps * size
                pygame.draw.ellipse(image, dark, (cx - r, cy - r * 0.6, r * 2, r * 1.4))
                pygame.draw.ellipse(image, rock, (cx - r * 0.9, cy - r * 0.75, r * 1.7, r * 1.2))
            # In the stream, the water bulges up white on its upstream side
            if stone["wet"]:
                cx, cy, r, q = stone["x"], stone["y"] + stone["side"] * size, size * 1.15, stone["squash"]
                pygame.draw.arc(image, wash, (cx - r * 1.1, cy - r * 0.95 * q, r * 2.2, r * 1.5 * q), 0.5, 2.65, max(1, s(2)))
                pygame.draw.arc(image, foam, (cx - r * 0.85, cy - r * 0.8 * q, r * 1.7, r * 1.15 * q), 0.9, 2.25, max(1, s(1)))
            # Its shadow, its side (the face toward us, below the top), the top, its lit
            # face, moss
            body = self.place(stone, stone["shape"])
            drop = stone["side"] * size
            whole = hull(body + [(x, y + drop) for x, y in body])
            pygame.draw.polygon(image, dark, [(x + size * 0.14, y + size * 0.12) for x, y in whole])
            pygame.draw.polygon(image, side, whole)
            pygame.draw.lines(image, dark, True, whole, 1)
            pygame.draw.polygon(image, rock, body)
            pygame.draw.polygon(image, light, self.place(stone, stone["shape"], 0.58, (-0.14, -0.16)))
            if stone["mossy"]:
                cap = [(u, v) for u, v in stone["shape"] if u < 0.35 and v < 0.25]
                if len(cap) >= 3:
                    pygame.draw.polygon(image, moss, self.place(stone, cap, 0.85, (-0.08, -0.06)))
            pygame.draw.lines(image, dark, True, body, 1)
        self.image = image
        self.painted_palette = palette

    def wobble(self):
        for stone in self.rocks:
            stone["jitter"] = make_jitter(8, self.JITTER)
        self.image = None

    def draw(self, surface, palette):
        if self.image is None or self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.image, (0, 0))


def draw_leaf(surface, color, shadow, x, y, angle, length, squash=1):
    # A fallen leaf: a pointed oval with a midrib, and a shadow just below it. squash
    # flattens it the way the view flattens everything lying on the ground
    tip = (math.cos(angle) * length, math.sin(angle) * length * squash)
    side = (-math.sin(angle) * length * 0.38, math.cos(angle) * length * 0.38 * squash)
    shape = [(x + tip[0], y + tip[1]), (x + side[0], y + side[1]), (x - tip[0], y - tip[1]), (x - side[0], y - side[1])]
    pygame.draw.polygon(surface, shadow, [(px + 1, py + 1.5) for px, py in shape])
    pygame.draw.polygon(surface, color, shape)
    pygame.draw.line(surface, color.lerp((0, 0, 0), 0.2), shape[0], shape[2])


class BrookLeaves(Layer):
    # Fallen leaves lying still on the banks and the gravel (the ones on the water drift:
    # see brook_flow.py), each with a faint shadow and a midrib. Painted once into an image
    #
    # Palette colors it uses:
    #   "litter"                    a list of fallen leaf colors

    LEAVES = 26
    SIZE = (4.5, 7.5)               # half a leaf's length, pixels at the medium size

    def __init__(self, scene, course):
        super().__init__(scene)
        self.course = course
        self.leaves = []
        for i in range(self.LEAVES):
            y = random.uniform(0, HEIGHT)
            x = course.center(y) + random.choice((-1, 1)) * random.uniform(1.25, 2.6) * course.half_width(y)
            self.leaves.append((x, y, random.uniform(0, math.pi), s(random.uniform(*self.SIZE)), random.random()))
        self.image = None
        self.painted_palette = None

    def paint(self, palette):
        image = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        colors = [pygame.Color(color) for color in palette.get("litter", [palette["muted"]])]
        shadow = (0, 0, 0, int(255 * palette.get("shadow", 0.3) * 0.5))
        for x, y, angle, length, pick in self.leaves:
            view = self.scene.view
            draw_leaf(image, colors[int(pick * len(colors)) % len(colors)], shadow, x, y, angle,
                      length * view.scale(y), view.flatten(y) / view.near_flatten)
        self.image = image
        self.painted_palette = palette

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.image, (0, 0))


class BrookHaze(Layer):
    # A faint veil over the far (top) end of the brook, so it reads as further away: soft
    # light in the air by day, darkness gathering under the trees at night. Painted once
    #
    # Palette colors it uses:
    #   "haze"                  the veil's color
    #   "haze_strength"         how strong it is at the very top, 0 to 1

    REACH = 0.5                     # how far down the window it fades out

    def __init__(self, scene):
        super().__init__(scene)
        self.image = None
        self.painted_palette = None

    def paint(self, palette):
        height = max(1, int(HEIGHT * self.REACH))
        color = pygame.Color(palette.get("haze", palette["bg"]))
        strength = palette.get("haze_strength", 0.2)
        image = pygame.Surface((1, height), pygame.SRCALPHA)
        for y in range(height):
            fade = 1 - y / height
            image.set_at((0, y), (color.r, color.g, color.b, int(255 * strength * fade * fade)))
        self.image = pygame.transform.scale(image, (WIDTH, height))
        self.painted_palette = palette

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.image, (0, 0))


class FallenLog(Layer):
    # A fallen tree trunk lying across the brook from bank to bank, on games when that's how
    # the brook is crossed. Bark with a lit top and a shaded underside, a sawn-off end with
    # its rings showing, a broken-off end, a stub of a branch and a patch of moss, a shadow
    # on the water below it, and a pale line where the water presses against its upstream
    # side. Painted once, and again on each wobble tick
    #
    # Palette colors it uses:
    #   "bark", "bark_light", "bark_dark"   the trunk, its lit top and its shaded underside
    #   "wood", "wood_ring"                 the sawn end and its rings
    #   "moss", "foam", "water"

    RADIUS = 14                     # half the trunk's thickness, pixels at the medium size
    OVERHANG = (25, 55)             # how far each end reaches past the gravel onto the moss
    TILT = 34                       # how far one end may sit higher than the other, at most
    SAMPLES = 16                    # points along each edge
    JITTER = 0.6                    # how far the edges wobble, in pixels

    def __init__(self, scene, course):
        super().__init__(scene)
        self.course = course
        self.present = course.crossing == "log"
        y = course.crossing_y
        tilt = random.uniform(-s(self.TILT), s(self.TILT))
        self.start = (course.bank(y, -1) - s(random.uniform(*self.OVERHANG)), y - tilt / 2)
        self.end = (course.bank(y, 1) + s(random.uniform(*self.OVERHANG)), y + tilt / 2)
        self.radius = s(self.RADIUS) * scene.view.scale(y)
        self.squash = scene.view.flatten(y) / scene.view.near_flatten
        self.sawn_left = random.random() < 0.5
        self.stub = random.uniform(0.25, 0.4) if random.random() < 0.5 else random.uniform(0.6, 0.75)
        self.moss_at = random.uniform(0.15, 0.85)
        self.bark_marks = [(random.uniform(0.04, 0.96), random.uniform(-0.6, 0.6), random.uniform(0.02, 0.05))
                           for i in range(18)]
        self.jitter = make_jitter(self.SAMPLES * 2, self.JITTER)
        self.image = None
        self.painted_palette = None

    def along(self, t, across=0.0):
        # A point t of the way from start to end, across * radius off the middle line
        # (positive across is the underside, toward us)
        (x0, y0), (x1, y1) = self.start, self.end
        length = math.hypot(x1 - x0, y1 - y0)
        nx, ny = -(y1 - y0) / length, (x1 - x0) / length
        r = self.radius * across
        return (x0 + (x1 - x0) * t + nx * r, y0 + (y1 - y0) * t + ny * r * self.squash)

    def band(self, top, bottom, wobble=True, t0=0.0, t1=1.0):
        # The outline of a strip along the trunk between two offsets across it
        upper, lower = [], []
        for i in range(self.SAMPLES):
            t = t0 + (t1 - t0) * i / (self.SAMPLES - 1)
            push = (self.jitter[i], self.jitter[self.SAMPLES + i]) if wobble else (0, 0)
            ux, uy = self.along(t, top)
            lx, ly = self.along(t, bottom)
            upper.append((ux, uy + push[0]))
            lower.append((lx, ly + push[1]))
        return upper + lower[::-1]

    def paint(self, palette):
        image = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        bark = pygame.Color(palette.get("bark", palette["muted"]))
        light = pygame.Color(palette.get("bark_light", palette.get("bark", palette["muted"])))
        dark = pygame.Color(palette.get("bark_dark", palette["muted"]))
        wood = pygame.Color(palette.get("wood", palette.get("bark_light", palette["muted"])))
        ring = pygame.Color(palette.get("wood_ring", palette.get("bark_dark", palette["muted"])))
        moss = pygame.Color(palette.get("moss", palette["muted"]))
        foam = pygame.Color(palette.get("foam", palette["text"]))
        water = pygame.Color(palette.get("water", palette["bg"]))
        course, r = self.course, self.radius

        # Its shadow, falling down and away from the light
        shade = (0, 0, 0, int(255 * min(0.6, palette.get("shadow", 0.3) * 1.1)))
        shadow = [(x + r * 0.5, y + r * 1.1) for x, y in self.band(-0.9, 1.0, False)]
        pygame.draw.polygon(image, shade, shadow)

        # Where the water presses against its upstream side
        line = []
        for i in range(40):
            x, y = self.along(i / 39, -1.25)
            if course.inside(x, y, 1.0):
                line.append((x, y))
            elif len(line) > 1:
                break
        if len(line) > 1:
            pygame.draw.lines(image, water.lerp(foam, 0.5), False, line, max(1, s(2)))

        # The branch stub, sticking up and back from the top
        bx, by = self.along(self.stub, -0.6)
        direction = -1 if self.stub < 0.5 else 1
        tip = (bx + direction * r * 0.9, by - r * 1.5 * self.squash)
        stub = [(bx - r * 0.35, by), (tip[0] - r * 0.15, tip[1]), (tip[0] + r * 0.2, tip[1] + r * 0.1), (bx + r * 0.35, by)]
        pygame.draw.polygon(image, bark, stub)
        pygame.draw.lines(image, dark, True, stub, 1)
        pygame.draw.ellipse(image, wood, (tip[0] - r * 0.22, tip[1] - r * 0.12, r * 0.44, r * 0.26))

        # The trunk: underside, bark, lit top, bark marks, outline
        pygame.draw.polygon(image, bark, self.band(-1, 1))
        pygame.draw.polygon(image, dark, self.band(0.35, 1, t0=0.01, t1=0.99))
        pygame.draw.polygon(image, light, self.band(-0.75, -0.3, False, 0.03, 0.97))
        for t, across, length in self.bark_marks:
            a, b = self.along(t, across), self.along(t + length, across)
            pygame.draw.line(image, dark, a, b, 1)
        pygame.draw.polygon(image, dark, self.band(-1, 1), 1)

        # Moss on top
        for k in range(6):
            mx, my = self.along(self.moss_at + (k - 2.5) * 0.018, -0.45 + 0.12 * math.sin(k * 1.7))
            pygame.draw.circle(image, moss, (mx, my), r * (0.32 + 0.1 * math.sin(k * 2.3)))

        # The ends: one sawn flat with its rings showing, one broken off ragged
        sawn, broken = (0.0, 1.0) if self.sawn_left else (1.0, 0.0)
        ex, ey = self.along(sawn)
        face = pygame.Rect(0, 0, r * 0.8, r * 2 * self.squash + 2)
        face.center = (ex, ey)
        pygame.draw.ellipse(image, wood, face)
        pygame.draw.ellipse(image, ring, face, 1)
        pygame.draw.ellipse(image, ring, face.inflate(-face.width * 0.45, -face.height * 0.45), 1)
        pygame.draw.circle(image, ring, face.center, max(1, r * 0.1))
        step = 1 if broken == 0.0 else -1
        jag = [self.along(broken, -1)]
        for k, across in enumerate((-0.6, -0.2, 0.2, 0.6)):
            jag.append(self.along(broken - step * (0.012 if k % 2 else -0.012), across))
        jag.append(self.along(broken, 1))
        jag.append(self.along(broken + step * 0.02, 0))
        pygame.draw.polygon(image, wood.lerp(dark, 0.35), jag)

        self.image = image
        self.painted_palette = palette

    def wobble(self):
        self.jitter = make_jitter(self.SAMPLES * 2, self.JITTER)
        self.image = None

    def draw(self, surface, palette):
        if not self.present:
            return
        if self.image is None or self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.image, (0, 0))
