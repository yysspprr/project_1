# The city theme's scenery: standing on a rooftop at the edge of a big city, looking out
# over the skyline. Far off, hazy towers (one with a tall spire); closer, rows of office and
# apartment blocks with grids of windows; an elevated railway on its arches running across;
# and in the bottom corners, the roof we're on: a wooden water tower on the left, a chimney,
# an aerial and potted plants on the right
#
# The buildings don't move, so each row is painted once into an image (and again only when
# the palette changes). Every building remembers where its windows are, so lights can come
# on in them later

import math

import random

import pygame

from partials.config import WIDTH, HEIGHT, s
from partials.backgrounds.base import Layer
from partials.backgrounds.sky import Sky
from partials.backgrounds.peaks import wash, quiet_wash


class CitySky(Sky):
    # The usual sky, with the sun or moon high enough to clear the towers
    BODY_HEIGHT = 0.2


def tone(palette, index, distance):
    # One of the palette's building colors, faded into the haze with distance
    tones = palette["building_tones"]
    return pygame.Color(tones[index % len(tones)]).lerp(pygame.Color(palette["haze"]), distance)


class Skyline(Layer):
    # One row of buildings, side by side and a little overlapping, each with its own color,
    # height and rooftop (a stepped crown, a water tank, an aerial, a pitched roof or a dome),
    # and a grid of windows. Lower down they fade into the haze over the streets; everything
    # below that is haze, until the next row in front covers it
    #
    # Palette colors it uses:
    #   "building_tones"    a list of wall colors the buildings pick from
    #   "haze"              the city air they fade into with distance
    #   "window"            the windows, unlit
    #   "lit_side"          the sides facing the sun or moon catch a little of this...
    #   "lit_side_amount"   ... this much (0-1)
    #   "roof_dark"         rooftop odds and ends

    FADE = 90                       # how far below the row's tops it fades into the haze
    QUIET_GENTLE = 0.5

    def __init__(self, scene, tops, widths, distance, window, gap, landmarks=()):
        # tops, widths: (lowest, highest) at the medium size; distance: 0 near, 1 far;
        # window, gap: a window's size and the spacing between them; landmarks: buildings
        # placed by hand, as (x, width, top, kind)
        super().__init__(scene)
        self.distance = distance
        self.window = (max(1, s(window[0])), max(1, s(window[1])))
        self.gap = (max(2, s(gap[0])), max(2, s(gap[1])))
        self.buildings = []
        x = -s(random.uniform(5, 20))
        while x < WIDTH + s(10):
            w = s(random.uniform(*widths))
            top = s(random.uniform(*tops))
            if random.random() < 0.15:
                top -= s(random.uniform(15, 35))                # now and then a taller one
            kind = random.choice(("plain", "plain", "setback", "tank", "antenna", "crown", "pitched", "dome", "glass"))
            self.buildings.append(self.make_building(x, w, top, kind))
            x += w * random.uniform(0.75, 1.05)
        for lx, lw, ltop, kind in landmarks:
            self.buildings.append(self.make_building(s(lx), s(lw), s(ltop), kind))
        random.shuffle(self.buildings)                          # so they overlap every which way
        for b in self.buildings:
            if b["landmark"]:
                self.buildings.remove(b)
                self.buildings.append(b)                        # landmarks stand in front of their row
        self.high = min(b["top"] for b in self.buildings) - s(60)
        self.low = max(b["top"] for b in self.buildings)
        self.mean = sum(b["top"] for b in self.buildings) / len(self.buildings)
        self.bottom = int(self.mean + s(self.FADE)) + 1
        # The windows that can light up: not hidden behind a building in front, and not in
        # the blank walls or the glass towers (they have no window grid)
        self.lights = []
        for i, b in enumerate(self.buildings):
            if b["skip"] or b["kind"] == "glass":
                continue
            for wx, wy, ww, wh in b["windows"]:
                hidden = False
                for c in self.buildings[i + 1:]:
                    if c["x"] - 1 <= wx + ww / 2 <= c["x"] + c["w"] + c["side"] + 1 and wy + wh / 2 >= c["top"]:
                        hidden = True
                        break
                if not hidden:
                    self.lights.append((wx, wy, ww, wh))
        self.tips = []                  # the tops of the masts and spires, for their warning lights
        self.image = None
        self.painted_palette = None

    def make_building(self, x, w, top, kind):
        b = {"x": x, "w": w, "top": top, "kind": kind, "tone": random.randrange(8), "landmark": kind in ("spire", "needle"),
             "side": int(w * random.uniform(0.12, 0.22)), "windows": [], "skip": random.random() < 0.12}
        # The window grid, across the front and down to where the haze swallows it
        wx, wy = self.window
        gx, gy = self.gap
        cols = max(1, int((w - gx) / gx))
        margin = (w - cols * gx) / 2 + (gx - wx) / 2
        y = top + gy * 0.8
        while y < top + s(self.FADE) * 1.6:
            for c in range(cols):
                if random.random() < 0.9:
                    b["windows"].append((x + margin + c * gx, y, wx, wy))
            y += gy
        return b

    # ---- Painting ----

    def paint_roof(self, image, b, color, dark, k):
        x, w, top = b["x"], b["w"], b["top"] - self.high
        kind = b["kind"]
        middle = x + w / 2
        tip = {"spire": (middle, top - 70 * k), "needle": (middle, top - 46 * k), "crown": (middle, top - 30 * k),
               "antenna": (middle + w * 0.1, top - 22 * k)}.get(kind)
        if tip is not None:
            self.tips.append((tip[0], tip[1] + self.high, kind in ("spire", "needle")))
        if kind == "setback":
            pygame.draw.rect(image, color, (x + w * 0.15, top - 10 * k, w * 0.7, 10 * k + 1))
            pygame.draw.rect(image, color, (x + w * 0.3, top - 18 * k, w * 0.4, 8 * k + 1))
        elif kind == "tank":
            tx = x + w * random.uniform(0.25, 0.7)
            for lx in (-3, 3):
                pygame.draw.line(image, dark, (tx + lx * k, top), (tx + lx * k, top - 5 * k), 1)
            pygame.draw.rect(image, dark, (tx - 4 * k, top - 11 * k, 8 * k, 6 * k))
            pygame.draw.polygon(image, dark, [(tx - 4.5 * k, top - 11 * k), (tx + 4.5 * k, top - 11 * k), (tx, top - 14 * k)])
        elif kind == "antenna":
            pygame.draw.rect(image, color, (x + w * 0.2, top - 5 * k, w * 0.35, 5 * k + 1))
            pygame.draw.line(image, dark, (middle + w * 0.1, top), (middle + w * 0.1, top - 22 * k), 1)
        elif kind == "crown":
            for step in range(3):                               # an art deco crown of steps, and a mast
                inset = w * (0.12 + step * 0.12)
                pygame.draw.rect(image, color, (x + inset, top - (step + 1) * 6 * k, w - inset * 2, 6 * k + 1))
            pygame.draw.line(image, color, (middle, top - 18 * k), (middle, top - 30 * k), max(1, int(1.5 * k)))
        elif kind == "pitched":
            pygame.draw.polygon(image, dark.lerp(color, 0.5), [(x - 1, top), (x + w + 1, top), (middle, top - w * 0.3)])
        elif kind == "dome":
            pygame.draw.ellipse(image, dark.lerp(color, 0.6), (middle - w * 0.25, top - w * 0.25, w * 0.5, w * 0.5))
            pygame.draw.line(image, dark, (middle, top - w * 0.25), (middle, top - w * 0.25 - 5 * k), 1)
        elif kind == "spire":
            for step in range(4):                               # tiers narrowing up to a long spire
                inset = w * (0.1 + step * 0.1)
                pygame.draw.rect(image, color, (x + inset, top - (step + 1) * 9 * k, w - inset * 2, 9 * k + 1))
            pygame.draw.polygon(image, color, [(middle - w * 0.12, top - 36 * k), (middle + w * 0.12, top - 36 * k), (middle, top - 70 * k)])
        elif kind == "needle":
            pygame.draw.rect(image, color, (x + w * 0.3, top - 8 * k, w * 0.4, 8 * k + 1))
            pygame.draw.line(image, color, (middle, top - 8 * k), (middle, top - 46 * k), max(1, int(1.5 * k)))
        # Little things on most roofs: boxes and vents
        if kind in ("plain", "glass", "tank") and w > s(20):
            bx = x + w * random.uniform(0.1, 0.6)
            pygame.draw.rect(image, dark.lerp(color, 0.4), (bx, top - 3 * k, w * 0.2, 3 * k + 1))

    def paint(self, palette):
        height = self.bottom - self.high
        self.image = pygame.Surface((WIDTH, height), pygame.SRCALPHA)
        k = s(1) * (1 - self.distance * 0.35)
        haze = pygame.Color(palette["haze"])
        lit = pygame.Color(palette["lit_side"])
        amount = palette["lit_side_amount"]
        window = pygame.Color(palette["window"])
        dark_base = pygame.Color(palette["roof_dark"])
        state = random.getstate()
        random.seed(len(self.buildings) * 7919 + int(self.distance * 100))     # the same rooftops every time it's painted
        self.tips = []
        for b in self.buildings:
            color = tone(palette, b["tone"], self.distance)
            dark = dark_base.lerp(haze, self.distance)
            x, w, top = b["x"], b["w"], b["top"] - self.high
            # Its side face, catching the light (the sun and moon are over to the right)
            side = b["side"]
            pygame.draw.polygon(self.image, color.lerp(lit, amount), [(x + w, top), (x + w + side, top + side * 0.35), (x + w + side, height),
                                                                    (x + w, height)])
            pygame.draw.rect(self.image, color, (x, top, w, height - top))
            self.paint_roof(self.image, b, color, dark, k)
            # Windows: a grid, or tall strips of glass for the glass towers
            pane = color.lerp(window, 0.7)
            if b["kind"] == "glass":
                for wx, wy, ww, wh in b["windows"][:max(1, int((w - self.gap[0]) / self.gap[0]))]:
                    pygame.draw.rect(self.image, pane, (wx, top + s(3), ww, height))
            elif not b["skip"]:
                for wx, wy, ww, wh in b["windows"]:
                    pygame.draw.rect(self.image, pane, (wx, wy - self.high, ww, wh))
            pygame.draw.line(self.image, color.lerp(dark, 0.4), (x, top), (x + w, top), 1)            # the cornice
        random.setstate(state)
        start = self.mean - self.high
        fade = s(self.FADE)
        wash(self.image, haze, lambda y: ((y - start) / fade) ** 1.1 if y > start else 0)
        quiet_wash(self.scene, self.image, haze, self.QUIET_GENTLE)
        self.painted_palette = palette

    def fade_at(self, y):
        # How far into the haze the row has faded at height y: 0 at the tops, 1 in the haze
        start = self.mean
        return max(0.0, min(1.0, ((y - start) / s(self.FADE)) ** 1.1 if y > start else 0.0))

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.image, (0, self.high))
        if self.bottom < HEIGHT:
            surface.fill(pygame.Color(palette["haze"]), (0, self.bottom, WIDTH, HEIGHT - self.bottom))


class Viaduct(Layer):
    # An elevated railway running right across the view on a long row of arches, the rails
    # along its top. Its feet are lost in the haze over the streets
    #
    # Palette colors it uses:
    #   "viaduct", "viaduct_dark"   its stone, and the shadows in its arches
    #   "rail"                      the rails and railings
    #   "haze"

    Y = 432                         # the top of the deck, at the medium size
    DECK = 9                        # the deck's depth
    ARCH = 38                       # one arch's width
    QUIET_GENTLE = 0.5

    def __init__(self, scene):
        super().__init__(scene)
        self.y = s(self.Y)
        self.image = None
        self.painted_palette = None

    def paint(self, palette):
        haze = pygame.Color(palette["haze"])
        stone = pygame.Color(palette["viaduct"])
        dark = pygame.Color(palette["viaduct_dark"])
        rail = pygame.Color(palette["rail"])
        height = s(90)
        self.image = pygame.Surface((WIDTH, height), pygame.SRCALPHA)
        deck = s(self.DECK)
        top = s(6)
        pygame.draw.rect(self.image, stone, (0, top, WIDTH, height - top))
        # The arches: dark openings under the deck, with a thick pier between each
        arch = s(self.ARCH)
        pier = s(9)
        x = -arch / 2
        while x < WIDTH:
            left, right = x + pier / 2, x + arch - pier / 2
            spring = top + deck + s(14)
            opening = [(left, height), (left, spring)]
            for i in range(9):
                a = math.pi * i / 8
                opening.append(((left + right) / 2 - math.cos(a) * (right - left) / 2, spring - math.sin(a) * (right - left) * 0.45))
            opening += [(right, spring), (right, height)]
            pygame.draw.polygon(self.image, dark, opening)
            x += arch
        pygame.draw.rect(self.image, stone.lerp(dark, 0.25), (0, top + deck - s(2), WIDTH, s(2)))     # a ledge under the deck
        # Railings along the top, with posts, and the rails
        pygame.draw.line(self.image, rail, (0, top - s(1)), (WIDTH, top - s(1)), max(1, s(1)))
        pygame.draw.line(self.image, rail, (0, top - s(5)), (WIDTH, top - s(5)), 1)
        for px in range(0, WIDTH, s(12)):
            pygame.draw.line(self.image, rail, (px, top - s(5)), (px, top), 1)
        wash(self.image, haze, lambda y: ((y - deck - top) / (height - deck - top)) ** 0.8 if y > deck + top else 0)
        quiet_wash(self.scene, self.image, haze, self.QUIET_GENTLE)
        self.top = top
        self.painted_palette = palette

    def rail_y(self):
        # Where the trains run, on the screen
        return self.y

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.image, (0, self.y - self.top))
        surface.fill(pygame.Color(palette["haze"]), (0, self.y - self.top + self.image.get_height(), WIDTH, HEIGHT))


class Rooftop(Layer):
    # The roof we're standing on, seen in both bottom corners: its low brick parapet running
    # away from us, the tarred roof inside it, a wooden water tower on steel legs on the left,
    # and on the right a brick chimney, a TV aerial and a row of potted plants on the parapet
    #
    # Palette colors it uses:
    #   "coping", "brick", "brick_dark", "roof"         the parapet and the roof
    #   "tank", "tank_dark", "hoop", "steel"            the water tower
    #   "pot", "leaf", "leaf_dark"                      the plants

    LEFT = [(-6, 546), (150, 598), (176, 670)]          # the parapet's top edge, far end, then toward us
    RIGHT = [(446, 566), (322, 606), (300, 670)]
    TANK = (52, 580)                                    # the water tower's feet, medium size
    CHIMNEY = (398, 574)
    AERIAL = (424, 572)

    def __init__(self, scene):
        super().__init__(scene)
        self.plants = []
        for i in range(3):
            u = 0.45 + i * 0.17 + random.uniform(-0.03, 0.03)
            x, y = self.along(self.RIGHT, u)
            self.plants.append((x, y, random.uniform(0.8, 1.2), random.random() < 0.5))
        self.image = None
        self.painted_palette = None

    def along(self, outline, u):
        (ax, ay), (bx, by) = outline[0], outline[1]
        return s(ax + (bx - ax) * u), s(ay + (by - ay) * u)

    def top_at(self, x):
        # The height of the parapet's top at x, on whichever side x is
        outline = self.LEFT if x < WIDTH / 2 else self.RIGHT
        (ax, ay), (bx, by) = [(s(px), s(py)) for px, py in outline[:2]]
        t = max(0, min(1, (x - ax) / (bx - ax)))
        return ay + (by - ay) * t

    def paint_corner(self, image, outline, palette, flip):
        k = s(1)
        coping = pygame.Color(palette["coping"])
        brick = pygame.Color(palette["brick"])
        brick_dark = pygame.Color(palette["brick_dark"])
        roof = pygame.Color(palette["roof"])
        a, b, c = [(s(x), s(y)) for x, y in outline]
        wall = s(16)
        corner = (0, HEIGHT) if not flip else (WIDTH, HEIGHT)
        # The roof inside the parapet, then the parapet's inner face with courses of brick
        pygame.draw.polygon(image, roof, [a, b, c, corner, (corner[0], a[1])])
        face = [a, b, (b[0], b[1] + wall), (a[0], a[1] + wall)]
        pygame.draw.polygon(image, brick, face)
        for n in range(1, 4):
            t = n / 4
            pygame.draw.line(image, brick_dark, (a[0], a[1] + wall * t), (b[0], b[1] + wall * t), 1)
        steps = int(abs(b[0] - a[0]) / s(9))
        for n in range(steps):
            for row in range(4):
                t = (n + (0.5 if row % 2 else 0)) / steps
                px = a[0] + (b[0] - a[0]) * t
                py = a[1] + (b[1] - a[1]) * t + wall * row / 4
                pygame.draw.line(image, brick_dark, (px, py), (px, py + wall / 4), 1)
        # The far end of the parapet turns toward us
        end = [b, c, (c[0] + (s(14) if not flip else -s(14)), c[1]), (b[0] + (s(5) if not flip else -s(5)), b[1])]
        pygame.draw.polygon(image, brick.lerp(brick_dark, 0.3), end)
        # The coping stones along the top
        pygame.draw.line(image, coping, (a[0], a[1] - k), (b[0], b[1] - k), max(2, s(4)))
        pygame.draw.line(image, coping, b, c, max(2, s(4)))
        pygame.draw.line(image, brick_dark, (a[0], a[1] + s(1)), (b[0], b[1] + s(1)), 1)

    def paint_tank(self, image, palette):
        k = s(1)
        x, y = s(self.TANK[0]), s(self.TANK[1])
        wood = pygame.Color(palette["tank"])
        dark = pygame.Color(palette["tank_dark"])
        hoop = pygame.Color(palette["hoop"])
        steel = pygame.Color(palette["steel"])
        w, legs, h = 44 * k, 42 * k, 46 * k
        top = y - legs - h
        # Steel legs with cross-bracing
        for lx in (-0.42, -0.14, 0.14, 0.42):
            pygame.draw.line(image, steel, (x + lx * w, y - legs), (x + lx * w * 1.15, y), max(2, s(2)))
        for lx in (-0.42, 0.14):
            pygame.draw.line(image, steel, (x + lx * w, y - legs), (x + (lx + 0.28) * w * 1.1, y - legs * 0.45), 1)
            pygame.draw.line(image, steel, (x + (lx + 0.28) * w, y - legs), (x + lx * w * 1.1, y - legs * 0.45), 1)
        pygame.draw.line(image, steel, (x - 0.46 * w, y - legs * 0.45), (x + 0.46 * w, y - legs * 0.45), 1)
        # The tank: wooden staves, lit on the right, held by iron hoops
        pygame.draw.rect(image, wood, (x - w / 2, top, w, h))
        pygame.draw.rect(image, dark, (x - w / 2, top, w * 0.3, h))
        for n in range(1, 9):
            sx = x - w / 2 + w * n / 9
            pygame.draw.line(image, dark, (sx, top + s(1)), (sx, top + h), 1)
        for n in range(4):
            hy = top + h * (0.12 + n * 0.25)
            pygame.draw.line(image, hoop, (x - w / 2, hy), (x + w / 2, hy), max(1, s(1)))
        pygame.draw.rect(image, steel, (x - w / 2 - s(2), top + h - s(2), w + s(4), s(3)))
        # Its pointed roof, with a little finial
        pygame.draw.polygon(image, dark, [(x - w / 2 - s(3), top + s(1)), (x + w / 2 + s(3), top + s(1)), (x, top - 16 * k)])
        pygame.draw.polygon(image, dark.lerp(wood, 0.45), [(x, top - 16 * k), (x + w / 2 + s(3), top + s(1)), (x + s(4), top + s(1))])
        pygame.draw.line(image, steel, (x, top - 16 * k), (x, top - 21 * k), 1)
        pygame.draw.circle(image, steel, (x, top - 21 * k), max(1, s(1.5)))
        # A ladder up the side
        lx = x + w / 2 - s(6)
        for side in (0, s(4)):
            pygame.draw.line(image, steel, (lx + side, y), (lx + side, top - s(2)), 1)
        for ry in range(int(top), int(y), max(3, s(5))):
            pygame.draw.line(image, steel, (lx, ry), (lx + s(4), ry), 1)
        self.tank_top = (x, top - 21 * k)

    def paint_right(self, image, palette):
        k = s(1)
        brick = pygame.Color(palette["brick"])
        dark = pygame.Color(palette["brick_dark"])
        coping = pygame.Color(palette["coping"])
        steel = pygame.Color(palette["steel"])
        # The chimney stack, with two pots
        x, y = s(self.CHIMNEY[0]), s(self.CHIMNEY[1])
        w, h = 22 * k, 46 * k
        pygame.draw.rect(image, brick, (x - w / 2, y - h, w, h))
        pygame.draw.rect(image, dark, (x - w / 2, y - h, w * 0.3, h))
        for n in range(1, int(h / s(5))):
            pygame.draw.line(image, dark, (x - w / 2, y - h + n * s(5)), (x + w / 2, y - h + n * s(5)), 1)
        pygame.draw.rect(image, coping, (x - w / 2 - s(2), y - h - s(3), w + s(4), s(4)))
        for px in (-5, 5):
            pygame.draw.rect(image, pygame.Color(palette["pot"]).lerp(dark, 0.3), (x + px * k - s(3), y - h - s(11), s(6), s(8)))
            pygame.draw.rect(image, dark, (x + px * k - s(3.5), y - h - s(12), s(7), s(2)))
        self.chimney_top = [(x - 5 * k, y - h - s(12)), (x + 5 * k, y - h - s(12))]
        # The TV aerial: a mast with crossbars
        ax, ay = s(self.AERIAL[0]), s(self.AERIAL[1])
        mast = 120 * k
        pygame.draw.line(image, steel, (ax, ay), (ax, ay - mast), max(1, s(2)))
        for n, length in enumerate((20, 16, 12)):
            by = ay - mast + s(6) + n * s(9)
            pygame.draw.line(image, steel, (ax - length * k / 2, by), (ax + length * k / 2, by), 1)
            for t in range(-2, 3):
                pygame.draw.line(image, steel, (ax + t * length * k / 5, by), (ax + t * length * k / 5, by - s(2)), 1)
        for side in (-1, 1):                                     # guy wires
            pygame.draw.line(image, steel.lerp(pygame.Color(palette["haze"]), 0.5), (ax, ay - mast * 0.6), (ax + side * s(16), ay + s(2)), 1)
        self.aerial_top = (ax, ay - mast)
        # Potted plants along the parapet
        pot = pygame.Color(palette["pot"])
        leaf = pygame.Color(palette["leaf"])
        leaf_dark = pygame.Color(palette["leaf_dark"])
        for px, py, size, tall in self.plants:
            pw, ph = 9 * k * size, 8 * k * size
            pygame.draw.polygon(image, pot, [(px - pw / 2, py - ph), (px + pw / 2, py - ph), (px + pw * 0.38, py - s(1)), (px - pw * 0.38, py - s(1))])
            pygame.draw.rect(image, pot.lerp((0, 0, 0), 0.2), (px - pw / 2 - s(1), py - ph - s(2), pw + s(2), s(2)))
            if tall:                                            # tall spiky leaves
                for n in range(6):
                    a = -math.pi / 2 + (n - 2.5) * 0.28
                    pygame.draw.line(image, leaf if n % 2 else leaf_dark, (px, py - ph), (px + math.cos(a) * 15 * k * size, py - ph + math.sin(a) * 15 * k * size),
                                     max(1, s(2)))
            else:                                               # a round leafy bush
                for n in range(7):
                    a = math.pi + n / 6 * math.pi
                    pygame.draw.circle(image, leaf_dark if n % 2 else leaf, (px + math.cos(a) * 5 * k * size, py - ph - 3 * k + math.sin(a) * 5 * k * size), 3.5 * k * size)
                pygame.draw.circle(image, leaf, (px, py - ph - 6 * k * size), 4 * k * size)

    def paint(self, palette):
        self.image = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.paint_corner(self.image, self.LEFT, palette, False)
        self.paint_corner(self.image, self.RIGHT, palette, True)
        self.paint_tank(self.image, palette)
        self.paint_right(self.image, palette)
        self.painted_palette = palette

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.image, (0, 0))
