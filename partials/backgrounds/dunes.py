# A desert seen from the top of a dune: pyramids on the far horizon, ranks of dunes rolling
# away with sharp crests (one face lit, one in shadow), sand rippled by the wind in front,
# and an oasis in a dip between the dunes: palms around a small still pool

import math

import random

import pygame

from partials.config import WIDTH, HEIGHT, CENTER_X, s
from partials.backgrounds.base import Layer


def hazed(palette, key, fallback, haze):
    # A palette color, faded toward the far sky by haze (things far off pale into it)
    color = pygame.Color(palette.get(key, fallback))
    return color.lerp(pygame.Color(palette.get("sky_low", palette["bg"])), max(0.0, min(1.0, haze)))


class Pyramids(Layer):
    # Two or three pyramids on the horizon at the left of the window, pale with distance:
    # each a lit face and a shaded face (the light comes from the right, where the sun or
    # moon is), with faint lines of stone courses. Painted once
    #
    # Palette colors it uses:
    #   "pyramid_lit", "pyramid_shadow"     its two faces
    #   "sky_low"                           what distance fades them toward

    PYRAMIDS = ((52, 64, 40, 0.3), (18, 40, 25, 0.42), (102, 30, 19, 0.5))   # (middle x, base width, height, haze), back ones last
    COURSES = 6

    def __init__(self, scene):
        super().__init__(scene)
        self.horizon = scene.view.horizon
        self.image = None
        self.painted_palette = None

    def paint(self, palette):
        image = pygame.Surface((WIDTH, int(self.horizon) + 4), pygame.SRCALPHA)
        base = self.horizon + s(3)
        for x, width, height, haze in sorted(self.PYRAMIDS, key=lambda p: -p[3]):
            x, half, top = s(x), s(width) / 2, base - s(height)
            lit = hazed(palette, "pyramid_lit", palette["muted"], haze)
            shadow = hazed(palette, "pyramid_shadow", palette["muted"], haze)
            # Seen a little from the right: the ridge running down toward us sits right of middle
            ridge = x + half * 0.3
            pygame.draw.polygon(image, shadow, [(x - half, base), (x, top), (ridge, base)])
            pygame.draw.polygon(image, lit, [(ridge, base), (x, top), (x + half, base)])
            for k in range(1, self.COURSES):
                t = k / self.COURSES
                y = top + (base - top) * t
                pygame.draw.line(image, lit.lerp(shadow, 0.35), (x + (ridge - x) * t, y), (x + half * t, y), 1)
                pygame.draw.line(image, shadow.lerp(lit, 0.25), (x - half * t, y), (x + (ridge - x) * t, y), 1)
        self.image = image
        self.painted_palette = palette

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.image, (0, 0))


class Dunes(Layer):
    # Ranks of dunes from the horizon down to the sand in front of us, each rank nearer,
    # bigger and less hazy than the last: a long rolling ridgeline rising to sharp peaks
    # and dipping into soft hollows, and two big dunes rising into the bottom corners in
    # front of us. The sun or moon is off to the right, so each peak's right side is lit
    # and a wedge of shadow runs down its left side from the peak; both fade into the plain
    # sand at the dunes' feet. The near sand is rippled by the wind. The dunes keep low in
    # the middle of the window. Painted once. Others ask crests() for the peaks (the wind
    # lifts sand off them)
    #
    # Palette colors it uses:
    #   "dune_lit", "dune_shadow"           the sunlit faces and the shaded ones
    #   "sand_far", "sand_near"             the sand far away and up close
    #   "sand_ripple"                       the wind ripples (falls back to a darker sand)
    #   "sky_low"                           what distance fades the dunes toward

    RANKS = ((0.93, 14, 0.5, 4.5), (0.8, 26, 0.35, 3.6), (0.62, 42, 0.2, 3.0), (0.4, 62, 0.08, 2.4), (0.15, 96, 0.0, 1.8), (0.04, 70, 0.0, 1.5))   # (depth, height, haze, peaks across the window)
    CORNERS = 230                   # how high the dunes in the bottom corners rise
    MIDDLE = 0.25                   # how much of their height dunes keep in the middle of the window
    SHARP = 0.6                     # how sharp the peaks are (1 = a plain point, higher = more pinched)
    SLANT = 0.12                    # how far right the shadow's edge leans by the dune's foot, as a share of the dune spacing
    RIPPLES = 70

    def __init__(self, scene):
        super().__init__(scene)
        view = scene.view
        self.horizon = view.horizon
        self.ranks = []
        for depth, height, haze, peaks in self.RANKS:
            self.ranks.append({"base": view.height_at(depth), "h": s(height), "haze": haze,
                               "length": WIDTH / peaks, "phase": random.uniform(0, math.pi),
                               "swell": random.uniform(0, 2 * math.pi), "middle": self.MIDDLE})
        # The big dunes in the bottom corners: one rank, one peak at each side, nothing in the middle
        self.ranks.append({"base": HEIGHT + s(40), "h": s(self.CORNERS), "haze": 0.0, "length": WIDTH * 0.92,
                           "phase": math.pi * 0.06, "swell": 0.0, "middle": 0.0, "corners": True})
        self.ripples = []
        for i in range(self.RIPPLES):
            y = view.random_y(0.15)
            if y < self.ranks[2]["base"]:
                continue
            self.ripples.append((random.uniform(-s(40), WIDTH), y, s(random.uniform(40, 120)) * view.scale(y), random.uniform(0, 2 * math.pi)))
        self.image = None
        self.painted_palette = None

    def crest(self, rank, x):
        # How high the rank's ridgeline stands at x: sharp peaks where the wave crosses zero
        wave = abs(math.sin(math.pi * x / rank["length"] + rank["phase"]))
        shape = (1 - wave) ** self.SHARP
        side = min(1, abs(x - CENTER_X) / CENTER_X)
        height = rank["h"] * (0.75 + 0.25 * math.sin(x / rank["length"] * 0.7 + rank["swell"]))
        return height * shape * (rank["middle"] + (1 - rank["middle"]) * side ** 1.3)

    def peaks(self, rank):
        # The x of every peak in the rank (where the wave crosses zero)
        k0 = math.ceil((rank["phase"] - math.pi * s(40) / rank["length"]) / math.pi)
        found = []
        k = -2
        while True:
            x = (k * math.pi - rank["phase"]) * rank["length"] / math.pi
            if x > WIDTH + s(40):
                break
            if x > -s(40):
                found.append(x)
            k += 1
        return found

    def crests(self):
        # (x, y, size) for each peak worth lifting sand off
        found = []
        for rank in self.ranks:
            for x in self.peaks(rank):
                h = self.crest(rank, x)
                if h > s(5) and 0 <= x <= WIDTH:
                    found.append((x, rank["base"] - h, h / s(40)))
        return found

    def sand_color(self, palette, y):
        far = pygame.Color(palette.get("sand_far", palette["bg"]))
        near = pygame.Color(palette.get("sand_near", palette["bg"]))
        return far.lerp(near, self.scene.view.nearness(y))

    def paint(self, palette):
        top = int(self.horizon - s(60))
        image = pygame.Surface((WIDTH, HEIGHT - top), pygame.SRCALPHA)
        for y in range(int(self.horizon), HEIGHT):
            pygame.draw.line(image, self.sand_color(palette, y), (0, y - top), (WIDTH, y - top))
        for rank in self.ranks:
            haze = rank["haze"]
            lit = hazed(palette, "dune_lit", palette["muted"], haze)
            shadow = hazed(palette, "dune_shadow", palette["muted"], haze)
            base = rank["base"]
            peaks = self.peaks(rank)
            for x in range(WIDTH):
                h = self.crest(rank, x)
                if h < 1:
                    continue
                crest = base - h
                # The nearest peak decides the shading: its left side is in shade, divided from
                # its lit right side by a line running from the peak down and a little to the right
                owner = min(peaks, key=lambda p: abs(p - x)) if peaks else x
                ph = max(self.crest(rank, owner), 1)
                away = (owner - x) / (rank["length"] / 2)            # 0 at the peak, 1 in the hollow to its left
                step = max(2, int(h / 16))
                y = crest
                while y < min(base, HEIGHT):
                    rise = max(0.0, min(1.0, (base - y) / max(h, 1)))
                    ground = self.sand_color(palette, y)
                    down = max(0.0, min(1.0, (y - (base - ph)) / ph))
                    dividing = owner + rank["length"] * self.SLANT * down
                    shade = 0.0
                    if x < dividing:
                        shade = 1.0 if away < 0.6 else max(0.0, 1 - (away - 0.6) / 0.4)
                    lit_color = ground.lerp(lit, rise ** 1.2)
                    shade_color = ground.lerp(shadow, min(1.0, 0.2 + rise) ** 0.6)
                    pygame.draw.line(image, lit_color.lerp(shade_color, shade), (x, y - top), (x, min(y + step, base) - top))
                    y += step
            # A thin bright edge along the crest, strongest at the peaks
            for x in peaks:
                h = self.crest(rank, x)
                if h < s(4):
                    continue
                points = [(px, base - self.crest(rank, px) - top) for px in range(int(x), int(x + rank["length"] * 0.18), 2)]
                if len(points) > 1:
                    pygame.draw.lines(image, lit.lerp((255, 255, 255), 0.3 * (1 - haze)), False, points, 1)
        ripple = palette.get("sand_ripple")
        for x0, y, length, phase in self.ripples:
            base = self.sand_color(palette, y)
            dark = pygame.Color(ripple) if ripple else base.lerp((0, 0, 0), 0.12)
            points = [(x0 + length * t, y + math.sin(phase + t * 5) * s(2) * self.scene.view.scale(y) - top) for t in [k / 8 for k in range(9)]]
            pygame.draw.lines(image, base.lerp(dark, 0.7), False, points, 1)
            pygame.draw.lines(image, base.lerp((255, 255, 255), 0.15), False, [(px, py - 1) for px, py in points], 1)
        self.image = image
        self.top = top
        self.painted_palette = palette

    def color_at(self, palette, y):
        if y < self.horizon:
            return None
        return self.sand_color(palette, y)

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.image, (0, self.top))


class DesertRocks(Layer):
    # A few weathered rocks half sunk in the sand in the lower corners: blocky, with a lit
    # top and right side, a shaded left side, and a shadow pooling out to the left. Painted once
    #
    # Palette colors it uses:
    #   "rock", "rock_light", "rock_dark"

    GROUPS = ((0.1, 0.78, 3), (0.86, 0.7, 2), (0.24, 0.93, 2), (0.93, 0.95, 3))     # (share across, share down, rocks)
    SIZE = (9, 20)

    def __init__(self, scene):
        super().__init__(scene)
        self.rocks = []
        for u, v, count in self.GROUPS:
            for k in range(count):
                x = WIDTH * u + random.uniform(-s(22), s(22))
                y = HEIGHT * v + random.uniform(-s(8), s(8))
                size = s(random.uniform(*self.SIZE)) * scene.view.scale(y)
                points = []
                corners = random.randint(5, 7)
                for c in range(corners):
                    a = math.pi + math.pi * c / (corners - 1)          # the upper half: the part above the sand
                    r = random.uniform(0.75, 1.05)
                    points.append((math.cos(a) * r, math.sin(a) * r * random.uniform(0.7, 1.1)))
                self.rocks.append((x, y, size, points))
        self.rocks.sort(key=lambda r: r[1])
        self.image = None
        self.painted_palette = None

    def paint(self, palette):
        image = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        rock = pygame.Color(palette.get("rock", palette["muted"]))
        light = pygame.Color(palette.get("rock_light", palette["muted"]))
        dark = pygame.Color(palette.get("rock_dark", palette["muted"]))
        for x, y, size, points in self.rocks:
            placed = [(x + u * size, y + v * size) for u, v in points]
            shade = (0, 0, 0, int(255 * palette.get("shadow", 0.3) * 0.7))
            pygame.draw.ellipse(image, shade, (x - size * 1.6, y - size * 0.15, size * 2.2, size * 0.45))
            pygame.draw.polygon(image, rock, placed)
            pygame.draw.polygon(image, dark, [placed[0], placed[1], (x - size * 0.15, y - size * 0.35), (x - size * 0.1, y)])
            pygame.draw.polygon(image, light, [placed[len(placed) // 2], placed[-2], placed[-1], (x + size * 0.2, y - size * 0.35)])
            pygame.draw.lines(image, dark, False, placed, 1)
        self.image = image
        self.painted_palette = palette

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.image, (0, 0))


class Oasis(Layer):
    # A small still pool in a dip between the dunes, behind the middle of the game: damp
    # darker sand around it, a fringe of grass and reeds, and the sky mirrored in the water.
    # Painted once. Others ask inside(x, y) whether a point is on the water
    #
    # Palette colors it uses:
    #   "pool_far", "pool_near", "pool_edge"    the water, and the dark line at its edge
    #   "damp_sand"                             the wet sand around it
    #   "oasis_grass", "oasis_grass_dark"       the grass and reeds

    CENTER_Y = 338                  # pixels at the medium size: behind the entry box
    HALF = (118, 34)
    DAMP = (34, 14)                 # how far the damp sand reaches past the water
    TUFTS = 46

    def __init__(self, scene):
        super().__init__(scene)
        self.cx, self.cy = CENTER_X, s(self.CENTER_Y)
        self.wave = [(random.uniform(0.03, 0.06), k, random.uniform(0, 2 * math.pi)) for k in (2, 3)]
        self.tufts = []
        for i in range(self.TUFTS):
            angle = random.uniform(0, 2 * math.pi)
            # More grass at the sides and back than in front, where it would hide the water
            if math.sin(angle) > 0.4 and random.random() < 0.7:
                continue
            self.tufts.append((angle, random.uniform(1.0, 1.12), random.random()))
        self.tufts.sort(key=lambda t: math.sin(t[0]))
        self.image = None
        self.painted_palette = None

    def reach(self, angle):
        return 1 + sum(amount * math.sin(k * angle + phase) for amount, k, phase in self.wave)

    def point(self, angle, share):
        r = self.reach(angle) * share
        return (self.cx + math.cos(angle) * s(self.HALF[0]) * r, self.cy + math.sin(angle) * s(self.HALF[1]) * r)

    def outline(self, grow=(0, 0), count=60):
        points = []
        for i in range(count):
            angle = 2 * math.pi * i / count
            r = self.reach(angle)
            points.append((self.cx + math.cos(angle) * (s(self.HALF[0]) * r + grow[0]),
                           self.cy + math.sin(angle) * (s(self.HALF[1]) * r + grow[1])))
        return points

    def inside(self, x, y, margin=1.0):
        dx, dy = (x - self.cx) / s(self.HALF[0]), (y - self.cy) / s(self.HALF[1])
        return dx * dx + dy * dy < (self.reach(math.atan2(dy, dx)) * margin) ** 2

    def water_color(self, palette, y):
        far = pygame.Color(palette.get("pool_far", palette["bg"]))
        near = pygame.Color(palette.get("pool_near", palette["bg"]))
        y0, y1 = self.cy - s(self.HALF[1]) * 1.2, self.cy + s(self.HALF[1]) * 1.2
        return far.lerp(near, max(0, min(1, (y - y0) / (y1 - y0))))

    def paint(self, palette):
        image = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        damp = pygame.Color(palette.get("damp_sand", palette["muted"]))
        behind = self.scene.color_at(palette, self.cy)
        # Damp sand fading out from the water in a few steps
        for k in range(4, 0, -1):
            share = k / 4
            pygame.draw.polygon(image, behind.lerp(damp, 1 - share * 0.75),
                                self.outline((s(self.DAMP[0]) * share, s(self.DAMP[1]) * share)))
        # Water: the sky mirrored, pale far, deeper near
        water = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for y in range(int(self.cy - s(self.HALF[1]) * 1.3), int(self.cy + s(self.HALF[1]) * 1.3) + 1):
            pygame.draw.line(water, self.water_color(palette, y), (0, y), (WIDTH, y))
        mask = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(mask, (255, 255, 255, 255), self.outline())
        water.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        image.blit(water, (0, 0))
        pygame.draw.lines(image, pygame.Color(palette.get("pool_edge", palette["muted"])), True, self.outline(), max(1, s(2)))
        # Grass and reeds around it
        grass = pygame.Color(palette.get("oasis_grass", palette["muted"]))
        dark = pygame.Color(palette.get("oasis_grass_dark", palette["muted"]))
        for angle, share, pick in self.tufts:
            x, y = self.point(angle, share)
            k = self.scene.view.scale(y)
            reeds = pick < 0.3
            for b in range(4 if reeds else 5):
                lean = (b - 2) * (0.25 if reeds else 0.5)
                height = s(16 if reeds else 7) * k * (0.7 + 0.3 * ((b * 0.37 + pick) % 1))
                pygame.draw.line(image, dark if b % 2 else grass, (x + b - 2, y), (x + b - 2 + lean * s(3), y - height), max(1, s(1)))
            if reeds:
                pygame.draw.line(image, dark.lerp((90, 60, 30), 0.5), (x, y - s(16) * k * 0.95), (x, y - s(16) * k * 0.75), max(2, s(2.5)))
        self.image = image
        self.painted_palette = palette

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.image, (0, 0))


class Palms(Layer):
    # Date palms around the oasis: tall curving trunks ringed with old leaf scars, a crown of
    # long arching fronds with leaflets along them, and clusters of dates under the crown.
    # The fronds sway in the wind and toss in gusts. Kept to the sides of the pool, out of
    # the middle of the game
    #
    # Palette colors it uses:
    #   "palm_trunk", "palm_trunk_dark"     the trunk and its rings
    #   "palm_frond", "palm_frond_dark"     the fronds, lit and shaded
    #   "dates"                             the fruit

    FRONDS = 9
    SWAY = 0.08                     # radians the fronds toss at a normal breeze

    def __init__(self, scene, oasis):
        super().__init__(scene)
        self.time = 0
        cx, cy = oasis.cx, oasis.cy
        spots = ((-150, -8, 112, -0.2), (-186, 22, 82, 0.12), (158, -14, 122, 0.18), (128, 26, 72, -0.1), (196, 30, 64, 0.05))
        self.palms = []
        for dx, dy, height, lean in spots:
            x, y = cx + s(dx), cy + s(dy)
            k = scene.view.scale(y)
            self.palms.append({"x": x, "y": y, "h": s(height) * k, "lean": lean, "k": k, "phase": random.uniform(0, 2 * math.pi),
                               "fronds": [(2 * math.pi * f / self.FRONDS + random.uniform(-0.2, 0.2), random.uniform(0.8, 1.15))
                                          for f in range(self.FRONDS)]})
        self.palms.sort(key=lambda p: p["y"])

    def update(self, dt):
        self.time += dt

    def trunk(self, palm):
        # Points up the trunk, curving with its lean
        x, y, h, lean = palm["x"], palm["y"], palm["h"], palm["lean"]
        return [(x + lean * h * t * t, y - h * t) for t in [k / 8 for k in range(9)]]

    def draw(self, surface, palette):
        bark = pygame.Color(palette.get("palm_trunk", palette["muted"]))
        bark_dark = pygame.Color(palette.get("palm_trunk_dark", palette["muted"]))
        frond = pygame.Color(palette.get("palm_frond", palette["muted"]))
        frond_dark = pygame.Color(palette.get("palm_frond_dark", palette["muted"]))
        dates = pygame.Color(palette.get("dates", palette["accent"]))
        wind = self.scene.weather.get("wind", 1)
        gust = self.scene.weather.get("gust", 0)
        for palm in self.palms:
            k = palm["k"]
            points = self.trunk(palm)
            sway = math.sin(self.time / 1400 + palm["phase"]) * self.SWAY * wind + gust * 0.12 * math.sin(self.time / 180)
            # Shift the top of the trunk a little with the sway
            points = [(x + sway * palm["h"] * 0.15 * (k2 / 8) ** 2, y) for k2, (x, y) in enumerate(points)]
            width = max(2, int(s(5) * k))
            pygame.draw.lines(surface, bark, False, points, width)
            for k2 in range(1, 8):
                x, y = points[k2]
                pygame.draw.line(surface, bark_dark, (x - width / 2, y), (x + width / 2, y + 1), 1)
            crown = points[-1]
            # Fronds: back ones (pointing away) first, darker; front ones last, lighter
            fronds = sorted(palm["fronds"], key=lambda f: math.sin(f[0]))
            for angle, length in fronds:
                facing = math.sin(angle)                    # -1 pointing away, 1 toward us
                reach = s(46) * k * length
                spread = math.cos(angle) + sway * 2.5 - (wind - 1) * 0.25
                color = frond_dark.lerp(frond, 0.5 + 0.5 * facing)
                spine = []
                for t in [n / 6 for n in range(7)]:
                    spine.append((crown[0] + spread * reach * t,
                                  crown[1] - reach * 0.35 * math.sin(t * math.pi * 0.8) + reach * 0.55 * t * t + facing * reach * 0.12 * t))
                pygame.draw.lines(surface, color, False, spine, max(1, int(s(2) * k)))
                for n in range(1, 6):
                    px, py = spine[n]
                    leaf = s(9) * k * (1 - n / 7) * length
                    pygame.draw.line(surface, color, (px, py), (px - leaf * 0.3, py + leaf), max(1, int(s(1.4) * k)))
                    pygame.draw.line(surface, color, (px, py), (px + leaf * 0.3, py + leaf * 0.9), max(1, int(s(1.4) * k)))
            for n in range(5):
                a = n * 1.3
                pygame.draw.circle(surface, dates, (crown[0] + math.cos(a) * s(3) * k, crown[1] + s(4) * k + math.sin(a) * s(1.5) * k), max(1, s(1.8) * k))
            pygame.draw.circle(surface, frond_dark, crown, max(2, s(3) * k))


class SandWisps(Layer):
    # Sand blown off the dune crests: thin wisps streaming downwind from a crest and fading
    # out, more of them the windier it is (and lots in a gust). Plus a low veil of drifting
    # sand skimming along the near ground in faint streaks
    #
    # Palette colors it uses:
    #   "sand_wisp"                 the blown sand at its thickest (it fades into what's behind)

    WISPS = 26                      # at a normal breeze
    LIFE = (900, 2000)
    STREAKS = 14
    QUIET = 0.6

    def __init__(self, scene, dunes):
        super().__init__(scene)
        self.dunes = dunes
        self.crests = dunes.crests()
        self.wisps = []
        self.streaks = [self.new_streak(random.uniform(-s(60), WIDTH)) for i in range(self.STREAKS)]

    def new_wisp(self):
        x, y, scale = random.choice(self.crests)
        life = random.uniform(*self.LIFE)
        return {"x": x + random.uniform(-s(4), s(6)) * scale, "y": y + random.uniform(0, s(2)), "age": 0.0, "life": life,
                "scale": max(0.3, scale), "rise": random.uniform(0.1, 0.4)}

    def new_streak(self, x=None):
        view = self.scene.view
        y = view.random_y(0.1)
        y = max(y, view.horizon + (HEIGHT - view.horizon) * 0.45)
        return {"x": WIDTH + s(10) if x is None else x, "y": y, "length": s(random.uniform(30, 90)) * view.scale(y),
                "speed": random.uniform(0.7, 1.3), "phase": random.uniform(0, 2 * math.pi)}

    def update(self, dt):
        wind = self.scene.weather.get("wind", 1)
        seconds = dt / 1000
        want = int(self.WISPS * max(0.2, wind) ** 1.5)
        while len(self.wisps) < want:
            self.wisps.append(self.new_wisp())
        for wisp in self.wisps:
            wisp["age"] += dt
            wisp["x"] -= s(40) * wind * wisp["scale"] * seconds         # the wind blows to the left here
            wisp["y"] -= s(6) * wisp["rise"] * wisp["scale"] * seconds
        self.wisps = [w for w in self.wisps if w["age"] < w["life"]]
        for i, streak in enumerate(self.streaks):
            streak["x"] -= s(90) * wind * streak["speed"] * self.scene.view.scale(streak["y"]) * seconds
            if streak["x"] + streak["length"] < -s(20):
                self.streaks[i] = self.new_streak()

    def draw(self, surface, palette):
        color = pygame.Color(palette.get("sand_wisp", palette.get("dune_lit", palette["text"])))
        wind = self.scene.weather.get("wind", 1)
        for wisp in self.wisps:
            t = wisp["age"] / wisp["life"]
            strength = math.sin(math.pi * t) * 0.7 * self.scene.keep(wisp["x"], self.QUIET)
            if strength < 0.05:
                continue
            behind = self.scene.color_at(palette, wisp["y"])
            length = s(10) * wisp["scale"] * (0.5 + t)
            pygame.draw.line(surface, behind.lerp(color, strength), (wisp["x"] + length, wisp["y"] + length * 0.15), (wisp["x"], wisp["y"]), 1)
        strength = min(0.6, 0.15 + 0.25 * wind)
        for streak in self.streaks:
            behind = self.scene.color_at(palette, streak["y"])
            shade = behind.lerp(color, strength * self.scene.keep(streak["x"], self.QUIET))
            y = streak["y"] + math.sin(streak["x"] / s(30) + streak["phase"]) * s(2)
            pygame.draw.line(surface, shade, (streak["x"], y), (streak["x"] + streak["length"], y - s(1)), 1)
