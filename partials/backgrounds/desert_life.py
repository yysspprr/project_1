# Life in the desert. Regulars: a lizard darting about the sand and stopping to bask, and a
# scarab rolling its ball along (by day); jerboas hopping about (by night). Rare visitors,
# one at a time: a hawk gliding over with its shadow sweeping across the sand (by day), a
# fennec fox trotting along a dune crest to sit and listen (by night), a camel caravan
# crossing a far ridge, or a mirage of water shimmering on the horizon (by day)

import math

import random

import pygame

from partials.config import WIDTH, HEIGHT, s
from partials.backgrounds.base import Layer
from partials.backgrounds.helpers import Timer
from partials.backgrounds.brook_life import Visitor, draw_shadow


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def ground_spot(scene, low=0.62, high=0.92):
    # Somewhere on the near sand, out at the sides where it won't sit behind the text
    x = scene.margin_x()
    x = max(s(18), min(WIDTH - s(18), x))
    return x, HEIGHT * random.uniform(low, high)


class Lizard(Layer):
    # A lizard on the near sand: it sits basking, doing little push-ups now and then, then
    # darts off in a quick dash to another spot, its tail swishing. Sometimes it dashes away
    # out of sight and another turns up a while later. Daytime only: needs "lizard"
    #
    # Palette colors it uses:
    #   "lizard", "lizard_dark"

    SIZE = 11                       # half its body length, pixels at the medium size up close
    BASK = (1500, 5000)
    DASH_TIME = (260, 420)
    AWAY = (6000, 15000)            # milliseconds before another turns up after one leaves

    def __init__(self, scene):
        super().__init__(scene)
        self.time = 0
        self.arrive()

    def arrive(self):
        x, y = ground_spot(self.scene)
        self.x, self.y = x, y
        self.heading = random.uniform(0, 2 * math.pi)
        self.state, self.wait = "bask", random.uniform(*self.BASK)
        self.dash = None

    def update(self, dt):
        self.time += dt
        if self.state == "away":
            self.wait -= dt
            if self.wait <= 0:
                self.arrive()
            return
        if self.state == "bask":
            self.wait -= dt
            if self.wait <= 0:
                leaving = random.random() < 0.15
                if leaving:
                    tx = -s(30) if self.x < WIDTH / 2 else WIDTH + s(30)
                    ty = self.y + random.uniform(-s(20), s(20))
                else:
                    for attempt in range(10):
                        angle = random.uniform(0, 2 * math.pi)
                        reach = s(random.uniform(40, 90))
                        tx, ty = self.x + math.cos(angle) * reach, self.y + math.sin(angle) * reach * 0.5
                        if self.scene.keep(tx) > 0.9 and HEIGHT * 0.58 < ty < HEIGHT * 0.95:
                            break
                    else:
                        tx, ty = ground_spot(self.scene)
                self.dash = {"from": (self.x, self.y), "to": (tx, ty), "age": 0.0, "time": random.uniform(*self.DASH_TIME), "leaving": leaving}
                self.heading = math.atan2(ty - self.y, tx - self.x)
                self.state = "dash"
        else:
            d = self.dash
            d["age"] += dt
            t = ease(d["age"] / d["time"])
            self.x = d["from"][0] + (d["to"][0] - d["from"][0]) * t
            self.y = d["from"][1] + (d["to"][1] - d["from"][1]) * t
            if d["age"] >= d["time"]:
                if d["leaving"]:
                    self.state, self.wait = "away", random.uniform(*self.AWAY)
                else:
                    self.state, self.wait = "bask", random.uniform(*self.BASK)

    def draw(self, surface, palette):
        if "lizard" not in palette or self.state == "away":
            return
        body = pygame.Color(palette["lizard"])
        dark = pygame.Color(palette.get("lizard_dark", palette["text"]))
        k = s(self.SIZE) * self.scene.view.scale(self.y) / s(6)
        squash = 0.55
        cos, sin = math.cos(self.heading), math.sin(self.heading)
        running = self.state == "dash"
        wiggle = math.sin(self.time / 40) * 0.5 if running else math.sin(self.time / 900) * 0.15
        push = max(0, math.sin(self.time / 180)) * 1.5 * k if not running and math.sin(self.time / 2300) > 0.6 else 0

        def at(u, v):
            # Along the body (u, toward the head) and across it (v), laid on the ground
            v += math.sin(u * 0.35 + wiggle * 3) * wiggle * 2
            return (self.x + (u * cos - v * sin) * k, self.y + (u * sin + v * cos) * k * squash - push * (u > 2))

        draw_shadow(surface, self.x, self.y + 2 * k * squash, 26 * k, 5 * k, 0.2)
        # Tail, legs, body, head
        tail = [at(-4 - n * 2.4, 0) for n in range(6)]
        pygame.draw.lines(surface, body, False, [at(-3, 0)] + tail, max(1, int(k * 1.6)))
        for u, side in ((3, 1), (3, -1), (-2.5, 1), (-2.5, -1)):
            step = math.sin(self.time / 35 + u + side) * 1.8 if running else 0
            knee = at(u + step * 0.5, side * 3)
            foot = at(u + (1.5 if u > 0 else -1.5) + step, side * 4.2)
            pygame.draw.lines(surface, dark, False, [at(u, side * 1.2), knee, foot], max(1, int(k)))
        points = [at(u, v) for u, v in ((6.5, 0), (5, 1.6), (2, 2.2), (-2, 2), (-4, 1.1), (-4.5, 0), (-4, -1.1), (-2, -2), (2, -2.2), (5, -1.6))]
        pygame.draw.polygon(surface, body, points)
        pygame.draw.lines(surface, dark, True, points, 1)
        for u in (-2, 0, 2):
            pygame.draw.circle(surface, dark, at(u, 0), max(1, k * 0.5))
        for side in (1, -1):
            pygame.draw.circle(surface, dark, at(5, side * 1.1), max(1, k * 0.45))


class Scarab(Layer):
    # A dung beetle rolling its ball across the near sand, walking backwards and pushing
    # with its hind legs, the ball turning as it goes. When it's gone off one side, another
    # sets off a while later. Daytime only: needs "scarab"
    #
    # Palette colors it uses:
    #   "scarab", "scarab_ball"

    SPEED = 9                       # pixels per second
    BALL = 4.5
    WAIT = (8000, 20000)

    def __init__(self, scene):
        super().__init__(scene)
        self.time = 0
        self.timer = Timer(self.WAIT)
        self.timer.left = random.uniform(1000, 6000)
        self.bug = None

    def update(self, dt):
        self.time += dt
        if self.bug is None:
            if self.timer.tick(dt):
                direction = random.choice((-1, 1))
                y = HEIGHT * random.uniform(0.86, 0.96)
                self.bug = {"x": -s(10) if direction > 0 else WIDTH + s(10), "y": y, "dir": direction, "roll": 0.0}
            return
        bug = self.bug
        speed = s(self.SPEED) * (0.6 + 0.4 * math.sin(self.time / 500) ** 2)          # it pushes in heaves
        bug["x"] += bug["dir"] * speed * dt / 1000
        bug["roll"] += speed * dt / 1000 / s(self.BALL)
        if not (-s(20) < bug["x"] < WIDTH + s(20)):
            self.bug = None

    def draw(self, surface, palette):
        if self.bug is None or "scarab" not in palette:
            return
        bug = self.bug
        beetle = pygame.Color(palette["scarab"])
        ball_color = pygame.Color(palette.get("scarab_ball", palette["muted"]))
        r = s(self.BALL)
        bx, by = bug["x"] + bug["dir"] * r * 1.1, bug["y"] - r
        draw_shadow(surface, bx, bug["y"], r * 2.6, r * 0.8, 0.22)
        pygame.draw.circle(surface, ball_color, (bx, by), r)
        for k in range(3):
            a = bug["roll"] * bug["dir"] + k * 2.1
            pygame.draw.circle(surface, ball_color.lerp((0, 0, 0), 0.2), (bx + math.cos(a) * r * 0.55, by + math.sin(a) * r * 0.55), max(1, r * 0.18))
        # The beetle: head down, back legs up on the ball
        x, y = bug["x"] - bug["dir"] * r * 0.2, bug["y"] - r * 0.45
        pygame.draw.ellipse(surface, beetle, (x - r * 0.75, y - r * 0.45, r * 1.5, r * 0.9))
        pygame.draw.line(surface, beetle, (x + bug["dir"] * r * 0.4, y - r * 0.2), (bx - bug["dir"] * r * 0.8, by - r * 0.1), 1)
        step = math.sin(self.time / 120) * r * 0.3
        for k in (-0.4, 0.2):
            pygame.draw.line(surface, beetle, (x + k * r, y + r * 0.3), (x + k * r + step, bug["y"]), 1)


class Jerboas(Layer):
    # A couple of jerboas out on the sand at night: tiny, with long hind legs and a long
    # tufted tail, they sit still, then bound off in a few long hops, stop, and sit again.
    # Night only: needs "jerboa"
    #
    # Palette colors it uses:
    #   "jerboa", "jerboa_light"

    COUNT = 2
    SIZE = 5.5
    SIT = (1500, 5000)
    HOP_TIME = 260
    HOPS = (2, 5)
    HOP = 22                        # how far one hop goes, pixels at the medium size

    def __init__(self, scene):
        super().__init__(scene)
        self.time = 0
        self.critters = []
        for i in range(self.COUNT):
            x, y = ground_spot(scene, 0.6, 0.94)
            self.critters.append({"x": x, "y": y, "dir": random.choice((-1, 1)), "wait": random.uniform(*self.SIT),
                                  "hops": 0, "hop": None})

    def update(self, dt):
        self.time += dt
        for c in self.critters:
            if c["hop"] is not None:
                c["hop"] += dt
                c["x"] += c["dir"] * s(self.HOP) * self.scene.view.scale(c["y"]) * dt / self.HOP_TIME
                if c["hop"] >= self.HOP_TIME:
                    c["hops"] -= 1
                    c["hop"] = 0.0 if c["hops"] > 0 else None
                    if c["hop"] is None:
                        c["wait"] = random.uniform(*self.SIT)
                continue
            c["wait"] -= dt
            if c["wait"] <= 0:
                # Off it goes, turning back before it leaves the margins
                c["dir"] = random.choice((-1, 1))
                if self.scene.keep(c["x"] + c["dir"] * s(60)) < 0.9 or not (s(10) < c["x"] + c["dir"] * s(60) < WIDTH - s(10)):
                    c["dir"] = -c["dir"]
                c["hops"] = random.randint(*self.HOPS)
                c["hop"] = 0.0

    def draw(self, surface, palette):
        if "jerboa" not in palette:
            return
        fur = pygame.Color(palette["jerboa"])
        light = pygame.Color(palette.get("jerboa_light", palette["jerboa"]))
        for c in self.critters:
            k = s(self.SIZE) * self.scene.view.scale(c["y"])
            up = math.sin(math.pi * c["hop"] / self.HOP_TIME) * k * 3 if c["hop"] is not None else 0
            x, y, f = c["x"], c["y"] - up, c["dir"]
            draw_shadow(surface, c["x"], c["y"], k * 3.2, k * 0.8, 0.2)
            tail = [(x - f * k, y - k * 0.6), (x - f * k * 3, y - k * 0.4), (x - f * k * 4.5, y - k * 1.0)]
            pygame.draw.lines(surface, fur, False, tail, 1)
            pygame.draw.circle(surface, light, tail[-1], max(1, k * 0.35))
            pygame.draw.ellipse(surface, fur, (x - k, y - k * 1.6, k * 2, k * 1.4))
            pygame.draw.circle(surface, fur, (x + f * k * 0.9, y - k * 1.6), k * 0.6)
            pygame.draw.line(surface, fur, (x + f * k * 0.8, y - k * 2), (x + f * k * 0.6, y - k * 2.8), 1)    # an ear
            legs = (x - f * k * 0.4, y) if c["hop"] is None else (x - f * k * 1.4, y + up * 0.3)
            pygame.draw.line(surface, fur, (x - f * k * 0.3, y - k * 0.4), legs, 1)


class Hawk(Visitor):
    # A hawk gliding across high over the desert on still wings, banking a little, with its
    # shadow sweeping across the sand far below (the sun being high, the shadow runs along
    # the ground under it). Daytime only
    #
    # Palette colors it uses:
    #   "hawk"

    TIME = 9000
    SIZE = 7

    def can_come(self, palette):
        return "hawk" in palette

    def start(self):
        super().start()
        self.age = 0
        self.dir = random.choice((-1, 1))
        self.y = random.uniform(0.2, 0.5) * self.scene.view.horizon
        self.shadow_y = HEIGHT * random.uniform(0.55, 0.8)

    def update(self, dt):
        if not self.active:
            return
        self.age += dt
        if self.age > self.TIME:
            self.active = False

    def draw(self, surface, palette):
        if not self.active or "hawk" not in palette:
            return
        t = self.age / self.TIME
        x = -s(30) + (WIDTH + s(60)) * t if self.dir > 0 else WIDTH + s(30) - (WIDTH + s(60)) * t
        y = self.y + math.sin(t * 6) * s(5)
        k = s(self.SIZE)
        bank = math.sin(t * 6) * 0.3
        color = self.scene.color_at(palette, y).lerp(pygame.Color(palette["hawk"]), 0.85 * self.scene.keep(x, 0.5))
        wing = [(x - k * 2.6, y + k * (0.3 + bank)), (x - k * 0.8, y - k * 0.4), (x, y), (x + k * 0.8, y - k * 0.4), (x + k * 2.6, y + k * (0.3 - bank))]
        pygame.draw.lines(surface, color, False, wing, max(1, s(2)))
        pygame.draw.polygon(surface, color, [(x - k * 0.4, y), (x + k * 0.4, y), (x + self.dir * k * 0.1, y + k * 0.9)])
        # Its shadow, racing over the sand below, stretched by the slant of the ground
        sx = x + self.dir * s(40)
        shade = pygame.Surface((int(k * 7), int(k * 2.2)), pygame.SRCALPHA)
        a = int(255 * palette.get("shadow", 0.3) * 0.45)
        pygame.draw.polygon(shade, (0, 0, 0, a), [(0, k * 1.3), (k * 3.5, k * 0.2), (k * 7, k * 1.3), (k * 3.5, k * 2.2)])
        surface.blit(shade, (sx - k * 3.5, self.shadow_y - k * 1.1))


class Fennec(Visitor):
    # A fennec fox at night: it trots in along a dune crest from the side of the window to
    # the nearest peak, sits there with its huge ears up, turning its head to listen, then
    # trots back the way it came. Night only
    #
    # Palette colors it uses:
    #   "fennec", "fennec_light", "fennec_dark"

    SIZE = 1.6
    SPEED = 30
    SIT = (6000, 10000)

    def __init__(self, scene, dunes):
        super().__init__(scene)
        self.dunes = dunes

    def can_come(self, palette):
        return "fennec" in palette

    def start(self):
        super().start()
        self.rank = self.dunes.ranks[4]
        # Its lookout: the highest point of the crest out in one of the margins
        side = random.choice((-1, 1))
        spots = [x for x in range(s(8), WIDTH - s(8), 2) if self.scene.keep(x) > 0.85 and (x < WIDTH / 2) == (side < 0)]
        if not spots:
            self.active = False
            return
        self.goal = max(spots, key=lambda x: self.dunes.crest(self.rank, x))
        self.home = -s(30) if self.goal < WIDTH / 2 else WIDTH + s(30)
        self.x = self.home
        self.facing = 1 if self.goal > self.home else -1
        self.state = "in"
        self.sit = random.uniform(*self.SIT)
        self.time = 0
        self.look = 0.0

    def ground(self, x):
        return self.rank["base"] - self.dunes.crest(self.rank, x)

    def update(self, dt):
        if not self.active:
            return
        self.time += dt
        step = s(self.SPEED) * dt / 1000
        if self.state == "in":
            self.x += self.facing * step
            if (self.x - self.goal) * self.facing >= 0:
                self.state = "sit"
        elif self.state == "sit":
            self.sit -= dt
            self.look = math.sin(self.time / 1100)
            if self.sit <= 0:
                self.facing = -self.facing
                self.state = "out"
        else:
            self.x += self.facing * step
            if (self.x - self.home) * self.facing >= 0:
                self.active = False

    def draw(self, surface, palette):
        if not self.active or "fennec" not in palette:
            return
        fur = pygame.Color(palette["fennec"])
        light = pygame.Color(palette.get("fennec_light", palette["fennec"]))
        dark = pygame.Color(palette.get("fennec_dark", palette["text"]))
        k = s(self.SIZE)
        f, x = self.facing, self.x
        y = self.ground(x)
        sitting = self.state == "sit"
        trot = math.sin(self.time / 110)
        # Tail, legs, body, head with its enormous ears
        pygame.draw.lines(surface, fur, False, [(x - f * 5 * k, y - 5 * k), (x - f * 9 * k, y - (3 if sitting else 5) * k), (x - f * 11 * k, y - 2 * k)], max(2, int(k * 2.4)))
        pygame.draw.circle(surface, dark, (x - f * 11 * k, y - 2 * k), max(1, k * 1.2))
        if sitting:
            pygame.draw.ellipse(surface, fur, (x - 4 * k, y - 9 * k, 8 * k, 9 * k))
            pygame.draw.line(surface, fur, (x + f * 2 * k, y - 4 * k), (x + f * 2.5 * k, y), max(1, int(k * 1.4)))
            head = (x + f * 1.5 * k + self.look * k, y - 11 * k)
        else:
            for n, u in enumerate((3.5, 2.5, -2.5, -3.5)):
                swing = trot * 1.5 * k * (1 if n % 2 else -1)
                pygame.draw.line(surface, fur if n % 2 else dark, (x + f * u * k, y - 4 * k), (x + f * u * k + swing, y), max(1, int(k * 1.2)))
            pygame.draw.ellipse(surface, fur, (x - 5 * k, y - 7.5 * k, 10 * k, 4.5 * k))
            head = (x + f * 6 * k, y - 8.5 * k)
        pygame.draw.circle(surface, fur, head, 2.4 * k)
        pygame.draw.polygon(surface, fur, [(head[0] + f * 1.8 * k, head[1]), (head[0] + f * 4 * k, head[1] + 0.8 * k), (head[0] + f * 1.5 * k, head[1] + 1.5 * k)])
        for side in (-1, 1):
            base = head[0] + side * 1.3 * k
            ear = [(base - 1.2 * k, head[1] - 1 * k), (base + side * 1.4 * k, head[1] - 7 * k), (base + 1.2 * k, head[1] - 1 * k)]
            pygame.draw.polygon(surface, fur, ear)
            pygame.draw.polygon(surface, light, [(base - 0.5 * k, head[1] - 1.5 * k), (base + side * 1.2 * k, head[1] - 5.5 * k), (base + 0.5 * k, head[1] - 1.5 * k)])
        pygame.draw.circle(surface, light, (head[0] + f * 0.9 * k, head[1] - 0.2 * k), max(1, k * 0.5))


class Caravan(Visitor):
    # A camel caravan crossing a far ridge in silhouette: a walker in front leading a string
    # of camels, heads nodding and legs swinging as they plod along, small and hazy with
    # distance, fading behind the middle of the game
    #
    # Palette colors it uses:
    #   "caravan"                   their silhouettes (faded with the distance)

    SPEED = 9                       # pixels per second
    CAMELS = (3, 5)

    def __init__(self, scene, dunes):
        super().__init__(scene)
        self.dunes = dunes

    def can_come(self, palette):
        return "caravan" in palette

    def start(self):
        super().start()
        self.rank = self.dunes.ranks[1]
        self.dir = random.choice((-1, 1))
        self.x = -s(20) if self.dir > 0 else WIDTH + s(20)
        self.count = random.randint(*self.CAMELS)
        self.time = 0

    def update(self, dt):
        if not self.active:
            return
        self.time += dt
        self.x += self.dir * s(self.SPEED) * dt / 1000
        last = self.x - self.dir * s(14) * (self.count + 1)            # the camel at the back
        if (self.dir > 0 and last > WIDTH + s(30)) or (self.dir < 0 and last < -s(30)):
            self.active = False

    def draw(self, surface, palette):
        if not self.active or "caravan" not in palette:
            return
        color = pygame.Color(palette["caravan"])
        rank = self.rank
        k = s(1.3)
        f = self.dir
        for n in range(self.count + 1):
            x = self.x - f * s(14) * n
            if not (-s(20) < x < WIDTH + s(20)):
                continue
            y = rank["base"] - self.dunes.crest(rank, x)
            shade = self.scene.color_at(palette, y - 4 * k).lerp(color, 0.75 * self.scene.keep(x, 0.6))
            step = math.sin(self.time / 260 + n * 1.3)
            if n == 0:
                # The walker leading them
                pygame.draw.line(surface, shade, (x, y - 1), (x, y - 6 * k), max(1, int(k * 1.5)))
                pygame.draw.circle(surface, shade, (x, y - 7 * k), max(1, k * 1.1))
                pygame.draw.line(surface, shade, (x, y - 1), (x + step * k, y), 1)
                continue
            # A camel: four legs, a humped body, a long neck and a nodding head
            for u in (-3, -2, 2, 3):
                swing = step * k * (1 if u > 0 else -1)
                pygame.draw.line(surface, shade, (x + u * k, y - 5 * k), (x + u * k + swing, y), 1)
            pygame.draw.ellipse(surface, shade, (x - 4 * k, y - 8 * k, 8 * k, 3.5 * k))
            pygame.draw.circle(surface, shade, (x - k * 0.5, y - 8.2 * k), 1.8 * k)
            nod = math.sin(self.time / 260 + n) * 0.6 * k
            pygame.draw.line(surface, shade, (x + f * 3.5 * k, y - 7 * k), (x + f * 5.5 * k, y - 10 * k + nod), max(1, int(k * 1.2)))
            pygame.draw.line(surface, shade, (x + f * 5.5 * k, y - 10 * k + nod), (x + f * 7 * k, y - 9.5 * k + nod), max(1, int(k * 1.2)))


class Mirage(Visitor):
    # By day, now and then a mirage: a sheet of shimmering "water" appears low on the
    # horizon at one side, the sky mirrored in it, wavering, then fades away again. Drawn
    # just before the heat shimmer, so that wavers it too. Daytime only
    #
    # Palette colors it uses:
    #   "mirage"                    the false water (it fades into the sand around it)

    TIME = 16000
    WIDTH_SHARE = (0.22, 0.34)

    def can_come(self, palette):
        return "mirage" in palette

    def start(self):
        super().start()
        self.age = 0
        self.width = WIDTH * random.uniform(*self.WIDTH_SHARE)
        self.x = random.choice((s(10), WIDTH - s(10) - self.width))

    def update(self, dt):
        if not self.active:
            return
        self.age += dt
        if self.age > self.TIME:
            self.active = False

    def draw(self, surface, palette):
        if not self.active or "mirage" not in palette:
            return
        fade = math.sin(math.pi * self.age / self.TIME) ** 0.7
        water = pygame.Color(palette["mirage"])
        horizon = self.scene.view.horizon
        for row in range(int(s(9))):
            y = horizon + s(1) + row
            share = 1 - row / s(9)
            inset = self.width * 0.5 * (1 - math.sqrt(max(0.0, share))) + math.sin(self.age / 300 + row) * s(3)
            behind = self.scene.color_at(palette, y)
            pygame.draw.line(surface, behind.lerp(water, fade * (0.4 + 0.5 * share)), (self.x + inset, y), (self.x + self.width - inset, y))
