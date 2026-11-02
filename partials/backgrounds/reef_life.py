# Life on the reef. Regulars: schools of little fish wheeling through the water, a
# clownfish darting in and out of its anemone, a crab sidling over the sand, an octopus
# on a rock changing colour, and jellyfish pulsing slowly upward (glowing at night).
# Rare visitors, one at a time: a sea turtle gliding by, a manta ray sweeping overhead,
# a shark's shape far off in the blue, a whale's shadow passing over the surface, and the
# old treasure chest in the sand creaking open with a burst of bubbles
#
# Anything moving through the water stirs the plankton (glowing trails at night)

import math

import random

import pygame

from partials.config import WIDTH, HEIGHT, CENTER_X, s
from partials.backgrounds.base import Layer
from partials.backgrounds.brook_light import glow_sprite
from partials.backgrounds.brook_life import Visitor
from partials.backgrounds.reef import SURFACE_Y


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def fish_shape(surface, color, x, y, length, facing, tail_beat, eye=None, stripe=None, fin=None):
    # A little fish seen from the side: an oval body, a forked tail that beats, a fin on top
    h = length * 0.42
    pygame.draw.polygon(surface, color, [(x - facing * length * 0.42, y), (x - facing * length * 0.75, y - h * 0.55 + tail_beat),
                                         (x - facing * length * 0.68, y + tail_beat * 0.3), (x - facing * length * 0.75, y + h * 0.55 + tail_beat)])
    if fin is not None:
        pygame.draw.polygon(surface, fin, [(x - facing * length * 0.15, y - h * 0.45), (x + facing * length * 0.05, y - h * 0.85), (x + facing * length * 0.2, y - h * 0.4)])
    pygame.draw.ellipse(surface, color, (x - length * 0.5, y - h / 2, length, h))
    if stripe is not None:
        for u in stripe:
            pygame.draw.line(surface, stripe[u], (x + facing * u * length, y - h * 0.42), (x + facing * u * length, y + h * 0.42), max(1, int(length * 0.09)))
    if eye is not None:
        pygame.draw.circle(surface, eye, (x + facing * length * 0.3, y - h * 0.1), max(1, length * 0.06))


class FishSchool(Layer):
    # A school of small fish wheeling through the water together: a leader wanders, turning
    # back before it strays too far, and the rest follow in loose formation, each a little
    # behind, tails beating. Faint behind the middle of the game
    #
    # Palette colors it uses:
    #   key (given when made): a list of body colors for this school
    #   "fish_eye"

    SPEED = 34

    def __init__(self, scene, key, count, height, plankton=None):
        super().__init__(scene)
        self.key = key
        self.plankton = plankton
        self.time = 0
        self.low, self.high = height
        self.x, self.y = random.uniform(0, WIDTH), random.uniform(*height)
        self.heading = random.choice((0, math.pi)) + random.uniform(-0.3, 0.3)
        self.turn = 0.0
        self.fish = [{"dx": -s(random.uniform(6, 34)), "dy": s(random.uniform(-14, 14)), "x": self.x, "y": self.y,
                      "length": s(random.uniform(10, 14)), "phase": random.uniform(0, 6), "pick": random.random()} for i in range(count)]

    def update(self, dt):
        self.time += dt
        seconds = dt / 1000
        self.turn += random.uniform(-1, 1) * seconds * 2
        self.turn = max(-1.0, min(1.0, self.turn))
        # Turn back from the edges and from the surface and floor
        if self.x < -s(30) and math.cos(self.heading) < 0.3 or self.x > WIDTH + s(30) and math.cos(self.heading) > -0.3:
            self.turn = 1.6
        if self.y < self.low:
            self.turn = 1.2 if math.cos(self.heading) > 0 else -1.2
        if self.y > self.high:
            self.turn = -1.2 if math.cos(self.heading) > 0 else 1.2
        self.heading += self.turn * seconds
        speed = s(self.SPEED)
        self.x += math.cos(self.heading) * speed * seconds
        self.y += math.sin(self.heading) * speed * seconds * 0.5
        cos, sin = math.cos(self.heading), math.sin(self.heading)
        for f in self.fish:
            tx = self.x + f["dx"] * cos - f["dy"] * sin
            ty = self.y + f["dx"] * sin * 0.5 + f["dy"] * cos
            f["x"] += (tx - f["x"]) * min(1, seconds * 3)
            f["y"] += (ty - f["y"]) * min(1, seconds * 3)
        if self.plankton is not None and random.random() < dt / 150:
            f = random.choice(self.fish)
            self.plankton.stir(f["x"], f["y"], s(12))

    def draw(self, surface, palette):
        colors = [pygame.Color(c) for c in palette.get(self.key, [palette["muted"]])]
        eye = pygame.Color(palette.get("fish_eye", palette["text"]))
        facing = 1 if math.cos(self.heading) >= 0 else -1
        for f in self.fish:
            behind = self.scene.color_at(palette, f["y"])
            show = self.scene.keep(f["x"], 0.55)
            color = behind.lerp(colors[int(f["pick"] * len(colors)) % len(colors)], show)
            beat = math.sin(self.time / 90 + f["phase"]) * f["length"] * 0.12
            fish_shape(surface, color, f["x"], f["y"], f["length"], facing, beat, eye=behind.lerp(eye, show))


class Anemone(Layer):
    # A sea anemone on the reef at the left, its tentacles swaying, and a clownfish that lives
    # in it: darting out in little loops, hovering, and diving back in among the tentacles
    #
    # Palette colors it uses:
    #   "anemone", "anemone_tip"
    #   "clownfish", "clownfish_band", "fish_eye"

    TENTACLES = 16

    def __init__(self, scene, floor):
        super().__init__(scene)
        self.x = s(66)
        self.y = floor.floor_y(self.x) + s(14)
        self.time = 0
        self.fish = {"angle": 0.0, "reach": 0.0, "goal": 0.0, "wait": 1000}
        self.out = [0.0, 0.0]                               # the fish's offset from its home

    def update(self, dt):
        self.time += dt
        f = self.fish
        f["wait"] -= dt
        if f["wait"] <= 0:
            f["goal"] = random.choice((0.0, 0.0, 0.6, 1.0))
            f["angle"] = random.uniform(-2.6, -0.5)
            f["wait"] = random.uniform(900, 2600)
        f["reach"] += (f["goal"] - f["reach"]) * min(1, dt / 350)

    def draw(self, surface, palette):
        body = pygame.Color(palette.get("anemone", palette["accent"]))
        tip = pygame.Color(palette.get("anemone_tip", palette["text"]))
        swell = self.scene.weather.get("surge", 0)
        stem = pygame.Rect(0, 0, s(18), s(12))
        stem.midbottom = (self.x, self.y)
        pygame.draw.ellipse(surface, body.lerp((0, 0, 0), 0.25), stem)
        top = (self.x, self.y - s(9))
        f = self.fish
        fx = self.x + math.cos(f["angle"]) * s(26) * f["reach"] + math.sin(self.time / 400) * s(2)
        fy = top[1] + math.sin(f["angle"]) * s(18) * f["reach"] - s(2)
        facing = 1 if math.cos(f["angle"]) * (f["goal"] - f["reach"]) >= 0 else -1
        clown = pygame.Color(palette.get("clownfish", palette["accent"]))
        band = pygame.Color(palette.get("clownfish_band", palette["text"]))
        eye = pygame.Color(palette.get("fish_eye", palette["text"]))
        hidden = f["reach"] < 0.15
        if hidden:
            fish_shape(surface, clown, fx, fy + s(3), s(10), facing, math.sin(self.time / 80) * s(1), eye=eye,
                       stripe={0.2: band, -0.15: band})
        # Tentacles
        for k in range(self.TENTACLES):
            a = -math.pi / 2 + (k - self.TENTACLES / 2) * 0.17
            length = s(16) * (0.8 + 0.3 * math.sin(k * 1.7))
            sway = swell * 0.35 + math.sin(self.time / 700 + k * 0.6) * 0.15
            mid = (top[0] + math.cos(a + sway * 0.5) * length * 0.5, top[1] + math.sin(a + sway * 0.5) * length * 0.5)
            end = (top[0] + math.cos(a + sway) * length, top[1] + math.sin(a + sway) * length)
            pygame.draw.lines(surface, body, False, [top, mid, end], max(2, s(3)))
            pygame.draw.circle(surface, tip, end, max(1, s(2)))
        if not hidden:
            fish_shape(surface, clown, fx, fy, s(10), facing, math.sin(self.time / 80) * s(1), eye=eye,
                       stripe={0.2: band, -0.15: band})


class Crab(Layer):
    # A crab on the sand: it scuttles sideways in short dashes, stops, raises and snaps its
    # claws, and scuttles on, turning back at the edges. It keeps to the near sand
    #
    # Palette colors it uses:
    #   "crab", "crab_dark"

    SIZE = 1.3

    def __init__(self, scene, floor):
        super().__init__(scene)
        self.floor = floor
        self.x = random.uniform(0.1, 0.9) * WIDTH
        self.y = HEIGHT - s(random.uniform(18, 40))
        self.dir = random.choice((-1, 1))
        self.moving = 0.0
        self.wait = 1000.0
        self.time = 0

    def update(self, dt):
        self.time += dt
        if self.moving > 0:
            self.moving -= dt
            self.x += self.dir * s(40) * dt / 1000
            if self.x < s(15) or self.x > WIDTH - s(15):
                self.dir = -self.dir
                self.x = max(s(15), min(WIDTH - s(15), self.x))
        else:
            self.wait -= dt
            if self.wait <= 0:
                self.moving = random.uniform(500, 1600)
                self.wait = random.uniform(1200, 4500)
                if random.random() < 0.35:
                    self.dir = -self.dir

    def draw(self, surface, palette):
        shell = pygame.Color(palette.get("crab", palette["accent"]))
        dark = pygame.Color(palette.get("crab_dark", palette["text"]))
        k = s(self.SIZE)
        x, y = self.x, self.y
        walking = self.moving > 0
        snap = (not walking) and math.sin(self.time / 300) > 0.4
        pygame.draw.ellipse(surface, (0, 0, 0, 0) if False else dark.lerp(self.scene.color_at(palette, y), 0.6), (x - 9 * k, y - 1 * k, 18 * k, 3 * k))
        for side in (-1, 1):
            for n in range(3):
                step = math.sin(self.time / 60 + n * 2 + side) * 1.5 * k if walking else 0
                knee = (x + side * (5 + n * 1.5) * k, y - 4 * k + step * 0.3)
                foot = (x + side * (8 + n * 1.8) * k, y + step * 0.2)
                pygame.draw.lines(surface, dark, False, [(x + side * 3 * k, y - 3 * k), knee, foot], max(1, int(k)))
            lift = 3 * k if snap else 0
            arm = (x + side * 6 * k, y - 7 * k - lift)
            pygame.draw.line(surface, shell, (x + side * 3 * k, y - 4 * k), arm, max(1, int(k * 1.4)))
            pygame.draw.ellipse(surface, shell, (arm[0] - 2.2 * k, arm[1] - 2.5 * k, 4.4 * k, 3.6 * k))
            if snap and math.sin(self.time / 90) > 0:
                pygame.draw.line(surface, dark, (arm[0], arm[1] - k), (arm[0] + side * 2 * k, arm[1] - 2.5 * k), 1)
        body = pygame.Rect(0, 0, 13 * k, 7 * k)
        body.midbottom = (x, y - 1 * k)
        pygame.draw.ellipse(surface, shell, body)
        for side in (-1, 1):
            pygame.draw.line(surface, dark, (x + side * 2 * k, body.top + k), (x + side * 2.5 * k, body.top - 2 * k), 1)
            pygame.draw.circle(surface, dark, (x + side * 2.5 * k, body.top - 2 * k), max(1, k * 0.8))


class Octopus(Layer):
    # An octopus resting on a rock on the reef at the right: its arms curl and uncurl, its
    # mantle swells as it breathes, its eyes blink, and its colour slowly shifts, flushing
    # dark and fading pale again
    #
    # Palette colors it uses:
    #   "octopus" (a list of the colours it shifts between), "octopus_eye"

    SIZE = 1.3

    def __init__(self, scene, floor):
        super().__init__(scene)
        self.x = WIDTH - s(74)
        self.y = floor.floor_y(self.x) + s(28)
        self.time = 0

    def update(self, dt):
        self.time += dt

    def draw(self, surface, palette):
        colors = [pygame.Color(c) for c in palette.get("octopus", [palette["accent"]])]
        t = (self.time / 7000) % len(colors)
        color = colors[int(t)].lerp(colors[(int(t) + 1) % len(colors)], ease(t - int(t)))
        dark = color.lerp((0, 0, 0), 0.3)
        k = s(self.SIZE)
        x, y = self.x, self.y
        for n in range(8):
            base = (x + (n - 3.5) * 2.4 * k, y - 2 * k)
            spread = (n - 3.5) / 3.5
            curl = math.sin(self.time / 900 + n * 1.3)
            points = [base]
            angle = math.pi / 2 + spread * 1.2
            px, py = base
            for seg in range(6):
                angle += curl * 0.25 * (1 if spread >= 0 else -1)
                px += math.cos(angle) * 3 * k * (1 - seg * 0.08) * (1 if spread >= 0 else 1)
                py += math.sin(angle) * 1.6 * k
                px += spread * 2.2 * k
                points.append((px, py))
            pygame.draw.lines(surface, dark if n % 2 else color, False, points, max(1, int(k * 2.2 * 0.8)))
        breath = math.sin(self.time / 1100) * 0.8 * k
        mantle = pygame.Rect(0, 0, 13 * k + breath, 16 * k + breath)
        mantle.midbottom = (x + 2 * k, y - 1 * k)
        pygame.draw.ellipse(surface, color, mantle)
        pygame.draw.ellipse(surface, color.lerp((255, 255, 255), 0.18), (mantle.left + 2 * k, mantle.top + 2 * k, 5 * k, 6 * k))
        blink = math.sin(self.time / 2600) > 0.97
        eye = pygame.Color(palette.get("octopus_eye", palette["text"]))
        for side in (-1, 1):
            ex, ey = x + 2 * k + side * 3.5 * k, y - 4 * k
            if blink:
                pygame.draw.line(surface, dark, (ex - 1.5 * k, ey), (ex + 1.5 * k, ey), 1)
            else:
                pygame.draw.circle(surface, eye, (ex, ey), max(1, 1.6 * k))
                pygame.draw.line(surface, dark, (ex - k, ey), (ex + k, ey), 1)


class Jellyfish(Layer):
    # Jellyfish drifting slowly upward, their bells pulsing (each squeeze pushes them up),
    # trailing frilly tentacles that sway behind. At night they glow softly. When one reaches
    # the surface, another drifts up from below somewhere else
    #
    # Palette colors it uses:
    #   "jelly", "jelly_glow" (night only)

    COUNT = 2
    SIZE = 11

    def __init__(self, scene, plankton=None):
        super().__init__(scene)
        self.plankton = plankton
        self.time = 0
        self.jellies = [self.new_jelly(random.uniform(HEIGHT * 0.3, HEIGHT * 0.8)) for i in range(self.COUNT)]
        self.glow = None
        self.painted_palette = None

    def new_jelly(self, y=None):
        return {"x": self.scene.margin_x() if random.random() < 0.7 else random.uniform(0, WIDTH),
                "y": HEIGHT + s(20) if y is None else y, "phase": random.uniform(0, 6), "size": s(self.SIZE) * random.uniform(0.8, 1.2)}

    def update(self, dt):
        self.time += dt
        swell = self.scene.weather.get("surge", 0)
        for i, j in enumerate(self.jellies):
            pulse = max(0.0, math.sin(self.time / 600 + j["phase"]))
            j["y"] -= (s(4) + pulse * s(14)) * dt / 1000
            j["x"] += swell * s(6) * dt / 1000
            if self.plankton is not None and random.random() < dt / 200:
                self.plankton.stir(j["x"], j["y"] + j["size"], s(16))
            if j["y"] < s(SURFACE_Y) + s(20):
                self.jellies[i] = self.new_jelly()

    def draw(self, surface, palette):
        jelly = pygame.Color(palette.get("jelly", palette["text"]))
        glowing = "jelly_glow" in palette
        if glowing and self.painted_palette is not palette:
            c = pygame.Color(palette["jelly_glow"])
            self.glow = glow_sprite(s(24), (c.r * 0.45, c.g * 0.45, c.b * 0.45), 1.0, 8)
            self.painted_palette = palette
        for j in self.jellies:
            x, y, r = j["x"], j["y"], j["size"]
            show = self.scene.keep(x, 0.5)
            behind = self.scene.color_at(palette, y)
            color = behind.lerp(jelly, 0.75 * show)
            squeeze = max(0.0, math.sin(self.time / 600 + j["phase"]))
            if glowing:
                surface.blit(self.glow, self.glow.get_rect(center=(int(x), int(y))), special_flags=pygame.BLEND_RGB_ADD)
            for n in range(5):
                tx = x + (n - 2) * r * 0.32
                points = [(tx + math.sin(self.time / 500 + n + t * 4) * r * 0.25 * t, y + r * 0.3 + t * r * 2.4) for t in [m / 5 for m in range(6)]]
                pygame.draw.lines(surface, behind.lerp(jelly, 0.5 * show), False, points, 1)
            w = r * (2 - squeeze * 0.45)
            h = r * (1.2 + squeeze * 0.35)
            bell = [(x + math.cos(a) * w / 2, y - math.sin(a) * h) for a in [math.pi * m / 12 for m in range(13)]]
            pygame.draw.polygon(surface, color, bell)
            pygame.draw.lines(surface, behind.lerp(jelly.lerp((255, 255, 255), 0.4), 0.8 * show), False, bell, 1)


class SeaTurtle(Visitor):
    # A sea turtle gliding slowly across the open water, flippers sweeping, head out in front
    #
    # Palette colors it uses:
    #   "turtle", "turtle_shell", "turtle_dark"

    TIME = 16000

    def __init__(self, scene, plankton=None):
        super().__init__(scene)
        self.plankton = plankton

    def start(self):
        super().start()
        self.age = 0
        self.dir = random.choice((-1, 1))
        self.y = HEIGHT * random.uniform(0.2, 0.5)

    def update(self, dt):
        if not self.active:
            return
        self.age += dt
        if self.plankton is not None and random.random() < dt / 120:
            self.plankton.stir(*self.where(), s(26))
        if self.age > self.TIME:
            self.active = False

    def where(self):
        t = self.age / self.TIME
        x = -s(50) + (WIDTH + s(100)) * t if self.dir > 0 else WIDTH + s(50) - (WIDTH + s(100)) * t
        return x, self.y + math.sin(t * 5) * s(12)

    def draw(self, surface, palette):
        if not self.active:
            return
        x, y = self.where()
        f = self.dir
        skin = pygame.Color(palette.get("turtle", palette["muted"]))
        shell = pygame.Color(palette.get("turtle_shell", palette["muted"]))
        dark = pygame.Color(palette.get("turtle_dark", palette["text"]))
        show = self.scene.keep(x, 0.3)
        behind = self.scene.color_at(palette, y)
        skin, shell, dark = behind.lerp(skin, show), behind.lerp(shell, show), behind.lerp(dark, show)
        k = s(2.2)
        stroke = math.sin(self.age / 700)
        for back, sweep in ((False, stroke), (True, -stroke)):
            if back:
                flipper = [(x - f * 6 * k, y + 2 * k), (x - f * 12 * k, y + (5 + sweep * 2) * k), (x - f * 9 * k, y + 1 * k)]
            else:
                flipper = [(x + f * 4 * k, y + 1 * k), (x + f * 2 * k + f * sweep * 3 * k, y + (10 + sweep * 5) * k), (x + f * 9 * k, y + 2 * k)]
            pygame.draw.polygon(surface, skin, flipper)
        pygame.draw.circle(surface, skin, (x + f * 13 * k, y - 0.5 * k), 3 * k)
        pygame.draw.circle(surface, dark, (x + f * 14 * k, y - 1.2 * k), max(1, 0.6 * k))
        carapace = pygame.Rect(0, 0, 22 * k, 11 * k)
        carapace.center = (x, y - 1 * k)
        pygame.draw.ellipse(surface, shell, carapace)
        for u in (-0.25, 0.05, 0.35):
            pygame.draw.circle(surface, dark, (x + f * u * 22 * k * 0.6, y - 2.5 * k), 2.5 * k, 1)
        pygame.draw.ellipse(surface, dark, carapace, 1)


class MantaRay(Visitor):
    # A manta ray sweeping slowly across high up near the surface, its great wings rising and
    # falling, a dark diamond against the light
    #
    # Palette colors it uses:
    #   "manta"

    TIME = 12000

    def start(self):
        super().start()
        self.age = 0
        self.dir = random.choice((-1, 1))

    def update(self, dt):
        if not self.active:
            return
        self.age += dt
        if self.age > self.TIME:
            self.active = False

    def draw(self, surface, palette):
        if not self.active:
            return
        t = self.age / self.TIME
        x = -s(60) + (WIDTH + s(120)) * t if self.dir > 0 else WIDTH + s(60) - (WIDTH + s(120)) * t
        y = s(SURFACE_Y) + s(46) + math.sin(t * 4) * s(8)
        f = self.dir
        flap = math.sin(self.age / 650)
        k = s(2.2)
        behind = self.scene.color_at(palette, y)
        color = behind.lerp(pygame.Color(palette.get("manta", palette["text"])), 0.7 * self.scene.keep(x, 0.5))
        body = [(x + f * 9 * k, y), (x + f * 2 * k, y - 4 * k), (x - f * 2 * k, y - (14 + flap * 6) * k), (x - f * 6 * k, y - 2 * k),
                (x - f * 10 * k, y), (x - f * 6 * k, y + 2 * k), (x - f * 2 * k, y + (14 + flap * 6) * k * 0.5), (x + f * 2 * k, y + 3 * k)]
        pygame.draw.polygon(surface, color, body)
        pygame.draw.line(surface, color, (x - f * 10 * k, y), (x - f * 20 * k, y + 1 * k), 1)
        for side in (-1, 1):
            pygame.draw.line(surface, color, (x + f * 9 * k, y + side * 1.2 * k), (x + f * 11.5 * k, y + side * 2 * k), max(1, int(k * 0.6)))


class FarShark(Visitor):
    # A shark's shape gliding by far off in the blue, low and hazy, there and gone
    #
    # Palette colors it uses:
    #   "far_rock"                  its silhouette, faded with the distance

    TIME = 14000

    def __init__(self, scene, floor):
        super().__init__(scene)
        self.floor = floor

    def start(self):
        super().start()
        self.age = 0
        self.dir = random.choice((-1, 1))
        self.y = self.floor.floor_y(CENTER_X) - s(random.uniform(70, 120))

    def update(self, dt):
        if not self.active:
            return
        self.age += dt
        if self.age > self.TIME:
            self.active = False

    def draw(self, surface, palette):
        if not self.active:
            return
        t = self.age / self.TIME
        x = -s(40) + (WIDTH + s(80)) * t if self.dir > 0 else WIDTH + s(40) - (WIDTH + s(80)) * t
        y = self.y + math.sin(t * 3) * s(4)
        f = self.dir
        k = s(1.3)
        behind = self.scene.color_at(palette, y)
        color = behind.lerp(pygame.Color(palette.get("far_rock", palette["muted"])), 0.45 * min(1, math.sin(math.pi * t) * 3))
        sweep = math.sin(self.age / 300) * 2 * k
        body = [(x + f * 14 * k, y), (x + f * 6 * k, y - 3 * k), (x - f * 8 * k, y - 2 * k), (x - f * 14 * k, y + sweep * 0.3),
                (x - f * 8 * k, y + 2 * k), (x + f * 6 * k, y + 2.5 * k)]
        pygame.draw.polygon(surface, color, body)
        pygame.draw.polygon(surface, color, [(x + f * 2 * k, y - 2.5 * k), (x - f * 2 * k, y - 8 * k), (x - f * 3 * k, y - 2.2 * k)])
        pygame.draw.polygon(surface, color, [(x - f * 13 * k, y + sweep * 0.3), (x - f * 19 * k, y - 6 * k + sweep), (x - f * 17 * k, y + sweep * 0.3),
                                             (x - f * 19 * k, y + 5 * k + sweep)])


class WhaleShadow(Visitor):
    # A whale passing overhead: its huge shadow sliding slowly along the surface, dimming the
    # light rays as it goes over
    #
    # Palette colors it uses:
    #   "whale"                     the shadow

    TIME = 18000

    def start(self):
        super().start()
        self.age = 0
        self.dir = random.choice((-1, 1))

    def update(self, dt):
        if not self.active:
            return
        self.age += dt
        if self.age > self.TIME:
            self.active = False

    def draw(self, surface, palette):
        if not self.active:
            return
        t = self.age / self.TIME
        x = -s(160) + (WIDTH + s(320)) * t if self.dir > 0 else WIDTH + s(160) - (WIDTH + s(320)) * t
        y = s(SURFACE_Y) + s(10)
        f = self.dir
        k = s(3.2)
        shade = pygame.Surface((int(70 * k), int(22 * k)), pygame.SRCALPHA)
        c = pygame.Color(palette.get("whale", palette["text"]))
        a = int(255 * 0.35)
        cx, cy = shade.get_width() / 2, shade.get_height() / 2
        body = [(cx + f * 26 * k, cy), (cx + f * 18 * k, cy - 5 * k), (cx - f * 10 * k, cy - 4 * k), (cx - f * 24 * k, cy - 1 * k),
                (cx - f * 32 * k, cy - 6 * k), (cx - f * 30 * k, cy), (cx - f * 32 * k, cy + 6 * k), (cx - f * 24 * k, cy + 1 * k),
                (cx - f * 10 * k, cy + 4 * k), (cx + f * 18 * k, cy + 5 * k)]
        pygame.draw.polygon(shade, (c.r, c.g, c.b, a), body)
        pygame.draw.polygon(shade, (c.r, c.g, c.b, a), [(cx + f * 8 * k, cy + 3 * k), (cx - f * 2 * k, cy + 10 * k), (cx - f * 4 * k, cy + 3 * k)])
        surface.blit(shade, (x - cx, y - cy))


class TreasureChest(Visitor):
    # An old treasure chest half sunk in the sand at the right. Once in a while its lid
    # creaks open, a burst of bubbles escapes and gold glints inside; then it settles shut
    #
    # Palette colors it uses:
    #   "chest", "chest_band", "gold"

    TIME = 7000

    def __init__(self, scene, floor, bubbles):
        super().__init__(scene)
        self.bubbles = bubbles
        self.x = WIDTH - s(42)
        self.y = HEIGHT - s(70)
        self.age = 0
        self.time = 0

    def start(self):
        super().start()
        self.age = 0

    def update(self, dt):
        self.time += dt
        if not self.active:
            return
        before = self.age
        self.age += dt
        if before < 1500 <= self.age:
            for k in range(14):
                self.bubbles.bubbles.append({"x": self.x + random.uniform(-s(8), s(8)), "y": self.y - s(8) - random.uniform(0, s(10)),
                                             "r": s(random.uniform(1.4, 3.4)), "phase": random.uniform(0, 6), "speed": random.uniform(1.0, 1.6)})
        if self.age > self.TIME:
            self.active = False

    def lid(self):
        if not self.active:
            return 0.0
        a = self.age
        if a < 1500:
            return ease(a / 1500)
        if a < self.TIME - 1500:
            return 1.0
        return 1 - ease((a - self.TIME + 1500) / 1500)

    def draw(self, surface, palette):
        wood = pygame.Color(palette.get("chest", palette["muted"]))
        band = pygame.Color(palette.get("chest_band", palette["text"]))
        gold = pygame.Color(palette.get("gold", palette["accent"]))
        k = s(1.8)
        x, y = self.x, self.y
        box = pygame.Rect(0, 0, 24 * k, 12 * k)
        box.midbottom = (x, y)
        open_ = self.lid()
        if open_ > 0.05:
            pygame.draw.ellipse(surface, gold, (box.left + 2 * k, box.top - 3 * k, box.width - 4 * k, 6 * k))
            if math.sin(self.time / 160) > 0.3:
                pygame.draw.line(surface, gold.lerp((255, 255, 255), 0.7), (x + 3 * k, box.top - 3 * k), (x + 3 * k, box.top - 6 * k), 1)
        pygame.draw.rect(surface, wood, box)
        for u in (0.2, 0.8):
            pygame.draw.line(surface, band, (box.left + box.width * u, box.top), (box.left + box.width * u, box.bottom), max(1, int(k)))
        pygame.draw.rect(surface, band, box, 1)
        # The lid: shut, it sits on top; open, it swings back
        h = 7 * k * (1 - open_ * 0.6)
        lid = pygame.Rect(box.left, box.top - h - open_ * 5 * k, box.width, h)
        pygame.draw.ellipse(surface, wood.lerp((0, 0, 0), 0.15 * open_), lid.inflate(0, h * 0.4).move(0, h * 0.2))
        pygame.draw.rect(surface, band, (x - 1.5 * k, box.top - 1 * k, 3 * k, 3 * k))
        # Half sunk: sand heaped against its front
        sand = self.scene.color_at(palette, y)
        pygame.draw.ellipse(surface, pygame.Color(palette.get("sand", palette["muted"])), (box.left - 4 * k, y - 3 * k, box.width + 8 * k, 6 * k))
