# The brook's moving water: lines of current running downstream, little ripples trailing
# behind the stones, and leaves drifting along on the surface. Everything moves with the
# water, so it slows down where the brook widens into its calm pool

import math

import random

import pygame

from partials.config import HEIGHT, s
from partials.backgrounds.base import Layer
from partials.backgrounds.helpers import Timer
from partials.backgrounds.brook import draw_leaf


def flow_speed(course, x, y, wind=1):
    # How fast the water moves at (x, y), in pixels per second: fastest in the middle of the
    # channel, slow along the edges, and slow in the wide pool (the same water spread wider)
    half = max(course.half_width(y), 1)
    across = min(1, abs(x - course.center(y)) / half)
    narrow = course.view.scale(y) * s(course.WIDTH) / half
    return s(BrookCurrent.SPEED) * narrow * (1 - 0.6 * across * across) * (0.85 + 0.15 * wind)


class BrookCurrent(Layer):
    # Short pale lines drifting down the channel, each bending with the water's course.
    # Each one fades in, travels a while and fades out again, so they never pop
    #
    # Palette colors it uses:
    #   "ripple"                the lines at their brightest (they fade into the water)

    COUNT = 34
    SPEED = 30                      # pixels per second in the middle of the channel
    LENGTH = (8, 20)                # pixels at the medium size
    LIFE = (2500, 5000)             # milliseconds each line lasts
    STRENGTH = 0.9                  # how close to "ripple" they get at their brightest
    QUIET = 0.6                     # how much they soften behind the game's middle column

    def __init__(self, scene, course, water):
        super().__init__(scene)
        self.course = course
        self.water = water
        self.lines = [self.new_line(random.uniform(0, HEIGHT), random.random()) for i in range(self.COUNT)]

    def new_line(self, y, age=0.0):
        life = random.uniform(*self.LIFE)
        return {"across": random.uniform(-0.8, 0.8), "y": y, "length": s(random.uniform(*self.LENGTH)),
                "life": life, "age": age * life, "wiggle": random.uniform(0, 2 * math.pi)}

    def update(self, dt):
        course = self.course
        wind = self.scene.weather.get("wind", 1)
        for i, line in enumerate(self.lines):
            x = course.center(line["y"]) + line["across"] * course.half_width(line["y"])
            line["y"] += flow_speed(course, x, line["y"], wind) * dt / 1000
            line["age"] += dt
            if line["age"] > line["life"] or line["y"] > HEIGHT + s(25):
                self.lines[i] = self.new_line(random.uniform(-s(20), HEIGHT))

    def draw(self, surface, palette):
        course = self.course
        ripple = pygame.Color(palette.get("ripple", palette.get("shallows", palette["text"])))
        width = max(1, s(1))
        for line in self.lines:
            fade = math.sin(math.pi * line["age"] / line["life"])
            points = []
            for k in range(4):
                y = line["y"] - line["length"] * k / 3
                wiggle = math.sin(line["wiggle"] + y / s(9)) * s(1.2)
                points.append((course.center(y) + line["across"] * course.half_width(y) + wiggle, y))
            x, y = points[0]
            strength = self.STRENGTH * fade * self.scene.keep(x, self.QUIET)
            color = self.water.water_color(palette, x, y).lerp(ripple, max(0, min(1, strength)))
            pygame.draw.lines(surface, color, False, points, width)


class BrookWakes(Layer):
    # Little curved ripples trailing behind each stone out in the water: one forms just
    # below the stone every second or so, slides downstream, widens and fades
    #
    # Palette colors it uses:
    #   "ripple"                the ripples when fresh (they fade into the water)

    EVERY = (800, 1500)             # milliseconds between ripples behind each stone
    LIFE = 1800                     # milliseconds each ripple lasts
    STRENGTH = 0.8
    QUIET = 0.6

    def __init__(self, scene, course, water, rocks):
        super().__init__(scene)
        self.course = course
        self.water = water
        self.stones = [stone for stone in rocks.rocks if stone["wet"]]
        self.timers = [Timer(self.EVERY) for stone in self.stones]
        for timer in self.timers:
            timer.left = random.uniform(0, self.EVERY[1])     # don't all start in step
        self.ripples = []

    def update(self, dt):
        wind = self.scene.weather.get("wind", 1)
        for stone, timer in zip(self.stones, self.timers):
            if timer.tick(dt):
                self.ripples.append({"stone": stone, "age": 0.0,
                                     "speed": flow_speed(self.course, stone["x"], stone["y"], wind) * 0.6})
        for ripple in self.ripples:
            ripple["age"] += dt
        self.ripples = [ripple for ripple in self.ripples if ripple["age"] < self.LIFE]

    def draw(self, surface, palette):
        color_of = pygame.Color(palette.get("ripple", palette.get("shallows", palette["text"])))
        width = max(1, s(1))
        for ripple in self.ripples:
            stone = ripple["stone"]
            t = ripple["age"] / self.LIFE
            size = stone["size"]
            y = stone["y"] + size * 0.55 + ripple["speed"] * ripple["age"] / 1000
            step_x, step_y = self.course.direction(y)
            x = stone["x"] + (y - stone["y"]) * step_x / step_y          # follow the water's bend
            radius = size * (0.8 + 0.7 * t)
            fade = min(1, t * 6) * (1 - t)                                # quick to form, slow to go
            strength = self.STRENGTH * fade * self.scene.keep(x, self.QUIET)
            color = self.water.water_color(palette, x, y).lerp(color_of, max(0, min(1, strength)))
            # The lower half of a flat ellipse: a curve bowing downstream
            flat = 0.9 * stone["squash"]
            pygame.draw.arc(surface, color, (x - radius, y - radius * flat / 2, radius * 2, radius * flat),
                            math.pi * 1.12, math.pi * 1.88, width)


class DriftingLeaves(Layer):
    # A few fallen leaves floating down the brook, turning slowly as they go and steering
    # around the stones instead of sliding over them. When one leaves the bottom of the
    # window, another drops in at the top
    #
    # Palette colors it uses:
    #   "litter"                a list of fallen leaf colors

    COUNT = 6
    SIZE = (4.5, 7)                 # half a leaf's length, pixels at the medium size
    SPEED = 0.8                     # leaves ride a little slower than the current lines
    SPIN = 0.35                     # how fast they turn, at most, in radians per second
    SWERVE = 0.7                    # how hard they steer around stones

    def __init__(self, scene, course, water, rocks):
        super().__init__(scene)
        self.course = course
        self.water = water
        self.stones = [stone for stone in rocks.rocks if stone["wet"]]
        self.leaves = [self.new_leaf(random.uniform(0, HEIGHT)) for i in range(self.COUNT)]

    def new_leaf(self, y):
        return {"across": random.uniform(-0.7, 0.7), "y": y, "angle": random.uniform(0, math.pi),
                "spin": random.uniform(-self.SPIN, self.SPIN), "size": s(random.uniform(*self.SIZE)),
                "pick": random.random()}

    def update(self, dt):
        course = self.course
        wind = self.scene.weather.get("wind", 1)
        for i, leaf in enumerate(self.leaves):
            half = max(course.half_width(leaf["y"]), 1)
            x = course.center(leaf["y"]) + leaf["across"] * half
            leaf["y"] += flow_speed(course, x, leaf["y"], wind) * self.SPEED * dt / 1000
            leaf["angle"] += leaf["spin"] * dt / 1000
            # Steer around any stone just ahead
            for stone in self.stones:
                gap = stone["size"] * 1.3 + leaf["size"]
                ahead = stone["y"] - leaf["y"]
                if -gap * 0.5 < ahead < gap * 1.6 and abs(stone["x"] - x) < gap:
                    away = 1 if x >= stone["x"] else -1
                    leaf["across"] += away * self.SWERVE * dt / 1000
            leaf["across"] = max(-0.85, min(0.85, leaf["across"]))
            if leaf["y"] > HEIGHT + s(15):
                self.leaves[i] = self.new_leaf(-s(15))

    def draw(self, surface, palette):
        course = self.course
        colors = [pygame.Color(color) for color in palette.get("litter", [palette["muted"]])]
        for leaf in self.leaves:
            x = course.center(leaf["y"]) + leaf["across"] * course.half_width(leaf["y"])
            y = leaf["y"]
            shadow = self.water.water_color(palette, x, y).lerp((0, 0, 0), 0.25)
            color = colors[int(leaf["pick"] * len(colors)) % len(colors)]
            view = self.scene.view
            draw_leaf(surface, color, shadow, x, y, leaf["angle"], leaf["size"] * view.scale(y),
                      view.flatten(y) / view.near_flatten)
