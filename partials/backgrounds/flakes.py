# Light things drifting down: snowflakes here, but with other settings and colors
# the same layer could drop petals, ash or seeds

import math

import random

import pygame

from partials.config import WIDTH, s
from partials.backgrounds.base import Layer


class Snowfall(Layer):
    # Flakes fall toward a spot on the ground, fluttering from side to side and drifting
    # with the wind (the scene's weather["wind"]). Close to us they're bigger, fall faster
    # and flutter wider; far away they're tiny and slow. How many there are follows the
    # scene's weather["storm"]: a few lazy flakes when calm, a flurry in a full storm.
    # A flake that reaches its spot just disappears into the snow
    #
    # Palette colors it uses:
    #   "flake"         the flakes (falls back to "text")
    #   "flake_edge"    an outline on the bigger flakes, so they show against pale skies (optional)

    MOST = 150                      # flakes at once in a full storm
    LEAST = 0.15                    # share of that when it's calm
    SIZE = (1.5, 3.8)               # flake radius up close, in pixels at the medium size
    FALL = (28, 48)                 # how fast they fall up close, pixels per second
    FALL_HEIGHT = 700               # how far above its landing spot a flake starts, up close
    FLUTTER = (5, 15)               # how far they swing side to side up close
    FLUTTER_TIME = (1600, 3600)     # milliseconds for one swing back and forth
    DRIFT = 22                      # pixels per second sideways at a normal breeze, up close
    SPREAD = 0.45                   # how much they crowd toward the back (see Perspective.random_y)
    STRENGTH = 0.95                 # how strongly they show (0 = invisible, 1 = full "flake" color)
    QUIET = 0.45                    # how much they fade behind the game's text (0 = not at all)
    SPAWN = 40                      # most new flakes per second while there are too few

    def __init__(self, scene, on_land=None):
        super().__init__(scene)
        self.on_land = on_land
        self.time = 0
        self.flakes = []
        # Start with the sky already full, at different points of their fall
        for i in range(self.wanted()):
            flake = self.make_flake()
            flake["y"] = flake["land"] - flake["drop"] * random.random()
            self.flakes.append(flake)
        self.spawn_left = 0

    def wanted(self):
        storm = self.scene.weather["storm"]
        return round(self.MOST * (self.LEAST + (1 - self.LEAST) * storm))

    def make_flake(self):
        view = self.scene.view
        land = view.random_y(self.SPREAD)
        scale = view.scale(land)
        drop = s(self.FALL_HEIGHT) * scale
        return {
            "x": random.uniform(-s(40), WIDTH + s(40)),
            "y": land - drop,
            "land": land,
            "drop": drop,
            "scale": scale,
            "size": s(random.uniform(*self.SIZE)) * scale,
            "speed": s(random.uniform(*self.FALL)) * scale,
            "flutter": s(random.uniform(*self.FLUTTER)) * scale,
            "period": random.randint(*self.FLUTTER_TIME),
            "phase": random.uniform(0, 2 * math.pi),
        }

    def update(self, dt):
        self.time += dt
        seconds = dt / 1000
        wind = self.scene.weather["wind"]

        falling = []
        for flake in self.flakes:
            flake["y"] += flake["speed"] * seconds
            flake["x"] += s(self.DRIFT) * wind * flake["scale"] * seconds
            if flake["y"] < flake["land"]:
                falling.append(flake)
            elif self.on_land is not None:
                self.on_land(flake["x"], flake["land"])
        self.flakes = falling

        # Top up toward how many there should be, a few at a time so it never pops
        self.spawn_left += self.SPAWN * seconds
        while len(self.flakes) < self.wanted() and self.spawn_left >= 1:
            self.flakes.append(self.make_flake())
            self.spawn_left -= 1
        self.spawn_left = min(self.spawn_left, 3)

    def draw(self, surface, palette):
        view = self.scene.view
        flake_color = pygame.Color(palette.get("flake", palette["text"]))
        edge = palette.get("flake_edge")
        edge_color = pygame.Color(edge) if edge else None

        for flake in self.flakes:
            swing = math.sin(self.time / flake["period"] * 2 * math.pi + flake["phase"]) * flake["flutter"]
            x = flake["x"] + swing
            y = flake["y"]
            behind = self.scene.color_at(palette, y)
            strength = self.STRENGTH * view.clarity(flake["land"]) * self.scene.keep(x, self.QUIET)
            radius = max(1, flake["size"])
            if edge_color is not None and radius >= 2:
                pygame.draw.circle(surface, behind.lerp(edge_color, strength * 0.7), (x, y), radius + 1)
            pygame.draw.circle(surface, behind.lerp(flake_color, strength), (x, y), radius)
