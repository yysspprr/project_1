# Under the sea, looking out across a coral reef: the rippling underside of the surface
# above, light rays slanting down through blue water that fades into deep haze, far-off
# rocks in silhouette, coral and sponges along the sandy floor at the sides, tall kelp
# swaying up the edges, bubbles rising and specks drifting in the water

import math

import random

import pygame

from partials.config import WIDTH, HEIGHT, CENTER_X, s
from partials.backgrounds.base import Layer
from partials.backgrounds.brook_light import glow_sprite


FLOOR_Y = 488                       # where the sandy floor starts in the middle, pixels at the medium size
SURFACE_Y = 22                      # how far down the surface's underside sits


def surge(scene):
    # The swell: water rocking gently back and forth, -1 to 1
    return scene.weather.get("surge", 0.0)


class OpenWater(Layer):
    # The water itself: pale and bright just under the surface, deepening to the floor, with
    # far-off shapes fading into the haze: a rock arch on one side, a kelp forest on the
    # other, and a ridge of reef along the back. Painted once
    #
    # Palette colors it uses:
    #   "water_top", "water_mid", "water_deep"     the water near the surface, halfway, at the floor
    #   "far_rock"                                  the faraway shapes (fading into the water)

    def __init__(self, scene):
        super().__init__(scene)
        self.image = None
        self.painted_palette = None

    def water_color(self, palette, y):
        top = pygame.Color(palette.get("water_top", palette["bg"]))
        mid = pygame.Color(palette.get("water_mid", palette["bg"]))
        deep = pygame.Color(palette.get("water_deep", palette["bg"]))
        t = max(0.0, min(1.0, y / HEIGHT))
        return top.lerp(mid, t / 0.5) if t < 0.5 else mid.lerp(deep, (t - 0.5) / 0.5)

    def paint(self, palette):
        image = pygame.Surface((WIDTH, HEIGHT))
        for y in range(HEIGHT):
            pygame.draw.line(image, self.water_color(palette, y), (0, y), (WIDTH, y))
        far = pygame.Color(palette.get("far_rock", palette["muted"]))
        rng = random.Random(11)
        floor = s(FLOOR_Y)

        def faded(y, amount):
            return self.water_color(palette, y).lerp(far, amount)

        # A low ridge of reef along the back, very faint
        ridge = [(x, floor - s(46) - math.sin(x / s(37)) * s(10) - math.sin(x / s(13)) * s(4)) for x in range(-4, WIDTH + 8, 4)]
        pygame.draw.polygon(image, faded(floor - s(40), 0.22), ridge + [(WIDTH + 4, HEIGHT), (-4, HEIGHT)])
        # A rock arch on the left
        arch = [(0, floor - s(150)), (s(30), floor - s(170)), (s(62), floor - s(150)), (s(78), floor - s(90)), (s(86), floor),
                (s(60), floor), (s(56), floor - s(80)), (s(36), floor - s(110)), (s(18), floor - s(80)), (s(12), floor), (0, floor)]
        pygame.draw.polygon(image, faded(floor - s(100), 0.38), arch)
        # Kelp forest on the right: tall wavy stalks
        for k in range(7):
            x = WIDTH - s(10) - k * s(14) + rng.uniform(-s(4), s(4))
            top = floor - s(rng.uniform(180, 300))
            points = [(x + math.sin(t * 5 + k) * s(6), floor - (floor - top) * t) for t in [n / 12 for n in range(13)]]
            pygame.draw.lines(image, faded(floor - s(150), 0.3 - k * 0.025), False, points, max(2, s(4)))
        self.image = image
        self.painted_palette = palette

    def color_at(self, palette, y):
        return self.water_color(palette, y)

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.image, (0, 0))


class Surface(Layer):
    # The underside of the sea surface across the top of the window: a bright band above a
    # rippling edge that rolls with the swell, flecked with glints where the sun (or moon)
    # comes through
    #
    # Palette colors it uses:
    #   "surface", "surface_glint"

    GLINTS = 22

    def __init__(self, scene):
        super().__init__(scene)
        self.time = 0
        self.glints = [(random.uniform(0, WIDTH), random.uniform(0.2, 0.9), random.uniform(600, 1600), random.uniform(0, 6)) for i in range(self.GLINTS)]

    def update(self, dt):
        self.time += dt

    def edge(self, x):
        t = self.time / 1000
        return s(SURFACE_Y) + math.sin(x / s(28) + t * 1.1) * s(4) + math.sin(x / s(11) - t * 1.7) * s(1.6)

    def draw(self, surface, palette):
        top = pygame.Color(palette.get("surface", palette["text"]))
        below = self.scene.color_at(palette, s(SURFACE_Y + 6))
        points = [(x, self.edge(x)) for x in range(-4, WIDTH + 8, 4)]
        pygame.draw.polygon(surface, top.lerp(below, 0.45), [(-4, -1), (WIDTH + 4, -1)] + points[::-1])
        pygame.draw.polygon(surface, top, [(-4, -1), (WIDTH + 4, -1)] + [(x, y - s(5)) for x, y in points[::-1]])
        pygame.draw.lines(surface, top.lerp((255, 255, 255), 0.4), False, points, 1)
        glint = pygame.Color(palette.get("surface_glint", palette["text"]))
        for x, v, period, phase in self.glints:
            flash = max(0.0, math.sin(self.time / period + phase)) ** 3
            if flash < 0.1:
                continue
            y = self.edge(x) * v
            pygame.draw.line(surface, top.lerp(glint, flash), (x - s(3), y), (x + s(3), y), 1)


class LightRays(Layer):
    # Shafts of light slanting down from the surface, each slowly brightening and fading and
    # swaying a little with the swell. Soft and faint behind the middle of the game. Strong in
    # the sunlit shallows, faint by moonlight
    #
    # Palette colors it uses:
    #   "ray"                   the light (added onto the water)
    #   "ray_strength"          how bright at their brightest, 0 to 1

    RAYS = 7
    LEVELS = 10

    def __init__(self, scene):
        super().__init__(scene)
        self.time = 0
        self.rays = []
        for i in range(self.RAYS):
            self.rays.append({"x": WIDTH * (i + random.uniform(0.1, 0.9)) / self.RAYS, "width": s(random.uniform(18, 40)),
                              "length": HEIGHT * random.uniform(0.55, 0.9), "period": random.uniform(5000, 11000),
                              "phase": random.uniform(0, 6)})
        self.sprites = None
        self.painted_palette = None

    def paint(self, palette):
        color = pygame.Color(palette.get("ray", palette["text"]))
        strength = palette.get("ray_strength", 0.2)
        self.sprites = []
        lean = 0.28                                         # how far they slant, sideways per pixel down
        for ray in self.rays:
            w, length = int(ray["width"]), int(ray["length"])
            image = pygame.Surface((w + int(length * lean) + 4, length))
            image.fill((0, 0, 0))
            for y in range(length):
                fade = (1 - y / length) ** 1.4
                x0 = y * lean
                for k in range(3):                          # soft edges: a brighter core
                    inset = w * k / 7
                    share = strength * fade * (0.35 + 0.3 * k) * self.scene.keep(ray["x"] + x0, 0.6)
                    pygame.draw.line(image, (int(color.r * share / 2.2), int(color.g * share / 2.2), int(color.b * share / 2.2)),
                                     (x0 + inset, y), (x0 + w - inset, y))
            levels = []
            for level in range(1, self.LEVELS + 1):
                copy = image.copy()
                copy.fill((int(255 * level / self.LEVELS),) * 3, special_flags=pygame.BLEND_RGB_MULT)
                levels.append(copy)
            self.sprites.append(levels)
        self.painted_palette = palette

    def update(self, dt):
        self.time += dt

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        light = min(1.2, self.scene.weather.get("light", 1))
        for ray, levels in zip(self.rays, self.sprites):
            show = 0.5 + 0.5 * math.sin(self.time / ray["period"] * 2 * math.pi + ray["phase"])
            level = int(show * light * self.LEVELS)
            if level <= 0:
                continue
            sway = surge(self.scene) * s(8)
            surface.blit(levels[min(level, self.LEVELS) - 1], (ray["x"] + sway - ray["width"] / 2, s(SURFACE_Y)), special_flags=pygame.BLEND_RGB_ADD)


class ReefFloor(Layer):
    # The sea floor: sand rippled by the current, low in the middle and heaped up at the
    # sides, where the reef grows: branching coral, sea fans, brain coral, table coral, tube
    # sponges and rocks, with tufts of sea grass, shells and a starfish on the sand. The
    # middle stays open sand behind the game. Painted once
    #
    # Palette colors it uses:
    #   "sand", "sand_dark", "sand_ripple"
    #   "rock", "rock_dark"
    #   "coral" (a list), "coral_dark"
    #   "seagrass", "shell", "starfish"

    def __init__(self, scene):
        super().__init__(scene)
        self.image = None
        self.painted_palette = None
        rng = random.Random(5)
        self.seed = rng.random()

    def floor_y(self, x):
        # The sand's top edge: low in the middle, rising toward the sides
        side = abs(x - CENTER_X) / CENTER_X
        return s(FLOOR_Y) - side ** 2.0 * s(120) + math.sin(x / s(23)) * s(3)

    def paint(self, palette):
        rng = random.Random(5)
        image = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        sand = pygame.Color(palette.get("sand", palette["muted"]))
        sand_dark = pygame.Color(palette.get("sand_dark", palette["muted"]))
        ripple = pygame.Color(palette.get("sand_ripple", palette["muted"]))
        rock = pygame.Color(palette.get("rock", palette["muted"]))
        rock_dark = pygame.Color(palette.get("rock_dark", palette["muted"]))
        corals = [pygame.Color(c) for c in palette.get("coral", [palette["accent"]])]
        coral_dark = pygame.Color(palette.get("coral_dark", palette["muted"]))
        grass = pygame.Color(palette.get("seagrass", palette["muted"]))

        # Sand, darker toward us
        edge = [(x, self.floor_y(x)) for x in range(-4, WIDTH + 8, 4)]
        pygame.draw.polygon(image, sand, edge + [(WIDTH + 4, HEIGHT), (-4, HEIGHT)])
        top = min(y for x, y in edge)
        for y in range(int(top), HEIGHT, 2):
            share = (y - top) / (HEIGHT - top)
            band = pygame.Surface((WIDTH, 2), pygame.SRCALPHA)
            band.fill((sand_dark.r, sand_dark.g, sand_dark.b, int(255 * 0.55 * share)))
            image.blit(band, (0, y), special_flags=0)
        mask = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(mask, (255, 255, 255, 255), edge + [(WIDTH + 4, HEIGHT), (-4, HEIGHT)])
        image.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        for k in range(26):
            x0 = rng.uniform(-s(30), WIDTH)
            y = rng.uniform(top + s(10), HEIGHT - s(4))
            if y < self.floor_y(x0) + s(6):
                continue
            length = s(rng.uniform(30, 80))
            points = [(x0 + length * t, y + math.sin(t * 6 + k) * s(1.5)) for t in [n / 8 for n in range(9)]]
            pygame.draw.lines(image, ripple, False, points, 1)

        def rocks(x, y, size):
            pts = []
            for c in range(7):
                a = math.pi + math.pi * c / 6
                r = size * rng.uniform(0.7, 1.05)
                pts.append((x + math.cos(a) * r * 1.3, y + math.sin(a) * r))
            pygame.draw.polygon(image, rock, pts)
            pygame.draw.polygon(image, rock_dark, [pts[0], pts[1], pts[2], (x - size * 0.2, y)])
            pygame.draw.lines(image, rock_dark, False, pts, 1)

        def branching(x, y, size, color):
            def branch(px, py, angle, length, depth):
                ex, ey = px + math.cos(angle) * length, py + math.sin(angle) * length
                pygame.draw.line(image, color, (px, py), (ex, ey), max(2, int(size * 0.12 * (depth + 1))))
                pygame.draw.circle(image, color.lerp((255, 255, 255), 0.25), (ex, ey), max(1, size * 0.06 * (depth + 1)))
                if depth > 0:
                    for turn in (-0.45, 0.4):
                        branch(ex, ey, angle + turn + rng.uniform(-0.15, 0.15), length * 0.7, depth - 1)
            for a in (-math.pi / 2 - 0.35, -math.pi / 2, -math.pi / 2 + 0.4):
                branch(x, y, a, size * 0.45, 2)

        def fan(x, y, size, color):
            for k in range(13):
                a = -math.pi / 2 + (k - 6) * 0.12
                tip = (x + math.cos(a) * size * 1.2, y + math.sin(a) * size * 1.2)
                pygame.draw.line(image, color, (x, y), tip, 1)
            pygame.draw.arc(image, color, (x - size * 1.2, y - size * 1.2, size * 2.4, size * 2.4), math.pi * 0.27, math.pi * 0.73, max(1, s(2)))
            for r in (0.5, 0.85):
                pygame.draw.arc(image, color, (x - size * 1.2 * r, y - size * 1.2 * r, size * 2.4 * r, size * 2.4 * r), math.pi * 0.27, math.pi * 0.73, 1)
            pygame.draw.line(image, coral_dark, (x, y), (x, y - size * 0.2), max(2, s(2)))

        def brain(x, y, size, color):
            dome = pygame.Rect(0, 0, size * 2.2, size * 1.5)
            dome.midbottom = (x, y + size * 0.15)
            half = [(x + math.cos(a) * dome.width / 2, y - math.sin(a) * dome.height * 0.75) for a in [math.pi * n / 16 for n in range(17)]]
            pygame.draw.polygon(image, color, half)
            pygame.draw.lines(image, coral_dark, False, half, 1)
            for k in range(4):
                points = [(dome.left + dome.width * (0.15 + 0.7 * t), y - size * (0.2 + 0.18 * k) + math.sin(t * 9 + k) * size * 0.06)
                          for t in [n / 10 for n in range(11)]]
                pygame.draw.lines(image, coral_dark, False, points, 1)

        def table(x, y, size, color):
            pygame.draw.line(image, color.lerp(coral_dark, 0.3), (x, y), (x, y - size * 0.7), max(2, int(size * 0.18)))
            plate = pygame.Rect(0, 0, size * 2.6, size * 0.5)
            plate.center = (x, y - size * 0.8)
            pygame.draw.ellipse(image, color, plate)
            pygame.draw.ellipse(image, coral_dark, plate, 1)

        def sponges(x, y, size, color):
            for k, (dx, h) in enumerate(((-0.4, 1.2), (0.05, 1.6), (0.45, 1.0))):
                tube = pygame.Rect(0, 0, size * 0.42, size * h)
                tube.midbottom = (x + dx * size, y)
                pygame.draw.rect(image, color, tube, border_radius=int(size * 0.18))
                pygame.draw.ellipse(image, coral_dark, (tube.left + 1, tube.top, tube.width - 2, size * 0.18))

        def grass_tuft(x, y, size):
            for k in range(5):
                lean = (k - 2) * 0.25
                points = [(x + k - 2 + math.sin(t * 3 + k) * size * 0.1 + lean * size * t, y - size * t) for t in [n / 5 for n in range(6)]]
                pygame.draw.lines(image, grass, False, points, max(1, s(1.4)))

        # The reef: clusters at both sides, nothing behind the middle
        growth = [branching, fan, brain, table, sponges]
        for side in (-1, 1):
            for k in range(11):
                along = rng.uniform(0.0, 0.3)
                x = along * WIDTH if side < 0 else WIDTH - along * WIDTH
                y = self.floor_y(x) + s(rng.uniform(4, 30)) + (k // 5) * s(60)
                size = s(rng.uniform(18, 32)) * (1.2 - along) * (1 + 0.25 * (k // 5))
                kind = growth[(k + (side > 0)) % len(growth)]
                rocks(x + rng.uniform(-s(10), s(10)), y + s(3), size * 0.7)
                kind(x, y, size, corals[(k * 3 + side) % len(corals)])
                grass_tuft(x + rng.uniform(-s(18), s(18)), y + s(4), s(rng.uniform(10, 18)))
        # Shells and a starfish out on the sand
        shell = pygame.Color(palette.get("shell", palette["muted"]))
        for k in range(5):
            x = rng.uniform(s(20), WIDTH - s(20))
            y = rng.uniform(self.floor_y(x) + s(30), HEIGHT - s(10))
            pygame.draw.ellipse(image, shell, (x - s(3), y - s(2), s(6), s(4)))
            pygame.draw.line(image, sand_dark, (x, y - s(2)), (x, y + s(2)), 1)
        star = pygame.Color(palette.get("starfish", palette["accent"]))
        sx, sy = WIDTH * 0.72, HEIGHT - s(26)
        points = []
        for k in range(10):
            a = -math.pi / 2 + k * math.pi / 5 + 0.2
            r = s(9) if k % 2 == 0 else s(3.5)
            points.append((sx + math.cos(a) * r, sy + math.sin(a) * r * 0.6))
        pygame.draw.polygon(image, star, points)
        self.image = image
        self.painted_palette = palette

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.image, (0, 0))


class Kelp(Layer):
    # Tall kelp growing up both edges of the window from the floor: long stalks with leafy
    # blades along them and little floats, swaying with the swell, the tops moving most
    #
    # Palette colors it uses:
    #   "kelp", "kelp_dark"

    STALKS = 6
    SEGMENTS = 14

    def __init__(self, scene, floor):
        super().__init__(scene)
        self.floor = floor
        self.time = 0
        self.stalks = []
        for i in range(self.STALKS):
            side = -1 if i % 2 == 0 else 1
            x = (s(random.uniform(-6, 30)) if side < 0 else WIDTH - s(random.uniform(-6, 30)))
            self.stalks.append({"x": x, "base": floor.floor_y(x) + s(random.uniform(10, 40)),
                                "height": HEIGHT * random.uniform(0.45, 0.75), "phase": random.uniform(0, 6),
                                "side": side, "dark": i >= 3, "lean": side * -random.uniform(0.02, 0.1)})
        self.stalks.sort(key=lambda k: k["dark"], reverse=True)

    def update(self, dt):
        self.time += dt

    def draw(self, surface, palette):
        light = pygame.Color(palette.get("kelp", palette["muted"]))
        dark = pygame.Color(palette.get("kelp_dark", palette["muted"]))
        swell = surge(self.scene)
        for stalk in self.stalks:
            color = dark if stalk["dark"] else light
            points = []
            for n in range(self.SEGMENTS + 1):
                t = n / self.SEGMENTS
                sway = (swell * s(22) + math.sin(self.time / 1300 + stalk["phase"] + t * 2.5) * s(5)) * t ** 1.6
                points.append((stalk["x"] + stalk["lean"] * stalk["height"] * t + sway, stalk["base"] - stalk["height"] * t))
            pygame.draw.lines(surface, color, False, points, max(2, s(3)))
            for n in range(1, self.SEGMENTS):
                x, y = points[n]
                side = 1 if n % 2 else -1
                length = s(16) * (1 - n / (self.SEGMENTS + 4))
                droop = (points[n + 1][0] - points[n - 1][0]) * 0.8
                blade = [(x, y), (x + side * length * 0.6 + droop, y - length * 0.45), (x + side * length + droop * 1.4, y - length * 0.2),
                         (x + side * length * 0.5 + droop, y + length * 0.05)]
                pygame.draw.polygon(surface, color, blade)
                if n % 3 == 0:
                    pygame.draw.circle(surface, color.lerp((255, 255, 255), 0.15), (x, y), max(1, s(2.4)))


class Bubbles(Layer):
    # Bubbles rising from a few spots among the coral in little wobbling streams, plus the odd
    # stray one, growing a touch as they rise and vanishing at the surface
    #
    # Palette colors it uses:
    #   "bubble"                its rim and glint (the inside shows the water)

    VENTS = 4
    EVERY = (250, 900)              # milliseconds between bubbles from one vent

    def __init__(self, scene, floor):
        super().__init__(scene)
        self.vents = []
        self.bubbles = []
        self.time = 0
        if floor is not None:
            self.place_vents(floor)

    def place_vents(self, floor):
        self.vents = []
        for i in range(self.VENTS):
            x = random.uniform(0.04, 0.26) * WIDTH
            if i % 2:
                x = WIDTH - x
            self.vents.append({"x": x, "y": floor.floor_y(x) + s(6), "wait": random.uniform(0, 1000), "burst": 0})

    def update(self, dt):
        self.time += dt
        for vent in self.vents:
            vent["wait"] -= dt
            if vent["wait"] <= 0:
                vent["wait"] = random.uniform(*self.EVERY)
                self.bubbles.append({"x": vent["x"] + random.uniform(-s(2), s(2)), "y": vent["y"], "r": s(random.uniform(1.2, 2.8)),
                                     "phase": random.uniform(0, 6), "speed": random.uniform(0.8, 1.3)})
        swell = surge(self.scene)
        for bubble in self.bubbles:
            bubble["y"] -= s(42) * bubble["speed"] * dt / 1000
            bubble["x"] += (math.sin(self.time / 180 + bubble["phase"]) * s(10) + swell * s(8)) * dt / 1000
            bubble["r"] += s(0.15) * dt / 1000
        self.bubbles = [b for b in self.bubbles if b["y"] > s(SURFACE_Y) + s(2)]

    def draw(self, surface, palette):
        rim = pygame.Color(palette.get("bubble", palette["text"]))
        for b in self.bubbles:
            strength = 0.75 * self.scene.keep(b["x"], 0.5)
            behind = self.scene.color_at(palette, b["y"])
            pygame.draw.circle(surface, behind.lerp(rim, strength), (b["x"], b["y"]), b["r"], 1)
            pygame.draw.circle(surface, behind.lerp(rim, strength), (b["x"] - b["r"] * 0.35, b["y"] - b["r"] * 0.35), max(1, b["r"] * 0.3))


class MarineSnow(Layer):
    # Tiny specks drifting slowly through the water, sinking a little and rocking with the swell
    #
    # Palette colors it uses:
    #   "speck"

    COUNT = 50

    def __init__(self, scene):
        super().__init__(scene)
        self.specks = [{"x": random.uniform(0, WIDTH), "y": random.uniform(0, HEIGHT), "depth": random.uniform(0.3, 1),
                        "phase": random.uniform(0, 6)} for i in range(self.COUNT)]
        self.time = 0

    def update(self, dt):
        self.time += dt
        swell = surge(self.scene)
        for p in self.specks:
            p["y"] += s(4) * p["depth"] * dt / 1000
            p["x"] += (swell * s(10) + math.sin(self.time / 2000 + p["phase"]) * s(2)) * p["depth"] * dt / 1000
            if p["y"] > HEIGHT:
                p["y"], p["x"] = s(SURFACE_Y), random.uniform(0, WIDTH)
            p["x"] %= WIDTH

    def draw(self, surface, palette):
        speck = pygame.Color(palette.get("speck", palette["text"]))
        for p in self.specks:
            behind = self.scene.color_at(palette, p["y"])
            strength = 0.45 * p["depth"] * self.scene.keep(p["x"], 0.6)
            surface.set_at((int(p["x"]), int(p["y"])), behind.lerp(speck, strength))
            if p["depth"] > 0.8:
                surface.set_at((int(p["x"]) + 1, int(p["y"])), behind.lerp(speck, strength * 0.6))
