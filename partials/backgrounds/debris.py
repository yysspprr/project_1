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
    # They drift with the wind (the scene's weather["wind"]), slowly turn one way and then
    # the other, rock in a storm, and get pushed and bob when something lands close by.
    # A drop that hits one dead on makes it dip and sends a ripple out from it
    # (through on_ripple, so it doesn't need to know who draws ripples).
    # Each casts a soft shadow on the water, soaks up water and darkens as it ages,
    # and now and then one sinks and a new one drifts in
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

    HIT_BOB = 2.2                   # a drop landing right on it makes it bob this much harder
    STORM_ROCK = 1.2                # how far it rocks in a full storm, up close, in pixels
    SHADOW = (0.22, 0.12)           # how dark each of the two shadow steps is (0 = none, 1 = black)
    SHADOW_OFFSET = (2, 4)          # how far down each step falls, up close, in pixels
    SOAK = 0.4                      # how much darker it gets by the time it sinks
    QUIET = 0.5                     # how much it fades behind the game's text (0 = not at all, 1 = like ripples)

    def __init__(self, scene, on_ripple=None):
        super().__init__(scene)
        self.on_ripple = on_ripple  # called as on_ripple(x, y, size=..., ...) to make a ripple
        self.time = 0               # milliseconds since it started: keeps the rocking going
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
            "bob_size": 1,
            "rock": random.uniform(0, 2 * math.pi),                     # where it is in its rocking
            "age": 0,
            "lifetime": random.randint(*self.LIFETIME),
        }

    # ---- Reacting to drops ----

    def nudge(self, x, y):
        # Something landed at (x, y): push away whatever floats close by, and make it bob.
        # Returns True if it landed right on top of something
        view = self.scene.view
        hit_any = False
        for item in self.items:
            size = view.scale(item["y"])
            reach = s(self.REACH) * size
            # Measure on the surface itself: up and down on screen is squashed
            dx = item["x"] - x
            dy = (item["y"] - y) / view.flatten(item["y"])
            distance = math.hypot(dx, dy)
            if distance >= reach:
                continue

            closeness = 1 - distance / reach
            item["bob"] = 0
            item["bob_size"] = closeness
            item["kick"] += random.uniform(-2, 2) * self.SPIN * closeness

            if distance < item["length"] * size * 0.7 and self.presence(item) > 0.5:
                # Dead on: it dips hard and the ripple starts from it, not from the drop
                hit_any = True
                item["bob_size"] = self.HIT_BOB
                if self.on_ripple is not None:
                    self.on_ripple(item["x"], item["y"], size=0.8, echoes=1, splash=False)
            elif distance > 0:
                item["push_x"] += dx / distance * s(self.PUSH) * size * closeness
                item["push_y"] += dy / distance * s(self.PUSH) * size * closeness * view.flatten(item["y"])
        return hit_any

    # ---- Layer methods ----

    def update(self, dt):
        view = self.scene.view
        seconds = dt / 1000
        slow_down = 0.5 ** (dt / self.PUSH_FADE)

        self.time += dt
        wind = self.scene.weather["wind"]

        for i, item in enumerate(self.items):
            size = view.scale(item["y"])
            item["spin"].update(dt)
            item["angle"] += (item["spin"].value + item["kick"]) * seconds
            item["x"] += (s(self.DRIFT) * wind + item["wander"]) * size * seconds + item["push_x"] * seconds
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

    def bob_offset(self, item):
        scale = self.scene.view.scale(item["y"])
        offset = 0
        if item["bob"] < self.BOB_TIME:
            progress = item["bob"] / self.BOB_TIME
            offset = math.sin(progress * math.pi * 2) * (1 - progress) * s(self.BOB_DEPTH) * item["bob_size"] * scale
        rock = math.sin(self.time / 450 + item["rock"]) * s(self.STORM_ROCK) * self.scene.weather["storm"] * scale
        return offset + rock

    def soak(self, item):
        # 0 when fresh, 1 when it's about to sink: it darkens over the second half of its life
        return max(0, (item["age"] / item["lifetime"] - 0.5) * 2)

    def shifted(self, points, dy):
        moved = []
        for x, y in points:
            moved.append((x, y + dy))
        return moved

    def place(self, item, points, jitter=None):
        # Turn the item's own shape into points on the screen, lying on the surface,
        # with its outline wobble, and dipped by any bobbing or rocking
        if jitter:
            pushed = []
            for i, (u, v) in enumerate(points):
                push = 1 + jitter[i]
                pushed.append((u * push, v * push))
            points = pushed
        y = item["y"] + self.bob_offset(item)
        return self.scene.view.lay_flat(points, item["x"], y, item["angle"], item["length"])

    def draw(self, surface, palette):
        view = self.scene.view
        leaf_colors = palette.get("leaves", [palette["muted"]])
        twig_color = pygame.Color(palette.get("twig", palette["muted"]))
        black = pygame.Color(0, 0, 0)

        for item in self.items:
            water = self.scene.color_at(palette, item["y"])
            presence = self.presence(item) * self.scene.keep(item["x"], self.QUIET)
            strength = self.STRENGTH * view.clarity(item["y"]) * presence
            if strength <= 0:
                continue
            scale = view.scale(item["y"])
            line = max(1, round(s(self.LINE_WIDTH) * scale))

            if item["twig"]:
                base = twig_color
                shapes = []
                for points in item["lines"]:
                    shapes.append(self.place(item, points))
            else:
                base = pygame.Color(leaf_colors[int(item["color_pick"] * len(leaf_colors))])
                shapes = [self.place(item, item["outline"], item["jitter"])]
            base = base.lerp(black, self.SOAK * self.soak(item))

            # The shadow first, in two soft steps: the farther, fainter one underneath
            for step in (1, 0):
                shadow = water.lerp(black, self.SHADOW[step] * presence)
                dy = s(self.SHADOW_OFFSET[step]) * scale * view.flatten(item["y"]) * 2
                for points in shapes:
                    if item["twig"]:
                        pygame.draw.lines(surface, shadow, False, self.shifted(points, dy), line + 1)
                    else:
                        pygame.draw.polygon(surface, shadow, self.shifted(points, dy))

            if item["twig"]:
                color = water.lerp(base, strength)
                for points in shapes:
                    pygame.draw.lines(surface, color, False, points, line)
                continue

            fill = water.lerp(base, strength)
            edge = water.lerp(base.lerp(black, self.OUTLINE), strength)
            pygame.draw.polygon(surface, fill, shapes[0])
            pygame.draw.lines(surface, edge, True, shapes[0], line)
            pygame.draw.lines(surface, edge, False, self.place(item, item["lines"][0]), line)
