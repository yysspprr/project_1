# Life at the seaside. Regulars: seagulls wheeling overhead (now and then one lands on the
# sand to strut about), crabs on the wet sand dashing away from each wave, sandpipers
# running in and out with the water's edge, and trails of footprints that the waves wash
# away. Rare visitors, one at a time: dolphins leaping far out, a sailboat crossing the
# horizon, a bottle washing ashore, a whale's spout, a kite dancing in the breeze (by day),
# and turtle hatchlings scrambling down to the sea (by night)

import math

import random

import pygame

from partials.config import WIDTH, HEIGHT, s
from partials.backgrounds.base import Layer
from partials.backgrounds.helpers import Timer
from partials.backgrounds.brook_life import Visitor, draw_shadow
from partials.backgrounds.beach import SHORE, shore_y


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


class Gulls(Layer):
    # Seagulls gliding and wheeling over the sea on bent wings, flapping now and then. Every
    # so often one comes down to land on the dry sand at the side, struts about, and takes off
    # again. By day only (needs "gull")
    #
    # Palette colors it uses:
    #   "gull", "gull_dark"

    COUNT = 3

    def __init__(self, scene):
        super().__init__(scene)
        self.time = 0
        self.horizon = scene.view.horizon
        self.birds = []
        for i in range(self.COUNT):
            self.birds.append({"cx": random.uniform(0, WIDTH), "cy": random.uniform(self.horizon * 0.4, self.horizon + s(80)),
                               "r": s(random.uniform(40, 90)), "angle": random.uniform(0, 6), "speed": random.uniform(0.25, 0.45) * random.choice((1, -1)),
                               "flap": 0.0, "landing": None})
        self.land_wait = random.uniform(20000, 40000)

    def update(self, dt):
        self.time += dt
        seconds = dt / 1000
        for b in self.birds:
            if b["landing"] is not None:
                land = b["landing"]
                land["age"] += dt
                if land["age"] > land["time"]:
                    b["landing"] = None
                continue
            b["angle"] += b["speed"] * seconds
            b["cx"] += math.sin(self.time / 7000 + b["r"]) * s(6) * seconds
            if random.random() < seconds * 0.3:
                b["flap"] = 1.2
            b["flap"] = max(0.0, b["flap"] - seconds)
        self.land_wait -= dt
        if self.land_wait <= 0:
            self.land_wait = random.uniform(30000, 60000)
            b = random.choice(self.birds)
            if b["landing"] is None:
                spot = (self.scene.margin_x(), HEIGHT - s(random.uniform(30, 70)))
                spot = (max(s(70), min(WIDTH - s(120), spot[0])), spot[1])
                b["landing"] = {"spot": spot, "age": 0.0, "time": random.uniform(8000, 14000), "from": self.position(b)}

    def position(self, b):
        return (b["cx"] + math.cos(b["angle"]) * b["r"], b["cy"] + math.sin(b["angle"]) * b["r"] * 0.3)

    def draw(self, surface, palette):
        if "gull" not in palette:
            return
        white = pygame.Color(palette["gull"])
        dark = pygame.Color(palette.get("gull_dark", palette["text"]))
        for b in self.birds:
            if b["landing"] is not None:
                self.draw_landing(surface, b, white, dark)
                continue
            x, y = self.position(b)
            far = max(0.4, min(1.0, (y - self.horizon * 0.3) / s(150)))
            k = s(1.7) * far
            beat = math.sin(self.time / 90) * (b["flap"] > 0) * 3 * k
            behind = self.scene.color_at(palette, y) or pygame.Color(palette.get("sky_low", palette["bg"]))
            shade = behind.lerp(white, self.scene.keep(x, 0.6))
            pygame.draw.lines(surface, shade, False, [(x - 9 * k, y - 1 * k + beat), (x - 4 * k, y - 3 * k), (x, y), (x + 4 * k, y - 3 * k), (x + 9 * k, y - 1 * k + beat)],
                              max(1, int(k * 1.6)))
            pygame.draw.line(surface, behind.lerp(dark, 0.8 * self.scene.keep(x, 0.5)), (x - 9 * k, y - 1 * k + beat), (x - 7 * k, y - 1.6 * k + beat), 1)

    def draw_landing(self, surface, b, white, dark):
        land = b["landing"]
        a, t = land["age"], land["time"]
        sx, sy = land["spot"]
        fx, fy = land["from"]
        if a < 1500 or a > t - 1500:                        # gliding down, or off again
            u = ease(a / 1500) if a < 1500 else 1 - ease((a - t + 1500) / 1500)
            x, y = fx + (sx - fx) * u, fy + (sy - s(4) - fy) * u
            k = s(1.3)
            beat = math.sin(self.time / 80) * 3 * k
            pygame.draw.lines(surface, white, False, [(x - 9 * k, y + beat), (x - 4 * k, y - 3 * k), (x, y), (x + 4 * k, y - 3 * k), (x + 9 * k, y + beat)], max(1, int(k * 1.6)))
            return
        # On the sand, strutting back and forth
        walk = math.sin((a - 1500) / 1800)
        x, y = sx + walk * s(14), sy
        facing = 1 if math.cos((a - 1500) / 1800) > 0 else -1
        k = s(1.4)
        draw_shadow(surface, x, y, 14 * k, 3 * k, 0.25)
        step = math.sin(a / 120) * k
        for d in (-1, 1):
            pygame.draw.line(surface, dark.lerp(white, 0.2), (x + d * k, y - 4 * k), (x + d * k + step * d, y), 1)
        pygame.draw.ellipse(surface, white, (x - 5 * k, y - 9 * k, 10 * k, 6 * k))
        pygame.draw.polygon(surface, dark, [(x - facing * 2 * k, y - 8.5 * k), (x - facing * 8 * k, y - 7 * k), (x - facing * 3 * k, y - 5.5 * k)])
        bob = abs(math.sin(a / 240)) * k
        pygame.draw.circle(surface, white, (x + facing * 4 * k, y - 10 * k + bob), 2.4 * k)
        pygame.draw.line(surface, (230, 170, 40), (x + facing * 6 * k, y - 10 * k + bob), (x + facing * 8.5 * k, y - 9.5 * k + bob), max(1, int(k)))
        pygame.draw.circle(surface, dark, (x + facing * 4.8 * k, y - 10.6 * k + bob), max(1, k * 0.5))


class Crabs(Layer):
    # A couple of crabs on the wet sand, out at the sides. When a wave comes running up near
    # them they scuttle off sideways up the beach; when it's drawn back they wander down again
    #
    # Palette colors it uses:
    #   "crab", "crab_dark"

    COUNT = 2

    def __init__(self, scene, waves):
        super().__init__(scene)
        self.waves = waves
        self.time = 0
        self.crabs = []
        for i in range(self.COUNT):
            x = random.uniform(s(60), s(110)) if i == 0 else WIDTH - random.uniform(s(80), s(130))
            self.crabs.append({"x": x, "y": shore_y(x) + s(30), "dir": random.choice((-1, 1)), "moving": False})

    def update(self, dt):
        self.time += dt
        for c in self.crabs:
            water = self.waves.reach(c["x"])
            low = shore_y(c["x"]) + s(14)
            c["moving"] = False
            if water > c["y"] - s(10):                      # the water's coming: run!
                c["y"] += s(55) * dt / 1000
                c["x"] += c["dir"] * s(25) * dt / 1000
                c["moving"] = True
            elif c["y"] > low + s(6) and random.random() < dt / 2500:
                c["dir"] = random.choice((-1, 1))
            elif c["y"] > low and math.sin(self.time / 3000 + c["x"]) > 0.3:
                c["y"] -= s(10) * dt / 1000                 # wander back down toward the water
                c["moving"] = True
            c["y"] = min(c["y"], HEIGHT - s(20))
            c["x"] = max(s(20), min(WIDTH - s(20), c["x"]))

    def draw(self, surface, palette):
        shell = pygame.Color(palette.get("crab", palette["accent"]))
        dark = pygame.Color(palette.get("crab_dark", palette["text"]))
        k = s(1.0)
        for c in self.crabs:
            x, y = c["x"], c["y"]
            for side in (-1, 1):
                for n in range(3):
                    step = math.sin(self.time / 50 + n * 2 + side) * 1.2 * k if c["moving"] else 0
                    pygame.draw.lines(surface, dark, False, [(x + side * 3 * k, y - 2 * k), (x + side * (5 + n * 1.4) * k, y - 3.5 * k + step * 0.3),
                                                             (x + side * (7.5 + n * 1.6) * k, y + step * 0.2)], 1)
                pygame.draw.ellipse(surface, shell, (x + side * 6 * k - 2 * k, y - 7 * k, 4 * k, 3.2 * k))
            pygame.draw.ellipse(surface, shell, (x - 6 * k, y - 6 * k, 12 * k, 6 * k))
            for side in (-1, 1):
                pygame.draw.circle(surface, dark, (x + side * 2 * k, y - 7 * k), max(1, k * 0.7))


class Sandpipers(Layer):
    # A little flock of sandpipers at the right of the beach, running on twinkling legs to
    # follow the water's edge: chasing it down the sand as it draws back, pecking, and
    # scurrying up ahead of the next wave
    #
    # Palette colors it uses:
    #   "sandpiper", "sandpiper_dark"

    COUNT = 3

    def __init__(self, scene, waves):
        super().__init__(scene)
        self.waves = waves
        self.time = 0
        self.birds = [{"x": WIDTH - s(random.uniform(40, 120)), "y": 0.0, "phase": random.uniform(0, 6), "lag": random.uniform(0.5, 1.5), "moving": False} for i in range(self.COUNT)]
        for b in self.birds:
            b["y"] = shore_y(b["x"]) + s(20)

    def update(self, dt):
        self.time += dt
        for b in self.birds:
            target = self.waves.reach(b["x"]) + s(5) + b["lag"] * s(3)
            b["moving"] = abs(target - b["y"]) > s(1.5)
            b["y"] += (target - b["y"]) * min(1, dt / 1000 * 4 / b["lag"])
            b["x"] += math.sin(self.time / 2500 + b["phase"]) * s(4) * dt / 1000

    def draw(self, surface, palette):
        body = pygame.Color(palette.get("sandpiper", palette["muted"]))
        dark = pygame.Color(palette.get("sandpiper_dark", palette["text"]))
        k = s(1.0)
        for b in self.birds:
            x, y = b["x"], b["y"]
            facing = -1
            peck = (not b["moving"]) and math.sin(self.time / 300 + b["phase"]) > 0.6
            run = math.sin(self.time / 40 + b["phase"]) * 1.5 * k if b["moving"] else 0
            pygame.draw.line(surface, dark, (x, y - 3 * k), (x + run, y), 1)
            pygame.draw.line(surface, dark, (x, y - 3 * k), (x - run, y), 1)
            pygame.draw.ellipse(surface, body, (x - 4 * k, y - 7 * k, 8 * k, 4.5 * k))
            head = (x + facing * 3.5 * k, y - (5 if peck else 7.5) * k)
            pygame.draw.circle(surface, body, head, 1.8 * k)
            pygame.draw.line(surface, dark, head, (head[0] + facing * 3.5 * k, head[1] + (1.5 if peck else 0.5) * k), 1)


class Footprints(Layer):
    # Now and then a trail of footprints appears along the beach, step by step, as if someone
    # unseen were strolling along the water's edge; the waves wash away the prints they reach,
    # and the rest slowly fade
    #
    # Palette colors it uses:
    #   "footprint"                 the prints pressed into the sand

    EVERY = (40000, 80000)
    STEP = 400                      # milliseconds between steps
    LIFE = 40000

    def __init__(self, scene, sea, waves):
        super().__init__(scene)
        self.sea = sea
        self.waves = waves
        self.timer = Timer(self.EVERY)
        self.timer.left = random.uniform(3000, 15000)
        self.prints = []
        self.walk = None

    def update(self, dt):
        if self.walk is None and self.timer.tick(dt):
            direction = random.choice((-1, 1))
            self.walk = {"x": -s(10) if direction > 0 else WIDTH + s(10), "dir": direction, "foot": 1, "wait": 0.0,
                         "depth": random.uniform(16, 34)}
        if self.walk is not None:
            w = self.walk
            w["wait"] -= dt
            if w["wait"] <= 0:
                w["wait"] = self.STEP
                w["x"] += w["dir"] * s(11)
                w["foot"] = -w["foot"]
                y = shore_y(w["x"]) + s(w["depth"]) + w["foot"] * s(2.5)
                self.prints.append({"x": w["x"], "y": y, "age": 0.0, "dir": w["dir"]})
                if not (-s(20) < w["x"] < WIDTH + s(20)):
                    self.walk = None
        for p in self.prints:
            p["age"] += dt
            if self.waves.reach(p["x"]) > p["y"] + s(1):
                p["age"] = self.LIFE                        # washed away
        self.prints = [p for p in self.prints if p["age"] < self.LIFE]

    def draw(self, surface, palette):
        mark = pygame.Color(palette.get("footprint", palette["muted"]))
        for p in self.prints:
            fade = (1 - p["age"] / self.LIFE) * self.scene.keep(p["x"], 0.6)
            behind = self.sea.color_under(palette, p["x"], p["y"])
            color = behind.lerp(mark, 0.9 * fade)
            pygame.draw.ellipse(surface, color, (p["x"] - s(2.6), p["y"] - s(1.2), s(5.2), s(2.4)))
            pygame.draw.circle(surface, color, (p["x"] + p["dir"] * s(3.5), p["y"]), max(1, s(1.1)))


class Dolphins(Visitor):
    # Two or three dolphins leaping out of the sea far off, one after another, in curving arcs
    #
    # Palette colors it uses:
    #   "dolphin"

    TIME = 9000

    def start(self):
        super().start()
        self.age = 0
        self.dir = random.choice((-1, 1))
        self.x = WIDTH - random.uniform(s(50), s(110))
        self.y = self.scene.view.horizon + s(random.uniform(30, 60))
        self.count = random.randint(2, 3)

    def update(self, dt):
        if not self.active:
            return
        self.age += dt
        if self.age > self.TIME:
            self.active = False

    def draw(self, surface, palette):
        if not self.active:
            return
        color = pygame.Color(palette.get("dolphin", palette["muted"]))
        k = s(1.2)
        for n in range(self.count):
            for jump in range(3):
                t = (self.age - n * 400 - jump * 2800) / 1100
                if not 0 <= t <= 1:
                    continue
                x = self.x + self.dir * (jump * s(34) + t * s(26) + n * s(8))
                y = self.y - math.sin(math.pi * t) * s(14)
                angle = (0.5 - t) * 1.6 * self.dir
                body = []
                for u in range(7):
                    v = (u - 3) / 3
                    body.append((x + v * 7 * k * self.dir, y - (1 - v * v) * 1.5 * k + v * angle * 5 * k * self.dir))
                pygame.draw.lines(surface, color, False, body, max(2, int(k * 2.6)))
                pygame.draw.polygon(surface, color, [(x - self.dir * 1 * k, y - 2 * k), (x - self.dir * 3 * k, y - 5 * k), (x + self.dir * 1 * k, y - 2 * k)])
                if t < 0.15 or t > 0.85:
                    pygame.draw.circle(surface, pygame.Color(palette.get("surf", palette["text"])), (x, self.y), max(1, s(2)), 1)


class Sailboat(Visitor):
    # A sailboat crossing slowly along the horizon, its white sail leaning a little in the wind
    #
    # Palette colors it uses:
    #   "sail", "hull"

    TIME = 40000

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
        x = -s(20) + (WIDTH + s(40)) * t if self.dir > 0 else WIDTH + s(20) - (WIDTH + s(40)) * t
        y = self.scene.view.horizon + s(3)
        k = s(1.1)
        bob = math.sin(self.age / 700) * 0.4 * k
        sail = pygame.Color(palette.get("sail", palette["text"]))
        hull = pygame.Color(palette.get("hull", palette["muted"]))
        pygame.draw.polygon(surface, hull, [(x - 6 * k, y - 2 * k + bob), (x + 6 * k, y - 2 * k + bob), (x + 4 * k, y + bob), (x - 4 * k, y + bob)])
        pygame.draw.polygon(surface, sail, [(x + self.dir * 0.5 * k, y - 15 * k + bob), (x + self.dir * 0.5 * k, y - 3 * k + bob), (x + self.dir * 6 * k, y - 3 * k + bob)])
        pygame.draw.polygon(surface, sail.lerp(hull, 0.15), [(x - self.dir * 0.5 * k, y - 12 * k + bob), (x - self.dir * 0.5 * k, y - 3 * k + bob), (x - self.dir * 4 * k, y - 3 * k + bob)])


class Bottle(Visitor):
    # A bottle with a rolled-up message inside bobbing in on the shallows, washed up onto the
    # wet sand by a wave, lying there glinting a while, then carried off again
    #
    # Palette colors it uses:
    #   "bottle", "message"

    def __init__(self, scene, waves):
        super().__init__(scene)
        self.waves = waves

    def start(self):
        super().start()
        self.x = self.scene.margin_x()
        self.x = max(s(80), min(WIDTH - s(80), self.x))
        self.y = shore_y(self.x) - s(60)
        self.state = "in"
        self.age = 0
        self.time = 0
        self.stay = random.uniform(25000, 40000)

    def update(self, dt):
        if not self.active:
            return
        self.time += dt
        self.age += dt
        shore = shore_y(self.x)
        if self.state == "in":
            self.y += s(8) * dt / 1000
            if self.y >= shore:
                self.state = "beached"
                self.age = 0
        elif self.state == "beached":
            reach = self.waves.reach(self.x)
            if reach > self.y and self.y < shore + s(30):
                self.y = min(reach, shore + s(30))           # nudged up by the waves
            if self.age > self.stay:
                self.state = "out"
        else:
            self.y -= s(10) * dt / 1000
            if self.y < shore - s(70):
                self.active = False

    def draw(self, surface, palette):
        if not self.active:
            return
        glass = pygame.Color(palette.get("bottle", palette["muted"]))
        paper = pygame.Color(palette.get("message", palette["text"]))
        k = s(1.2)
        afloat = self.state != "beached"
        bob = math.sin(self.time / 400) * k if afloat else 0
        tilt = math.sin(self.time / 600) * 0.3 if afloat else 0.2
        x, y = self.x, self.y + bob
        cos, sin = math.cos(tilt), math.sin(tilt)

        def at(u, v):
            return (x + u * cos - v * sin, y + u * sin + v * cos)

        body = [at(-6 * k, -2 * k), at(3 * k, -2 * k), at(5 * k, -1 * k), at(8 * k, -1 * k), at(8 * k, 1 * k), at(5 * k, 1 * k), at(3 * k, 2 * k), at(-6 * k, 2 * k)]
        pygame.draw.polygon(surface, glass, body)
        pygame.draw.line(surface, paper, at(-4 * k, 0), at(2 * k, 0), max(1, int(k * 1.6)))
        pygame.draw.line(surface, glass.lerp((255, 255, 255), 0.6), at(-4 * k, -1.3 * k), at(1 * k, -1.3 * k), 1)
        pygame.draw.rect(surface, (120, 80, 50), (*at(8 * k, -1 * k), max(1, int(k * 1.4)), max(1, int(k * 2))))


class WhaleSpout(Visitor):
    # Far out, a whale surfaces: a puff of spray goes up, its dark back rolls over and its
    # tail lifts before it slips under again
    #
    # Palette colors it uses:
    #   "dolphin" (its back), "surf" (the spray)

    TIME = 7000

    def start(self):
        super().start()
        self.age = 0
        self.x = WIDTH - random.uniform(s(40), s(100))
        self.y = self.scene.view.horizon + s(random.uniform(12, 24))

    def update(self, dt):
        if not self.active:
            return
        self.age += dt
        if self.age > self.TIME:
            self.active = False

    def draw(self, surface, palette):
        if not self.active:
            return
        body = pygame.Color(palette.get("dolphin", palette["muted"]))
        spray = pygame.Color(palette.get("surf", palette["text"]))
        x, y, a = self.x, self.y, self.age
        k = s(1.0)
        if a < 2000:
            t = a / 2000
            h = math.sin(math.pi * min(1, t * 1.5)) * 12 * k
            behind = self.scene.color_at(palette, y - h)
            for n in range(5):
                pygame.draw.circle(surface, behind.lerp(spray, 0.8 * (1 - t)), (x + (n - 2) * 1.5 * k * t * 2, y - h + abs(n - 2) * k), max(1, k * (1 + t)))
        if 1500 < a < 4500:
            t = (a - 1500) / 3000
            back = [(x - 10 * k + t * 6 * k, y), (x - 4 * k + t * 6 * k, y - 3 * k * math.sin(math.pi * t)), (x + 6 * k + t * 6 * k, y)]
            pygame.draw.polygon(surface, body, back)
        if 4500 < a < 6500:
            t = (a - 4500) / 2000
            lift = math.sin(math.pi * t) * 8 * k
            tx = x + 10 * k
            pygame.draw.polygon(surface, body, [(tx, y), (tx - 1 * k, y - lift * 0.6), (tx - 5 * k, y - lift), (tx, y - lift * 0.75), (tx + 5 * k, y - lift),
                                                (tx + 1 * k, y - lift * 0.6)])


class Kite(Visitor):
    # By day, a kite flying high on the sea breeze at the right of the sky, its string running
    # down out of sight, diving and swooping, its tail of bows fluttering
    #
    # Palette colors it uses:
    #   "kite", "kite_tail"

    TIME = 30000

    def can_come(self, palette):
        return "kite" in palette

    def start(self):
        super().start()
        self.age = 0

    def update(self, dt):
        if not self.active:
            return
        self.age += dt
        if self.age > self.TIME:
            self.active = False

    def draw(self, surface, palette):
        if not self.active or "kite" not in palette:
            return
        a = self.age
        rise = ease(a / 3000) * (1 - ease((a - self.TIME + 3000) / 3000))
        wind = self.scene.weather.get("wind", 1)
        x = WIDTH - s(60) + math.sin(a / 1300) * s(14) * wind
        y = HEIGHT * 0.55 - (HEIGHT * 0.55 - s(70)) * rise + math.sin(a / 900) * s(8)
        tilt = math.sin(a / 1300) * 0.35
        k = s(1.6)
        cos, sin = math.cos(tilt), math.sin(tilt)

        def at(u, v):
            return (x + u * cos - v * sin, y + u * sin + v * cos)

        color = pygame.Color(palette["kite"])
        tail = pygame.Color(palette.get("kite_tail", palette["kite"]))
        string_end = (WIDTH + s(20), HEIGHT + s(20))
        mid = ((x + string_end[0]) / 2 + s(10), (y + string_end[1]) / 2 + s(20))
        pygame.draw.lines(surface, pygame.Color(palette.get("gull_dark", palette["text"])), False, [at(0, 6 * k), mid, string_end], 1)
        points = [at(0, -8 * k), at(5 * k, -1 * k), at(0, 8 * k), at(-5 * k, -1 * k)]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, color.lerp((0, 0, 0), 0.2), [at(0, -8 * k), at(5 * k, -1 * k), at(0, 8 * k)])
        pygame.draw.line(surface, color.lerp((255, 255, 255), 0.4), at(0, -8 * k), at(0, 8 * k), 1)
        px, py = at(0, 8 * k)
        tail_points = [(px, py)]
        for n in range(1, 7):
            tail_points.append((px + math.sin(a / 200 + n) * 3 * k * n * 0.4, py + n * 4 * k))
        pygame.draw.lines(surface, tail, False, tail_points, 1)
        for n in (2, 4, 6):
            bx, by = tail_points[n]
            pygame.draw.polygon(surface, tail, [(bx - 2 * k, by - 1 * k), (bx + 2 * k, by + 1 * k), (bx + 2 * k, by - 1 * k), (bx - 2 * k, by + 1 * k)])


class Hatchlings(Visitor):
    # By night, a handful of baby turtles burst from a nest high on the beach and scramble down
    # the sand toward the moonlit water, flippers going, until the waves carry them off.
    # Night only
    #
    # Palette colors it uses:
    #   "hatchling"

    COUNT = 6

    def __init__(self, scene, waves):
        super().__init__(scene)
        self.waves = waves

    def can_come(self, palette):
        return "hatchling" in palette

    def start(self):
        super().start()
        self.nest = (max(s(80), min(WIDTH - s(100), self.scene.margin_x())), HEIGHT - s(25))
        self.time = 0
        self.babies = [{"x": self.nest[0] + random.uniform(-s(6), s(6)), "y": self.nest[1], "delay": random.uniform(0, 4000),
                        "speed": random.uniform(0.7, 1.2), "wobble": random.uniform(0, 6), "gone": False} for i in range(self.COUNT)]

    def update(self, dt):
        if not self.active:
            return
        self.time += dt
        for b in self.babies:
            if b["gone"] or self.time < b["delay"]:
                continue
            b["y"] -= s(9) * b["speed"] * dt / 1000
            b["x"] += math.sin(self.time / 300 + b["wobble"]) * s(3) * dt / 1000
            if self.waves.reach(b["x"]) > b["y"] or b["y"] < shore_y(b["x"]):
                b["gone"] = True
        if all(b["gone"] for b in self.babies):
            self.active = False

    def draw(self, surface, palette):
        if not self.active or "hatchling" not in palette:
            return
        color = pygame.Color(palette["hatchling"])
        k = s(0.9)
        nx, ny = self.nest
        pygame.draw.ellipse(surface, color.lerp((0, 0, 0), 0.5), (nx - 8 * k, ny - 2 * k, 16 * k, 5 * k))
        for b in self.babies:
            if b["gone"] or self.time < b["delay"]:
                continue
            x, y = b["x"], b["y"]
            paddle = math.sin(self.time / 90 + b["wobble"]) * 1.5 * k
            for side in (-1, 1):
                pygame.draw.line(surface, color, (x + side * 1.5 * k, y), (x + side * 4 * k, y - paddle * side), 1)
            pygame.draw.ellipse(surface, color, (x - 2.5 * k, y - 2 * k, 5 * k, 4 * k))
            pygame.draw.circle(surface, color, (x, y - 3 * k), max(1, k * 1.2))
