# Light things drifting down: snowflakes here, but with other settings and colors
# the same layer could drop petals, ash or seeds

import math

import random

import pygame

from partials.config import WIDTH, HEIGHT, s
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


class DiamondDust(Layer):
    # Tiny ice crystals floating in still, cold, sunny air: they hang and drift slowly with
    # the wind, and now and then one catches the light and glints. Only when it's bright
    # (the scene's weather["light"]) and not snowing (weather["storm"])
    #
    # Palette colors it uses:
    #   "dust"          the crystals (no diamond dust without it)
    #   "dust_edge"     an outline, so they show against a pale sky (optional)

    COUNT = 40
    DRIFT = 6                       # pixels per second sideways at a normal breeze
    BOB = (2, 6)                    # how far they float up and down, in pixels
    BOB_TIME = (3000, 7000)
    TWINKLE = (900, 2600)           # milliseconds between glints of one crystal
    STRENGTH = 0.85
    QUIET = 0.7

    def __init__(self, scene):
        super().__init__(scene)
        self.time = 0
        self.crystals = []
        for i in range(self.COUNT):
            self.crystals.append({
                "x": random.uniform(0, WIDTH),
                "y": random.uniform(s(10), HEIGHT - s(60)),
                "bob": s(random.uniform(*self.BOB)),
                "bob_time": random.randint(*self.BOB_TIME),
                "twinkle": random.randint(*self.TWINKLE),
                "phase": random.uniform(0, 2 * math.pi),
            })

    def update(self, dt):
        self.time += dt
        drift = s(self.DRIFT) * self.scene.weather["wind"] * dt / 1000
        for crystal in self.crystals:
            crystal["x"] += drift
            if crystal["x"] > WIDTH + s(4):
                crystal["x"] = -s(4)
                crystal["y"] = random.uniform(s(10), HEIGHT - s(60))

    def draw(self, surface, palette):
        if "dust" not in palette:
            return
        weather = self.scene.weather
        show = max(0, min(1, weather["light"])) * (1 - weather["storm"]) ** 2
        if show < 0.05:
            return
        dust = pygame.Color(palette["dust"])
        edge = pygame.Color(palette["dust_edge"]) if "dust_edge" in palette else None
        for crystal in self.crystals:
            # Mostly faint, with a short sharp glint once per twinkle
            wave = math.sin(self.time / crystal["twinkle"] * 2 * math.pi + crystal["phase"])
            glint = max(0, wave) ** 8
            strength = self.STRENGTH * show * (0.25 + 0.75 * glint) * self.scene.keep(crystal["x"], self.QUIET)
            if strength < 0.05:
                continue
            y = crystal["y"] + math.sin(self.time / crystal["bob_time"] * 2 * math.pi + crystal["phase"]) * crystal["bob"]
            behind = self.scene.color_at(palette, y)
            x = crystal["x"]
            if edge is not None:
                pygame.draw.circle(surface, behind.lerp(edge, min(1, strength * 0.7)), (x, y), 1.5)
            if glint > 0.6:
                # The glint: a tiny four-pointed star
                arm = s(2.5)
                if edge is not None:
                    shade = behind.lerp(edge, min(1, strength * 0.7))
                    pygame.draw.line(surface, shade, (x - arm - 1, y), (x + arm + 1, y), 3)
                    pygame.draw.line(surface, shade, (x, y - arm - 1), (x, y + arm + 1), 3)
                color = behind.lerp(dust, min(1, strength))
                pygame.draw.line(surface, color, (x - arm, y), (x + arm, y))
                pygame.draw.line(surface, color, (x, y - arm), (x, y + arm))
            surface.set_at((int(x), int(y)), behind.lerp(dust, min(1, strength)))
