# Weather in the mountains: snow streaming off the great summit in the wind, shadows of
# clouds sliding over the snowfields (by day), and now and then an avalanche billowing down
# a face far away, or the mist pouring over a ridge like a slow waterfall
#
# Most of it is made of soft round puffs (see Puffs), painted ahead of time at a handful of
# sizes so a frame only has to blit them

import math

import random

import pygame

from partials.config import WIDTH, HEIGHT, s
from partials.backgrounds.base import Layer
from partials.backgrounds.helpers import Timer


class Puffs:
    # Soft round puffs of one color at a range of sizes, faint at the edge and thicker in
    # the middle. get(radius) gives the nearest one; set its alpha before blitting it

    SIZES = (2, 3, 4, 5, 6, 8, 10, 12, 14, 17, 20, 24, 28, 33, 40, 48)   # radii at the medium size

    def __init__(self, color):
        color = pygame.Color(color)
        self.radii = []
        self.sprites = []
        for size in self.SIZES:
            radius = max(2, s(size))
            if self.radii and radius == self.radii[-1]:
                continue
            self.radii.append(radius)
            self.sprites.append(self.paint(radius, color))

    @staticmethod
    def paint(radius, color):
        side = radius * 2 + 2
        sprite = pygame.Surface((side, side), pygame.SRCALPHA)
        sprite.fill((color.r, color.g, color.b, 0))
        rings = 8
        for ring in range(rings):
            paint = pygame.Color(color.r, color.g, color.b, int(255 * ((ring + 1) / rings) ** 1.4))
            pygame.draw.circle(sprite, paint, (side / 2, side / 2), radius * (1 - ring / rings))
        small = pygame.transform.smoothscale(sprite, (max(1, side // 3), max(1, side // 3)))
        return pygame.transform.smoothscale(small, (side, side))

    def get(self, radius):
        best = 0
        for i, r in enumerate(self.radii):
            if abs(r - radius) < abs(self.radii[best] - radius):
                best = i
        return self.sprites[best]

    def draw(self, surface, x, y, radius, strength):
        # One puff centered on (x, y); strength 0-1
        if strength <= 0.01:
            return
        sprite = self.get(radius)
        sprite.set_alpha(int(255 * min(1, strength)))
        surface.blit(sprite, (x - sprite.get_width() / 2, y - sprite.get_height() / 2))


class SummitPlume(Layer):
    # Snow torn off the great summit by the high winds, streaming away to the left in a long
    # thinning plume. Stronger when it's windy, wilder in a gust
    #
    # Palette colors it uses:
    #   "plume"

    RATE = 9                        # puffs a second in a normal breeze
    LIFE = (4500, 7500)             # milliseconds a puff lasts
    SPEED = 16                      # pixels a second it streams away, in a normal breeze
    SIZE = (3, 18)                  # a puff's radius as it leaves the summit and at the end
    STRENGTH = 0.85                 # how thick a puff is at its thickest

    def __init__(self, scene, summit):
        super().__init__(scene)
        self.summit = summit
        self.puffs = []
        self.waiting = 0
        self.palette = None
        self.sprites = None
        for i in range(30):             # already blowing when the scene appears
            self.update(200)

    def update(self, dt):
        wind = self.scene.weather["wind"] + self.scene.weather.get("gust", 0)
        self.waiting -= dt * self.RATE * max(0.3, wind) / 1000
        while self.waiting <= 0:
            self.waiting += 1
            self.puffs.append({"x": self.summit[0] + random.uniform(-s(3), s(4)), "y": self.summit[1] + random.uniform(s(1), s(6)),
                               "age": 0.0, "life": random.uniform(*self.LIFE), "rise": random.uniform(-2, 4),
                               "speed": random.uniform(0.7, 1.3)})
        seconds = dt / 1000
        for p in self.puffs:
            p["age"] += dt
            p["x"] -= s(self.SPEED) * wind * p["speed"] * seconds
            p["y"] += s(p["rise"]) * seconds
        self.puffs = [p for p in self.puffs if p["age"] < p["life"]]

    def draw(self, surface, palette):
        if self.palette is not palette:
            self.sprites = Puffs(palette["plume"])
            self.palette = palette
        wind = self.scene.weather["wind"] + self.scene.weather.get("gust", 0)
        thick = self.STRENGTH * min(1.2, 0.45 + 0.4 * wind)
        for p in self.puffs:
            t = p["age"] / p["life"]
            radius = s(self.SIZE[0]) + (s(self.SIZE[1]) - s(self.SIZE[0])) * t ** 0.7
            fade = min(1, t * 10) * (1 - t) ** 1.3
            self.sprites.draw(surface, p["x"], p["y"], radius, thick * fade * self.scene.keep(p["x"], 0.3))


class CloudShadows(Layer):
    # By day, the shadows of passing clouds sliding slowly over the snowfields, darkening the
    # peaks as they go. Only shows on the peaks themselves, and only when the sun is out
    #
    # Palette colors it uses:
    #   "cloud_shadow"              the color of snow in a cloud's shadow (no shadows without it)

    COUNT = 2
    SPEED = 6                       # pixels a second, in a normal breeze
    STRENGTH = 0.45

    def __init__(self, scene, peaks):
        super().__init__(scene)
        self.peaks = peaks
        self.shadows = [self.make_shadow(random.uniform(-s(60), WIDTH + s(60))) for i in range(self.COUNT)]
        self.palette = None

    def make_shadow(self, x):
        return {"x": x, "y": s(random.uniform(60, 190)), "w": s(random.uniform(130, 220)), "h": s(random.uniform(50, 90))}

    def update(self, dt):
        wind = self.scene.weather["wind"]
        for i, shade in enumerate(self.shadows):
            shade["x"] -= s(self.SPEED) * wind * dt / 1000
            if shade["x"] + shade["w"] < -s(20):
                self.shadows[i] = self.make_shadow(WIDTH + s(20) + random.uniform(0, s(200)))

    def paint(self, palette):
        # The peaks' shape (to cut the shadows to) and one soft shadow to stretch
        self.shape = self.peaks.image.copy()
        self.shape.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
        self.layer = pygame.Surface(self.shape.get_size(), pygame.SRCALPHA)
        self.blob = Puffs.paint(s(48), pygame.Color(palette["cloud_shadow"]))
        self.palette = palette

    def draw(self, surface, palette):
        if "cloud_shadow" not in palette or self.peaks.image is None:
            return
        if self.palette is not palette:
            self.paint(palette)
        light = max(0, min(1, self.scene.weather["light"]))
        self.layer.fill((0, 0, 0, 0))
        for shade in self.shadows:
            blob = pygame.transform.scale(self.blob, (int(shade["w"]), int(shade["h"])))
            blob.set_alpha(int(255 * self.STRENGTH * light))
            self.layer.blit(blob, (shade["x"], shade["y"] - shade["h"] / 2))
        self.layer.blit(self.shape, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surface.blit(self.layer, (0, 0))


class Avalanche(Layer):
    # Every few minutes, far away on one of the great faces, a slab of snow breaks loose:
    # a white streak runs down the slope, a billowing cloud boiling up behind its front,
    # and the cloud lingers and slowly settles long after the snow has stopped
    #
    # Palette colors it uses:
    #   "plume"                     the snow cloud

    WAIT = (100000, 220000)         # milliseconds between avalanches
    FIRST = (40000, 100000)
    RUN = 6000                      # how long the snow takes to run down the face
    LIFE = (5000, 9000)             # how long each puff of its cloud lingers

    def __init__(self, scene, peaks):
        super().__init__(scene)
        self.peaks = peaks
        self.timer = Timer(self.WAIT)
        self.timer.left = random.uniform(*self.FIRST)
        self.run = None
        self.puffs = []
        self.palette = None

    def start(self):
        # High on the shadowed face of one of the two great peaks (where the white cloud shows
        # up best), sliding down the fall line
        big, right = self.peaks.summits[2], self.peaks.summits[1]
        if random.random() < 0.6:
            x0, y0, lean = big[0] - s(random.uniform(8, 24)), big[1] + s(random.uniform(30, 50)), random.uniform(-0.4, -0.15)
        else:
            x0, y0, lean = right[0] - s(random.uniform(6, 18)), right[1] + s(random.uniform(22, 36)), random.uniform(-0.3, -0.1)
        self.run = {"x": x0, "y": y0, "lean": lean, "age": 0.0, "end": self.peaks.base - s(20), "spawn": 0.0}

    def update(self, dt):
        if self.run is None and self.timer.tick(dt):
            self.start()
        if self.run is not None:
            run = self.run
            run["age"] += dt
            t = min(1, run["age"] / self.RUN)
            speed = 0.4 + 1.2 * t                       # it gathers speed
            drop = (run["end"] - run["y"]) * dt / self.RUN * speed
            run["y"] += drop
            run["x"] += drop * run["lean"]
            run["spawn"] -= dt
            if run["spawn"] <= 0:
                run["spawn"] = 90
                self.puffs.append({"x": run["x"] + random.uniform(-s(3), s(3)), "y": run["y"], "age": 0.0,
                                   "life": random.uniform(*self.LIFE), "grow": s(random.uniform(6, 14)) * (0.5 + t)})
            if run["y"] >= run["end"] or run["age"] > self.RUN * 1.6:
                self.run = None
        for p in self.puffs:
            p["age"] += dt
            p["y"] -= s(1.5) * dt / 1000                # the cloud billows up a little
        self.puffs = [p for p in self.puffs if p["age"] < p["life"]]

    def draw(self, surface, palette):
        if self.run is None and not self.puffs:
            return
        if self.palette is not palette:
            self.sprites = Puffs(palette["plume"])
            self.palette = palette
        for p in self.puffs:
            t = p["age"] / p["life"]
            radius = s(2) + p["grow"] * min(1, t * 2.5) ** 0.6
            fade = min(1, t * 8) * (1 - t) ** 1.2
            self.sprites.draw(surface, p["x"], p["y"] - radius * 0.3, radius, 0.8 * fade * self.scene.keep(p["x"], 0.6))
        if self.run is not None:                        # the snow itself, a bright streak at the front
            self.sprites.draw(surface, self.run["x"], self.run["y"], s(3), 0.9)


class MistFall(Layer):
    # Now and then the mist rises behind a ridge on the right and spills over its crest,
    # pouring slowly down the near slope like a waterfall and melting away into the valley
    #
    # Palette colors it uses:
    #   "mist"

    WAIT = (90000, 200000)          # milliseconds between falls
    FIRST = (25000, 70000)
    TIME = (35000, 55000)           # how long it pours, rising and fading at each end
    RATE = 7                        # puffs a second at its fullest
    LIFE = (7000, 11000)
    FLOW = (-5, 9)                  # how it flows: pixels a second sideways and down

    def __init__(self, scene, ridge):
        super().__init__(scene)
        self.ridge = ridge
        self.timer = Timer(self.WAIT)
        self.timer.left = random.uniform(*self.FIRST)
        self.age = None
        self.puffs = []
        self.waiting = 0
        self.palette = None

    def start(self):
        self.age = 0.0
        self.time = random.uniform(*self.TIME)
        self.left = WIDTH - s(random.uniform(70, 85))     # where along the crest it spills over
        self.right = WIDTH + s(5)

    def strength(self):
        if self.age is None:
            return 0
        edge = 6000
        return max(0, min(1, self.age / edge, (self.time - self.age) / edge))

    def update(self, dt):
        if self.age is None:
            if self.timer.tick(dt):
                self.start()
        else:
            self.age += dt
            self.waiting -= dt * self.RATE * self.strength() / 1000
            while self.waiting <= 0:
                self.waiting += 1
                x = random.uniform(self.left, self.right)
                self.puffs.append({"x": x, "y": self.ridge.top_at(x) - s(random.uniform(0, 4)), "age": 0.0,
                                   "life": random.uniform(*self.LIFE), "speed": random.uniform(0.7, 1.2)})
            if self.age > self.time:
                self.age = None
        seconds = dt / 1000
        wind = self.scene.weather["wind"]
        for p in self.puffs:
            p["age"] += dt
            t = p["age"] / p["life"]
            p["x"] += s(self.FLOW[0]) * (0.5 + 0.5 * wind) * p["speed"] * seconds
            p["y"] += s(self.FLOW[1]) * p["speed"] * min(1, t * 3) * seconds     # tips over the crest, then falls
        self.puffs = [p for p in self.puffs if p["age"] < p["life"]]

    def draw(self, surface, palette):
        if not self.puffs:
            return
        if self.palette is not palette:
            self.sprites = Puffs(palette["mist"])
            self.palette = palette
        for p in self.puffs:
            t = p["age"] / p["life"]
            radius = s(7) + s(16) * t
            fade = min(1, t * 5) * (1 - t) ** 1.3
            self.sprites.draw(surface, p["x"], p["y"], radius, 0.55 * fade)
