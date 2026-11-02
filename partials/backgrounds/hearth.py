# A cozy room, seen from a comfy chair: a papered wall with wood panelling below, a window
# on the left looking out at the sky, a fireplace on the right with a fire crackling in it
# and a clock ticking on the mantel, a wooden floor with a rug, and the arm of our chair
# and a steaming mug in front of us. The middle of the wall stays plain behind the text

import math

import random

import pygame

from partials.config import WIDTH, HEIGHT, CENTER_X, s
from partials.backgrounds.base import Layer
from partials.backgrounds.brook_light import glow_sprite


WAINSCOT_TOP = 392                  # where the wood panelling starts, pixels at the medium size
FLOOR_TOP = 466                     # where the wall meets the floor


class Room(Layer):
    # The room itself: wallpaper with a faint pattern of little sprigs, a picture rail near
    # the top, wood panelling along the bottom of the wall, a skirting board, and a floor of
    # boards running away from us (closer together toward the wall) with a rug on it.
    # Painted once
    #
    # Palette colors it uses:
    #   "wall", "wall_pattern"              the wallpaper and its pattern
    #   "wainscot", "wainscot_dark"         the panelling and its grooves and shadows
    #   "floor", "floor_line"               the boards and the gaps between them
    #   "rug", "rug_border", "rug_pattern"  the rug

    BOARDS = 15
    SPRIGS = (9, 13)                # columns and rows of the wallpaper pattern

    def __init__(self, scene):
        super().__init__(scene)
        self.image = None
        self.painted_palette = None

    def paint(self, palette):
        image = pygame.Surface((WIDTH, HEIGHT))
        wall = pygame.Color(palette.get("wall", palette["bg"]))
        pattern = pygame.Color(palette.get("wall_pattern", palette["bg"]))
        wood = pygame.Color(palette.get("wainscot", palette["muted"]))
        wood_dark = pygame.Color(palette.get("wainscot_dark", palette["muted"]))
        floor = pygame.Color(palette.get("floor", palette["muted"]))
        line = pygame.Color(palette.get("floor_line", palette["muted"]))
        top, ground = s(WAINSCOT_TOP), s(FLOOR_TOP)

        # Wallpaper: a slightly darker band up by the ceiling, and rows of little sprigs
        image.fill(wall)
        for y in range(0, s(60)):
            pygame.draw.line(image, wall.lerp((0, 0, 0), 0.12 * (1 - y / s(60))), (0, y), (WIDTH, y))
        columns, rows = self.SPRIGS
        for row in range(rows):
            for col in range(columns):
                x = (col + (0.5 if row % 2 else 0)) * WIDTH / (columns - 1)
                y = s(30) + row * (top - s(40)) / rows
                pygame.draw.line(image, pattern, (x, y - s(4)), (x, y + s(4)), 1)
                pygame.draw.circle(image, pattern, (x - s(2.5), y - s(1.5)), max(1, s(1.4)))
                pygame.draw.circle(image, pattern, (x + s(2.5), y - s(3)), max(1, s(1.4)))
        # Picture rail
        pygame.draw.rect(image, wood, (0, s(26), WIDTH, s(4)))
        pygame.draw.line(image, wood_dark, (0, s(30)), (WIDTH, s(30)), 1)

        # Panelling: a top rail, panels with bevelled edges, a skirting board
        pygame.draw.rect(image, wood, (0, top, WIDTH, ground - top))
        pygame.draw.rect(image, wood.lerp((255, 255, 255), 0.12), (0, top, WIDTH, s(5)))
        pygame.draw.line(image, wood_dark, (0, top + s(5)), (WIDTH, top + s(5)), 1)
        panel_width = s(62)
        for x in range(s(8), WIDTH, panel_width + s(8)):
            rect = pygame.Rect(x, top + s(13), panel_width, ground - top - s(30))
            pygame.draw.rect(image, wood.lerp(wood_dark, 0.25), rect)
            pygame.draw.lines(image, wood_dark, False, [rect.bottomleft, rect.topleft, rect.topright], 1)
            pygame.draw.lines(image, wood.lerp((255, 255, 255), 0.15), False, [rect.topright, rect.bottomright, rect.bottomleft], 1)
        pygame.draw.rect(image, wood_dark, (0, ground - s(10), WIDTH, s(10)))

        # The floor: boards running away from us, their gaps converging toward the middle of the wall
        for y in range(ground, HEIGHT):
            depth = (y - ground) / (HEIGHT - ground)
            pygame.draw.line(image, floor.lerp((0, 0, 0), 0.25 * (1 - depth)), (0, y), (WIDTH, y))
        vanish = (CENTER_X, ground - s(380))
        for k in range(-self.BOARDS, self.BOARDS + 1):
            bottom_x = CENTER_X + k * s(46)
            t = (ground - vanish[1]) / (HEIGHT - vanish[1])
            top_x = vanish[0] + (bottom_x - vanish[0]) * t
            pygame.draw.line(image, line, (top_x, ground), (bottom_x, HEIGHT), 1)
        for k in range(5):
            y = ground + (HEIGHT - ground) * (k / 5) ** 1.6
            pygame.draw.line(image, line.lerp(floor, 0.5), (0, y), (WIDTH, y), 1)

        # The rug: an oval with a border and a simple pattern, lying flat in front of the fire
        rug = pygame.Rect(0, 0, s(330), s(120))
        rug.center = (CENTER_X + s(30), ground + s(105))
        pygame.draw.ellipse(image, pygame.Color(palette.get("rug_border", palette["muted"])), rug)
        pygame.draw.ellipse(image, pygame.Color(palette.get("rug", palette["muted"])), rug.inflate(-s(18), -s(10)))
        stripe = pygame.Color(palette.get("rug_pattern", palette.get("rug_border", palette["muted"])))
        for k in (0.55, 0.3):
            pygame.draw.ellipse(image, stripe, rug.inflate(-rug.width * (1 - k), -rug.height * (1 - k)), 1)
        self.image = image
        self.painted_palette = palette

    def color_at(self, palette, y):
        if y < s(WAINSCOT_TOP):
            return pygame.Color(palette.get("wall", palette["bg"]))
        if y < s(FLOOR_TOP):
            return pygame.Color(palette.get("wainscot", palette["muted"]))
        return pygame.Color(palette.get("floor", palette["muted"]))

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.image, (0, 0))


class Window(Layer):
    # A tall window on the left of the wall, divided into panes, looking out on the sky:
    # rolling hills and a few trees far off, clouds drifting by day, stars and the moon by
    # night. Curtains hang either side, stirring in a draft; a plant sits on the sill. By day
    # sunlight through it lays a bright patch on the floor. Others ask glass() for the rectangle
    # of the glass (the weather outside is drawn inside it)
    #
    # Palette colors it uses:
    #   "outside_top", "outside_low"        the sky outside
    #   "outside_hill", "outside_tree"      the hills and trees
    #   "cloud", "star", "moon"             clouds (day), stars and the moon (night)
    #   "frame", "frame_dark"               the window frame
    #   "curtain", "curtain_dark"           the curtains
    #   "plant", "plant_pot"                the plant on the sill
    #   "sunlight"                          the patch of light on the floor (day only: none without it)

    X, Y, W, H = 22, 132, 96, 196   # the glass, pixels at the medium size
    PANES = (2, 3)

    def __init__(self, scene):
        super().__init__(scene)
        self.rect = pygame.Rect(s(self.X), s(self.Y), s(self.W), s(self.H))
        self.time = 0
        self.clouds = [(random.uniform(0, self.rect.width), random.uniform(0.1, 0.45), random.uniform(0.6, 1.2)) for i in range(3)]
        self.stars = [(random.uniform(0, 1), random.uniform(0, 0.6), random.uniform(0, 6)) for i in range(16)]
        self.view = None
        self.painted_palette = None
        self.outside = None             # the weather outside, drawn on the glass (see WindowWeather)
        self.passing = []               # anything else seen through the glass: each has draw_on_glass()

    def glass(self):
        return self.rect

    def paint(self, palette):
        # The still part of the view: sky gradient, hills, trees
        r = self.rect
        view = pygame.Surface(r.size)
        top = pygame.Color(palette.get("outside_top", palette["bg"]))
        low = pygame.Color(palette.get("outside_low", palette["bg"]))
        for y in range(r.height):
            pygame.draw.line(view, top.lerp(low, y / r.height), (0, y), (r.width, y))
        hill = pygame.Color(palette.get("outside_hill", palette["muted"]))
        rng = random.Random(3)
        for layer, (height, shade) in enumerate(((0.62, 0.4), (0.72, 0.0))):
            color = hill.lerp(low, shade)
            points = [(x, r.height * height + math.sin(x / s(20) + layer * 2) * s(6)) for x in range(0, r.width + 4, 4)]
            pygame.draw.polygon(view, color, points + [(r.width, r.height), (0, r.height)])
        tree = pygame.Color(palette.get("outside_tree", palette["muted"]))
        for k in range(5):
            x = rng.uniform(0, r.width)
            y = r.height * 0.72 + math.sin(x / s(20) + 2) * s(6)
            h = s(rng.uniform(14, 26))
            pygame.draw.polygon(view, tree, [(x - h * 0.3, y + 2), (x, y - h), (x + h * 0.3, y + 2)])
        self.view = view
        self.painted_palette = palette

    def update(self, dt):
        self.time += dt

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        r = self.rect
        clear = 1 - (self.outside.cover() if self.outside is not None else 0)
        sun = palette.get("sunlight")
        if sun:
            # The sunny patch on the floor: the window's shape thrown down and toward us
            ground = s(FLOOR_TOP)
            patch = pygame.Surface((WIDTH, HEIGHT - ground), pygame.SRCALPHA)
            light = pygame.Color(sun)
            strength = int(255 * 0.13 * min(1.2, self.scene.weather.get("light", 1)) * clear)
            pygame.draw.polygon(patch, (light.r, light.g, light.b, strength),
                                [(r.left + s(30), s(14)), (r.right + s(60), s(14)), (r.right + s(150), s(150)), (r.left + s(70), s(150))])
            surface.blit(patch, (0, ground))
        surface.blit(self.view, r.topleft)
        # Clouds by day, stars and the moon by night
        if palette.get("cloud") and clear > 0.3:
            cloud = pygame.Color(palette["cloud"])
            wind = self.scene.weather.get("wind", 1)
            for i, (x0, v, size) in enumerate(self.clouds):
                x = r.left + (x0 + self.time / 1000 * s(3) * wind * size) % (r.width + s(60)) - s(30)
                y = r.top + r.height * v
                w = s(26) * size
                clip = surface.get_clip()
                surface.set_clip(r)
                for k in range(3):
                    pygame.draw.circle(surface, cloud, (x + (k - 1) * w * 0.35, y - (w * 0.12 if k == 1 else 0)), w * 0.28)
                pygame.draw.ellipse(surface, cloud, (x - w * 0.6, y - w * 0.1, w * 1.2, w * 0.28))
                surface.set_clip(clip)
        if palette.get("star") and clear > 0.3:
            star = pygame.Color(palette["star"])
            for u, v, phase in self.stars:
                twinkle = (0.5 + 0.5 * math.sin(self.time / 900 + phase)) * clear
                x, y = r.left + u * r.width, r.top + v * r.height
                pygame.draw.circle(surface, self.view.get_at((int(u * (r.width - 1)), int(v * (r.height - 1)))).lerp(star, twinkle), (x, y), 1)
        if palette.get("moon") and clear > 0.3:
            moon = pygame.Color(palette["moon"])
            pygame.draw.circle(surface, moon, (r.left + r.width * 0.7, r.top + r.height * 0.18), s(8))
            pygame.draw.circle(surface, self.view.get_at((int(r.width * 0.7) + s(5), int(r.height * 0.18))),
                               (r.left + r.width * 0.7 + s(5), r.top + r.height * 0.18 - s(2)), s(7))
        clip = surface.get_clip()
        surface.set_clip(r)
        for thing in self.passing:
            thing.draw_on_glass(surface, palette)
        surface.set_clip(clip)
        if self.outside is not None:
            self.outside.draw_on_glass(surface, palette)
        self.draw_frame(surface, palette)

    def draw_frame(self, surface, palette):
        r = self.rect
        frame = pygame.Color(palette.get("frame", palette["muted"]))
        dark = pygame.Color(palette.get("frame_dark", palette["text"]))
        # Glazing bars
        cols, rows = self.PANES
        for c in range(1, cols):
            x = r.left + r.width * c / cols
            pygame.draw.line(surface, frame, (x, r.top), (x, r.bottom), max(2, s(3)))
        for k in range(1, rows):
            y = r.top + r.height * k / rows
            pygame.draw.line(surface, frame, (r.left, y), (r.right, y), max(2, s(3)))
        # The frame, and the sill sticking out below it
        pygame.draw.rect(surface, frame, r.inflate(s(10), s(10)), s(6))
        pygame.draw.rect(surface, dark, r.inflate(s(10), s(10)), 1)
        sill = pygame.Rect(r.left - s(12), r.bottom + s(4), r.width + s(24), s(8))
        pygame.draw.rect(surface, frame, sill)
        pygame.draw.line(surface, dark, sill.bottomleft, sill.bottomright, max(1, s(2)))
        # A plant on the sill
        pot = pygame.Rect(0, 0, s(16), s(14))
        pot.midbottom = (r.left + s(22), sill.top + 1)
        green = pygame.Color(palette.get("plant", palette["muted"]))
        for k in range(7):
            a = -math.pi / 2 + (k - 3) * 0.38 + math.sin(self.time / 1500 + k) * 0.03
            length = s(14 + (k % 3) * 4)
            tip = (pot.centerx + math.cos(a) * length, pot.top + math.sin(a) * length)
            pygame.draw.line(surface, green, (pot.centerx, pot.top + 1), tip, max(1, s(2)))
            pygame.draw.ellipse(surface, green, (tip[0] - s(3), tip[1] - s(2), s(6), s(4)))
        pygame.draw.polygon(surface, pygame.Color(palette.get("plant_pot", palette["accent"])),
                            [pot.topleft, pot.topright, (pot.right - s(3), pot.bottom), (pot.left + s(3), pot.bottom)])
        # Curtains: gathered folds hanging either side, stirring a little
        curtain = pygame.Color(palette.get("curtain", palette["accent"]))
        fold = pygame.Color(palette.get("curtain_dark", palette["accent"]))
        for side in (-1, 1):
            edge = r.left - s(14) if side < 0 else r.right + s(14)
            inner = r.left + s(6) if side < 0 else r.right - s(6)
            sway = math.sin(self.time / 1700 + side) * s(1.5) * self.scene.weather.get("wind", 1)
            top, bottom = r.top - s(16), r.bottom + s(32)
            shape = [(edge, top), (inner, top), (inner + sway - side * s(8), (top + bottom) * 0.5), (inner - side * s(10) + sway * 1.6, bottom), (edge, bottom)]
            pygame.draw.polygon(surface, curtain, shape)
            for k in (0.3, 0.6):
                x0 = edge + (inner - edge) * k
                pygame.draw.line(surface, fold, (x0, top), (x0 - side * s(4) + sway, bottom), max(1, s(2)))
        rod = pygame.Rect(r.left - s(22), r.top - s(20), r.width + s(44), s(4))
        pygame.draw.rect(surface, dark, rod)


class Fireplace(Layer):
    # A fireplace on the right of the wall: a stone surround with a dark opening, a wooden
    # mantel shelf with a ticking clock (its pendulum swinging), two candles and a little
    # vase on it, and in the hearth a fire: logs on a grate, flickering tongues of flame,
    # glowing embers and sparks drifting up. The fire's light flickers over the whole room,
    # strongest at night. Others ask fire_at() for where the fire is
    #
    # Palette colors it uses:
    #   "stone", "stone_dark"               the surround
    #   "mantel", "frame_dark"              the shelf
    #   "fire", "fire_core", "ember"        the flames and embers
    #   "firelight"                         the glow cast over the room
    #   "firelight_strength"                how strong that is, 0 to 1
    #   "brass", "candle", "candle_flame"   the clock, the candles

    X, TOP, WIDTH_, MANTEL = 330, 300, 110, 292     # pixels at the medium size: left edge, top of the surround, width, mantel height
    GLOW = 300
    SPARKS = 10
    SETTLE = (35000, 90000)         # milliseconds between logs settling
    SETTLE_TIME = 1600

    def __init__(self, scene):
        super().__init__(scene)
        self.left = s(self.X)
        self.right = min(WIDTH + s(10), self.left + s(self.WIDTH_))
        self.ground = s(FLOOR_TOP)
        self.opening = pygame.Rect(self.left + s(22), s(386), self.right - self.left - s(40), self.ground - s(386))
        self.time = 0
        self.sparks = []
        self.settled = None
        self.settle_wait = random.uniform(*self.SETTLE)
        self.surround = None
        self.glow = None
        self.painted_palette = None

    def fire_at(self):
        return (self.opening.centerx, self.opening.bottom - s(14))

    def paint(self, palette):
        image = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        stone = pygame.Color(palette.get("stone", palette["muted"]))
        dark = pygame.Color(palette.get("stone_dark", palette["text"]))
        mantel = pygame.Color(palette.get("mantel", palette["muted"]))
        top = s(self.TOP)
        surround = pygame.Rect(self.left, top, self.right - self.left, self.ground - top)
        pygame.draw.rect(image, stone, surround)
        # Stone blocks
        rows = 6
        for k in range(rows):
            y = top + (self.ground - top) * k / rows
            pygame.draw.line(image, dark, (self.left, y), (self.right, y), 1)
            offset = s(14) if k % 2 else 0
            for x in range(self.left + offset, self.right, s(28)):
                pygame.draw.line(image, dark, (x, y), (x, y + (self.ground - top) / rows), 1)
        # The opening: an arch, dark inside, sooty at the back
        o = self.opening
        pygame.draw.rect(image, dark.lerp((0, 0, 0), 0.5), o)
        pygame.draw.ellipse(image, dark.lerp((0, 0, 0), 0.5), (o.left, o.top - o.width * 0.25, o.width, o.width * 0.5))
        pygame.draw.rect(image, dark.lerp((0, 0, 0), 0.75), o.inflate(-s(14), -s(8)).move(0, s(4)))
        # The hearthstone in front
        pygame.draw.rect(image, stone.lerp(dark, 0.3), (self.left - s(8), self.ground - s(4), self.right - self.left + s(16), s(9)))
        # The mantel shelf, with what stands on it
        shelf = pygame.Rect(self.left - s(10), s(self.MANTEL), self.right - self.left + s(20), s(8))
        pygame.draw.rect(image, mantel, shelf)
        pygame.draw.line(image, pygame.Color(palette.get("frame_dark", palette["text"])), shelf.bottomleft, shelf.bottomright, max(1, s(2)))
        brass = pygame.Color(palette.get("brass", palette["accent"]))
        candle = pygame.Color(palette.get("candle", palette["text"]))
        for x in (self.left + s(8), self.right - s(16)):
            pygame.draw.rect(image, candle, (x, shelf.top - s(18), s(5), s(18)))
            pygame.draw.rect(image, brass, (x - s(2), shelf.top - s(3), s(9), s(3)))
        vase = pygame.Rect(0, 0, s(10), s(14))
        vase.midbottom = (self.right - s(32), shelf.top)
        pygame.draw.ellipse(image, pygame.Color(palette.get("plant_pot", palette["accent"])), vase)
        self.surround = image
        self.shelf = shelf
        self.glow = None
        if "candle_flame" in palette:
            c = pygame.Color(palette["candle_flame"])
            self.candle_glow = glow_sprite(s(14), (c.r * 0.35, c.g * 0.3, c.b * 0.2), 1.0, 8)
        if "fire" in palette:
            color = pygame.Color(palette.get("firelight", palette["fire"]))
            r = s(self.GLOW)
            strength = palette.get("firelight_strength", 0.3)
            self.glow = glow_sprite(r, (color.r * strength, color.g * strength, color.b * strength), 0.8, 40)
            self.hearth_glow = glow_sprite(o.width * 0.8, (color.r * 0.5, color.g * 0.35, color.b * 0.2), 0.7, 10)
        self.painted_palette = palette

    def update(self, dt):
        self.time += dt
        if self.settled is not None:
            self.settled += dt
            if self.settled > self.SETTLE_TIME:
                self.settled = None
        self.settle_wait -= dt
        if self.settle_wait <= 0:
            self.settle_wait = random.uniform(*self.SETTLE)
            self.settle()
        if random.random() < dt / 160 and len(self.sparks) < self.SPARKS:
            x, y = self.fire_at()
            self.sparks.append({"x": x + random.uniform(-s(12), s(12)), "y": y - s(10), "age": 0.0, "life": random.uniform(500, 1200),
                                "drift": random.uniform(-1, 1)})
        for spark in self.sparks:
            spark["age"] += dt
            spark["y"] -= s(30) * dt / 1000
            spark["x"] += spark["drift"] * s(6) * dt / 1000
        self.sparks = [spark for spark in self.sparks if spark["age"] < spark["life"] and spark["y"] > self.opening.top - s(6)]

    def settle(self):
        # A log shifts and settles: a burst of sparks, and the flames dip and flare
        x, y = self.fire_at()
        for k in range(16):
            self.sparks.append({"x": x + random.uniform(-s(16), s(16)), "y": y - random.uniform(0, s(12)), "age": 0.0,
                                "life": random.uniform(600, 1500), "drift": random.uniform(-2.5, 2.5)})
        self.settled = 0.0

    def flicker(self):
        t = self.time
        flicker = 0.8 + 0.12 * math.sin(t / 70) * math.sin(t / 173) + 0.08 * math.sin(t / 41 + 1)
        if self.settled is not None:
            # Dip, then flare up a little brighter for a moment
            a = self.settled / self.SETTLE_TIME
            flicker *= 1 - 0.35 * math.sin(math.pi * min(1, a * 3)) * (a < 0.33) + 0.25 * math.sin(math.pi * a) * (a >= 0.33)
        return flicker

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.surround, (0, 0))
        o = self.opening
        flicker = self.flicker()
        x, y = self.fire_at()
        k = s(1)
        # Logs on the grate, glowing embers under them
        ember = pygame.Color(palette.get("ember", palette.get("fire", palette["accent"])))
        wood = pygame.Color(palette.get("mantel", palette["muted"])).lerp((0, 0, 0), 0.5)
        pygame.draw.ellipse(surface, ember.lerp((0, 0, 0), 0.5 - 0.3 * flicker), (x - s(26), y + s(4), s(52), s(9)))
        for a, dy in ((0.15, 6), (-0.15, 6), (0.0, 0)):
            pygame.draw.line(surface, wood, (x - math.cos(a) * s(22), y + s(dy) + math.sin(a) * s(4)),
                             (x + math.cos(a) * s(22), y + s(dy) - math.sin(a) * s(4)), max(3, s(6)))
        if "fire" in palette:
            fire = pygame.Color(palette["fire"])
            core = pygame.Color(palette.get("fire_core", palette["fire"]))
            for n, (offset, height) in enumerate(((-0.6, 0.6), (0.55, 0.7), (-0.2, 1.0), (0.25, 0.9), (0, 1.2))):
                sway = math.sin(self.time / (80 + n * 19) + n * 1.7) * s(2.5)
                h = s(30) * height * flicker * (0.85 + 0.15 * math.sin(self.time / (60 + n * 13) + n))
                bx = x + offset * s(16)
                tongue = [(bx - s(6), y + s(2)), (bx + sway * 0.4 - s(3.5), y - h * 0.5), (bx + sway, y - h),
                          (bx + sway * 0.4 + s(3.5), y - h * 0.5), (bx + s(6), y + s(2))]
                pygame.draw.polygon(surface, fire, tongue)
                pygame.draw.polygon(surface, core, [((px - bx) * 0.5 + bx, y - (y - py) * 0.55) for px, py in tongue])
            for spark in self.sparks:
                fade = 1 - spark["age"] / spark["life"]
                pygame.draw.circle(surface, core.lerp((40, 20, 10), 1 - fade), (spark["x"], spark["y"]), max(1, s(1)))
            level = int(255 * flicker)
            glow = self.hearth_glow.copy()
            glow.fill((level, level, level), special_flags=pygame.BLEND_RGB_MULT)
            surface.blit(glow, glow.get_rect(center=(x, y - s(8))), special_flags=pygame.BLEND_RGB_ADD)
        self.draw_clock(surface, palette)
        if "candle_flame" in palette:
            flame = pygame.Color(palette["candle_flame"])
            for n, cx in enumerate((self.left + s(8) + s(2.5), self.right - s(16) + s(2.5))):
                wave = math.sin(self.time / (110 + n * 37) + n) * s(0.8)
                top = self.shelf.top - s(18)
                pygame.draw.polygon(surface, flame, [(cx - s(2), top - s(1)), (cx + wave, top - s(8)), (cx + s(2), top - s(1))])
                pygame.draw.circle(surface, flame.lerp((255, 255, 255), 0.5), (cx, top - s(2.5)), max(1, s(1.2)))
                glow = self.candle_glow.copy()
                level = int(255 * (0.85 + 0.15 * math.sin(self.time / 90 + n)))
                glow.fill((level, level, level), special_flags=pygame.BLEND_RGB_MULT)
                surface.blit(glow, glow.get_rect(center=(int(cx), int(top - s(4)))), special_flags=pygame.BLEND_RGB_ADD)

    def draw_clock(self, surface, palette):
        # A small mantel clock: a wooden case, a round face, and a pendulum swinging below
        brass = pygame.Color(palette.get("brass", palette["accent"]))
        case = pygame.Color(palette.get("mantel", palette["muted"])).lerp((0, 0, 0), 0.2)
        dark = pygame.Color(palette.get("frame_dark", palette["text"]))
        cx = (self.left + self.right) / 2 + s(4)
        bottom = self.shelf.top
        body = pygame.Rect(0, 0, s(24), s(34))
        body.midbottom = (cx, bottom)
        pygame.draw.rect(surface, case, body, border_radius=s(6))
        face = (cx, body.top + s(10))
        pygame.draw.circle(surface, brass, face, s(8))
        pygame.draw.circle(surface, pygame.Color(palette.get("candle", palette["text"])), face, s(6.5))
        seconds = self.time / 1000
        for length, turns in ((s(5), seconds / 3600), (s(4), seconds / 43200 + 0.3)):
            a = turns * 2 * math.pi - math.pi / 2
            pygame.draw.line(surface, dark, face, (face[0] + math.cos(a) * length, face[1] + math.sin(a) * length), 1)
        swing = math.sin(seconds * math.pi) * 0.3              # one swing a second
        window = pygame.Rect(0, 0, s(14), s(12))
        window.midtop = (cx, body.top + s(19))
        pygame.draw.rect(surface, dark, window)
        tip = (cx + math.sin(swing) * s(9), window.top + math.cos(swing) * s(9))
        pygame.draw.line(surface, brass, (cx, window.top), tip, 1)
        pygame.draw.circle(surface, brass, tip, max(1, s(2.2)))


class Firelight(Layer):
    # The fire's warm light thrown over the room, flickering with the flames: strong at night,
    # a faint warmth by day. Drawn over everything in the room (but under the game)

    def __init__(self, scene, fireplace):
        super().__init__(scene)
        self.fireplace = fireplace

    def draw(self, surface, palette):
        glow = self.fireplace.glow
        if glow is None:
            return
        level = int(255 * self.fireplace.flicker())
        sprite = glow.copy()
        sprite.fill((level, level, level), special_flags=pygame.BLEND_RGB_MULT)
        x, y = self.fireplace.fire_at()
        surface.blit(sprite, sprite.get_rect(center=(int(x), int(y - s(60)))), special_flags=pygame.BLEND_RGB_ADD)


class Nook(Layer):
    # What's right in front of us: the rolled arm of our armchair in the bottom left corner,
    # and in the bottom right a little table with a mug on it, steam curling up from it
    #
    # Palette colors it uses:
    #   "chair", "chair_dark"               the armchair's upholstery
    #   "table", "frame_dark"               the table
    #   "mug", "mug_dark"                   the mug
    #   "steam"                             the steam (fades into what's behind it)

    STEAM = 7

    def __init__(self, scene):
        super().__init__(scene)
        self.time = 0
        self.mug = (WIDTH - s(48), HEIGHT - s(58))
        self.wisps = [{"age": random.uniform(0, 3000), "life": random.uniform(2400, 3600), "phase": random.uniform(0, 6)} for i in range(self.STEAM)]

    def update(self, dt):
        self.time += dt
        for wisp in self.wisps:
            wisp["age"] += dt
            if wisp["age"] > wisp["life"]:
                wisp["age"], wisp["phase"] = 0.0, random.uniform(0, 6)

    def draw(self, surface, palette):
        chair = pygame.Color(palette.get("chair", palette["accent"]))
        chair_dark = pygame.Color(palette.get("chair_dark", palette["accent"]))
        # The chair arm: a big rolled cushion coming in from the bottom left
        arm = pygame.Rect(-s(40), HEIGHT - s(70), s(140), s(120))
        pygame.draw.ellipse(surface, chair_dark, arm.move(0, s(6)))
        pygame.draw.ellipse(surface, chair, arm)
        pygame.draw.arc(surface, chair_dark, arm.inflate(-s(30), -s(40)).move(s(10), -s(6)), 0.3, 2.6, max(1, s(2)))
        for k in range(5):
            pygame.draw.circle(surface, chair_dark, (arm.left + s(52) + k * s(14), arm.top + s(28) + (k % 2) * s(3)), max(1, s(1.6)))
        # The table and the mug
        table = pygame.Color(palette.get("table", palette["muted"]))
        dark = pygame.Color(palette.get("frame_dark", palette["text"]))
        top = pygame.Rect(0, 0, s(120), s(26))
        top.center = (WIDTH - s(30), HEIGHT - s(36))
        pygame.draw.ellipse(surface, dark, top.move(0, s(5)))
        pygame.draw.ellipse(surface, table, top)
        mx, my = self.mug
        mug = pygame.Color(palette.get("mug", palette["text"]))
        mug_dark = pygame.Color(palette.get("mug_dark", palette["muted"]))
        pygame.draw.circle(surface, mug, (mx + s(12), my + s(10)), s(6), max(2, s(3)))
        pygame.draw.rect(surface, mug, (mx - s(11), my, s(22), s(24)), border_bottom_left_radius=s(5), border_bottom_right_radius=s(5))
        pygame.draw.ellipse(surface, mug_dark, (mx - s(11), my - s(4), s(22), s(8)))
        pygame.draw.ellipse(surface, mug_dark.lerp((0, 0, 0), 0.3), (mx - s(8), my - s(2), s(16), s(5)))
        # Steam: thin wisps curling up and fading
        steam = pygame.Color(palette.get("steam", palette["text"]))
        for wisp in self.wisps:
            t = wisp["age"] / wisp["life"]
            points = []
            for n in range(6):
                u = t * 0.6 + n * 0.08
                y = my - s(6) - u * s(80)
                x = mx + math.sin(u * 7 + wisp["phase"] + self.time / 700) * s(5) * (0.5 + u)
                points.append((x, y))
            behind = self.scene.color_at(palette, points[0][1])
            color = behind.lerp(steam, 0.5 * max(0.0, math.sin(math.pi * min(1.0, t))))
            pygame.draw.lines(surface, color, False, points, 1)
