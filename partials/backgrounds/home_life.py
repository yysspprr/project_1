# Life at home: the cat asleep by the fire, and what passes by outside the window: a bird
# landing on the sill now and then (by day, when it's not raining or snowing), and once in
# a while someone walking past far off, under an umbrella if it's raining

import math

import random

import pygame

from partials.config import WIDTH, HEIGHT, s
from partials.backgrounds.base import Layer
from partials.backgrounds.helpers import Timer
from partials.backgrounds.brook_life import draw_shadow
from partials.backgrounds.hearth import FLOOR_TOP


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


class Cat(Layer):
    # A cat curled up asleep on the hearth in front of the fire, breathing slowly, an ear
    # twitching and the tip of its tail flicking now and then. Every minute or so it wakes:
    # lifts its head, sits up, washes a paw, gives a long stretch, turns round and curls up
    # again. At night the firelight catches its eyes when they're open
    #
    # Palette colors it uses:
    #   "cat", "cat_dark", "cat_light"      its coat, its stripes and outline, its chest and muzzle
    #   "cat_eye"                           its eyes

    SIZE = 2.0
    SLEEP = (40000, 90000)          # milliseconds asleep between wakings
    STAGES = (("lift", 1200), ("look", 2500), ("sit", 900), ("wash", 3800), ("stretch", 2200), ("turn", 900), ("curl", 1300))

    def __init__(self, scene, fireplace):
        super().__init__(scene)
        fx, fy = fireplace.fire_at()
        self.x = min(fx - s(4), WIDTH - s(34))
        self.y = s(FLOOR_TOP) + s(30)
        self.facing = -1                                    # its head toward the room
        self.time = 0
        self.stage = None                                   # asleep when None
        self.stage_age = 0
        self.sleep = random.uniform(10000, self.SLEEP[1])
        self.twitch = 0

    def update(self, dt):
        self.time += dt
        if self.stage is None:
            self.sleep -= dt
            if random.random() < dt / 6000:
                self.twitch = 300
            self.twitch = max(0, self.twitch - dt)
            if self.sleep <= 0:
                self.stage, self.stage_age = 0, 0
            return
        self.stage_age += dt
        name, length = self.STAGES[self.stage]
        if self.stage_age >= length:
            if name == "turn":
                self.facing = -self.facing
            self.stage += 1
            self.stage_age = 0
            if self.stage >= len(self.STAGES):
                self.stage = None
                self.sleep = random.uniform(*self.SLEEP)

    def pose(self):
        # How the cat is right now: how far up it is (0 curled, 1 sitting), and its stretch
        if self.stage is None:
            return 0.0, 0.0, 0.0
        name, length = self.STAGES[self.stage]
        t = self.stage_age / length
        head = 1.0
        if name == "lift":
            return 0.0, 0.0, ease(t)
        if name == "look":
            return 0.0, 0.0, head
        if name == "sit":
            return ease(t), 0.0, head
        if name in ("wash", "turn"):
            return 1.0, 0.0, head
        if name == "stretch":
            return 1.0 - math.sin(math.pi * t) * 0.6, math.sin(math.pi * t), head
        return 1.0 - ease(t), 0.0, 1.0 - ease(t)            # curl back down

    def draw(self, surface, palette):
        coat = pygame.Color(palette.get("cat", palette["muted"]))
        dark = pygame.Color(palette.get("cat_dark", palette["text"]))
        light = pygame.Color(palette.get("cat_light", palette["muted"]))
        eye = pygame.Color(palette.get("cat_eye", palette["text"]))
        k = s(self.SIZE)
        f, x, y = self.facing, self.x, self.y
        up, stretch, head_up = self.pose()
        draw_shadow(surface, x, y, 30 * k, 6 * k, 0.3)
        breath = math.sin(self.time / 900) * 0.6 * k if self.stage is None else 0
        name = self.STAGES[self.stage][0] if self.stage is not None else None

        # Body: a loaf curled on the floor, rising into a sitting cat
        body = pygame.Rect(0, 0, (24 - 9 * up) * k, (10 + 5 * up) * k + breath)
        body.midbottom = (x - f * up * 3 * k, y)
        if stretch:
            # A stretch: front down and forward, rear up
            body = pygame.Rect(0, 0, 26 * k, 9 * k)
            body.midbottom = (x, y - 2 * k * stretch)
        # The tail: wrapped round the front when curled or sitting, held up high in a stretch
        flick = math.sin(self.time / 140) * 2 * k if (self.stage is None and math.sin(self.time / 1700) > 0.7) else 0
        if stretch:
            tail = [(body.centerx - f * 12 * k, body.centery), (body.centerx - f * 16 * k, body.centery - 8 * k * stretch),
                    (body.centerx - f * 14 * k, body.centery - 14 * k * stretch)]
        else:
            tail = [(body.centerx - f * body.width / 2, y - 3 * k), (body.centerx - f * 2 * k, y + 1 * k),
                    (body.centerx + f * body.width / 2, y), (body.centerx + f * (body.width / 2 + 3 * k) + flick, y - 2 * k)]
        pygame.draw.lines(surface, coat, False, tail, max(2, int(k * 3)))
        pygame.draw.ellipse(surface, coat, body)
        if stretch:
            for u in (-10, -8, 9, 11):
                pygame.draw.line(surface, coat, (body.centerx - f * u * k, body.centery), (body.centerx - f * u * k * 1.1, y), max(1, int(k * 2)))
        for n in range(3):
            sx = body.left + body.width * (0.3 + n * 0.18)
            pygame.draw.line(surface, dark, (sx, body.top + 1), (sx + f * k, body.top + body.height * 0.4), 1)
        if up > 0.5 and not stretch:
            chest = pygame.Rect(0, 0, 6 * k, 8 * k * up)
            chest.midbottom = (body.centerx + f * body.width * 0.3, y - 1 * k)
            pygame.draw.ellipse(surface, light, chest)

        # Head: tucked down on its paws when asleep, raised when awake
        tucked = (body.centerx + f * (body.width / 2 - 2 * k), y - 4 * k)
        raised = (body.centerx + f * (body.width / 2 - 1 * k), body.top - 3 * k)
        if stretch:
            raised = (body.centerx + f * 13 * k, y - 6 * k)
        hx = tucked[0] + (raised[0] - tucked[0]) * head_up
        hy = tucked[1] + (raised[1] - tucked[1]) * head_up
        look = 0
        if name == "look":
            look = math.sin(self.stage_age / 500) * 1.5 * k
        if name == "wash":
            hy += math.sin(self.stage_age / 160) * 1.2 * k
        hx += look
        pygame.draw.circle(surface, coat, (hx, hy), 4.6 * k)
        twitch = 1.2 * k if self.twitch else 0
        for side in (-1, 1):
            ex = hx + side * 2.4 * k
            tip_y = hy - 7 * k + (twitch if side < 0 else 0)
            pygame.draw.polygon(surface, coat, [(ex - 1.8 * k, hy - 2.6 * k), (ex + 1.8 * k, hy - 2.6 * k), (ex + side * 0.5 * k, tip_y)])
            pygame.draw.polygon(surface, light, [(ex - 0.8 * k, hy - 3 * k), (ex + 0.8 * k, hy - 3 * k), (ex + side * 0.4 * k, tip_y + 2 * k)])
        pygame.draw.circle(surface, light, (hx + f * 2 * k, hy + 1.6 * k), 1.9 * k)
        awake = head_up > 0.5 and name != "wash"
        for side in (-1, 1):
            ey = hy - 0.5 * k
            ex = hx + f * 1.2 * k + side * 1.6 * k
            if awake:
                pygame.draw.circle(surface, eye, (ex, ey), max(1, k * 0.9))
                pygame.draw.line(surface, dark, (ex, ey - k * 0.6), (ex, ey + k * 0.6), 1)
            else:
                pygame.draw.line(surface, dark, (ex - k * 0.8, ey), (ex + k * 0.8, ey + k * 0.3), 1)
        if name == "wash":
            paw = (hx + f * 3 * k, hy + 2 * k + math.sin(self.stage_age / 160) * k)
            pygame.draw.line(surface, coat, (body.centerx + f * body.width * 0.3, y - 3 * k), paw, max(2, int(k * 2.2)))


class SillBird(Layer):
    # Now and then by day, a little bird lands on the outside sill (the bottom of the window),
    # hops about, pecks, cocks its head, and flies off again. Not when it's raining or snowing,
    # nor at night. Seen through the glass: the window draws it (draw_on_glass)
    #
    # Palette colors it uses:
    #   "sill_bird", "sill_bird_breast"

    EVERY = (25000, 60000)
    STAY = (5000, 11000)
    FLY = 700

    def __init__(self, scene, window, weather):
        super().__init__(scene)
        self.window = window
        self.weather = weather
        window.passing.append(self)
        self.timer = Timer(self.EVERY)
        self.timer.left = random.uniform(5000, 20000)
        self.bird = None
        self.time = 0
        self.palette = None

    def update(self, dt):
        self.time += dt
        if self.bird is None:
            day = self.palette is not None and "sill_bird" in self.palette
            if day and self.weather.kind in ("clear", "fog") and self.timer.tick(dt):
                r = self.window.glass()
                spot = r.left + r.width * random.uniform(0.55, 0.85)          # clear of the plant on the sill
                side = random.choice((-1, 1))
                self.bird = {"x": spot, "from": (spot + side * s(70), r.top + s(20)), "age": 0.0,
                             "stay": random.uniform(*self.STAY), "facing": -side, "hop": None}
            return
        bird = self.bird
        bird["age"] += dt
        r = self.window.glass()
        if self.FLY < bird["age"] < self.FLY + bird["stay"] and random.random() < dt / 1200 and bird["hop"] is None:
            bird["hop"] = 0.0
            bird["facing"] = random.choice((-1, 1))
        if bird["hop"] is not None:
            bird["hop"] += dt
            bird["x"] += bird["facing"] * s(14) * dt / 1000
            bird["x"] = max(r.left + s(8), min(r.right - s(8), bird["x"]))
            if bird["hop"] > 250:
                bird["hop"] = None
        if bird["age"] > self.FLY * 2 + bird["stay"]:
            self.bird = None

    def draw(self, surface, palette):
        self.palette = palette                              # it learns whether it's day from here

    def draw_on_glass(self, surface, palette):
        if self.bird is None or "sill_bird" not in palette:
            return
        bird = self.bird
        r = self.window.glass()
        ground = r.bottom - s(2)
        age, stay = bird["age"], bird["stay"]
        if age < self.FLY:                                  # flying in
            t = ease(age / self.FLY)
            x = bird["from"][0] + (bird["x"] - bird["from"][0]) * t
            y = bird["from"][1] + (ground - bird["from"][1]) * t
            flying = True
        elif age > self.FLY + stay:                         # flying off
            t = ease((age - self.FLY - stay) / self.FLY)
            x = bird["x"] + (bird["from"][0] - bird["x"]) * t
            y = ground + (r.top - s(20) - ground) * t
            flying = True
        else:
            x, y, flying = bird["x"], ground, False
            if bird["hop"] is not None:
                y -= math.sin(math.pi * bird["hop"] / 250) * s(4)
        body = pygame.Color(palette["sill_bird"])
        breast = pygame.Color(palette.get("sill_bird_breast", palette["sill_bird"]))
        k = s(1.2)
        f = bird["facing"] if not flying else (1 if (bird["x"] - bird["from"][0]) * (1 if age < self.FLY else -1) > 0 else -1)
        peck = (not flying) and math.sin(self.time / 250) > 0.85
        pygame.draw.polygon(surface, body, [(x - f * 3 * k, y - 3 * k), (x - f * 6.5 * k, y - 4.5 * k), (x - f * 5.5 * k, y - 2 * k)])
        pygame.draw.ellipse(surface, body, (x - 4 * k, y - 6 * k, 8 * k, 5.5 * k))
        pygame.draw.ellipse(surface, breast, (x - f * 0.5 * k - 2 * k, y - 4.5 * k, 4.5 * k, 4 * k))
        head = (x + f * 3.5 * k, y - (4 if peck else 7) * k)
        pygame.draw.circle(surface, body, head, 2.4 * k)
        pygame.draw.circle(surface, (20, 20, 20), (head[0] + f * 0.8 * k, head[1] - 0.4 * k), max(1, k * 0.5))
        pygame.draw.line(surface, (60, 50, 40), (head[0] + f * 2 * k, head[1]), (head[0] + f * 3.4 * k, head[1] + 0.6 * k), 1)
        if flying:
            flap = math.sin(age / 40) * 4 * k
            pygame.draw.polygon(surface, body, [(x - 2 * k, y - 4 * k), (x + 2 * k, y - 4 * k), (x - f * k, y - 8 * k - flap)])


class Passerby(Layer):
    # Once in a while someone walks past outside, far off along the hillside: a small figure
    # with a gently bobbing walk, under an umbrella if it's raining, or with a lantern at night.
    # Seen through the glass: the window draws them (draw_on_glass)
    #
    # Palette colors it uses:
    #   "passerby"                  their silhouette
    #   "umbrella"                  the umbrella
    #   "lantern_light"             the lantern they carry at night (optional)

    EVERY = (50000, 120000)
    SPEED = 6                       # pixels per second

    def __init__(self, scene, window, weather):
        super().__init__(scene)
        self.window = window
        self.weather = weather
        window.passing.append(self)
        self.timer = Timer(self.EVERY)
        self.timer.left = random.uniform(15000, 45000)
        self.walker = None
        self.time = 0

    def update(self, dt):
        self.time += dt
        r = self.window.glass()
        if self.walker is None:
            if self.weather.kind != "fog" and self.timer.tick(dt):
                direction = random.choice((-1, 1))
                self.walker = {"x": r.left - s(6) if direction > 0 else r.right + s(6), "dir": direction}
            return
        self.walker["x"] += self.walker["dir"] * s(self.SPEED) * dt / 1000
        if not (r.left - s(10) < self.walker["x"] < r.right + s(10)):
            self.walker = None

    def draw_on_glass(self, surface, palette):
        if self.walker is None:
            return
        r = self.window.glass()
        x = self.walker["x"]
        # They walk along the nearer hill's line
        y = r.top + r.height * 0.72 + math.sin((x - r.left) / s(20) + 2) * s(6) + s(1)
        bob = abs(math.sin(self.time / 260)) * s(0.6)
        color = pygame.Color(palette.get("passerby", palette["text"]))
        k = s(0.9)
        pygame.draw.line(surface, color, (x, y - bob), (x, y - 7 * k - bob), max(1, int(k * 1.6)))
        pygame.draw.circle(surface, color, (x, y - 8.5 * k - bob), max(1, k * 1.3))
        step = math.sin(self.time / 260) * k
        pygame.draw.line(surface, color, (x, y - 2 * k - bob), (x + step, y), 1)
        pygame.draw.line(surface, color, (x, y - 2 * k - bob), (x - step, y), 1)
        if self.weather.kind == "rain":
            umbrella = pygame.Color(palette.get("umbrella", palette["accent"]))
            top = y - 13 * k - bob
            pygame.draw.polygon(surface, umbrella, [(x - 5 * k, top + 3 * k), (x, top), (x + 5 * k, top + 3 * k)])
            pygame.draw.line(surface, color, (x, top + 3 * k), (x, y - 7 * k - bob), 1)
        elif "lantern_light" in palette:
            light = pygame.Color(palette["lantern_light"])
            pygame.draw.circle(surface, light, (x + self.walker["dir"] * 2.5 * k, y - 4 * k - bob), max(1, k))
