# Life in the blossom garden. A regular: a little white-eye hopping about the blossom
# branch by day, shaking petals loose as it goes. Rare visitors, one at a time, every few
# minutes: a heron gliding in to stand in the pond's shallows and fish, a cat strolling
# across the bottom of the garden and sitting down for a moment, or (by day) a flock of
# birds bursting off the pagoda's roofs and wheeling away over the hills

import math

import random

import pygame

from partials.config import WIDTH, HEIGHT, s
from partials.backgrounds.base import Layer
from partials.backgrounds.brook_life import Visitor, draw_shadow


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


class WhiteEye(Layer):
    # A small olive-green bird with a white ring around its eye, perched among the blossoms
    # on the branch. Every second or two it hops to another cluster, flicking a few petals
    # loose; between hops it turns its head and bobs its tail. It sways with the branch.
    # Daytime only: needs "white_eye" in the palette
    #
    # Palette colors it uses:
    #   "white_eye", "white_eye_belly"      its back and its pale underside
    #   "branch"                            its beak and legs

    SIZE = 6                        # half its body length, pixels at the medium size
    STAY = (900, 2800)              # milliseconds between hops
    HOP_TIME = 280
    SHAKE = (1, 4)                  # petals a hop shakes loose

    def __init__(self, scene, branch, petals):
        super().__init__(scene)
        self.branch = branch
        self.petals = petals
        self.spot = random.randrange(len(branch.flowers))
        self.hop = None                                     # (from spot, to spot, age) while hopping
        self.wait = random.uniform(*self.STAY)
        self.facing = 1
        self.time = 0
        self.look = 0

    def update(self, dt):
        self.time += dt
        if self.hop is not None:
            start, end, age = self.hop
            age += dt
            if age >= self.HOP_TIME:
                self.spot, self.hop = end, None
                self.wait = random.uniform(*self.STAY)
                if random.random() < 0.5:
                    self.facing = -self.facing
                if "white_eye" in (self.palette or {}):
                    x, y = self.branch.flower_spots()[end]
                    for k in range(random.randint(*self.SHAKE)):
                        self.petals.falling.append(self.petals.new_petal(y + s(2), x + random.uniform(-s(4), s(4))))
            else:
                self.hop = (start, end, age)
            return
        self.wait -= dt
        if self.wait <= 0:
            spots = self.branch.flower_spots()
            here = spots[self.spot]
            near = sorted(range(len(spots)), key=lambda i: (spots[i][0] - here[0]) ** 2 + (spots[i][1] - here[1]) ** 2)
            end = random.choice(near[1:5])
            self.facing = 1 if spots[end][0] >= here[0] else -1
            self.hop = (self.spot, end, 0.0)
        if random.random() < dt / 700:
            self.look = random.choice((-1, 0, 1))

    palette = None

    def draw(self, surface, palette):
        self.palette = palette
        if "white_eye" not in palette:
            return
        spots = self.branch.flower_spots()
        if self.hop is not None:
            start, end, age = self.hop
            t = age / self.HOP_TIME
            (x0, y0), (x1, y1) = spots[start], spots[end]
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t - math.sin(math.pi * t) * s(8)
        else:
            x, y = spots[self.spot]
        size = s(self.SIZE)
        f = self.facing
        y -= size * 0.55                                    # sitting on top of the cluster
        back = pygame.Color(palette["white_eye"])
        belly = pygame.Color(palette.get("white_eye_belly", palette["white_eye"]))
        dark = pygame.Color(palette.get("branch", palette["text"]))
        bob = math.sin(self.time / 160) * 0.12 if self.hop is None else 0
        # Tail, body, belly, head, eye with its white ring, beak, and a wing when hopping
        pygame.draw.polygon(surface, back.lerp(dark, 0.3), [(x - f * size * 0.6, y), (x - f * size * 1.45, y + size * (0.25 + bob)),
                                                             (x - f * size * 1.35, y + size * (0.55 + bob))])
        body = pygame.Rect(0, 0, size * 1.7, size * 1.05)
        body.center = (x, y)
        pygame.draw.ellipse(surface, back, body)
        pygame.draw.ellipse(surface, belly, (body.x + size * 0.2, body.centery, size * 1.2, size * 0.5))
        head = (x + f * size * 0.75, y - size * 0.35)
        pygame.draw.circle(surface, back, head, size * 0.5)
        eye = (head[0] + f * size * (0.15 + 0.08 * self.look), head[1] - size * 0.05)
        pygame.draw.circle(surface, (255, 255, 255), eye, max(1.5, size * 0.22))
        pygame.draw.circle(surface, dark, eye, max(1, size * 0.11))
        pygame.draw.line(surface, dark, (head[0] + f * size * 0.42, head[1]), (head[0] + f * size * 0.8, head[1] + size * 0.08), max(1, s(1)))
        if self.hop is not None:
            flap = math.sin(self.hop[2] / 30)
            pygame.draw.polygon(surface, back.lerp(dark, 0.2), [(x - f * size * 0.2, y - size * 0.2), (x - f * size * 0.6, y - size * (0.6 + 0.4 * flap)),
                                                                (x + f * size * 0.3, y - size * 0.3)])
        else:
            for k in (-0.2, 0.15):
                pygame.draw.line(surface, dark, (x + k * size, y + size * 0.45), (x + k * size, y + size * 0.75), 1)


class Heron(Visitor):
    # A grey heron gliding in over the garden on wide slow wings, landing in the shallows at
    # the pond's edge and standing there, very still, neck folded. Now and then it straightens
    # and stabs at the water (a ring spreads), and after a while it takes off and flies away
    #
    # Palette colors it uses:
    #   "heron", "heron_dark", "heron_light", "heron_beak"

    SIZE = 1.7                      # how big, as a share of its drawing's own pixels at the medium size
    FLY_TIME = 3200
    STAND = (22000, 40000)
    STRIKE_EVERY = (5000, 11000)
    STRIKE_TIME = 700
    SPOT = (-0.12, 0.9)             # where in the pond it stands: direction from the middle, share to the edge

    def __init__(self, scene, pond, on_ring):
        super().__init__(scene)
        self.pond = pond
        self.on_ring = on_ring

    def start(self):
        super().start()
        self.spot = self.pond.point(*self.SPOT)
        self.state, self.age = "in", 0.0
        self.stand = random.uniform(*self.STAND)
        self.strike_wait = random.uniform(*self.STRIKE_EVERY)
        self.strike = None
        self.time = 0
        self.come = (WIDTH + s(40), s(30))
        self.go = (-s(50), s(20))

    def update(self, dt):
        if not self.active:
            return
        self.time += dt
        self.age += dt
        if self.state == "in" and self.age >= self.FLY_TIME:
            self.state, self.age = "stand", 0.0
            self.on_ring(self.spot[0], self.spot[1])
        elif self.state == "stand":
            if self.strike is None:
                self.strike_wait -= dt
                if self.strike_wait <= 0:
                    self.strike = 0.0
            else:
                before = self.strike
                self.strike += dt
                if before < self.STRIKE_TIME / 2 <= self.strike:
                    self.on_ring(self.spot[0] - self.scale() * 14, self.spot[1] + self.scale() * 1)
                if self.strike > self.STRIKE_TIME:
                    self.strike = None
                    self.strike_wait = random.uniform(*self.STRIKE_EVERY)
            if self.age >= self.stand and self.strike is None:
                self.state, self.age = "out", 0.0
        elif self.state == "out" and self.age >= self.FLY_TIME * 1.3:
            self.active = False

    def scale(self):
        return s(self.SIZE) * self.scene.view.scale(self.spot[1])

    def colors(self, palette):
        return (pygame.Color(palette.get("heron", palette["muted"])), pygame.Color(palette.get("heron_dark", palette["text"])),
                pygame.Color(palette.get("heron_light", palette["muted"])), pygame.Color(palette.get("heron_beak", palette["accent"])))

    def draw_standing(self, surface, palette, x, y, k):
        grey, dark, light, beak = self.colors(palette)
        reach = 0.0
        if self.strike is not None:
            reach = math.sin(math.pi * min(1, self.strike / self.STRIKE_TIME))
        # Legs into the water, with its feet's reflection broken by the surface
        for dx in (-1.2, 1.2):
            pygame.draw.line(surface, dark, (x + dx * k, y), (x + dx * k * 0.6, y - 14 * k), max(1, int(k * 1.1)))
        pygame.draw.ellipse(surface, dark.lerp(self.pond.water_color(palette, y), 0.6), (x - 5 * k, y - 1.2 * k, 10 * k, 2.4 * k), 1)
        # Body, tilted, with darker wing edge
        body = [(x - 7 * k, y - 21 * k), (x - 2 * k, y - 25 * k), (x + 7 * k, y - 22 * k), (x + 12 * k, y - 15 * k), (x + 4 * k, y - 13 * k), (x - 5 * k, y - 15 * k)]
        pygame.draw.polygon(surface, grey, body)
        pygame.draw.lines(surface, dark, False, [(x - 3 * k, y - 22 * k), (x + 6 * k, y - 19 * k), (x + 12 * k, y - 15 * k)], max(1, int(k * 1.2)))
        # Neck: folded in an S while it waits, straight out and down when it strikes
        rest = [(x - 6 * k, y - 21 * k), (x - 9 * k, y - 26 * k), (x - 6 * k, y - 31 * k), (x - 8 * k, y - 35 * k)]
        stab = [(x - 6 * k, y - 21 * k), (x - 10 * k, y - 17 * k), (x - 13 * k, y - 11 * k), (x - 15 * k, y - 6 * k)]
        neck = [(a[0] + (b[0] - a[0]) * reach, a[1] + (b[1] - a[1]) * reach) for a, b in zip(rest, stab)]
        pygame.draw.lines(surface, light, False, neck, max(2, int(k * 2.6)))
        hx, hy = neck[-1]
        direction = (-1, 0.15 + 0.9 * reach)
        length = math.hypot(*direction)
        dx, dy = direction[0] / length, direction[1] / length
        pygame.draw.circle(surface, light, (hx, hy), max(1.5, k * 2))
        pygame.draw.line(surface, beak, (hx + dx * k, hy + dy * k), (hx + dx * 8 * k, hy + dy * 8 * k), max(1, int(k * 1.2)))
        pygame.draw.line(surface, dark, (hx, hy - k), (hx + 6 * k, hy + 1 * k), 1)            # its black plume
        pygame.draw.circle(surface, dark, (hx - 0.6 * k, hy - 0.5 * k), max(1, k * 0.5))

    def draw_flying(self, surface, palette, x, y, k, heading):
        grey, dark, light, beak = self.colors(palette)
        flap = math.sin(self.time / 260)
        f = 1 if heading > 0 else -1
        # Wings: wide and slow, darker at the tips
        for side in (-1, 1):
            tip = (x + side * 4 * k, y - 18 * k * flap - 4 * k)
            wing = [(x - 6 * k, y), (x + 6 * k, y), tip]
            pygame.draw.polygon(surface, grey if side > 0 else grey.lerp(dark, 0.2), wing)
            pygame.draw.line(surface, dark, wing[0], tip, 1)
        pygame.draw.ellipse(surface, grey, (x - 9 * k, y - 2.5 * k, 18 * k, 5 * k))
        pygame.draw.circle(surface, light, (x + f * 9 * k, y - 1 * k), max(1.5, k * 2.2))           # neck tucked in
        pygame.draw.line(surface, beak, (x + f * 10 * k, y - 1 * k), (x + f * 16 * k, y), max(1, int(k)))
        pygame.draw.line(surface, dark, (x - f * 8 * k, y + k), (x - f * 18 * k, y + 2 * k), max(1, int(k)))   # legs trailing

    def draw(self, surface, palette):
        if not self.active:
            return
        k = self.scale()
        x, y = self.spot
        if self.state == "stand":
            self.draw_standing(surface, palette, x, y, k)
            return
        t = self.age / (self.FLY_TIME * (1.3 if self.state == "out" else 1))
        if self.state == "in":
            (x0, y0), (x1, y1), t = self.come, (x, y - 14 * k), ease(t)
            far = 1 - t
        else:
            (x0, y0), (x1, y1), t = (x, y - 14 * k), self.go, t * t
            far = t
        fx, fy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        size = k * (1 - 0.45 * far)
        if self.state == "in" and t > 0.9:
            self.draw_standing(surface, palette, x, y, k)
            return
        draw_shadow(surface, fx, y + (fy - y) * 0.15, 20 * size, 4 * size, 0.12 * (1 - far))
        self.draw_flying(surface, palette, fx, fy, size, x1 - x0)


class Cat(Visitor):
    # A cat strolling across the bottom of the garden, tail up. Partway across it stops,
    # sits down, looks about (at night its eyes catch the light), then gets up and strolls
    # on out of sight
    #
    # Palette colors it uses:
    #   "cat", "cat_dark", "cat_light"      its coat, its stripes and outline, its muzzle and chest
    #   "cat_eye"                           its eyes, shining at night (optional)

    SIZE = 1.5
    SPEED = 30
    SIT = (4000, 8000)
    Y = 26                          # how far above the bottom of the window it walks, pixels at the medium size

    def start(self):
        super().start()
        self.facing = random.choice((-1, 1))
        self.y = HEIGHT - s(self.Y)
        self.x = -s(30) if self.facing > 0 else WIDTH + s(30)
        self.sit_x = self.scene.margin_x()
        if (self.sit_x - self.x) * self.facing < s(40):
            self.sit_x = WIDTH - self.sit_x
        self.state = "walk"
        self.sit = random.uniform(*self.SIT)
        self.stride = 0.0
        self.time = 0
        self.sat = 0.0                                      # 0 standing, 1 sitting
        self.look = 0.0

    def update(self, dt):
        if not self.active:
            return
        self.time += dt
        if self.state == "walk":
            self.x += self.facing * s(self.SPEED) * dt / 1000
            self.stride += dt
            if self.sit is not None and (self.x - self.sit_x) * self.facing >= 0:
                self.state = "sit"
            if not (-s(40) < self.x < WIDTH + s(40)):
                self.active = False
        else:
            self.sat = min(1.0, self.sat + dt / 500)
            self.sit -= dt
            self.look = math.sin(self.time / 900) if self.sat >= 1 else 0
            if self.sit <= 0:
                self.sat = max(0.0, self.sat - dt / 300)
                if self.sat <= 0:
                    self.state, self.sit = "walk", None

    def draw(self, surface, palette):
        if not self.active:
            return
        coat = pygame.Color(palette.get("cat", palette["muted"]))
        dark = pygame.Color(palette.get("cat_dark", palette["text"]))
        light = pygame.Color(palette.get("cat_light", palette["muted"]))
        k = s(self.SIZE) * self.scene.view.scale(self.y)
        f, x, y = self.facing, self.x, self.y
        sat = ease(self.sat)
        walking = self.state == "walk"
        draw_shadow(surface, x, y, 26 * k, 5 * k, 0.25)
        # Body: long and level when walking, rear dropping to the ground when sitting
        hip = (x - f * 8 * k, y - 10 * k + sat * 6 * k)
        shoulder = (x + f * 6 * k, y - 11 * k - sat * 3 * k)
        # Tail: up and curling when walking, wrapped along the ground when sitting
        sway = math.sin(self.time / 400) * 2 * k
        up = [hip, (hip[0] - f * 4 * k, hip[1] - 6 * k), (hip[0] - f * 3 * k + sway, hip[1] - 13 * k), (hip[0] + sway * 0.5, hip[1] - 16 * k)]
        down = [hip, (hip[0] - f * 4 * k, y - 1 * k), (hip[0] + f * 3 * k, y), (hip[0] + f * 9 * k + sway * 0.3, y - 1 * k)]
        tail = [(a[0] + (b[0] - a[0]) * sat, a[1] + (b[1] - a[1]) * sat) for a, b in zip(up, down)]
        pygame.draw.lines(surface, coat, False, tail, max(2, int(k * 2.6)))
        # Legs
        for n, (along, front) in enumerate(((-7, False), (-5, False), (5, True), (7, True))):
            swing = math.sin(self.stride / 140 + n * math.pi / 2) * 3 * k if walking else 0
            top = (x + f * along * k, y - 8 * k)
            foot = (x + f * along * k + swing, y)
            if not front:
                foot = (foot[0] + (hip[0] + f * 3 * k - foot[0]) * sat, foot[1])
                top = (top[0] + (hip[0] - top[0]) * sat, top[1] + (y - 4 * k - top[1]) * sat)
            pygame.draw.line(surface, dark if n % 2 else coat, top, foot, max(1, int(k * 2.2)))
        pygame.draw.line(surface, coat, hip, shoulder, max(3, int(k * 8)))
        pygame.draw.circle(surface, coat, hip, k * 4.5 + sat * k * 1.5)
        pygame.draw.circle(surface, light, (shoulder[0] + f * 1.5 * k, shoulder[1] + 2 * k), k * 3)
        for n in range(3):
            sx = hip[0] + (shoulder[0] - hip[0]) * (0.3 + n * 0.2)
            sy = hip[1] + (shoulder[1] - hip[1]) * (0.3 + n * 0.2)
            pygame.draw.line(surface, dark, (sx, sy - 3.5 * k), (sx + f * k, sy - 1 * k), 1)
        # Head, ears, eyes
        hx, hy = shoulder[0] + f * 5 * k, shoulder[1] - 4 * k - sat * 2 * k
        turn = self.look * 1.5 * k
        pygame.draw.circle(surface, coat, (hx, hy), k * 4)
        for side in (-1, 1):
            ex = hx + side * 2.2 * k + turn * 0.5
            pygame.draw.polygon(surface, coat, [(ex - 1.6 * k, hy - 2.5 * k), (ex + 1.6 * k, hy - 2.5 * k), (ex + side * 0.4 * k, hy - 6.5 * k)])
        pygame.draw.circle(surface, light, (hx + f * 2.2 * k + turn, hy + 1.3 * k), k * 1.8)
        eye = pygame.Color(palette["cat_eye"]) if "cat_eye" in palette else dark
        for side in (-1, 1):
            pygame.draw.circle(surface, eye, (hx + f * 1.4 * k + side * 1.3 * k + turn, hy - 0.4 * k), max(1, k * 0.8))


class RoofBirds(Visitor):
    # A flock of small birds bursting off the pagoda's roofs all at once, as if startled by
    # its bell, and wheeling away over the hills, flapping and getting smaller until they're
    # gone. Daytime only
    #
    # Palette colors it uses:
    #   "roof_bird"             the birds

    COUNT = 8
    LIFE = 9000
    SPEED = 34

    def __init__(self, scene, pagoda):
        super().__init__(scene)
        self.pagoda = pagoda

    def can_come(self, palette):
        return "roof_bird" in palette

    def start(self):
        super().start()
        self.age = 0
        self.birds = []
        for i in range(self.COUNT):
            height = random.uniform(0.15, 0.75)
            self.birds.append({"x": self.pagoda.x + random.uniform(-s(14), s(14)),
                               "y": self.pagoda.base - s(70) * height,
                               "vx": -s(self.SPEED) * random.uniform(0.7, 1.2), "vy": -s(self.SPEED) * random.uniform(0.3, 0.7),
                               "phase": random.uniform(0, 2 * math.pi), "delay": random.uniform(0, 500),
                               "curve": random.uniform(-0.25, 0.1)})

    def update(self, dt):
        if not self.active:
            return
        self.age += dt
        seconds = dt / 1000
        for bird in self.birds:
            if self.age < bird["delay"]:
                continue
            # They wheel: their course bends slowly as they fly, and they slow into the distance
            angle = bird["curve"] * seconds
            vx, vy = bird["vx"], bird["vy"]
            bird["vx"], bird["vy"] = vx * math.cos(angle) - vy * math.sin(angle), vx * math.sin(angle) + vy * math.cos(angle)
            bird["vy"] += s(6) * seconds                    # leveling off
            slow = 1 - 0.6 * min(1, self.age / self.LIFE)
            bird["x"] += bird["vx"] * slow * seconds
            bird["y"] += bird["vy"] * slow * seconds
        if self.age > self.LIFE:
            self.active = False

    def draw(self, surface, palette):
        if not self.active or "roof_bird" not in palette:
            return
        color = pygame.Color(palette["roof_bird"])
        far = min(1, self.age / self.LIFE)
        size = s(4.5) * (1 - 0.6 * far)
        for bird in self.birds:
            if self.age < bird["delay"]:
                continue
            behind = self.scene.color_at(palette, bird["y"])
            fade = 1 - max(0, (far - 0.75) / 0.25)
            shade = behind.lerp(color, fade * self.scene.keep(bird["x"], 0.4))
            flap = math.sin(self.age / 70 + bird["phase"])
            x, y = bird["x"], bird["y"]
            pygame.draw.lines(surface, shade, False, [(x - size, y - size * 0.6 * flap), (x, y), (x + size, y - size * 0.6 * flap)],
                              max(1, s(1.3)))
