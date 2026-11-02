# The mountains theme's scenery: a great snowy range across the back, its feet lost in a
# sea of cloud, then rows of forested ridges stepping down toward us, each one hazier with
# distance, with banks of mist drifting between them. In the bottom corners, the rocky
# ledge we're standing on, with a stone cairn and a line of prayer flags in the wind
#
# Big things that don't move (the peaks, the ridges, the ledge) are painted once into
# images and only repainted when the palette changes, so they cost one blit a frame

import math

import random

import pygame

from partials.config import WIDTH, HEIGHT, s
from partials.backgrounds.base import Layer
from partials.backgrounds.sky import Sky
from partials.backgrounds.helpers import Swell


def jagged(start, end, rough, levels=4, sideways=False):
    # Points from start to end with the line between them broken up, like a ridgeline:
    # each pass puts a pushed-out midpoint between every two points. rough is how far,
    # as a share of the gap. Lines that run mostly up and down push sideways instead
    points = [start, end]
    for level in range(levels):
        broken = [points[0]]
        for a, b in zip(points, points[1:]):
            gap = math.hypot(b[0] - a[0], b[1] - a[1])
            push = random.uniform(-1, 1) * gap * rough
            middle = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            if sideways:
                broken.append((middle[0] + push, middle[1] + push * 0.2))
            else:
                broken.append((middle[0] + push * 0.2, middle[1] + push))
            broken.append(b)
        points = broken
    return points


def chain(keys, rough, sideways=False):
    # A jagged line through several key points in turn
    points = []
    for a, b in zip(keys, keys[1:]):
        points += jagged(a, b, rough, sideways=sideways)[:-1]
    points.append(keys[-1])
    return points


def wash(image, color, alpha_at, along="rows"):
    # Tint a see-through image toward color, only where it's already drawn: alpha_at(i)
    # (0-1) says how strongly for each row (or each column, with along="columns")
    width, height = image.get_size()
    tint = pygame.Surface((width, height), pygame.SRCALPHA)
    paint = pygame.Color(color)
    count = height if along == "rows" else width
    for i in range(count):
        strength = max(0.0, min(1.0, alpha_at(i)))
        if strength <= 0:
            continue
        paint.a = int(255 * strength)
        if along == "rows":
            pygame.draw.line(tint, paint, (0, i), (width, i))
        else:
            pygame.draw.line(tint, paint, (i, 0), (i, height))
    # Cut the tint to the image's own shape: white with the image's alpha, then the smaller of each
    shape = image.copy()
    shape.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
    tint.blit(shape, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    image.blit(tint, (0, 0))


def quiet_wash(scene, image, color, gentle, left=0):
    # Soften an image toward color in the quiet column, so the game's text stays easy to read
    wash(image, color, lambda x: 1 - scene.keep(x + left, gentle), along="columns")


class PeakSky(Sky):
    # The usual sky, with the sun or moon a little higher so it clears the peaks
    BODY_HEIGHT = 0.24


class GreatPeaks(Layer):
    # The snowy range at the back: a row of far, hazy summits, a lower peak in the middle
    # and two great ones in front, the biggest on the left. Each peak has a shadowed face
    # and a sunlit face (the light comes from the right, where the sun or moon is), with
    # snow above a ragged snowline, ribs of rock and a few crevasses. Their feet fade
    # into the haze where the sea of cloud lies
    #
    # Palette colors it uses:
    #   "snow_lit", "snow_shade"    snow in the light and in shadow
    #   "rock_lit", "rock_shade"    bare rock below the snowline and on the ribs
    #   "haze"                      the air between us and them: far things fade into it

    BASE = 235                      # where their feet are lost in the haze, at the medium size
    FADE = 95                       # how far above that they start fading
    QUIET_GENTLE = 0.45             # how much they soften behind the game's text

    # The near peaks, at the medium size: summit, the key points down each side to the
    # foot, where the line between the two faces meets the foot, and the snowline
    PEAKS = (
        {"top": (255, 128), "left": [(205, 165), (160, 235)], "right": [(300, 160), (345, 235)],
         "spine": 270, "snow": 182, "haze": 0.42},
        {"top": (365, 86), "left": [(330, 118), (300, 140), (235, 235)], "right": [(410, 112), (470, 175), (520, 235)],
         "spine": 385, "snow": 178, "haze": 0.14},
        {"top": (100, 38), "left": [(62, 92), (36, 122), (-70, 235)],
         "right": [(132, 84), (168, 112), (196, 100), (222, 132), (300, 235)],
         "spine": 128, "snow": 172, "haze": 0.0},
    )

    def __init__(self, scene):
        super().__init__(scene)
        self.base = s(self.BASE)
        self.bottom = self.base + s(40)
        self.peaks = []
        # A chain of far summits all the way across, faint in the haze
        x = -s(30)
        while x < WIDTH + s(30):
            top = (x + random.uniform(-s(10), s(10)), s(random.uniform(112, 150)))
            half = s(random.uniform(50, 80))
            self.peaks.append(self.make_peak(top, [(top[0] - half, self.bottom)], [(top[0] + half, self.bottom)],
                                             top[0] + random.uniform(-0.2, 0.4) * half, top[1] + s(40), 0.62))
            x += s(random.uniform(55, 85))
        for peak in self.PEAKS:
            top = (s(peak["top"][0]), s(peak["top"][1]))
            left = [(s(px), s(py)) for px, py in peak["left"]]
            right = [(s(px), s(py)) for px, py in peak["right"]]
            left[-1] = (left[-1][0], self.bottom)
            right[-1] = (right[-1][0], self.bottom)
            self.peaks.append(self.make_peak(top, left, right, s(peak["spine"]), s(peak["snow"]), peak["haze"]))
        self.summits = [p["top"] for p in self.peaks[-3:]]    # for the snow plume, later
        self.image = None
        self.painted_palette = None

    def make_peak(self, top, left, right, spine, snow, haze):
        left_line = chain([top] + left, 0.16)
        right_line = chain([top] + right, 0.16)
        bend = (spine - top[0]) * 0.6
        spine_line = chain([top, (top[0] + bend, top[1] + (self.bottom - top[1]) * 0.45), (spine, self.bottom)], 0.12, sideways=True)
        # The snowline: a wavering edge, lower on the sunny face (it has had less sun on
        # the shady side), with the odd rib of rock reaching up into the snow
        snowline = []
        waves = [(random.uniform(0, 6.3), s(random.uniform(18, 28)), s(10)), (random.uniform(0, 6.3), s(random.uniform(7, 11)), s(5))]
        x = left[-1][0]
        while x <= right[-1][0] + s(5):
            y = snow + (s(14) if x > spine else 0) + random.uniform(-s(1.5), s(1.5))
            for phase, length, height in waves:
                y += math.sin(x / length + phase) * height
            snowline.append((x, y))
            x += s(4)
        # Ribs of rock running down through the snow: thin streaks following the fall line,
        # mostly on the steep shadowed face
        ribs = []
        for i in range(random.randint(6, 10)):
            shady = random.random() < 0.65
            side = left_line if shady else right_line
            u = random.uniform(0.12, 0.7)
            sx, sy = side[int(u * (len(side) - 1))]
            sx += (spine - sx) * random.uniform(0.15, 0.6)
            length = s(random.uniform(10, 34))
            lean = random.uniform(-0.45, -0.15) if shady else random.uniform(0.1, 0.35)
            ribs.append((sx, sy + s(5), random.uniform(s(1), s(2.5)), length, lean))
        crevasses = []
        return {"top": top, "left": left_line, "right": right_line, "spine": spine_line, "snowline": snowline,
                "ribs": ribs, "crevasses": crevasses, "haze": haze}

    # ---- Painting ----

    def paint_peak(self, peak, palette):
        haze = pygame.Color(palette["haze"])

        def tone(key):
            return pygame.Color(palette[key]).lerp(haze, peak["haze"])

        size = (WIDTH, self.bottom)
        shade_face = peak["left"] + list(reversed(peak["spine"]))
        lit_face = peak["spine"] + list(reversed(peak["right"]))

        snow = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.polygon(snow, tone("snow_shade"), shade_face)
        pygame.draw.polygon(snow, tone("snow_lit"), lit_face)
        for cx, cy, w in peak["crevasses"]:
            pygame.draw.arc(snow, tone("snow_shade"), (cx - w, cy - w * 0.3, w * 2, w * 0.8), 0.3, 2.8, 1)

        rock = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.polygon(rock, tone("rock_shade"), shade_face)
        pygame.draw.polygon(rock, tone("rock_lit"), lit_face)
        above = peak["snowline"] + [(peak["snowline"][-1][0] + s(20), 0), (peak["snowline"][0][0] - s(20), 0)]
        pygame.draw.polygon(rock, (0, 0, 0, 0), above)
        # The ribs: thin streaks of rock running down through the snow
        spine_x = peak["spine"][-1][0]
        for x, y, w, length, lean in peak["ribs"]:
            color = tone("rock_shade") if x < spine_x else tone("rock_lit").lerp(tone("rock_shade"), 0.3)
            mid = (x + length * lean * 0.5 + w * 0.6, y + length * 0.5)
            pygame.draw.polygon(rock, color, [(x, y), (mid[0] + w, mid[1]), (x + length * lean, y + length), (mid[0] - w, mid[1] + w)])
        # Only where the peak itself is
        shape = snow.copy()
        shape.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
        rock.blit(shape, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        snow.blit(rock, (0, 0))
        # A crisp edge where the two faces meet
        pygame.draw.lines(snow, tone("snow_lit").lerp(tone("snow_shade"), 0.25), False, peak["spine"][:len(peak["spine"]) // 2], 1)
        return snow

    def paint(self, palette):
        self.image = pygame.Surface((WIDTH, self.bottom), pygame.SRCALPHA)
        for peak in self.peaks:
            self.image.blit(self.paint_peak(peak, palette), (0, 0))
        haze = pygame.Color(palette["haze"])
        start = self.base - s(self.FADE)
        wash(self.image, haze, lambda y: ((y - start) / (self.bottom - start)) ** 0.9 if y > start else 0)
        quiet_wash(self.scene, self.image, haze, self.QUIET_GENTLE)
        self.painted_palette = palette

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.image, (0, 0))


class Ridge(Layer):
    # One row of forested ridges, the treetops making a ragged edge along the top. Lower
    # down it fades into the haze of the valley, since mist lies in the low places; everything
    # below it is haze too, until the next ridge in front covers it
    #
    # Palette colors it uses:
    #   "ridge_near", "ridge_far"   the nearest ridge's color, and the furthest one's
    #   "haze"                      what they fade into

    FADE = 80                       # how far down from its highest point it fades into the haze
    QUIET_GENTLE = 0.45

    def __init__(self, scene, left_y, right_y, distance, bumps=14, tree=7):
        # left_y, right_y: roughly how high it is at each side (medium size); distance:
        # 0 for the nearest ridge, 1 for the furthest; bumps: how hilly; tree: tree height
        super().__init__(scene)
        self.distance = distance
        waves = [(random.uniform(0, 6.3), random.uniform(0.6, 1.4) / WIDTH * math.pi * k, s(bumps) / k) for k in (1, 2, 4)]
        ground = []
        for x in range(WIDTH + 1):
            y = s(left_y) + (s(right_y) - s(left_y)) * x / WIDTH
            for phase, freq, amp in waves:
                y += math.sin(x * freq * 2 + phase) * amp
            ground.append(y)
        # Fir tops along the crest: each a narrow triangle standing on the ground
        self.top = list(ground)
        x = random.uniform(0, s(4))
        while x < WIDTH:
            height = s(tree) * random.uniform(0.6, 1.3)
            half = height * random.uniform(0.28, 0.4)
            base = ground[int(x)]
            for col in range(max(0, int(x - half)), min(WIDTH, int(x + half)) + 1):
                tip = base - height + abs(col - x) / half * height
                self.top[col] = min(self.top[col], tip)
            x += half * random.uniform(1.0, 2.2)
            if random.random() < 0.08:
                x += s(random.uniform(6, 18))       # a clearing
        self.high = min(self.top)
        self.low = max(self.top)
        self.image = None
        self.painted_palette = None

    def top_at(self, x):
        return self.top[max(0, min(WIDTH, int(x)))]

    def color(self, palette):
        near = pygame.Color(palette["ridge_near"])
        return near.lerp(pygame.Color(palette["ridge_far"]), self.distance)

    def paint(self, palette):
        haze = pygame.Color(palette["haze"])
        top = int(self.high) - 1
        self.bottom = int(self.high + s(self.FADE)) + 1
        self.bottom = max(self.bottom, int(self.low) + s(10))
        self.image = pygame.Surface((WIDTH, self.bottom - top), pygame.SRCALPHA)
        points = [(x, y - top) for x, y in enumerate(self.top)]
        points += [(WIDTH, self.bottom - top), (0, self.bottom - top)]
        pygame.draw.polygon(self.image, self.color(palette), points)
        fade = s(self.FADE)
        wash(self.image, haze, lambda y: (y / fade) ** 1.2)
        quiet_wash(self.scene, self.image, haze, self.QUIET_GENTLE)
        self.top_y = top
        self.painted_palette = palette

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.image, (0, self.top_y))
        if self.bottom < HEIGHT:
            surface.fill(pygame.Color(palette["haze"]), (0, self.bottom, WIDTH, HEIGHT - self.bottom))


class MistBank(Layer):
    # A soft bank of mist lying across the valley at height y, drifting slowly sideways with
    # the wind. It's two sheets drifting at different speeds, so it seems to roll and change
    # shape, and it thickens and thins on its own
    #
    # Palette colors it uses:
    #   "mist"

    def __init__(self, scene, y, height, strength=0.7, speed=5):
        # y, height: the middle and depth of the bank (medium size); strength 0-1;
        # speed: pixels per second in a normal breeze
        super().__init__(scene)
        self.y = s(y)
        self.height = s(height)
        self.strength = strength
        self.speed = s(speed)
        self.tile = int(WIDTH * 1.5) // 8 * 8          # a multiple of 8, so the blur tiles without a seam
        self.shift = [random.uniform(0, self.tile), random.uniform(0, self.tile)]
        self.thickness = self.swell(0.55, 1.0, (6000, 14000))
        self.puffs = [self.make_puffs(), self.make_puffs()]
        self.sheets = None
        self.painted_palette = None

    def make_puffs(self):
        # Clumps of puffs with thinner stretches between, so it isn't an even strip
        puffs = []
        clumps = [random.uniform(0, self.tile) for i in range(random.randint(3, 4))]
        for i in range(int(self.tile / s(16))):
            if random.random() < 0.75:
                x = random.choice(clumps) + random.gauss(0, s(55))
            else:
                x = random.uniform(0, self.tile)
            w = s(random.uniform(50, 130))
            h = self.height * random.uniform(0.35, 0.75)
            puffs.append((x % self.tile, self.height + random.uniform(-0.3, 0.25) * self.height, w, h))
        return puffs

    def paint_sheet(self, puffs, palette):
        pad = 96
        color = pygame.Color(palette["mist"])
        sheet = pygame.Surface((self.tile + pad * 2, self.height * 2), pygame.SRCALPHA)
        sheet.fill((color.r, color.g, color.b, 0))       # see-through mist color, so the blur leaves no grey fringe
        color.a = 70
        for x, y, w, h in puffs:
            puff = pygame.Surface((int(w), int(h)), pygame.SRCALPHA)
            puff.fill((color.r, color.g, color.b, 0))
            pygame.draw.ellipse(puff, color, puff.get_rect())
            for wrap in (-self.tile, 0, self.tile):         # so the sheet tiles without a seam
                sheet.blit(puff, (pad + x + wrap - w / 2, y - h / 2))
        # Blurred: shrunk right down and grown back
        small = pygame.transform.smoothscale(sheet, (max(1, sheet.get_width() // 8), max(1, sheet.get_height() // 8)))
        sheet = pygame.transform.smoothscale(small, sheet.get_size())
        return sheet.subsurface((pad, 0, self.tile, self.height * 2)).copy()

    def update(self, dt):
        wind = self.scene.weather["wind"]
        self.shift[0] += self.speed * wind * dt / 1000
        self.shift[1] += self.speed * 0.6 * wind * dt / 1000

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.sheets = [self.paint_sheet(p, palette) for p in self.puffs]
            self.painted_palette = palette
        alpha = int(255 * self.strength * self.thickness.value)
        for i, sheet in enumerate(self.sheets):
            sheet.set_alpha(alpha)
            x = -int(self.shift[i] % self.tile)          # whole pixels, so the two copies meet exactly
            y = self.y - self.height + (s(4) if i else 0)
            surface.blit(sheet, (x, y))
            surface.blit(sheet, (x + self.tile, y))


class Ledge(Layer):
    # The rocky ledge we're standing on, rising in both bottom corners: tufts of grass and
    # a few alpine flowers on top, cracks in the rock, and on the left a cairn of stacked
    # stones with a pole for the prayer flags
    #
    # Palette colors it uses:
    #   "ledge_lit", "ledge_shade", "ledge_dark"    the rock
    #   "grass", "grass_dark", "flower", "flower_blue"
    #   "pole"                                      the flagpole

    LEFT = [(-6, 512), (22, 506), (52, 514), (76, 528), (92, 520), (106, 524), (114, 552), (124, 600), (130, 670)]
    RIGHT = [(446, 548), (426, 551), (406, 558), (390, 578), (380, 610), (371, 640), (366, 670)]
    CAIRN = 30                      # where the cairn stands on the left ledge (medium x)
    POLE = 76                       # how tall the flagpole is

    def __init__(self, scene):
        super().__init__(scene)
        self.sides = []
        for outline in (self.LEFT, self.RIGHT):
            keys = [(s(x), s(y)) for x, y in outline]
            top = chain(keys, 0.1)
            cracks = []
            for i in range(random.randint(3, 5)):
                px, py = top[random.randint(2, len(top) - 3)]
                cracks.append(jagged((px, py + s(6)), (px + random.uniform(-s(8), s(8)), py + s(random.uniform(18, 40))), 0.25, 2,
                                     sideways=True))
            tufts = []
            for a, b in zip(top[::2], top[2::2]):
                px, py = a
                steep = abs(b[1] - a[1]) > abs(b[0] - a[0]) * 1.2     # no grass on the cliff edge
                if 0 <= px <= WIDTH and not steep and random.random() < 0.6:
                    tufts.append((px, py + s(1), random.randint(3, 5), s(random.uniform(4, 8))))
            flowers = []
            for i in range(random.randint(2, 4)):
                px, py = top[random.randint(1, len(top) - 2)]
                if 0 <= px <= WIDTH:
                    flowers.append((px, py + s(random.uniform(1, 4)), random.random() < 0.5))
            self.sides.append({"top": top, "cracks": cracks, "tufts": tufts, "flowers": flowers})
        self.cairn_x = s(self.CAIRN)
        self.cairn_y = self.top_at(self.cairn_x) + s(2)
        self.stones = []
        y = self.cairn_y
        for i in range(5):
            w = s(26 - i * 4) * random.uniform(0.9, 1.1)
            h = s(8 - i * 0.6)
            self.stones.append((self.cairn_x + random.uniform(-s(2), s(2)), y - h / 2, w, h))
            y -= h * 0.8
        self.pole_top = (self.cairn_x + s(3), self.cairn_y - s(self.POLE))
        self.image = None
        self.painted_palette = None

    def top_at(self, x):
        # The height of the ledge's top at x (the left ledge on the left half, the right one
        # on the right half)
        top = sorted(self.sides[0 if x < WIDTH / 2 else 1]["top"])
        for a, b in zip(top, top[1:]):
            if a[0] <= x <= b[0]:
                return a[1] + (b[1] - a[1]) * (x - a[0]) / max(1, b[0] - a[0])
        return top[0][1] if x < top[0][0] else top[-1][1]

    def paint(self, palette):
        self.image = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        lit = pygame.Color(palette["ledge_lit"])
        shade = pygame.Color(palette["ledge_shade"])
        dark = pygame.Color(palette["ledge_dark"])
        grass = pygame.Color(palette["grass"])
        grass_dark = pygame.Color(palette["grass_dark"])
        for side in self.sides:
            top = side["top"]
            corner = (0, HEIGHT + s(5)) if top[0][0] < WIDTH / 2 else (WIDTH, HEIGHT + s(5))
            body = top + [(top[-1][0], HEIGHT + s(5)), corner]
            pygame.draw.polygon(self.image, shade, body)
            # A lit band along the top, where the light catches the rock
            rim = top + [(x + s(4), y + s(20)) for x, y in reversed(top)]
            pygame.draw.polygon(self.image, shade.lerp(lit, 0.5), rim)
            rim = top + [(x + s(2), y + s(9)) for x, y in reversed(top)]
            pygame.draw.polygon(self.image, lit, rim)
            for crack in side["cracks"]:
                pygame.draw.lines(self.image, dark, False, crack, max(1, s(1)))
            pygame.draw.lines(self.image, dark, False, top, max(1, s(1)))
            for x, y, blades, height in side["tufts"]:
                for b in range(blades):
                    lean = (b - blades / 2) * s(1.5)
                    color = grass if b % 2 else grass_dark
                    pygame.draw.line(self.image, color, (x + b - blades / 2, y), (x + lean, y - height * random.uniform(0.6, 1)), 1)
            for x, y, blue in side["flowers"]:
                petal = pygame.Color(palette["flower_blue"] if blue else palette["flower"])
                for a in range(5):
                    angle = a * 2 * math.pi / 5
                    pygame.draw.circle(self.image, petal, (x + math.cos(angle) * s(2), y - s(3) + math.sin(angle) * s(2)), max(1, s(1.4)))
                pygame.draw.circle(self.image, pygame.Color("#f2d24a"), (x, y - s(3)), max(1, s(1)))
        # The flagpole, pushed into the cairn, then the cairn's stones
        pole = pygame.Color(palette["pole"])
        pygame.draw.line(self.image, pole, (self.pole_top[0], self.cairn_y - s(10)), self.pole_top, max(2, s(2)))
        for x, y, w, h in self.stones:
            rect = pygame.Rect(0, 0, w, h)
            rect.center = (x, y)
            pygame.draw.ellipse(self.image, shade, rect)
            pygame.draw.ellipse(self.image, lit, (rect.x + s(1), rect.y, rect.w - s(3), rect.h * 0.55))
            pygame.draw.ellipse(self.image, dark, rect, 1)
        self.painted_palette = palette

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.image, (0, 0))


class PrayerFlags(Layer):
    # Strings of prayer flags running from the top of the pole on the cairn, down to the
    # ledge and away off the side, in the five colors (blue, white, red, green, yellow).
    # Each flag hangs from the string and flaps in the wind, its free edge rippling
    #
    # Palette colors it uses:
    #   "flags"         the five colors, in order
    #   "haze"          what they fade toward behind the game's text
    #   "string"        the string they hang from

    FLAG = (10, 12)                 # width and height, at the medium size

    def __init__(self, scene, ledge):
        super().__init__(scene)
        self.time = 0
        top = ledge.pole_top
        self.strings = [
            {"from": top, "to": (s(100), ledge.top_at(s(100)) - s(3)), "sag": s(12), "count": 5},
            {"from": top, "to": (-s(12), top[1] + s(30)), "sag": s(8), "count": 3},
        ]
        for string in self.strings:
            string["flags"] = [{"phase": random.uniform(0, 6.3), "rate": random.uniform(0.8, 1.3)} for i in range(string["count"])]

    def point(self, string, t):
        (ax, ay), (bx, by) = string["from"], string["to"]
        return (ax + (bx - ax) * t, ay + (by - ay) * t + string["sag"] * math.sin(math.pi * t))

    def update(self, dt):
        self.time += dt

    def draw(self, surface, palette):
        colors = [pygame.Color(c) for c in palette["flags"]]
        string_color = pygame.Color(palette["string"])
        haze = pygame.Color(palette["haze"])
        wind = self.scene.weather["wind"] + self.scene.weather.get("gust", 0)
        w, h = s(self.FLAG[0]), s(self.FLAG[1])
        for string in self.strings:
            line = [self.point(string, i / 16) for i in range(17)]
            pygame.draw.lines(surface, string_color, False, line, 1)
            n = string["count"]
            for i, flag in enumerate(string["flags"]):
                t0 = (i + 0.5) / (n + 0.5)
                t1 = t0 + (w / max(1, abs(string["to"][0] - string["from"][0]))) * 0.9
                a, b = self.point(string, t0), self.point(string, t1)
                if a[0] > b[0]:
                    a, b = b, a
                # The wind (blowing to the left, like the mist) lifts the flag's free edge and ripples it
                beat = math.sin(self.time / 160 * flag["rate"] + flag["phase"])
                lean = min(1.2, 0.25 + 0.35 * wind) + 0.12 * beat
                ripple = math.sin(self.time / 90 * flag["rate"] + flag["phase"] * 2) * s(1.5) * wind
                drop_x, drop_y = -math.sin(lean) * h, math.cos(lean) * h
                points = [a, b, (b[0] + drop_x, b[1] + drop_y), ((a[0] + b[0]) / 2 + drop_x + ripple, (a[1] + b[1]) / 2 + drop_y * 0.95),
                          (a[0] + drop_x * 0.95, a[1] + drop_y)]
                color = colors[(i + (0 if string["count"] > 4 else 2)) % 5]
                color = haze.lerp(color, self.scene.keep(a[0], 0.6))
                pygame.draw.polygon(surface, color, points)
                # A little printed square in the middle
                mx = (a[0] + b[0]) / 2 + drop_x * 0.5 + ripple * 0.5
                my = (a[1] + b[1]) / 2 + drop_y * 0.5
                pygame.draw.rect(surface, color.lerp((0, 0, 0), 0.25), (mx - s(2), my - s(2), max(1, s(4)), max(1, s(4))), 1)
