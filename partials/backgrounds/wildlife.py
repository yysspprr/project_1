# Little living things on and under the water: water striders and fish rising for air.
# They make their own ripples through on_ripple(x, y, size=..., ...), so they work
# with any background that has a ripples layer (or none: then they just don't ripple)

import math

import random

import pygame

from partials.config import WIDTH, HEIGHT, s
from partials.backgrounds.base import Layer


def calm(scene, start, end):
    # 1 when the storm is below start, 0 when it's above end, a smooth fade in between
    storm = scene.weather["storm"]
    t = max(0, min(1, (storm - start) / (end - start)))
    return 1 - t * t * (3 - 2 * t)


class WaterStriders(Layer):
    # Tiny long-legged bugs that skate on the surface: they rest, then dart off in a
    # quick glide, leaving little rings where they push off. Mostly what you see of
    # them is the dimples their feet make. They hide when the rain gets heavy
    #
    # Palette colors it uses:
    #   "bug"           the body and legs (falls back to "text")
    #   "glint"         the light caught in the dimples under its feet (falls back to "ripple")

    COUNT = 3
    SIZE = 4                        # body half-length up close, in pixels
    LINE_WIDTH = 1
    DIMPLE = 1.3                    # dimple radius up close, in pixels
    REST = (500, 2600)              # milliseconds it sits still
    DART_TIME = (200, 380)          # milliseconds a dart takes
    DART = (25, 70)                 # how far a dart goes up close, in pixels
    TURN = 70                       # most degrees it turns before a dart
    SPREAD = 0.2                    # how much they crowd toward the back (see Perspective.random_y)
    HIDE = (0.45, 0.75)             # they start hiding at this storm, and are all gone by this one
    STRENGTH = 0.9
    QUIET = 0.6                     # how much they fade behind the game's text (0 = not at all, 1 = fully)

    # The body and legs, in body half-lengths, pointing right. Each leg: body joint, foot
    BODY = [(-1, 0), (1, 0)]
    LEGS = [
        ((0.7, 0), (1.5, 0.6)), ((0.7, 0), (1.5, -0.6)),            # short front legs
        ((0.1, 0), (1.3, 3.6)), ((0.1, 0), (1.3, -3.6)),            # long middle legs: the oars
        ((-0.1, 0), (-3.2, 2.6)), ((-0.1, 0), (-3.2, -2.6)),        # long back legs
    ]
    FEET = [2, 3, 4, 5]             # which legs leave dimples (the long ones)

    def __init__(self, scene, on_ripple=None):
        super().__init__(scene)
        self.on_ripple = on_ripple
        self.bugs = []
        for i in range(self.COUNT):
            self.bugs.append(self.make_bug())

    def make_bug(self):
        y = self.scene.view.random_y(self.SPREAD)
        return {
            "x": self.scene.margin_x(),             # they live at the sides, out of the game's way
            "y": y,
            "angle": random.uniform(0, 360),
            "rest": random.randint(*self.REST),
            "dart": None,               # while darting: where from, where to, how long, how far along
        }

    def start_dart(self, bug):
        view = self.scene.view
        bug["angle"] += random.uniform(-self.TURN, self.TURN)
        turn = math.radians(bug["angle"])
        distance = s(random.randint(*self.DART)) * view.scale(bug["y"])
        to_x = bug["x"] + math.cos(turn) * distance
        to_y = bug["y"] + math.sin(turn) * distance * view.flatten(bug["y"])

        # Turn back instead of skating out of the window
        margin = s(20)
        if not (margin < to_x < WIDTH - margin and margin < to_y < HEIGHT - margin):
            bug["angle"] += 180
            to_x = bug["x"] - (to_x - bug["x"])
            to_y = bug["y"] - (to_y - bug["y"])

        # Skate sideways back out instead of into the middle, where the game's text is
        if self.scene.keep(to_x) < self.scene.keep(bug["x"]) and self.scene.keep(to_x) < 1:
            bug["angle"] = 180 - bug["angle"]
            to_x = bug["x"] - (to_x - bug["x"])

        bug["dart"] = {"from": (bug["x"], bug["y"]), "to": (to_x, to_y),
                       "time": random.randint(*self.DART_TIME), "age": 0}
        if self.on_ripple is not None:
            self.on_ripple(bug["x"], bug["y"], size=0.22, slow=0.55, echoes=0, strength=0.7, splash=False)

    def update(self, dt):
        if calm(self.scene, *self.HIDE) == 0:
            return                      # all hiding: nothing to do
        for bug in self.bugs:
            dart = bug["dart"]
            if dart is None:
                bug["rest"] -= dt
                if bug["rest"] <= 0:
                    self.start_dart(bug)
                continue

            dart["age"] += dt
            t = min(1, dart["age"] / dart["time"])
            glide = 1 - (1 - t) ** 3            # a quick push, then coasting to a stop
            bug["x"] = dart["from"][0] + (dart["to"][0] - dart["from"][0]) * glide
            bug["y"] = dart["from"][1] + (dart["to"][1] - dart["from"][1]) * glide
            if t >= 1:
                bug["dart"] = None
                bug["rest"] = random.randint(*self.REST)

    def draw(self, surface, palette):
        shown = calm(self.scene, *self.HIDE)
        if shown == 0:
            return
        view = self.scene.view
        bug_color = pygame.Color(palette.get("bug", palette["text"]))
        dimple_color = pygame.Color(palette.get("glint", palette["ripple"]))

        for bug in self.bugs:
            water = self.scene.color_at(palette, bug["y"])
            strength = self.STRENGTH * view.clarity(bug["y"]) * shown * self.scene.keep(bug["x"], self.QUIET)
            body_color = water.lerp(bug_color, strength)
            light = water.lerp(dimple_color, strength * 0.8)
            scale = view.scale(bug["y"])
            line = max(1, round(s(self.LINE_WIDTH) * scale))

            def place(points):
                return view.lay_flat(points, bug["x"], bug["y"], bug["angle"], s(self.SIZE))

            for i in self.FEET:
                foot = place([self.LEGS[i][1]])[0]
                pygame.draw.circle(surface, light, foot, max(1, s(self.DIMPLE) * scale), 1)
            for joint, foot in self.LEGS:
                pygame.draw.lines(surface, body_color, False, place([joint, foot]), line)
            pygame.draw.lines(surface, body_color, False, place(self.BODY), line + 1)


class RisingFish(Layer):
    # Now and then a fish comes up for a breath: a few bubbles pop, then its back
    # rolls through the surface and a big slow ripple spreads out.
    # Fish rise more often when it's calm, and hardly at all in a storm
    #
    # Palette colors it uses:
    #   "fish"          the fish's back (falls back to "text")
    #   "glint"         the bubbles (falls back to "ripple")

    WAIT = (6000, 18000)            # milliseconds between rises when it's calm
    STORM_WAIT = 4                  # in a full storm, the wait is this many times longer
    BUBBLES = (2, 4)                # how many bubbles come up first
    BUBBLE_GAP = (120, 380)         # milliseconds between bubbles
    BUBBLE_TIME = 300               # milliseconds a bubble sits before it pops
    BUBBLE_SIZE = 2.5               # bubble radius up close, in pixels
    BUBBLE_SPREAD = 12              # how far from the fish the bubbles come up, up close, in pixels
    ROLL_DELAY = 350                # milliseconds from the last bubble to the fish rolling up
    ROLL_TIME = 700                 # milliseconds the back is above water
    BACK = 30                       # half the length of the back that shows, up close, in pixels
    HUMP = 0.3                      # how high the back arches, as a share of its half-length
    FIN = 0.32                      # how tall the fin on its back is, as a share of its half-length
    LINE_WIDTH = 4
    SPREAD = 0.3                    # how much they rise toward the back (see Perspective.random_y)
    STRENGTH = 0.9

    def __init__(self, scene, on_ripple=None):
        super().__init__(scene)
        self.on_ripple = on_ripple
        self.wait = random.randint(*self.WAIT) // 2     # the first one comes a bit sooner
        self.rise = None

    def start_rise(self):
        view = self.scene.view
        x = self.scene.margin_x()                   # at the sides, out of the game's way
        y = view.random_y(self.SPREAD)
        scale = view.scale(y)

        bubbles = []
        time = 0
        for i in range(random.randint(*self.BUBBLES)):
            time += random.randint(*self.BUBBLE_GAP)
            bubbles.append({
                "time": time,
                "x": x + random.uniform(-1, 1) * s(self.BUBBLE_SPREAD) * scale,
                "y": y + random.uniform(-1, 1) * s(self.BUBBLE_SPREAD) * scale * view.flatten(y),
                "popped": False,
            })
        self.rise = {
            "x": x, "y": y,
            "angle": random.choice((0, 180)) + random.uniform(-25, 25),
            "bubbles": bubbles,
            "roll_at": time + self.BUBBLE_TIME + self.ROLL_DELAY,
            "rolled": False,
            "age": 0,
        }

    def update(self, dt):
        if self.rise is None:
            storm = self.scene.weather["storm"]
            self.wait -= dt / (1 + (self.STORM_WAIT - 1) * storm)
            if self.wait <= 0:
                self.start_rise()
            return

        rise = self.rise
        rise["age"] += dt
        for bubble in rise["bubbles"]:
            if not bubble["popped"] and rise["age"] >= bubble["time"] + self.BUBBLE_TIME:
                bubble["popped"] = True
                if self.on_ripple is not None:
                    self.on_ripple(bubble["x"], bubble["y"], size=0.18, slow=0.6, echoes=0, strength=0.8, splash=False)

        if not rise["rolled"] and rise["age"] >= rise["roll_at"]:
            rise["rolled"] = True
            if self.on_ripple is not None:
                self.on_ripple(rise["x"], rise["y"], size=1.7, slow=1.8, echoes=3, strength=1.1, splash=False)

        if rise["age"] >= rise["roll_at"] + self.ROLL_TIME:
            self.rise = None
            self.wait = random.randint(*self.WAIT)

    def draw(self, surface, palette):
        if self.rise is None:
            return
        rise = self.rise
        view = self.scene.view
        water = self.scene.color_at(palette, rise["y"])
        clarity = view.clarity(rise["y"])
        scale = view.scale(rise["y"])

        # Bubbles: little rings that swell a bit before they pop
        bubble_color = water.lerp(pygame.Color(palette.get("glint", palette["ripple"])), 0.8 * clarity)
        for bubble in rise["bubbles"]:
            age = rise["age"] - bubble["time"]
            if 0 <= age < self.BUBBLE_TIME:
                radius = max(1, s(self.BUBBLE_SIZE) * scale * (0.5 + 0.5 * age / self.BUBBLE_TIME))
                pygame.draw.circle(surface, bubble_color, (bubble["x"], bubble["y"]), radius, 1)

        # The back: an arch that rolls through the surface from head to tail.
        # Only the stretch between 'start' and 'end' (in -1..1 along the back) is above water
        age = rise["age"] - rise["roll_at"]
        if not 0 <= age < self.ROLL_TIME:
            return
        t = age / self.ROLL_TIME
        start = -1 + 2.6 * max(0, t - 0.3)
        end = min(1, -1 + 2.6 * t)
        if end <= start:
            return

        fish_color = water.lerp(pygame.Color(palette.get("fish", palette["text"])), self.STRENGTH * clarity)
        size = s(self.BACK) * scale
        lift = math.sin(math.pi * t)                      # rises, then sinks back
        turn = math.radians(rise["angle"])
        cos, sin = math.cos(turn), math.sin(turn)
        flatten = view.flatten(rise["y"])
        def back_point(u, extra=0):
            # A point along the back: along the surface (squashed), then straight up on screen
            arch = (1 - u * u) * self.HUMP * lift + extra
            return (rise["x"] + u * cos * size,
                    rise["y"] + u * sin * size * flatten - arch * size)

        points = []
        for i in range(9):
            points.append(back_point(start + (end - start) * i / 8))
        line = max(2, round(s(self.LINE_WIDTH) * scale))
        pygame.draw.lines(surface, fish_color, False, points, line)

        # The fin, just behind the middle of the back, while that part is out of the water
        if start < -0.05 and end > 0.25:
            fin = [back_point(-0.05), back_point(-0.25, self.FIN * lift), back_point(0.25)]
            pygame.draw.polygon(surface, fish_color, fin)
