# A tropical beach, looking out to sea (the seaside theme): the open sea to the horizon with a little palm cay
# and a far headland with a lighthouse, turquoise shallows inside a line of surf on the
# outer reef, and waves rolling in to break and wash up the sand, leaving it wet and
# shining as they draw back. A leaning palm frames the left, rocks and beach grass the right

import math

import random

import pygame

from partials.config import WIDTH, HEIGHT, CENTER_X, s
from partials.backgrounds.base import Layer


SHORE = 452                         # where the sea meets the sand when the water is still, pixels at the medium size
REEF = 236                          # the line of surf on the outer reef


def shore_y(x):
    # Where the still water meets the sand at x: the beach curves gently, a shallow cove
    return s(SHORE) + math.sin(x / s(95) + 0.8) * s(14) + math.sin(x / s(37)) * s(4)


class Sea(Layer):
    # The sea from the horizon to the shore, and the beach below it: deep blue far out,
    # turquoise over the shallows, a faint band of surf along the outer reef, then wet sand
    # darkening the shore and dry sand down to the bottom of the window. Far off: a little
    # cay with palms on the right, a headland with a lighthouse on the left. Painted once,
    # apart from the surf line, which shimmers
    #
    # Palette colors it uses:
    #   "sea_far", "sea_mid", "shallows"        the water out at the horizon, halfway, close in
    #   "surf"                                  the surf on the reef (and foam)
    #   "sand_wet", "sand_dry", "sand_near"     the beach
    #   "far_land", "far_palm"                  the headland and the cay (fading into the haze)
    #   "lighthouse", "lighthouse_band"

    def __init__(self, scene):
        super().__init__(scene)
        self.horizon = scene.view.horizon
        self.time = 0
        self.image = None
        self.painted_palette = None
        self.surf = [(random.uniform(0, WIDTH), random.uniform(0.5, 1.5), random.uniform(0, 6)) for i in range(16)]

    def sea_color(self, palette, y):
        far = pygame.Color(palette.get("sea_far", palette["bg"]))
        mid = pygame.Color(palette.get("sea_mid", palette["bg"]))
        near = pygame.Color(palette.get("shallows", palette["bg"]))
        reef = s(REEF)
        if y < reef:
            return far.lerp(mid, max(0.0, min(1.0, (y - self.horizon) / (reef - self.horizon))) ** 0.8)
        return mid.lerp(near, max(0.0, min(1.0, (y - reef) / (s(SHORE) - reef))) ** 0.7)

    def sand_color(self, palette, y, shore=None):
        wet = pygame.Color(palette.get("sand_wet", palette["muted"]))
        dry = pygame.Color(palette.get("sand_dry", palette["bg"]))
        near = pygame.Color(palette.get("sand_near", palette.get("sand_dry", palette["bg"])))
        shore = s(SHORE) if shore is None else shore
        if y < shore + s(28):
            return wet
        if y < shore + s(46):
            return wet.lerp(dry, max(0.0, min(1.0, (y - shore - s(28)) / s(18))))
        return dry.lerp(near, max(0.0, min(1.0, (y - shore - s(46)) / (HEIGHT - shore - s(46)))))

    def paint(self, palette):
        top = int(self.horizon - s(60))                    # a little above the horizon, for the far land
        image = pygame.Surface((WIDTH, HEIGHT - top), pygame.SRCALPHA)
        shore = s(SHORE)
        for y in range(int(self.horizon), HEIGHT):
            pygame.draw.line(image, self.sea_color(palette, y), (0, y - top), (WIDTH, y - top))
        # The beach, following the curve of the shore
        for x in range(0, WIDTH, 2):
            edge = shore_y(x)
            for y in range(int(edge), HEIGHT, 2):
                image.fill(self.sand_color(palette, y, edge), (x, y - top, 2, 2))
        # The shallows: a lighter, greener band where the sand shows through, and soft bands of colour further out
        near = pygame.Color(palette.get("shallows", palette["bg"]))
        for k in range(6):
            y = s(REEF) + (shore - s(REEF)) * (k + 0.5) / 6
            band = [(x, y + math.sin(x / s(40) + k) * s(3)) for x in range(-4, WIDTH + 8, 8)]
            pygame.draw.lines(image, self.sea_color(palette, y).lerp(near.lerp((255, 255, 255), 0.15), 0.25), False,
                              [(x, yy - top) for x, yy in band], 1)
        # The far headland with its lighthouse, and the little cay
        land = pygame.Color(palette.get("far_land", palette["muted"]))
        hz = self.horizon
        headland = [(-4, hz + 2), (-4, hz - s(16)), (s(18), hz - s(22)), (s(42), hz - s(18)), (s(70), hz - s(8)), (s(96), hz - s(2)), (s(110), hz + 2)]
        pygame.draw.polygon(image, land, [(x, y - top + 1) for x, y in headland])
        self.lamp = (s(28), hz - s(40))
        tower = pygame.Color(palette.get("lighthouse", palette["text"]))
        band = pygame.Color(palette.get("lighthouse_band", palette["accent"]))
        image_top = top
        self.tower_rect = pygame.Rect(s(24), hz - s(38), s(8), s(18))
        palm = pygame.Color(palette.get("far_palm", palette["muted"]))
        cay = [(WIDTH - s(120), hz + 1), (WIDTH - s(108), hz - s(3)), (WIDTH - s(80), hz - s(4)), (WIDTH - s(62), hz + 1)]
        pygame.draw.polygon(image, land, [(x, y - top + 1) for x, y in cay])
        for k, (px, h, lean) in enumerate(((WIDTH - s(100), 14, -0.3), (WIDTH - s(88), 18, 0.2), (WIDTH - s(76), 12, 0.35))):
            crown = (px + lean * s(h), hz - s(3) - s(h))
            pygame.draw.line(image, palm, (px, hz - s(3) - top + 1), (crown[0], crown[1] - top + 1), max(1, s(1.4)))
            for a in (-2.6, -2.0, -1.2, -0.5, 0.1):
                pygame.draw.line(image, palm, (crown[0], crown[1] - top + 1),
                                 (crown[0] + math.cos(a) * s(6), crown[1] + math.sin(a) * s(3) + s(2) - top + 1), 1)
        self.image = image
        self.top = top
        self.painted_palette = palette

    def color_at(self, palette, y):
        if y < self.horizon:
            return None
        return self.sea_color(palette, y) if y < s(SHORE) else self.sand_color(palette, y)

    def color_under(self, palette, x, y):
        # The colour at a point, following the curved shore
        edge = shore_y(x)
        return self.sea_color(palette, y) if y < edge else self.sand_color(palette, y, edge)

    def update(self, dt):
        self.time += dt

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.image, (0, self.top))
        # The lighthouse on its headland
        tower = pygame.Color(palette.get("lighthouse", palette["text"]))
        band = pygame.Color(palette.get("lighthouse_band", palette["accent"]))
        r = self.tower_rect
        pygame.draw.polygon(surface, tower, [(r.left, r.bottom), (r.left + s(1.5), r.top), (r.right - s(1.5), r.top), (r.right, r.bottom)])
        for k in (0.35, 0.7):
            y = r.top + r.height * k
            pygame.draw.line(surface, band, (r.left + s(1), y), (r.right - s(1), y), max(1, s(2)))
        pygame.draw.rect(surface, band, (r.left + s(1), r.top - s(4), r.width - s(2), s(4)))
        # Surf breaking along the outer reef: broken white streaks that come and go
        surf = pygame.Color(palette.get("surf", palette["text"]))
        y0 = s(REEF)
        for x, size, phase in self.surf:
            show = max(0.0, math.sin(self.time / 1300 + phase))
            if show < 0.1:
                continue
            behind = self.sea_color(palette, y0)
            length = s(14) * size * show
            pygame.draw.line(surface, behind.lerp(surf, 0.8 * show * self.scene.keep(x, 0.5)), (x - length, y0 + math.sin(phase) * s(2)),
                             (x + length, y0 + math.sin(phase) * s(2)), max(1, s(2)))


class Waves(Layer):
    # The waves on the beach, one after another: each swell rolls in and steepens, breaks
    # into a line of foam just off the shore, then runs up the sand as a thin sheet with a
    # lacy foam edge, slows, and draws back down, leaving a band of wet, shining sand behind
    # that slowly dulls. Every few waves a bigger one runs further up. Others ask reach(x)
    # for how far up the beach the water is right now (crabs and birds keep clear of it)
    #
    # Palette colors it uses:
    #   "shallows", "surf"              the sheet of water and the foam
    #   "sand_shine"                    the wet shine the water leaves behind

    PERIOD = (6500, 9000)           # milliseconds from one wave to the next
    RUN = (34, 62)                  # how far up the sand a wave runs, pixels at the medium size
    BIG = 0.2                       # chance a wave is a big one
    STEP = 4                        # pixels between points along the waterline

    def __init__(self, scene, sea):
        super().__init__(scene)
        self.sea = sea
        self.columns = list(range(-self.STEP, WIDTH + self.STEP * 2, self.STEP))
        self.wet = [0.0] * len(self.columns)                # how far up each column is still wet
        self.shine = [0.0] * len(self.columns)              # how fresh the wet is (1 just left, fading to 0)
        self.time = 0
        self.wave = None
        self.crest = self.edge = None
        self.new_wave()

    def new_wave(self):
        big = random.random() < self.BIG
        run = s(random.uniform(*self.RUN)) * (1.35 if big else 1)
        self.wave = {"age": 0.0, "period": random.uniform(*self.PERIOD), "run": run,
                     "phases": [random.uniform(0, 6) for k in range(3)], "big": big}

    def shape(self, x):
        # How the waterline wanders along the beach for this wave: 0.7 to 1.2 of its run
        a, b, c = self.wave["phases"]
        return 1 + 0.15 * math.sin(x / s(53) + a) + 0.08 * math.sin(x / s(19) + b) + 0.05 * math.sin(x / s(7) + c)

    def progress(self):
        # How far up the run the water is: rolling in and breaking (negative: still offshore),
        # running up, then drawing back
        t = self.wave["age"] / self.wave["period"]
        if t < 0.3:
            return t / 0.3 - 1                              # -1 far out .. 0 at the shore
        if t < 0.55:
            u = (t - 0.3) / 0.25
            return math.sin(u * math.pi / 2)                # rushing up, slowing
        u = (t - 0.55) / 0.45
        return 1 - u * u * (3 - 2 * u)                      # drawing back

    def reach(self, x):
        p = self.progress()
        return shore_y(x) + max(0.0, p) * self.wave["run"] * self.shape(x)

    def update(self, dt):
        self.time += dt
        self.wave["age"] += dt
        if self.wave["age"] > self.wave["period"]:
            self.new_wave()
        p = self.progress()
        for i, x in enumerate(self.columns):
            edge = shore_y(x) + max(0.0, p) * self.wave["run"] * self.shape(x)
            if edge >= self.wet[i] - 1 and p > 0:
                self.wet[i] = edge
                self.shine[i] = 1.0
            else:
                self.shine[i] = max(0.0, self.shine[i] - dt / 4500)
                if self.shine[i] <= 0:
                    self.wet[i] = shore_y(x)

    def draw(self, surface, palette):
        shallows = pygame.Color(palette.get("shallows", palette["bg"]))
        foam = pygame.Color(palette.get("surf", palette["text"]))
        shine = pygame.Color(palette.get("sand_shine", palette["text"]))
        shores = [shore_y(x) for x in self.columns]
        # The wet shine left by the last wave, fading
        for i in range(len(self.columns) - 1):
            shore = shores[i]
            if self.wet[i] <= shore + 1 or self.shine[i] <= 0.02:
                continue
            x0, x1 = self.columns[i], self.columns[i + 1]
            for y in range(int(shore), int(self.wet[i]), 6):
                sand = self.sea.sand_color(palette, y, shore)
                fresh = self.shine[i] * (1 - (y - shore) / max(1, self.wet[i] - shore)) ** 0.5
                surface.fill(sand.lerp(shine, 0.55 * fresh), (x0, y, x1 - x0, min(6, int(self.wet[i]) - y)))
        p = self.progress()
        quiet = [self.scene.keep(x, 0.6) for x in self.columns]
        self.crest, self.edge = None, None                  # for the glow at night (see GlowingSurf)
        if p < 0:
            # The swell rolling in: a line steepening and whitening as it nears the shore
            strength = (1 + p) ** 2
            points = [(x, shores[i] + p * s(70) + math.sin(x / s(30) + self.time / 700) * s(2)) for i, x in enumerate(self.columns)]
            behind = self.sea.sea_color(palette, points[len(points) // 2][1])
            pygame.draw.lines(surface, behind.lerp(foam, 0.75 * strength), False, points, max(1, int(s(1) + s(2) * strength)))
            if strength > 0.55:
                self.crest = (points, strength)
                # It breaks: foam tumbling along the crest
                for i in range(0, len(points), 3):
                    x, yy = points[i]
                    r = s(2.2) * strength * (0.6 + 0.4 * math.sin(i * 1.7 + self.time / 120))
                    pygame.draw.circle(surface, behind.lerp(foam, 0.85 * quiet[i]), (x, yy + s(2)), r)
            return
        # The sheet of water running up the sand, and its foam edge
        edge = [(x, shores[i] + p * self.wave["run"] * self.shape(x)) for i, x in enumerate(self.columns)]
        top = int(min(shores) - s(4))
        sheet = pygame.Surface((WIDTH, int(max(y for x, y in edge) - top) + s(6)), pygame.SRCALPHA)
        alpha = int(255 * 0.75)
        pygame.draw.polygon(sheet, (shallows.r, shallows.g, shallows.b, alpha),
                            [(self.columns[0], 0)] + [(x, y - top) for x, y in edge] + [(self.columns[-1], 0)])
        # Only over the sand: the water itself is already the sea's colour
        cut = [(self.columns[0], 0)] + [(x, shores[i] - top - s(2)) for i, x in enumerate(self.columns)] + [(self.columns[-1], 0)]
        pygame.draw.polygon(sheet, (0, 0, 0, 0), cut)
        surface.blit(sheet, (0, top))
        backwash = self.wave["age"] / self.wave["period"] > 0.55
        self.edge = (edge, 1 - p if backwash else 1.0)
        lace = foam if not backwash else foam.lerp(shallows, 0.4)
        pygame.draw.lines(surface, lace, False, edge, max(1, s(2)))
        for i in range(0, len(edge), 2):
            x, y = edge[i]
            if (i * 7 + int(self.time / 200)) % 5 == 0:
                continue
            pygame.draw.circle(surface, lace, (x, y - s(3) - (i % 3) * s(1)), max(1, s(1.4)))
        # A softer line of foam lingering just off the shore
        for i in range(0, len(self.columns), 2):
            x = self.columns[i]
            y = shores[i] - s(5) + math.sin(x / s(15) + self.time / 900) * s(1.5)
            pygame.draw.circle(surface, self.sea.sea_color(palette, y).lerp(foam, 0.5 * (1 - p) * quiet[i]), (x, y), max(1, s(1.2)))


class BeachPalm(Layer):
    # A tall palm leaning in from the bottom left corner, its trunk curving up the edge of the
    # window and its crown of long fronds spread overhead at the left, tossing in the sea
    # breeze. Its shadow lies across the sand
    #
    # Palette colors it uses:
    #   "palm_trunk", "palm_trunk_dark", "palm_frond", "palm_frond_dark", "coconut"

    FRONDS = 11

    def __init__(self, scene):
        super().__init__(scene)
        self.time = 0
        self.base = (s(-14), HEIGHT + s(10))
        self.crown = (s(52), s(160))
        self.fronds = [(-math.pi + math.pi * 1.25 * f / (self.FRONDS - 1) - 0.1 + random.uniform(-0.1, 0.1), random.uniform(0.85, 1.15),
                        random.uniform(0, 6)) for f in range(self.FRONDS)]

    def update(self, dt):
        self.time += dt

    def draw(self, surface, palette):
        bark = pygame.Color(palette.get("palm_trunk", palette["muted"]))
        bark_dark = pygame.Color(palette.get("palm_trunk_dark", palette["muted"]))
        frond = pygame.Color(palette.get("palm_frond", palette["muted"]))
        frond_dark = pygame.Color(palette.get("palm_frond_dark", palette["muted"]))
        wind = self.scene.weather.get("wind", 1)
        sway = math.sin(self.time / 1600) * 0.06 * wind
        (bx, by), (cx, cy) = self.base, self.crown
        cx += sway * s(40)
        # The trunk: a long curve, thick at the bottom, ringed
        points = []
        for k in range(13):
            t = k / 12
            points.append((bx + (cx - bx) * t + math.sin(t * math.pi) * s(30), by + (cy - by) * t))
        for k in range(12):
            width = max(4, int(s(20) * (1 - k / 16)))
            pygame.draw.line(surface, bark, points[k], points[k + 1], width)
            pygame.draw.line(surface, bark_dark, (points[k][0] - width / 2, points[k][1]), (points[k][0] + width / 2, points[k][1] + s(2)), 1)
        # Fronds: arching out from the crown and drooping, leaflets along them
        for angle, length, phase in sorted(self.fronds, key=lambda f: math.sin(f[0])):
            toss = math.sin(self.time / 900 + phase) * 0.06 * wind + sway
            reach = s(96) * length
            color = frond_dark if math.sin(angle) < -0.5 else frond
            spine = []
            for n in range(9):
                t = n / 8
                a = angle + toss + t * 0.6 * (1 if math.cos(angle) > 0 else -1) * 0.5
                spine.append((cx + math.cos(a) * reach * t, cy + math.sin(a) * reach * t * 0.6 + reach * 0.45 * t * t))
            pygame.draw.lines(surface, color, False, spine, max(2, s(3)))
            for n in range(1, 8):
                px, py = spine[n]
                leaf = s(16) * (1 - n / 9) * length
                pygame.draw.line(surface, color, (px, py), (px - leaf * 0.35, py + leaf), max(1, s(2.2)))
                pygame.draw.line(surface, color, (px, py), (px + leaf * 0.35, py + leaf * 0.85), max(1, s(2.2)))
        coconut = pygame.Color(palette.get("coconut", palette["muted"]))
        for k in range(3):
            pygame.draw.circle(surface, coconut, (cx + (k - 1) * s(5), cy + s(5) + (k % 2) * s(2)), s(4))


class BeachFront(Layer):
    # The near beach on the right: a few dark rocks with a little seaweed, tufts of beach
    # grass bending in the breeze, and shells and a starfish on the dry sand
    #
    # Palette colors it uses:
    #   "rock", "rock_dark", "beach_grass", "shell", "starfish", "seaweed"

    def __init__(self, scene):
        super().__init__(scene)
        self.time = 0
        rng = random.Random(8)
        self.rocks = [(WIDTH - s(rng.uniform(10, 70)), HEIGHT - s(rng.uniform(20, 70)), s(rng.uniform(12, 24))) for k in range(4)]
        self.rocks.sort(key=lambda r: r[1])
        self.tufts = [(WIDTH - s(rng.uniform(0, 110)), HEIGHT - s(rng.uniform(4, 100)), rng.random()) for k in range(9)]
        self.shells = [(rng.uniform(s(110), WIDTH - s(110)), rng.uniform(s(SHORE + 60), HEIGHT - s(10)), rng.random()) for k in range(6)]
        self.image = None
        self.painted_palette = None

    def paint(self, palette):
        image = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        rock = pygame.Color(palette.get("rock", palette["muted"]))
        dark = pygame.Color(palette.get("rock_dark", palette["muted"]))
        weed = pygame.Color(palette.get("seaweed", palette["muted"]))
        shell = pygame.Color(palette.get("shell", palette["text"]))
        star = pygame.Color(palette.get("starfish", palette["accent"]))
        for x, y, r in self.rocks:
            pygame.draw.ellipse(image, (0, 0, 0, 50), (x - r * 1.3, y - r * 0.15, r * 2.6, r * 0.5))
            points = [(x + math.cos(a) * r * (1.2 if math.cos(a) > 0 else 1.0), y - math.sin(a) * r * 0.8) for a in [math.pi * k / 8 for k in range(9)]]
            pygame.draw.polygon(image, rock, points)
            pygame.draw.polygon(image, dark, [points[4], points[5], points[6], points[7], points[8], (x - r * 0.2, y)])
            pygame.draw.lines(image, dark, False, points, 1)
            for k in range(3):
                pygame.draw.line(image, weed, (x - r * 0.6 + k * r * 0.5, y - r * 0.1), (x - r * 0.5 + k * r * 0.5, y + r * 0.15), max(1, s(2)))
        for x, y, pick in self.shells:
            if pick < 0.2:
                points = []
                for k in range(10):
                    a = -math.pi / 2 + k * math.pi / 5
                    rr = s(8) if k % 2 == 0 else s(3)
                    points.append((x + math.cos(a) * rr, y + math.sin(a) * rr * 0.6))
                pygame.draw.polygon(image, star, points)
            else:
                pygame.draw.ellipse(image, shell, (x - s(3.5), y - s(2.5), s(7), s(5)))
                for k in (-1, 0, 1):
                    pygame.draw.line(image, shell.lerp(dark, 0.4), (x, y + s(2)), (x + k * s(2.5), y - s(2)), 1)
        self.image = image
        self.painted_palette = palette

    def update(self, dt):
        self.time += dt

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.image, (0, 0))
        grass = pygame.Color(palette.get("beach_grass", palette["muted"]))
        wind = self.scene.weather.get("wind", 1)
        for x, y, pick in self.tufts:
            for b in range(6):
                lean = (b - 2.5) * 0.25 - 0.4 * wind - math.sin(self.time / 700 + pick * 6 + b * 0.3) * 0.15 * wind
                h = s(22) * (0.6 + 0.4 * ((b * 0.37 + pick) % 1))
                mid = (x + b - 3 + lean * h * 0.3, y - h * 0.5)
                tip = (x + b - 3 + lean * h * 0.8, y - h)
                pygame.draw.lines(surface, grass if b % 2 else grass.lerp((0, 0, 0), 0.2), False, [(x + b - 3, y), mid, tip], max(1, s(1.5)))
