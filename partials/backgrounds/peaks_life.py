# Life in the mountains. Regulars: a flock of choughs tumbling about in the wind and now and
# then settling on the ledge, an eagle that comes to circle over the valley, an ibex that
# picks its way onto the ledge to graze, and a marmot popping up from its burrow to look
# around (all by day). Rare visitors, one at a time: a rope of climbers inching up the great
# peak's ridge (with headlamps at night), a yak caravan crossing a far ridge to the
# monastery, a paraglider drifting down the valley (by day) and a snow leopard on the ledge

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


def faded(scene, palette, color, x, y, gentle=0.6):
    # A color faded toward what's behind it in the quiet column, so the game's text stays clear
    behind = pygame.Color(palette["haze"])
    return behind.lerp(pygame.Color(color), scene.keep(x, gentle))


class Choughs(Layer):
    # A loose flock of alpine choughs, black with yellow beaks, riding the updrafts: they
    # tumble and swoop about one side of the valley, now and then drift across to the other,
    # and every so often drop onto the ledge to strut and peck before taking off again.
    # By day (needs "chough")
    #
    # Palette colors it uses:
    #   "chough", "chough_beak"

    COUNT = 5
    SIDES = (40, 400)               # the two places they hang about, medium x
    LAND_WAIT = (25000, 50000)
    LAND_TIME = (8000, 16000)

    def __init__(self, scene, ledge):
        super().__init__(scene)
        self.ledge = ledge
        self.time = 0
        self.home = s(random.choice(self.SIDES))
        self.center = [self.home, s(420)]
        self.move_wait = random.uniform(15000, 30000)
        self.land = Timer(self.LAND_WAIT)
        self.land.left = random.uniform(8000, 20000)
        self.landed = None
        self.birds = [{"phase": random.uniform(0, 6.3), "r": random.uniform(0.5, 1.0), "speed": random.uniform(0.7, 1.3),
                       "flap": 0.0, "perch": 0.0, "x": 0.0, "y": 0.0} for i in range(self.COUNT)]
        for b in self.birds:
            b["x"], b["y"] = self.flying_spot(b)

    def flying_spot(self, b):
        t = self.time / 1000 * b["speed"]
        x = self.center[0] + math.sin(t * 0.7 + b["phase"]) * s(34) * b["r"] + math.sin(t * 1.9 + b["phase"] * 2) * s(8)
        y = self.center[1] + math.sin(t * 1.1 + b["phase"] * 3) * s(40) * b["r"] + math.cos(t * 2.3 + b["phase"]) * s(6)
        return x, y

    def update(self, dt):
        self.time += dt
        if self.landed is None:
            self.move_wait -= dt
            if self.move_wait <= 0:                         # off to the other side of the valley
                self.move_wait = random.uniform(20000, 40000)
                self.home = s(self.SIDES[1]) if self.home == s(self.SIDES[0]) else s(self.SIDES[0])
            if self.land.tick(dt):
                spots = []
                for b in self.birds:
                    x = self.home + random.uniform(-s(24), s(24)) if self.home < WIDTH / 2 else WIDTH - random.uniform(s(10), s(38))
                    x = max(s(46), min(s(100), x)) if self.home < WIDTH / 2 else x
                    spots.append(x)
                self.landed = {"age": 0.0, "time": random.uniform(*self.LAND_TIME), "spots": spots}
        else:
            self.landed["age"] += dt
            if self.landed["age"] > self.landed["time"]:
                self.landed = None
        self.center[0] += (self.home - self.center[0]) * min(1, dt / 4000)
        self.center[1] = s(420) + math.sin(self.time / 9000) * s(40)
        seconds = dt / 1000
        for i, b in enumerate(self.birds):
            if self.landed is not None:
                sx = self.landed["spots"][i]
                tx, ty = sx, self.ledge.top_at(sx)
                b["perch"] = min(1.0, b["perch"] + seconds / 1.2)
            else:
                tx, ty = self.flying_spot(b)
                b["perch"] = max(0.0, b["perch"] - seconds / 0.8)
            pull = min(1, dt / (250 if b["perch"] > 0 else 120))
            b["x"] += (tx - b["x"]) * pull
            b["y"] += (ty - b["y"]) * pull
            if random.random() < seconds * 0.8:
                b["flap"] = 0.6
            b["flap"] = max(0.0, b["flap"] - seconds)

    def draw(self, surface, palette):
        if "chough" not in palette:
            return
        k = 1.2 * UI_SCALE
        for i, b in enumerate(self.birds):
            x, y = b["x"], b["y"]
            body = faded(self.scene, palette, palette["chough"], x, y, 0.5)
            beak = faded(self.scene, palette, palette["chough_beak"], x, y, 0.5)
            standing = self.landed is not None and b["perch"] >= 1
            if standing:
                facing = 1 if math.sin(self.time / 1300 + b["phase"]) > 0 else -1
                hop = abs(math.sin(self.time / 180 + b["phase"])) * 2 * k if math.sin(self.time / 2100 + b["phase"]) > 0.7 else 0
                peck = math.sin(self.time / 400 + b["phase"] * 3) > 0.6
                pygame.draw.ellipse(surface, body, (x - 3 * k, y - 5 * k - hop, 6 * k, 4 * k))
                head = (x + facing * 3 * k, y - (4 if peck else 6) * k - hop)
                pygame.draw.circle(surface, body, head, 1.6 * k)
                pygame.draw.line(surface, beak, head, (head[0] + facing * 2.2 * k, head[1] + 0.8 * k), 1)
                pygame.draw.line(surface, body, (x - facing * 2 * k, y - 4 * k - hop), (x - facing * 5 * k, y - 3 * k - hop), max(1, int(k)))
                pygame.draw.line(surface, beak, (x, y - 1 * k - hop), (x, y), 1)
                continue
            # Flying: bent wings, flapping now and then, tumbling in the air
            beat = math.sin(self.time / 60 + i) * 3 * k if b["flap"] > 0 else math.sin(self.time / 500 + i) * k
            pygame.draw.lines(surface, body, False, [(x - 6 * k, y - 1 * k + beat), (x - 3 * k, y - 2 * k), (x, y), (x + 3 * k, y - 2 * k),
                                                     (x + 6 * k, y - 1 * k + beat)], max(1, int(k * 1.6)))
            pygame.draw.circle(surface, body, (x, y), max(1, k * 1.3))
            pygame.draw.line(surface, beak, (x, y), (x, y + k), 1)


class Eagle(Layer):
    # Every so often a golden eagle sails in on broad, fingered wings, circles slowly over the
    # valley at the side (tilting as it banks), and glides away again. By day (needs "eagle")
    #
    # Palette colors it uses:
    #   "eagle", "eagle_light"

    WAIT = (35000, 80000)
    LOOPS = (2, 4)                  # how many times round it goes
    LOOP_TIME = 9000
    CENTER = (385, 280)             # where it circles, medium size
    RADIUS = (34, 12)

    def __init__(self, scene):
        super().__init__(scene)
        self.time = 0
        self.timer = Timer(self.WAIT)
        self.timer.left = random.uniform(8000, 25000)
        self.flight = None

    def update(self, dt):
        self.time += dt
        if self.flight is None:
            if self.timer.tick(dt):
                loops = random.randint(*self.LOOPS)
                self.flight = {"age": 0.0, "time": 4000 + loops * self.LOOP_TIME + 4000, "loops": loops}
            return
        self.flight["age"] += dt
        if self.flight["age"] > self.flight["time"]:
            self.flight = None

    def spot(self, age):
        # Where it is age milliseconds into its visit: in from the right, round and round, off up to the right
        cx, cy = s(self.CENTER[0]), s(self.CENTER[1])
        rx, ry = s(self.RADIUS[0]), s(self.RADIUS[1])
        circling = self.flight["loops"] * self.LOOP_TIME
        if age < 4000:
            t = ease(age / 4000)
            start = (WIDTH + s(40), cy - s(70))
            return start[0] + (cx + rx - start[0]) * t, start[1] + (cy - start[1]) * t
        if age < 4000 + circling:
            a = (age - 4000) / self.LOOP_TIME * 2 * math.pi
            return cx + math.cos(a) * rx, cy - math.sin(a) * ry
        t = ease((age - 4000 - circling) / 4000)
        end = (WIDTH + s(50), cy - s(140))
        return cx + rx + (end[0] - cx - rx) * t, cy + (end[1] - cy) * t

    def draw(self, surface, palette):
        if self.flight is None or "eagle" not in palette:
            return
        age = self.flight["age"]
        x, y = self.spot(age)
        nx, ny = self.spot(age + 200)
        heading = 1 if nx >= x else -1
        bank = max(-1, min(1, (ny - y) / max(1, s(4))))      # tilts as it turns
        k = 1.6 * UI_SCALE
        dark = faded(self.scene, palette, palette["eagle"], x, y, 0.4)
        light = faded(self.scene, palette, palette["eagle_light"], x, y, 0.4)
        lift = (2 + bank) * k
        drop = (2 - bank) * k
        # Broad wings with the tips fingered, raised a little in a shallow V
        left = [(x, y), (x - 6 * k, y - lift * 0.6), (x - 13 * k, y - lift), (x - 15 * k, y - lift + 1.5 * k), (x - 12 * k, y - lift + 2.5 * k),
                (x - 5 * k, y + 2 * k)]
        right = [(x, y), (x + 6 * k, y - drop * 0.6), (x + 13 * k, y - drop), (x + 15 * k, y - drop + 1.5 * k), (x + 12 * k, y - drop + 2.5 * k),
                 (x + 5 * k, y + 2 * k)]
        pygame.draw.polygon(surface, dark, left)
        pygame.draw.polygon(surface, dark, right)
        for tip in ((x - 15 * k, y - lift + 1.5 * k), (x + 15 * k, y - drop + 1.5 * k)):
            side = 1 if tip[0] > x else -1
            for f in range(3):
                pygame.draw.line(surface, dark, tip, (tip[0] + side * 2 * k, tip[1] - k + f * k), 1)
        pygame.draw.polygon(surface, dark, [(x - 2 * k, y + 1 * k), (x + 2 * k, y + 1 * k), (x + 3 * k, y + 6 * k), (x - 3 * k, y + 6 * k)])
        pygame.draw.circle(surface, light, (x + heading * 2.5 * k, y - 0.5 * k), 1.6 * k)
        pygame.draw.line(surface, light, (x - 4 * k, y + 0.5 * k), (x + 4 * k, y + 0.5 * k), 1)


class Ibex(Layer):
    # Now and then an ibex picks its way along the ledge on the left: it stops beyond the
    # cairn, grazes on the tufts of grass, lifts its head to look out over the valley with its
    # great curved horns, and wanders off again. By day (needs "ibex")
    #
    # Palette colors it uses:
    #   "ibex", "ibex_dark", "ibex_horn"

    WAIT = (30000, 70000)
    STAY = (20000, 35000)
    SPOT = (60, 82)                 # where along the ledge it stops, medium x
    SPEED = 14                      # pixels a second, walking

    def __init__(self, scene, ledge):
        super().__init__(scene)
        self.ledge = ledge
        self.time = 0
        self.timer = Timer(self.WAIT)
        self.timer.left = random.uniform(6000, 20000)
        self.visit = None
        self.blocked = lambda: False                         # the snow leopard keeps it away

    @property
    def present(self):
        return self.visit is not None

    def update(self, dt):
        self.time += dt
        if self.visit is None:
            if self.timer.tick(dt) and not self.blocked():
                self.visit = {"x": -s(25), "goal": s(random.uniform(*self.SPOT)), "state": "in", "age": 0.0,
                              "stay": random.uniform(*self.STAY), "facing": 1}
            return
        v = self.visit
        v["age"] += dt
        step = s(self.SPEED) * dt / 1000
        if v["state"] == "in":
            v["x"] += step
            if v["x"] >= v["goal"]:
                v["state"], v["age"] = "stay", 0.0
        elif v["state"] == "stay":
            v["facing"] = 1 if math.sin(v["age"] / 6000) > -0.6 else -1
            if v["age"] > v["stay"]:
                v["state"] = "out"
        else:
            v["facing"] = -1
            v["x"] -= step
            if v["x"] < -s(30):
                self.visit = None

    def draw(self, surface, palette):
        if self.visit is None or "ibex" not in palette:
            return
        v = self.visit
        x = v["x"]
        y = self.ledge.top_at(max(0, x)) + s(1)
        f = v["facing"]
        k = 1.25 * UI_SCALE
        coat = pygame.Color(palette["ibex"])
        dark = pygame.Color(palette["ibex_dark"])
        horn = pygame.Color(palette["ibex_horn"])
        walking = v["state"] != "stay"
        grazing = v["state"] == "stay" and math.sin(v["age"] / 2500) > 0.1
        draw_shadow(surface, x, y, 24 * k, 4 * k, 0.3)
        # Legs: dark and slender, stepping when it walks
        for n, lx in enumerate((-6, -3.5, 4, 6.5)):
            swing = math.sin(self.time / 150 + n * 1.7) * 2 * k if walking else 0
            pygame.draw.line(surface, dark, (x + lx * k * f, y - 9 * k), (x + lx * k * f + swing, y), max(1, int(1.4 * k)))
        # A stocky body: a rounded back, deep chest, and a short dark tail
        body = [(x - f * 9 * k, y - 9 * k), (x - f * 9.5 * k, y - 13 * k), (x - f * 6 * k, y - 15.5 * k), (x + f * 3 * k, y - 15.5 * k),
                (x + f * 8 * k, y - 15 * k), (x + f * 9 * k, y - 10 * k), (x + f * 6 * k, y - 8 * k), (x - f * 6 * k, y - 8 * k)]
        pygame.draw.polygon(surface, coat, body)
        pygame.draw.lines(surface, dark, False, body[-3:], 1)                               # the shadow under its belly
        pygame.draw.line(surface, dark, (x - f * 9 * k, y - 13.5 * k), (x - f * 10.5 * k, y - 15 * k), max(1, int(1.5 * k)))
        # Neck and head: down to the grass, or up and looking out
        if grazing:
            head = (x + f * 13 * k, y - 3 * k)
        else:
            head = (x + f * 12 * k, y - 21 * k + math.sin(self.time / 900) * 0.5 * k)
        pygame.draw.polygon(surface, coat, [(x + f * 4 * k, y - 15 * k), (x + f * 9 * k, y - 10 * k), (head[0] + f * 1 * k, head[1] + 1 * k),
                                            (head[0] - f * 2 * k, head[1] - 1 * k)])
        pygame.draw.polygon(surface, coat, [(head[0] - f * 2 * k, head[1] - 2 * k), (head[0] + f * 4 * k, head[1] + 0.5 * k),
                                            (head[0] + f * 3.5 * k, head[1] + 2 * k), (head[0] - f * 1.5 * k, head[1] + 2 * k)])
        pygame.draw.line(surface, dark, (head[0] + f * 2 * k, head[1] + 2 * k), (head[0] + f * 1.5 * k, head[1] + 4.5 * k), max(1, int(k)))  # beard
        pygame.draw.circle(surface, dark, (head[0] + f * 0.8 * k, head[1] - 0.3 * k), max(1, k * 0.6))
        # The great horns: a long ridged arc sweeping up and back over its neck
        base = (head[0] - f * 1 * k, head[1] - 2 * k)
        radius = 6.5 * k
        center = (base[0] - f * radius, base[1])
        sweep = [(center[0] + f * radius * math.cos(a), center[1] - radius * math.sin(a)) for a in [i / 7 * 2.5 for i in range(8)]]
        pygame.draw.lines(surface, horn, False, sweep, max(2, int(2 * k)))
        for px, py in sweep[1:-1:2]:
            pygame.draw.circle(surface, dark, (px, py), max(1, k * 0.5))


class Marmot(Layer):
    # A marmot that lives under the ledge on the right: every so often it pops up out of its
    # burrow, sits up on its haunches to look around (turning its head, ducking to nibble), and
    # dives back in. By day (needs "marmot")
    #
    # Palette colors it uses:
    #   "marmot", "marmot_dark", "burrow"

    WAIT = (14000, 34000)
    STAY = (7000, 14000)
    X = 428                         # its burrow, medium x

    def __init__(self, scene, ledge):
        super().__init__(scene)
        self.time = 0
        self.x = s(self.X)
        self.y = ledge.top_at(self.x) + s(2)
        self.timer = Timer(self.WAIT)
        self.timer.left = random.uniform(3000, 10000)
        self.out = None

    def update(self, dt):
        self.time += dt
        if self.out is None:
            if self.timer.tick(dt):
                self.out = {"age": 0.0, "stay": random.uniform(*self.STAY)}
        else:
            self.out["age"] += dt
            if self.out["age"] > self.out["stay"]:
                self.out = None

    def draw(self, surface, palette):
        if "marmot" not in palette:
            return
        x, y, k = self.x, self.y, 1.2 * UI_SCALE
        pygame.draw.ellipse(surface, pygame.Color(palette["burrow"]), (x - 6 * k, y - 2 * k, 12 * k, 4 * k))
        if self.out is None:
            return
        a, stay = self.out["age"], self.out["stay"]
        rise = ease(a / 500) * (1 - ease((a - stay + 400) / 400))      # pops up quick, dives quicker
        if rise <= 0.02:
            return
        fur = pygame.Color(palette["marmot"])
        dark = pygame.Color(palette["marmot_dark"])
        height = 13 * k * rise
        look = math.sin(a / 1100)
        nibble = math.sin(a / 1700 + 1) > 0.75
        top = y - height + (3 * k if nibble else 0)
        # Cut off at the burrow's mouth: it's coming up out of the ground
        clip = surface.get_clip()
        surface.set_clip(pygame.Rect(0, 0, WIDTH, int(y + 1)).clip(clip) if clip else pygame.Rect(0, 0, WIDTH, int(y + 1)))
        pygame.draw.ellipse(surface, fur, (x - 4.5 * k, top + 3 * k, 9 * k, height + 2 * k))
        pygame.draw.ellipse(surface, fur.lerp((255, 255, 255), 0.25), (x - 2.5 * k, top + 6 * k, 5 * k, height - 3 * k))   # its paler front
        head = (x + look * 1.5 * k, top + 1.5 * k)
        pygame.draw.circle(surface, fur, head, 3.2 * k)
        pygame.draw.circle(surface, dark, (head[0] - 2.2 * k, head[1] - 2.3 * k), max(1, k))
        pygame.draw.circle(surface, dark, (head[0] + 2.2 * k, head[1] - 2.3 * k), max(1, k))
        pygame.draw.circle(surface, dark, (head[0] + look * 2.2 * k, head[1] + 0.5 * k), max(1, k * 0.7))
        if not nibble and rise > 0.9:
            for side in (-1, 1):                          # little paws held up to its chest
                pygame.draw.circle(surface, dark, (x + side * 1.5 * k, top + 7 * k), max(1, k * 0.8))
        surface.set_clip(clip)


class Climbers(Visitor):
    # A rope of climbers inching up the ridge of the great peak, tiny against the snow, one
    # after another along the rope. At night their headlamps glow, a little line of lights
    # high on the mountain
    #
    # Palette colors it uses:
    #   "climber"                   the climbers
    #   "headlamp"                  at night (no lamps without it)

    COUNT = 5
    TIME = 75000
    SPACING = 7                     # pixels between climbers along the ridge, medium size

    def __init__(self, scene, peaks):
        super().__init__(scene)
        line = peaks.peaks[-1]["left"]                  # the great peak's left ridge, summit first
        n = len(line) - 1
        self.path = list(reversed(line[int(n * 0.24):int(n * 0.58) + 1]))    # from low on the ridge, up toward the top
        self.length = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(self.path, self.path[1:]))
        self.palette = None

    def start(self):
        super().start()
        self.age = 0.0

    def update(self, dt):
        if not self.active:
            return
        self.age += dt
        if self.age > self.TIME:
            self.active = False

    def along(self, d):
        # The point d pixels along the path
        d = max(0, min(self.length, d))
        for a, b in zip(self.path, self.path[1:]):
            gap = math.hypot(b[0] - a[0], b[1] - a[1])
            if d <= gap:
                t = d / max(gap, 0.01)
                return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            d -= gap
        return self.path[-1]

    def draw(self, surface, palette):
        if not self.active:
            return
        if self.palette is not palette:
            self.lamp = glow_sprite(s(4), pygame.Color(palette["headlamp"])) if "headlamp" in palette else None
            self.palette = palette
        show = ease(self.age / 3000) * (1 - ease((self.age - self.TIME + 3000) / 3000))
        lead = s(self.SPACING) * (self.COUNT - 1) + (self.length - s(self.SPACING) * self.COUNT) * self.age / self.TIME
        color = pygame.Color(palette["climber"])
        k = max(1, s(1))
        for n in range(self.COUNT):
            # Each one stops now and then to rest, so the rope bunches up and stretches out
            pause = max(0, math.sin(self.age / 2300 + n * 1.3)) * s(2)
            x, y = self.along(lead - n * s(self.SPACING) - pause)
            body = pygame.Color(palette["snow_shade"]).lerp(color, show)
            pygame.draw.line(surface, body, (x, y - 1), (x, y - 1 - 2 * k), max(1, int(k)))
            if self.lamp is not None:
                lamp = self.lamp.copy()
                lamp.fill([int(255 * show * (0.75 + 0.25 * math.sin(self.age / 300 + n)))] * 3, special_flags=pygame.BLEND_RGB_MULT)
                surface.blit(lamp, lamp.get_rect(center=(x, y - 1 - 2 * k)), special_flags=pygame.BLEND_RGB_ADD)


class YakCaravan(Visitor):
    # A string of yaks with their herder walking along the crest of a far ridge toward the
    # monastery, tiny dark shapes against the mist, slowly plodding. By day (needs "yak")
    #
    # Palette colors it uses:
    #   "yak", "herder"

    COUNT = 4
    SPEED = 9                       # pixels a second, medium size

    def __init__(self, scene, ridge, monastery):
        super().__init__(scene)
        self.ridge = ridge
        self.end = monastery.x + s(14)

    def can_come(self, palette):
        return "yak" in palette

    def start(self):
        super().start()
        self.x = WIDTH + s(10)
        self.time = 0

    def update(self, dt):
        if not self.active:
            return
        self.time += dt
        self.x -= s(self.SPEED) * dt / 1000
        if self.x + s(12) * self.COUNT < self.end - s(10):
            self.active = False

    def draw(self, surface, palette):
        if not self.active or "yak" not in palette:
            return
        k = max(1, s(1))
        for n in range(self.COUNT + 1):
            x = self.x + n * s(12)
            if x < self.end:
                continue                                    # gone in at the monastery's gate
            if x > WIDTH + s(10):
                continue
            y = self.ridge.top_at(x) + s(1)
            bob = abs(math.sin(self.time / 400 + n)) * 0.6 * k
            if n == 0:                                      # the herder leads
                color = faded(self.scene, palette, palette["herder"], x, y)
                pygame.draw.line(surface, color, (x, y), (x, y - 5 * k - bob), max(1, int(k)))
                pygame.draw.circle(surface, color, (x, y - 6 * k - bob), max(1, k))
                continue
            color = faded(self.scene, palette, palette["yak"], x, y)
            pygame.draw.ellipse(surface, color, (x - 4 * k, y - 5 * k - bob, 8 * k, 4 * k))
            pygame.draw.circle(surface, color, (x - 4 * k, y - 4 * k - bob), max(1, 1.5 * k))      # head, down
            pygame.draw.line(surface, color, (x - 5 * k, y - 5.5 * k - bob), (x - 6 * k, y - 6.5 * k - bob), 1)  # a horn
            pygame.draw.rect(surface, color, (x - 3 * k, y - 4 * k - bob, 6 * k, 3 * k))    # shaggy skirt, legs
            for lx in (-3, 2):
                pygame.draw.line(surface, color, (x + lx * k, y - 2 * k), (x + lx * k + math.sin(self.time / 200 + n + lx) * k * 0.6, y), 1)
            pygame.draw.rect(surface, faded(self.scene, palette, palette["herder"], x, y), (x - 1 * k, y - 7 * k - bob, 3 * k, 2 * k))  # its load


class Paraglider(Visitor):
    # A paraglider, a bright arched wing with the pilot dangling below, drifting down the
    # valley on the right in long lazy turns. By day (needs "glider")
    #
    # Palette colors it uses:
    #   "glider", "glider_stripe", "pilot"

    TIME = 40000

    def can_come(self, palette):
        return "glider" in palette

    def start(self):
        super().start()
        self.age = 0.0
        self.x0 = WIDTH - s(random.uniform(45, 60))

    def update(self, dt):
        if not self.active:
            return
        self.age += dt
        if self.age > self.TIME:
            self.active = False

    def draw(self, surface, palette):
        if not self.active or "glider" not in palette:
            return
        t = self.age / self.TIME
        turn = math.sin(t * math.pi * 4)
        x = self.x0 + turn * s(22) + (1 - t) * s(70)
        y = s(120) + t * s(300)
        if t < 0.08:                                        # sails in from the right
            x += (1 - ease(t / 0.08)) * s(120)
        if t > 0.92:                                        # and away down the valley
            x += ease((t - 0.92) / 0.08) * s(120)
        k = 1.3 * UI_SCALE
        tilt = math.cos(t * math.pi * 4) * 0.25              # leaning into its turns
        cos, sin = math.cos(tilt), math.sin(tilt)

        def at(u, v):
            return (x + u * cos - v * sin, y + u * sin + v * cos)

        wing = pygame.Color(palette["glider"])
        stripe = pygame.Color(palette["glider_stripe"])
        pilot = pygame.Color(palette["pilot"])
        arch = [at(math.sin(a) * 13 * k, -math.cos(a) * 4 * k - 10 * k) for a in [i / 10 * 2.6 - 1.3 for i in range(11)]]
        under = [at(math.sin(a) * 12 * k, -math.cos(a) * 2.5 * k - 9 * k) for a in [i / 10 * 2.6 - 1.3 for i in range(11)]]
        pygame.draw.polygon(surface, wing, arch + list(reversed(under)))
        mid = len(arch) // 2
        pygame.draw.polygon(surface, stripe, [arch[mid - 1], arch[mid + 1], under[mid + 1], under[mid - 1]])
        body = at(0, 4 * k)
        for end in (under[1], under[-2], under[mid]):
            pygame.draw.line(surface, pilot.lerp(wing, 0.5), end, body, 1)
        pygame.draw.line(surface, pilot, body, at(0, 7 * k), max(1, int(k * 1.5)))
        pygame.draw.circle(surface, pilot, body, max(1, k))


class SnowLeopard(Visitor):
    # The rarest sight of all: a snow leopard padding softly onto the ledge on the left, its
    # long thick tail low behind it. It stops to sit and gaze out over the valley, tail tip
    # twitching, then slips away the way it came
    #
    # Palette colors it uses:
    #   "leopard", "leopard_spot"

    SPEED = 16
    STAY = (14000, 22000)
    SPOT = 74                       # where it sits, medium x

    def __init__(self, scene, ledge, ibex):
        super().__init__(scene)
        self.ledge = ledge
        self.ibex = ibex

    def can_come(self, palette):
        return "leopard" in palette and not self.ibex.present

    def start(self):
        super().start()
        self.x = -s(35)
        self.state = "in"
        self.age = 0.0
        self.time = 0.0
        self.stay = random.uniform(*self.STAY)
        self.facing = 1

    def update(self, dt):
        if not self.active:
            return
        self.time += dt
        self.age += dt
        step = s(self.SPEED) * dt / 1000
        if self.state == "in":
            self.x += step
            if self.x >= s(self.SPOT):
                self.state, self.age = "sit", 0.0
        elif self.state == "sit":
            if self.age > self.stay:
                self.state, self.facing = "out", -1
        else:
            self.x -= step
            if self.x < -s(40):
                self.active = False

    def draw(self, surface, palette):
        if not self.active or "leopard" not in palette:
            return
        x, f, k = self.x, self.facing, 1.3 * UI_SCALE
        y = self.ledge.top_at(max(0, x)) + s(1)
        fur = pygame.Color(palette["leopard"])
        spot = pygame.Color(palette["leopard_spot"])
        sit = ease(self.age / 1200) if self.state == "sit" else 0
        if self.state == "sit" and self.age > self.stay - 1200:
            sit = 1 - ease((self.age - self.stay + 1200) / 1200)
        walking = self.state != "sit"
        draw_shadow(surface, x, y, 28 * k, 4 * k, 0.3)
        # The tail: long and thick all the way, sweeping low behind and curling up at the tip
        twitch = math.sin(self.time / 260) * 1.5 * k
        tail = []
        for n in range(13):
            t = n / 12
            tail.append((x - f * (9 + t * 20) * k, y - 9 * k + math.sin(t * math.pi * 0.85) * 6 * k - t ** 3 * 9 * k + (twitch * t ** 2)
                         + sit * 4 * k * (1 - t)))
        for n, (tx, ty) in enumerate(tail):
            pygame.draw.circle(surface, fur, (tx, ty), 2.3 * k)
        for tx, ty in tail[3::3]:
            pygame.draw.circle(surface, spot, (tx, ty), max(1, 1.1 * k), 1)
        pygame.draw.circle(surface, spot, tail[-1], 1.6 * k)
        # Thick legs and big soft paws, padding along (the back ones folded under when it sits)
        for n, lx in enumerate((-8, -5, 5, 8)):
            if sit > 0.5 and lx < 0:
                continue
            swing = math.sin(self.time / 170 + n * 1.6) * 2 * k if walking else 0
            pygame.draw.line(surface, fur, (x + lx * k * f, y - 7 * k), (x + lx * k * f + swing, y - 1 * k), max(2, int(3 * k)))
            pygame.draw.circle(surface, fur, (x + lx * k * f + swing, y - 1 * k), 1.6 * k)
        # The body: haunches behind, shoulders in front (lifted when it sits)
        back_drop = sit * 4 * k
        hind = pygame.Rect(0, 0, 13 * k, 9 * k - back_drop * 0.5)
        hind.midbottom = (x - f * 4.5 * k, y - 3 * k)
        front = pygame.Rect(0, 0, 13 * k, 9 * k + sit * 3 * k)
        front.midbottom = (x + f * 3.5 * k, y - 4 * k)
        pygame.draw.ellipse(surface, fur, hind)
        pygame.draw.ellipse(surface, fur, front)
        for sx, sy in ((-7, -9), (-3, -10), (1, -10.5), (5, -10), (-5, -6.5), (0, -7), (4, -7)):
            lift = -sit * 3 * k if sx > 0 else back_drop * 0.3
            pygame.draw.circle(surface, spot, (x + f * sx * k, y + sy * k + lift), max(1, k * 0.9), 1)
        # A round head with small ears, lifted to gaze out when it sits
        head = (x + f * 10.5 * k, y - 12.5 * k - sit * 5 * k + (1 * k if walking else 0))
        for side in (-1, 1):
            pygame.draw.circle(surface, fur, (head[0] + side * 2 * k - f * 0.5 * k, head[1] - 3 * k), max(1, 1.3 * k))
        pygame.draw.circle(surface, fur, head, 3.6 * k)
        pygame.draw.ellipse(surface, fur, (head[0] + f * 1 * k - 2 * k, head[1] - 0.5 * k, 4.5 * k, 3.2 * k))      # its muzzle
        pygame.draw.circle(surface, spot, (head[0] + f * 1.4 * k, head[1] - 1 * k), max(1, k * 0.6))
        pygame.draw.circle(surface, spot, (head[0] + f * 3.4 * k, head[1] + 0.6 * k), max(1, k * 0.6))
