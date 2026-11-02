# Life in the city. Regulars: pigeons strutting and bobbing along the parapet (by day), a
# cat sitting on the other parapet watching the world go by, trains rattling across the
# viaduct, and planes passing high overhead (with a contrail by day, blinking lights by
# night). Rare visitors, one at a time: a murmuration of starlings swirling over the
# skyline (by day), a helicopter, a blimp, and someone out on their balcony watering their
# plants (by day)

import math

import random

import pygame

from partials.config import WIDTH, HEIGHT, UI_SCALE, s
from partials.backgrounds.base import Layer
from partials.backgrounds.helpers import Timer
from partials.backgrounds.brook_life import Visitor, draw_shadow
from partials.backgrounds.brook_light import glow_sprite


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def faded(scene, palette, color, x, gentle=0.5):
    # A color faded toward the haze in the quiet column, so the game's text stays clear
    return pygame.Color(palette["haze"]).lerp(pygame.Color(color), scene.keep(x, gentle))


class Pigeons(Layer):
    # A few pigeons on the parapet on the left: strutting about with their heads bobbing,
    # pecking at crumbs, now and then puffing up. Every so often something startles them and
    # they clatter off together, circle away, and come gliding back. By day (needs "pigeon")
    #
    # Palette colors it uses:
    #   "pigeon", "pigeon_dark", "pigeon_neck", "pigeon_feet"

    COUNT = 4
    RANGE = (78, 142)               # where along the parapet they walk, medium x
    STARTLE = (40000, 90000)
    AWAY = (9000, 18000)

    def __init__(self, scene, rooftop):
        super().__init__(scene)
        self.rooftop = rooftop
        self.time = 0
        self.birds = []
        for i in range(self.COUNT):
            x = s(random.uniform(*self.RANGE))
            self.birds.append({"x": x, "goal": x, "facing": random.choice((-1, 1)), "wait": random.uniform(0, 3000),
                               "peck": 0.0, "phase": random.uniform(0, 6.3), "fly": None})
        self.startle = Timer(self.STARTLE)
        self.startle.left = random.uniform(20000, 50000)
        self.away = None

    def update(self, dt):
        self.time += dt
        if self.away is None and self.startle.tick(dt):
            self.away = {"age": 0.0, "time": random.uniform(*self.AWAY)}
            for b in self.birds:
                b["fly"] = {"from": (b["x"], self.ground(b["x"])), "dir": random.uniform(-1.4, -0.6), "delay": random.uniform(0, 300)}
        if self.away is not None:
            self.away["age"] += dt
            if self.away["age"] > self.away["time"]:
                self.away = None
                for b in self.birds:
                    b["fly"] = None
                    b["x"] = s(random.uniform(*self.RANGE))
                    b["goal"] = b["x"]
            return
        seconds = dt / 1000
        for b in self.birds:
            b["wait"] -= dt
            if abs(b["goal"] - b["x"]) > s(1):
                step = s(9) * seconds
                b["facing"] = 1 if b["goal"] > b["x"] else -1
                b["x"] += max(-step, min(step, b["goal"] - b["x"]))
            elif b["wait"] <= 0:
                b["wait"] = random.uniform(1500, 5000)
                if random.random() < 0.6:
                    b["goal"] = max(s(self.RANGE[0]), min(s(self.RANGE[1]), b["x"] + s(random.uniform(-18, 18))))
                else:
                    b["peck"] = 1.0
            b["peck"] = max(0.0, b["peck"] - seconds * 0.8)

    def ground(self, x):
        return self.rooftop.top_at(x) - s(2)

    def landing(self):
        # How far back they are when gliding in: 1 far away, 0 landed
        if self.away is None:
            return 0
        a, t = self.away["age"], self.away["time"]
        return 1 - ease((a - (t - 2500)) / 2500) if a > t - 2500 else None

    def draw(self, surface, palette):
        if "pigeon" not in palette:
            return
        k = 1.2 * UI_SCALE
        grey = pygame.Color(palette["pigeon"])
        dark = pygame.Color(palette["pigeon_dark"])
        neck = pygame.Color(palette["pigeon_neck"])
        feet = pygame.Color(palette["pigeon_feet"])
        for n, b in enumerate(self.birds):
            if self.away is not None:
                a = self.away["age"]
                t = self.away["time"]
                if a < 3000:                                    # off they go, up and away to the left
                    u = max(0, (a - b["fly"]["delay"]) / 3000)
                    x = b["fly"]["from"][0] + b["fly"]["dir"] * u * s(160)
                    y = b["fly"]["from"][1] - u * s(140) + math.sin(u * 3) * s(10)
                elif a > t - 2500:                              # and back again, gliding in
                    u = ease((a - (t - 2500)) / 2500)
                    x = b["x"] - (1 - u) * s(120)
                    y = self.ground(b["x"]) - (1 - u) * s(90)
                else:
                    continue
                beat = math.sin(self.time / 45 + n) * 3 * k
                pygame.draw.lines(surface, grey, False, [(x - 6 * k, y - 1 * k + beat), (x - 2 * k, y - 2 * k), (x + 2 * k, y - 2 * k), (x + 6 * k, y - 1 * k + beat)],
                                  max(1, int(1.6 * k)))
                pygame.draw.circle(surface, dark, (x, y), 1.4 * k)
                continue
            x, y, f = b["x"], self.ground(b["x"]), b["facing"]
            walking = abs(b["goal"] - x) > s(1)
            bob = math.sin(self.time / 110 + b["phase"]) * 1.5 * k if walking else 0
            peck = b["peck"] > 0 and math.sin(b["peck"] * 14) > 0
            draw_shadow(surface, x, y, 10 * k, 2 * k, 0.25)
            for lx in (-1, 1):
                step = math.sin(self.time / 110 + b["phase"] + lx) * k if walking else 0
                pygame.draw.line(surface, feet, (x + lx * k, y - 2 * k), (x + lx * k + step, y), max(1, int(k * 0.8)))
            pygame.draw.ellipse(surface, grey, (x - 5 * k, y - 7 * k, 10 * k, 6 * k))
            pygame.draw.polygon(surface, dark, [(x - f * 6.5 * k, y - 5 * k), (x - f * 2 * k, y - 6 * k), (x - f * 1 * k, y - 4 * k)])     # tail
            pygame.draw.line(surface, dark, (x - f * 2 * k, y - 4.5 * k), (x + f * 1 * k, y - 4 * k), 1)                                    # wing bars
            pygame.draw.line(surface, dark, (x - f * 2.5 * k, y - 3.5 * k), (x + f * 0.5 * k, y - 3 * k), 1)
            head = (x + f * (4 * k + (2 * k if peck else bob * 0.6)), y - (3 * k if peck else 9 * k))
            pygame.draw.line(surface, neck, (x + f * 3 * k, y - 6 * k), head, max(2, int(2.5 * k)))
            pygame.draw.circle(surface, grey, head, 2 * k)
            pygame.draw.line(surface, dark, (head[0] + f * 1.5 * k, head[1]), (head[0] + f * 3 * k, head[1] + 0.6 * k), 1)
            pygame.draw.circle(surface, (230, 120, 40), (head[0] + f * 0.6 * k, head[1] - 0.5 * k), max(1, k * 0.5))


class RoofCat(Layer):
    # A cat sitting on the parapet on the right, tail hanging down over the edge and swishing.
    # It looks about, now and then washes a paw, and every so often gets up, pads along the
    # parapet a little way and settles again. At night its eyes catch the light
    #
    # Palette colors it uses:
    #   "cat", "cat_dark"
    #   "cat_eye"           its eyes shining, at night (only when it's there)

    SPOTS = (418, 436)              # where it likes to sit, medium x

    def __init__(self, scene, rooftop):
        super().__init__(scene)
        self.rooftop = rooftop
        self.time = 0
        self.x = s(random.uniform(*self.SPOTS))
        self.goal = self.x
        self.facing = -1
        self.wait = random.uniform(15000, 30000)
        self.wash = None

    def update(self, dt):
        self.time += dt
        if abs(self.goal - self.x) > s(1):
            step = s(10) * dt / 1000
            self.facing = 1 if self.goal > self.x else -1
            self.x += max(-step, min(step, self.goal - self.x))
            return
        self.facing = -1
        self.wait -= dt
        if self.wait <= 0:
            self.wait = random.uniform(15000, 35000)
            if random.random() < 0.5:
                self.goal = s(random.uniform(*self.SPOTS))
            else:
                self.wash = 0.0
        if self.wash is not None:
            self.wash += dt
            if self.wash > 4000:
                self.wash = None

    def draw(self, surface, palette):
        k = 1.25 * UI_SCALE
        fur = pygame.Color(palette["cat"])
        dark = pygame.Color(palette["cat_dark"])
        x, f = self.x, self.facing
        y = self.rooftop.top_at(x) - s(2)
        walking = abs(self.goal - x) > s(1)
        if walking:
            # Padding along: a low body, legs stepping, tail up in a curve
            for n, lx in enumerate((-5, -3, 3, 5)):
                step = math.sin(self.time / 130 + n * 1.6) * 1.5 * k
                pygame.draw.line(surface, fur, (x + lx * k, y - 5 * k), (x + lx * k + step, y), max(1, int(1.6 * k)))
            pygame.draw.ellipse(surface, fur, (x - 7 * k, y - 9 * k, 14 * k, 6 * k))
            pygame.draw.lines(surface, fur, False, [(x - f * 6 * k, y - 7 * k), (x - f * 9 * k, y - 11 * k), (x - f * 8 * k, y - 15 * k)], max(1, int(1.6 * k)))
            head = (x + f * 7 * k, y - 9 * k)
        else:
            # Sitting upright, tail hanging down over the edge of the parapet and swishing
            swish = math.sin(self.time / 700) * 2.5 * k
            pygame.draw.lines(surface, fur, False, [(x + 3 * k, y - 1 * k), (x + 6 * k, y + 3 * k), (x + 6 * k + swish * 0.5, y + 9 * k),
                                                    (x + 5 * k + swish, y + 14 * k)], max(1, int(1.8 * k)))
            pygame.draw.ellipse(surface, fur, (x - 5 * k, y - 11 * k, 10 * k, 11 * k))
            pygame.draw.ellipse(surface, fur, (x - 4 * k, y - 3 * k, 9 * k, 3.5 * k))              # its haunches
            look = math.sin(self.time / 2600) * 1.5 * k
            head = (x + look, y - 13 * k)
            if self.wash is not None and math.sin(self.wash / 260) > -0.3:                      # licking a raised paw
                pygame.draw.line(surface, fur, (x - 2 * k, y - 7 * k), (head[0] - 2 * k, head[1] + 2 * k), max(1, int(1.8 * k)))
        pygame.draw.circle(surface, fur, head, 3.4 * k)
        for side in (-1, 1):
            pygame.draw.polygon(surface, fur, [(head[0] + side * 1 * k, head[1] - 2.5 * k), (head[0] + side * 3.4 * k, head[1] - 1.5 * k),
                                               (head[0] + side * 3 * k, head[1] - 5.5 * k)])
        pygame.draw.line(surface, dark, (head[0] - 3 * k, head[1] + 3.4 * k), (head[0] + 3 * k, head[1] + 3.4 * k), 1)     # its collar
        if "cat_eye" in palette and not walking:
            blink = (self.time % 5000) < 150
            if not blink:
                for side in (-1, 1):
                    pygame.draw.circle(surface, pygame.Color(palette["cat_eye"]), (head[0] + side * 1.3 * k, head[1] - 0.3 * k), max(1, k * 0.6))


class Trains(Layer):
    # Every so often a train comes rattling across the viaduct, one way or the other: a row of
    # carriages with a band of windows (lit warm at night), rocking a little on the rails
    #
    # Palette colors it uses:
    #   "train", "train_dark", "train_window"
    #   "train_lit"         its lit windows, at night (none lit without it)

    WAIT = (14000, 34000)
    CARS = (3, 6)
    CAR = (34, 11)                  # a carriage's length and height, medium size
    SPEED = 85                      # pixels a second

    def __init__(self, scene, viaduct):
        super().__init__(scene)
        self.viaduct = viaduct
        self.time = 0
        self.timer = Timer(self.WAIT)
        self.timer.left = random.uniform(3000, 12000)
        self.train = None

    def update(self, dt):
        self.time += dt
        if self.train is None:
            if self.timer.tick(dt):
                cars = random.randint(*self.CARS)
                way = random.choice((-1, 1))
                length = cars * (s(self.CAR[0]) + s(2))
                self.train = {"cars": cars, "way": way, "x": -length if way > 0 else WIDTH, "length": length}
            return
        t = self.train
        t["x"] += t["way"] * s(self.SPEED) * dt / 1000
        if (t["way"] > 0 and t["x"] > WIDTH) or (t["way"] < 0 and t["x"] + t["length"] < 0):
            self.train = None

    def draw(self, surface, palette):
        if self.train is None:
            return
        t = self.train
        w, h = s(self.CAR[0]), s(self.CAR[1])
        rail = self.viaduct.rail_y() - s(1)
        night = "train_lit" in palette
        for n in range(t["cars"]):
            x = t["x"] + n * (w + s(2))
            if x > WIDTH or x + w < 0:
                continue
            mid = x + w / 2
            rock = round(math.sin(self.time / 90 + n * 1.3) * 0.5)
            body = faded(self.scene, palette, palette["train"], mid)
            dark = faded(self.scene, palette, palette["train_dark"], mid)
            glass = faded(self.scene, palette, palette["train_lit" if night else "train_window"], mid, 0.4)
            top = rail - h + rock
            front = (n == 0 and t["way"] < 0) or (n == t["cars"] - 1 and t["way"] > 0)
            pygame.draw.rect(surface, body, (x, top, w, h - s(2)), border_radius=max(1, s(3)) if front else max(1, s(1)))
            pygame.draw.line(surface, dark, (x + s(1), top + s(1)), (x + w - s(1), top + s(1)), 1)                       # the roof
            pygame.draw.rect(surface, glass, (x + s(3), top + s(3), w - s(6), max(1, s(3))))                              # windows
            for wx in range(int(x + s(8)), int(x + w - s(4)), max(3, s(7))):
                pygame.draw.line(surface, body, (wx, top + s(3)), (wx, top + s(5)), 1)
            pygame.draw.line(surface, dark, (x, top + h - s(3)), (x + w, top + h - s(3)), 1)
            for wx in (x + s(5), x + s(9), x + w - s(9), x + w - s(5)):                                              # wheels
                pygame.draw.circle(surface, dark, (wx, rail - s(1)), max(1, s(1.6)))
        # The pantograph on the leading car, reaching up for the wire
        lead = t["x"] + (t["cars"] - 1) * (w + s(2)) + w * 0.6 if t["way"] > 0 else t["x"] + w * 0.4
        dark = faded(self.scene, palette, palette["train_dark"], lead)
        pygame.draw.lines(surface, dark, False, [(lead - s(3), rail - h), (lead, rail - h - s(4)), (lead + s(3), rail - h - s(4))], 1)


class Planes(Layer):
    # A plane passing high over the city every so often. By day it's a little silver shape
    # drawing a contrail that slowly spreads and fades; at night just its lights: red and
    # green on the wingtips and a white strobe flashing
    #
    # Palette colors it uses:
    #   "plane", "contrail"         by day
    #   "nav_red", "nav_green", "strobe"    at night (lights instead of a plane without "strobe")

    WAIT = (25000, 60000)
    SPEED = 16                      # pixels a second: it's very high up
    TRAIL = 9000                    # how long a stretch of contrail lasts

    def __init__(self, scene):
        super().__init__(scene)
        self.time = 0
        self.timer = Timer(self.WAIT)
        self.timer.left = random.uniform(5000, 20000)
        self.plane = None
        self.trail = []

    def update(self, dt):
        self.time += dt
        if self.plane is None and self.timer.tick(dt):
            way = random.choice((-1, 1))
            y = s(random.uniform(30, 80))
            self.plane = {"x": -s(10) if way > 0 else WIDTH + s(10), "y": y, "way": way, "climb": random.uniform(-0.06, 0.06)}
        if self.plane is not None:
            p = self.plane
            p["x"] += p["way"] * s(self.SPEED) * dt / 1000
            p["y"] += p["climb"] * s(self.SPEED) * dt / 1000
            self.trail.append({"x": p["x"] - p["way"] * s(4), "y": p["y"], "age": 0.0})
            if p["x"] < -s(20) or p["x"] > WIDTH + s(20):
                self.plane = None
        for point in self.trail:
            point["age"] += dt
        self.trail = [point for point in self.trail if point["age"] < self.TRAIL]
        if len(self.trail) > 400:
            self.trail = self.trail[-400:]

    def draw(self, surface, palette):
        night = "strobe" in palette
        if not night and self.trail:
            # The contrail: thin and bright just behind the plane, spreading and fading behind
            trail = pygame.Color(palette["contrail"])
            wind = self.scene.weather["wind"]
            for point in self.trail[::3]:
                t = point["age"] / self.TRAIL
                x, y = point["x"] - wind * s(3) * t * 4, point["y"] + t * s(2)
                behind = self.scene.color_at(palette, y)
                color = behind.lerp(trail, (1 - t) ** 1.2 * 0.9 * self.scene.keep(x, 0.5))
                pygame.draw.circle(surface, color, (x, y), max(1, s(1.5) + s(3) * t))
        if self.plane is None:
            return
        p = self.plane
        x, y, way = p["x"], p["y"], p["way"]
        behind = self.scene.color_at(palette, y)
        if night:
            fade = self.scene.keep(x, 0.4)
            blink = (self.time % 1200) < 120
            for side, key in ((-1, "nav_red"), (1, "nav_green")):
                pygame.draw.circle(surface, behind.lerp(pygame.Color(palette[key]), 0.9 * fade), (x + side * way * s(3), y + s(1)), 1)
            if blink:
                pygame.draw.circle(surface, behind.lerp(pygame.Color(palette["strobe"]), fade), (x, y), max(1, s(1.4)))
            return
        body = behind.lerp(pygame.Color(palette["plane"]), self.scene.keep(x, 0.4))
        k = UI_SCALE
        pygame.draw.line(surface, body, (x - way * 5 * k, y), (x + way * 5 * k, y), max(1, int(1.5 * k)))
        pygame.draw.polygon(surface, body, [(x - way * 1 * k, y), (x - way * 3 * k, y + 1 * k), (x + way * 0.5 * k, y + 1 * k)])
        pygame.draw.line(surface, body, (x - way * 5 * k, y), (x - way * 6 * k, y - 2 * k), 1)


class Starlings(Visitor):
    # A murmuration: a great flock of starlings swirling over the skyline as one, stretching,
    # folding and turning inside out as it drifts across the sky. By day (needs "starling")
    #
    # Palette colors it uses:
    #   "starling"

    COUNT = 150
    TIME = 45000

    def can_come(self, palette):
        return "starling" in palette

    def start(self):
        super().start()
        self.age = 0.0
        self.way = random.choice((-1, 1))
        self.birds = [(random.uniform(0, 6.3), random.uniform(0, 6.3), random.uniform(0.3, 1.0), random.uniform(0.6, 1.4)) for i in range(self.COUNT)]

    def update(self, dt):
        if not self.active:
            return
        self.age += dt
        if self.age > self.TIME:
            self.active = False

    def draw(self, surface, palette):
        if not self.active or "starling" not in palette:
            return
        t = self.age / 1000
        u = self.age / self.TIME
        cx = -s(80) + (WIDTH + s(160)) * u if self.way > 0 else WIDTH + s(80) - (WIDTH + s(160)) * u
        cy = s(115) + math.sin(t * 0.25) * s(30)
        # The flock's shape keeps changing: how wide and tall it is, and how it's twisted
        rx = s(56) * (0.7 + 0.4 * math.sin(t * 0.31))
        ry = s(26) * (0.7 + 0.5 * math.sin(t * 0.23 + 1))
        twist = math.sin(t * 0.17) * 1.2
        color = pygame.Color(palette["starling"])
        size = max(1, s(1.5))
        for a, b, r, speed in self.birds:
            px = math.sin(t * 0.6 * speed + a) * rx * r + math.sin(t * 1.3 + b) * s(6)
            py = math.cos(t * 0.5 * speed + b) * ry * r * math.sin(a + t * 0.2) + math.cos(t * 1.1 + a) * s(4)
            x = cx + px * math.cos(twist) - py * math.sin(twist)
            y = cy + px * math.sin(twist) * 0.5 + py
            behind = self.scene.color_at(palette, y)
            surface.fill(behind.lerp(color, 0.85 * self.scene.keep(x, 0.5)), (x, y, size, size))


class Helicopter(Visitor):
    # A helicopter clattering in over the rooftops on the right, hovering a while (turning
    # this way and that), then heading off again. At night a red light blinks on its tail and
    # a searchlight sweeps the roofs below
    #
    # Palette colors it uses:
    #   "heli", "heli_glass", "rotor"
    #   "searchlight"       its beam, at night (no beam without it)
    #   "nav_red"

    TIME = 26000
    HOVER = (396, 236)              # where it hovers, medium size

    def start(self):
        super().start()
        self.age = 0.0
        self.palette = None

    def update(self, dt):
        if not self.active:
            return
        self.age += dt
        if self.age > self.TIME:
            self.active = False

    def place(self):
        hx, hy = s(self.HOVER[0]), s(self.HOVER[1])
        a = self.age
        if a < 5000:                                        # flying in from the right
            u = ease(a / 5000)
            return hx + (1 - u) * s(120), hy - (1 - u) * s(40), -1
        if a > self.TIME - 5000:                            # and away up to the right
            u = ease((a - self.TIME + 5000) / 5000)
            return hx + u * s(130), hy - u * s(70), 1
        return hx + math.sin(a / 2300) * s(8), hy + math.sin(a / 1700) * s(4), (1 if math.sin(a / 4000) > 0.3 else -1)

    def draw(self, surface, palette):
        if not self.active:
            return
        x, y, f = self.place()
        k = 1.2 * UI_SCALE
        body = pygame.Color(palette["heli"])
        glass = pygame.Color(palette["heli_glass"])
        if "searchlight" in palette and 4000 < self.age < self.TIME - 4000:
            # A pale cone of light down to the rooftops, swinging slowly
            sweep = math.sin(self.age / 2500) * s(30)
            ground = (x + sweep, y + s(200))
            left = int(min(x, ground[0]) - s(20))
            beam = pygame.Surface((int(abs(ground[0] - x)) + s(42), s(204)), pygame.SRCALPHA)
            light = pygame.Color(palette["searchlight"])
            light.a = 40
            pygame.draw.polygon(beam, light, [(x - s(1) - left, s(3)), (x + s(1) - left, s(3)), (ground[0] + s(18) - left, s(200)),
                                              (ground[0] - s(18) - left, s(200))])
            surface.blit(beam, (left, y))
        pygame.draw.line(surface, body, (x - f * 4 * k, y), (x - f * 15 * k, y - 2 * k), max(1, int(1.8 * k)))         # tail boom
        pygame.draw.line(surface, body, (x - f * 15 * k, y - 2 * k), (x - f * 16 * k, y - 6 * k), max(1, int(1.5 * k)))  # tail fin
        spin = (self.age // 40) % 2
        pygame.draw.line(surface, pygame.Color(palette["rotor"]), (x - f * 16 * k, y - 6 * k - 2 * k * spin), (x - f * 16 * k, y - 2 * k + 2 * k * spin), 1)
        pygame.draw.ellipse(surface, body, (x - 6 * k, y - 4 * k, 12 * k, 8 * k))
        pygame.draw.ellipse(surface, glass, (x + f * 1 * k - 2.5 * k, y - 3 * k, 5 * k, 4 * k))
        for side in (-1, 1):                                                                                          # skids
            pygame.draw.line(surface, body, (x + side * 3 * k, y + 4 * k), (x + side * 3 * k, y + 6 * k), 1)
        pygame.draw.line(surface, body, (x - 7 * k, y + 6 * k), (x + 6 * k, y + 6 * k), 1)
        pygame.draw.line(surface, body, (x, y - 4 * k), (x, y - 6 * k), 1)
        reach = 14 * k * (0.6 + 0.4 * abs(math.sin(self.age / 25)))                                                  # the rotor's blur
        pygame.draw.line(surface, pygame.Color(palette["rotor"]), (x - reach, y - 6 * k), (x + reach, y - 6 * k), 1)
        if (self.age % 1000) < 140:
            pygame.draw.circle(surface, pygame.Color(palette["nav_red"]), (x - f * 15 * k, y - 2 * k), max(1, k))


class Blimp(Visitor):
    # A blimp drifting slowly across the sky above the towers, its fins and little gondola
    # underneath; at night its side glows softly and a light blinks on its tail
    #
    # Palette colors it uses:
    #   "blimp", "blimp_dark", "blimp_stripe"
    #   "blimp_glow"        its side lit up, at night
    #   "nav_red"

    TIME = 70000

    def start(self):
        super().start()
        self.age = 0.0
        self.way = random.choice((-1, 1))
        self.y = s(random.uniform(85, 110))

    def update(self, dt):
        if not self.active:
            return
        self.age += dt
        if self.age > self.TIME:
            self.active = False

    def draw(self, surface, palette):
        if not self.active:
            return
        u = self.age / self.TIME
        x = -s(40) + (WIDTH + s(80)) * u if self.way > 0 else WIDTH + s(40) - (WIDTH + s(80)) * u
        y = self.y + math.sin(self.age / 3000) * s(2)
        k = 1.3 * UI_SCALE
        f = self.way
        fade = self.scene.keep(x, 0.45)
        behind = self.scene.color_at(palette, y)
        body = behind.lerp(pygame.Color(palette["blimp"]), fade)
        dark = behind.lerp(pygame.Color(palette["blimp_dark"]), fade)
        stripe = behind.lerp(pygame.Color(palette["blimp_glow" if "blimp_glow" in palette else "blimp_stripe"]), fade)
        tail = x - f * 14 * k
        for dy in (-1, 1):
            pygame.draw.polygon(surface, dark, [(tail + f * 3 * k, y + dy * 2 * k), (tail - f * 3 * k, y + dy * 7 * k), (tail - f * 4 * k, y + dy * 2 * k)])
        pygame.draw.ellipse(surface, body, (x - 16 * k, y - 6 * k, 32 * k, 12 * k))
        pygame.draw.ellipse(surface, dark, (x - 16 * k, y - 1 * k, 32 * k, 7 * k))
        pygame.draw.ellipse(surface, body, (x - 15 * k, y - 6 * k, 30 * k, 9 * k))
        pygame.draw.rect(surface, stripe, (x - 9 * k, y - 1.5 * k, 18 * k, 2 * k))
        pygame.draw.rect(surface, dark, (x - 3 * k, y + 5 * k, 6 * k, 2.5 * k), border_radius=max(1, int(k)))         # the gondola
        if (self.age % 1500) < 150:
            pygame.draw.circle(surface, pygame.Color(palette["nav_red"]), (tail - f * 4 * k, y), max(1, k))


class BalconyGardener(Visitor):
    # Someone stepping out onto their little balcony on one of the buildings on the left,
    # watering the pots of flowers along its railing with a can, a sparkle of water falling,
    # then going back in. By day (needs "person")
    #
    # Palette colors it uses:
    #   "person", "person_shirt", "balcony", "flower_pots", "water"

    TIME = 26000

    def __init__(self, scene, row):
        super().__init__(scene)
        # A balcony on the left of the row, below a building's roofline and clear of the bridge
        spots = [b for b in row.buildings if s(8) < b["x"] + b["w"] * 0.5 < s(60) and not b["landmark"]]
        b = min(spots, key=lambda b: b["top"]) if spots else row.buildings[0]
        self.x = max(s(16), min(s(56), b["x"] + b["w"] * 0.5))
        self.y = b["top"] + s(30)

    def can_come(self, palette):
        return "person" in palette

    def start(self):
        super().start()
        self.age = 0.0

    def update(self, dt):
        if not self.active:
            return
        self.age += dt
        if self.age > self.TIME:
            self.active = False

    def draw(self, surface, palette):
        if not self.active or "person" not in palette:
            return
        k = UI_SCALE
        x, y = self.x, self.y
        show = ease(self.age / 1500) * (1 - ease((self.age - self.TIME + 1500) / 1500))
        rail = pygame.Color(palette["balcony"])
        # The balcony: a little slab and railing, with pots along it
        pygame.draw.rect(surface, rail, (x - 12 * k, y, 24 * k, 2 * k))
        pygame.draw.line(surface, rail, (x - 12 * k, y - 6 * k), (x + 12 * k, y - 6 * k), 1)
        for rx in range(int(x - 12 * k), int(x + 12 * k) + 1, max(2, int(3 * k))):
            pygame.draw.line(surface, rail, (rx, y - 6 * k), (rx, y), 1)
        pots = [pygame.Color(c) for c in palette["flower_pots"]]
        for n, px in enumerate((-8, -2, 4, 9)):
            pygame.draw.rect(surface, pygame.Color(palette["balcony"]).lerp((150, 80, 50), 0.6), (x + px * k - 1.5 * k, y - 9 * k, 3 * k, 3 * k))
            pygame.draw.circle(surface, pots[n % len(pots)], (x + px * k, y - 10 * k), 1.6 * k)
        if show <= 0.02:
            return
        # The gardener, out from the doorway behind, moving along the pots with the can
        along = math.sin(self.age / 4000) * 5 * k
        px, py = x + along, y - 1 * k
        person = pygame.Color(palette["person"])
        shirt = pygame.Color(palette["person_shirt"])
        rise = (1 - show) * 6 * k
        pygame.draw.rect(surface, shirt, (px - 2.5 * k, py - 12 * k + rise, 5 * k, 7 * k))
        pygame.draw.circle(surface, person, (px, py - 14 * k + rise), 2 * k)
        pygame.draw.line(surface, shirt, (px + 2 * k, py - 10 * k + rise), (px + 5 * k, py - 8 * k + rise), max(1, int(k)))       # arm out
        can = (px + 6 * k, py - 8 * k + rise)
        pygame.draw.rect(surface, pygame.Color(palette["balcony"]), (can[0] - 1.5 * k, can[1] - 1 * k, 3 * k, 2.5 * k))
        if 3000 < self.age < self.TIME - 3000 and math.sin(self.age / 4000 * 3) > -0.5:
            water = pygame.Color(palette["water"])
            for n in range(4):                                  # drops falling onto the pots
                t = ((self.age / 300) + n / 4) % 1
                surface.fill(water, (can[0] + 3 * k, can[1] + t * 5 * k, 1, 1))
