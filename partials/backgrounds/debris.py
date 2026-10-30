# Little things floating on the surface: leaves and twigs

import math

import random

import pygame

from partials.config import WIDTH, s
from partials.backgrounds.base import Layer
from partials.backgrounds.helpers import Swell, make_jitter


def leaf_shape(points=14):
    # An almond-shaped leaf, a bit wider toward the stem, 2 units long, pointing right.
    # Returns the outline and the line down its middle (stem included)
    outline = []
    for i in range(points):
        angle = 2 * math.pi * i / points
        width = 0.42 * (0.75 - 0.25 * math.cos(angle))     # wider at the back, narrow at the tip
        outline.append((math.cos(angle), width * math.sin(angle)))
    middle = [(-1.35, 0.05), (-1, 0), (0.85, 0)]
    return outline, middle


def twig_shape():
    # A thin, slightly crooked stick with one short side branch, about 2 units long.
    # Returns no outline (it's just lines) and a list of lines
    bend = random.uniform(-0.12, 0.12)
    stick = [(-1, 0), (-0.3, bend), (0.4, -bend * 0.5), (1, bend * 0.4)]
    fork = random.uniform(-0.2, 0.4)
    side = random.choice((-1, 1))
    branch = [(fork, bend * 0.3), (fork + 0.35, side * 0.3)]
    return None, [stick, branch]


class FloatingDebris(Layer):
    # Leaves and twigs lying flat on the surface, seen through the scene's perspective.
    # They drift with the wind, slowly turn one way and then the other, get pushed and
    # bob when something lands close by, and now and then one sinks and a new one drifts in
    #
    # Palette colors it uses:
    #   "leaves"        a list of leaf colors (falls back to "muted")
    #   "twig"          the twig color (falls back to "muted")

    COUNT = 6                       # how many things float at once
    TWIGS = 0.3                     # share of them that are twigs
    LEAF_SIZE = (14, 21)            # half the leaf's length, up close, in pixels
    TWIG_SIZE = (22, 34)            # half the twig's length, up close, in pixels
    LINE_WIDTH = 2                  # outline and twig thickness, up close
    STRENGTH = 0.85                 # how strongly they show (0 = invisible, 1 = full color)
    OUTLINE = 0.35                  # how much darker the outline is than the fill

    DRIFT = 10                      # pixels per second sideways, up close, at a wind of 1
    WANDER = 3                      # pixels per second each one strays on its own, up close
    SPIN = 10                       # most degrees per second one turns
    LIFETIME = (25000, 50000)       # milliseconds before it soaks through and sinks
    FADE_TIME = 2500                # milliseconds to fade in or sink away
    SPREAD = 0.15                   # how much they crowd toward the back (see Perspective.random_y)

    REACH = 45                      # a drop this close pushes it, up close, in pixels
    PUSH = 30                       # how hard: pixels per second, right next to the drop
    PUSH_FADE = 500                 # milliseconds for a push to halve
    BOB_TIME = 700                  # milliseconds a bob lasts
    BOB_DEPTH = 2                   # how far it dips, up close, in pixels
    JITTER = 0.06                   # outline wobble, as a share of its size

    def __init__(self, scene):
        super().__init__(scene)
        self.wind = 1               # the background can change this; 1 is a normal breeze
        self.items = []
        for i in range(self.COUNT):
            item = self.make_item(x=random.uniform(0, WIDTH))
            item["age"] = random.randint(self.FADE_TIME, item["lifetime"] // 2)     # already floating
            self.items.append(item)

    def make_item(self, x=None):
        view = self.scene.view
        y = view.random_y(self.SPREAD)
        is_twig = random.random() < self.TWIGS
        if is_twig:
            outline, lines = twig_shape()
            half_length = random.randint(*self.TWIG_SIZE)
        else:
            outline, middle = leaf_shape()
            lines = [middle]
            half_length = random.randint(*self.LEAF_SIZE)

        if x is None:
            x = random.uniform(0, WIDTH)

        return {
            "twig": is_twig,
            "outline": outline,
            "lines": lines,
            "jitter": make_jitter(len(outline), self.JITTER) if outline else None,
            "x": x,
            "y": y,
            "length": s(half_length),
            "angle": random.uniform(0, 360),
            "spin": Swell(-self.SPIN, self.SPIN, (3000, 8000)),        # turns one way, then the other
            "wander": random.uniform(-1, 1) * s(self.WANDER),           # its own little current
            "color_pick": random.random(),
            "push_x": 0,
            "push_y": 0,
            "kick": 0,                                                  # extra spin from a nearby drop
            "bob": self.BOB_TIME,                                       # not bobbing
            "age": 0,
            "lifetime": random.randint(*self.LIFETIME),
        }

    # ---- Reacting to drops ----

    def nudge(self, x, y):
        # Something landed at (x, y): push away whatever floats close by, and make it bob
        view = self.scene.view
        for item in self.items:
            size = view.scale(item["y"])
            reach = s(self.REACH) * size
            # Measure on the surface itself: up and down on screen is squashed
            dx = item["x"] - x
            dy = (item["y"] - y) / view.flatten(item["y"])
            distance = math.hypot(dx, dy)
            if distance < reach:
                closeness = 1 - distance / reach
                if distance > 0:
                    item["push_x"] += dx / distance * s(self.PUSH) * size * closeness
                    item["push_y"] += dy / distance * s(self.PUSH) * size * closeness * view.flatten(item["y"])
                item["bob"] = 0
                item["kick"] += random.uniform(-2, 2) * self.SPIN * closeness

    # ---- Layer methods ----

    def update(self, dt):
        view = self.scene.view
        seconds = dt / 1000
        slow_down = 0.5 ** (dt / self.PUSH_FADE)

        for i, item in enumerate(self.items):
            size = view.scale(item["y"])
            item["spin"].update(dt)
            item["angle"] += (item["spin"].value + item["kick"]) * seconds
            item["x"] += (s(self.DRIFT) * self.wind + item["wander"]) * size * seconds + item["push_x"] * seconds
            item["y"] += item["push_y"] * seconds
            item["push_x"] *= slow_down
            item["push_y"] *= slow_down
            item["kick"] *= slow_down
            item["bob"] += dt
            item["age"] += dt

            # Gone: sunk, or drifted out of the window. A new one takes its place
            margin = item["length"] * 2
            if item["age"] >= item["lifetime"]:
                self.items[i] = self.make_item()
            elif item["x"] > WIDTH + margin:
                self.items[i] = self.make_item(x=-margin)
                self.items[i]["age"] = self.FADE_TIME           # drifts in whole, no fading in
            elif item["x"] < -margin:
                self.items[i] = self.make_item(x=WIDTH + margin)
                self.items[i]["age"] = self.FADE_TIME

    def wobble(self):
        for item in self.items:
            if item["outline"]:
                item["jitter"] = make_jitter(len(item["outline"]), self.JITTER)

    def presence(self, item):
        # 0 to 1: fades in when it appears, fades out as it sinks
        fade_in = item["age"] / self.FADE_TIME
        fade_out = (item["lifetime"] - item["age"]) / self.FADE_TIME
        return max(0, min(1, fade_in, fade_out))

    def place(self, item, points, jitter=None):
        # Turn the item's own shape into points on the screen:
        # sized, turned, then squashed like everything lying on the surface
        view = self.scene.view
        size = item["length"] * view.scale(item["y"])
        flatten = view.flatten(item["y"])
        turn = math.radians(item["angle"])
        cos, sin = math.cos(turn), math.sin(turn)

        # A bob dips it down and back up
        bob_y = 0
        if item["bob"] < self.BOB_TIME:
            progress = item["bob"] / self.BOB_TIME
            bob_y = math.sin(progress * math.pi * 2) * (1 - progress) * s(self.BOB_DEPTH) * view.scale(item["y"])

        placed = []
        for i, (u, v) in enumerate(points):
            push = 1 + (jitter[i] if jitter else 0)
            u, v = u * push, v * push
            placed.append((item["x"] + (u * cos - v * sin) * size,
                           item["y"] + bob_y + (u * sin + v * cos) * size * flatten))
        return placed

    def draw(self, surface, palette):
        view = self.scene.view
        leaf_colors = palette.get("leaves", [palette["muted"]])
        twig_color = pygame.Color(palette.get("twig", palette["muted"]))

        for item in self.items:
            water = self.scene.color_at(palette, item["y"])
            strength = self.STRENGTH * view.clarity(item["y"]) * self.presence(item)
            if strength <= 0:
                continue
            line = max(1, round(s(self.LINE_WIDTH) * view.scale(item["y"])))

            if item["twig"]:
                color = water.lerp(twig_color, strength)
                for points in item["lines"]:
                    pygame.draw.lines(surface, color, False, self.place(item, points), line)
                continue

            base = pygame.Color(leaf_colors[int(item["color_pick"] * len(leaf_colors))])
            fill = water.lerp(base, strength)
            edge = water.lerp(base.lerp(pygame.Color(0, 0, 0), self.OUTLINE), strength)

            outline = self.place(item, item["outline"], item["jitter"])
            pygame.draw.polygon(surface, fill, outline)
            pygame.draw.lines(surface, edge, True, outline, line)
            pygame.draw.lines(surface, edge, False, self.place(item, item["lines"][0]), line)
