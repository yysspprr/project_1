# A little village out on the snow: a few cottages with snowy roofs and smoking
# chimneys, some firs around them, and windows that light up and go dark at night

import math

import random

import pygame

from partials.config import CENTER_X, s
from partials.backgrounds.base import Layer
from partials.backgrounds.mountains import draw_fir


class Village(Layer):
    # Sits in a side margin, partway out across the snow, so it's never behind the game's
    # text. Everything is drawn standing up, sized by the scene's perspective.
    # Each cottage and fir casts a long shadow across the snow, pointing away from the sun
    # or moon (the scene's weather["light_x"] and ["light_y"]), stronger in bright light.
    # Chimney smoke rises and drifts with the wind. At night (when the palette has a
    # "window_lit" color) windows light up and go dark one by one, every so often
    #
    # Palette colors it uses:
    #   "wall", "roof", "roof_snow"     the cottages (roof snow falls back to "snow_top")
    #   "window"                        an unlit window
    #   "window_lit"                    a lit window (night only: no lights without it)
    #   "fir", "fir_snow"               the firs
    #   "smoke"                         chimney smoke (no smoke without it)
    #   "snow_shadow"                   the shadows on the snow
    #   "shadow"                        how dark shadows are in this light, 0-1

    SIDE = "left"
    DEPTH = 0.25                    # how far away it is: 0 = right in front of us, 1 = the horizon
    COTTAGES = 3
    FIRS = 3
    COTTAGE_WIDTH = (58, 74)        # pixels, as if up close (they're shrunk by the distance)
    WALL_HEIGHT = (32, 40)
    ROOF_HEIGHT = (24, 30)
    FIR_HEIGHT = (70, 110)
    SPACING = 0.9                   # how close together the cottages stand, in cottage widths

    LIGHT_ON = (20000, 80000)       # milliseconds a window stays lit
    LIGHT_OFF = (8000, 45000)       # ... and stays dark
    LIGHT_GLOW = 2.4                # how far a lit window's glow reaches, in window sizes

    SMOKE_EVERY = (260, 420)        # milliseconds between puffs
    SMOKE_LIFE = (2800, 4200)
    SMOKE_RISE = 34                 # pixels per second, as if up close
    SMOKE_DRIFT = 26                # pixels per second sideways at a normal breeze, as if up close
    SMOKE_SIZE = (6, 20)            # puff radius when it starts and when it fades, as if up close
    SMOKE_STRENGTH = 0.7

    SHADOW = 0.5                    # how dark the shadows are in full light, without a palette "shadow"
    CAST_LENGTH = 1.1               # shadow length in heights, with the light 60% of the way up the sky

    def __init__(self, scene):
        super().__init__(scene)
        view = scene.view
        self.base_y = view.height_at(self.DEPTH)
        self.scale = view.scale(self.base_y)
        self.time = 0
        margin = CENTER_X - scene.QUIET_WIDTH
        left_edge = s(6) if self.SIDE == "left" else CENTER_X + scene.QUIET_WIDTH
        self.things = []            # cottages and firs, back to front

        x = left_edge
        for i in range(self.COTTAGES):
            width = s(random.randint(*self.COTTAGE_WIDTH)) * self.scale
            depth_shift = random.uniform(-1, 1) * s(4) * self.scale
            cottage = {
                "kind": "cottage",
                "x": x + width / 2,
                "y": self.base_y + depth_shift,
                "width": width,
                "wall": s(random.randint(*self.WALL_HEIGHT)) * self.scale,
                "roof": s(random.randint(*self.ROOF_HEIGHT)) * self.scale,
                "chimney": random.uniform(-0.3, 0.3),
                "windows": [],
                "puffs": [],
                "next_puff": random.randint(*self.SMOKE_EVERY),
            }
            # One window somewhere along the wall, or two evenly spaced
            spots = [random.choice((0.3, 0.5, 0.7))] if random.random() < 0.5 else [0.3, 0.7]
            for along in spots:
                cottage["windows"].append({
                    "along": along,
                    "lit": random.random() < 0.6,
                    "timer": random.randint(0, self.LIGHT_ON[1]),
                })
            # Where its chimney pokes out of the roof: smoke comes out here
            wall_top = cottage["y"] - cottage["wall"]
            roof_top = wall_top - cottage["roof"]
            cottage["chimney_top"] = (cottage["x"] + cottage["chimney"] * width / 2, roof_top + cottage["roof"] * 0.25)
            self.things.append(cottage)
            x += width * self.SPACING + s(random.uniform(2, 8)) * self.scale
            if x > left_edge + margin:
                break

        for i in range(self.FIRS):
            self.things.append({
                "kind": "fir",
                "x": left_edge + random.uniform(0, margin),
                "y": self.base_y + random.uniform(-1, 1) * s(10) * self.scale,
                "height": s(random.randint(*self.FIR_HEIGHT)) * self.scale,
            })
        self.things.sort(key=lambda thing: thing["y"])     # further back first
        self.glows = {}             # lit windows' glows, made once per color and size

    # ---- Shadows ----

    def cast(self, x, y):
        # Which way and how far the shadow of one pixel of height falls, from a base at (x, y)
        weather = self.scene.weather
        light_x, light_y = weather.get("light_x"), weather.get("light_y")
        horizon = self.scene.view.horizon
        if light_x is None or light_y is None or horizon <= 0:
            return (-0.6, 0.2)
        away_x, away_y = x - light_x, y - horizon
        distance = math.hypot(away_x, away_y) or 1
        height = max(0.15, (horizon - light_y) / horizon)
        length = self.CAST_LENGTH * 0.6 / height
        # Lying on the ground, it's squashed like everything else down there
        flatten = self.scene.view.flatten(y)
        return (away_x / distance * length, away_y / distance * length * flatten)

    def draw_shadow(self, surface, thing, color):
        x, y = thing["x"], thing["y"]
        along_x, along_y = self.cast(x, y)
        if thing["kind"] == "cottage":
            half = thing["width"] / 2
            tall = thing["wall"] + thing["roof"] * 0.6
            near = [(x - half, y), (x + half, y)]
        else:
            half = thing["height"] * 0.25
            tall = thing["height"]
            near = [(x - half, y), (x + half, y)]
        far = [(px + along_x * tall, py + along_y * tall) for px, py in near]
        if thing["kind"] == "fir":
            tip = ((far[0][0] + far[1][0]) / 2, (far[0][1] + far[1][1]) / 2)
            pygame.draw.polygon(surface, color, near + [tip])
        else:
            pygame.draw.polygon(surface, color, [near[0], near[1], far[1], far[0]])

    # ---- Cottages ----

    def draw_cottage(self, surface, palette, cottage, night):
        x, y = cottage["x"], cottage["y"]
        half = cottage["width"] / 2
        wall_top = y - cottage["wall"]
        roof_top = wall_top - cottage["roof"]
        overhang = cottage["width"] * 0.08

        wall = pygame.Color(palette.get("wall", palette["muted"]))
        roof = pygame.Color(palette.get("roof", palette.get("wall", palette["muted"])))
        snow = pygame.Color(palette.get("roof_snow", palette.get("snow_top", palette["bg"])))

        # The chimney sits behind the roof
        chimney_x, chimney_top = cottage["chimney_top"]
        chimney_w = max(2, cottage["width"] * 0.1)
        pygame.draw.rect(surface, wall.lerp(pygame.Color(0, 0, 0), 0.2),
                         (chimney_x - chimney_w / 2, chimney_top, chimney_w, wall_top - chimney_top))
        pygame.draw.rect(surface, snow, (chimney_x - chimney_w / 2 - 1, chimney_top - 1, chimney_w + 2, max(1, chimney_w * 0.4)))

        pygame.draw.rect(surface, wall, (x - half, wall_top, cottage["width"], cottage["wall"]))
        roof_points = [(x - half - overhang, wall_top), (x, roof_top), (x + half + overhang, wall_top)]
        pygame.draw.polygon(surface, roof, roof_points)
        # A thick layer of snow on the roof, a little ragged along its bottom edge
        thick = max(2, cottage["roof"] * 0.35)
        pygame.draw.polygon(surface, snow, [roof_points[0], roof_points[1], roof_points[2],
                                            (roof_points[2][0] - overhang, wall_top - thick * 0.3),
                                            (x, roof_top + thick),
                                            (roof_points[0][0] + overhang, wall_top - thick * 0.3)])

        # Windows
        size = max(2, cottage["width"] * 0.16)
        window = pygame.Color(palette.get("window", palette["muted"]))
        lit = palette.get("window_lit")
        for pane in cottage["windows"]:
            wx = x - half + cottage["width"] * pane["along"]
            wy = wall_top + cottage["wall"] * 0.35
            rect = (wx - size / 2, wy, size, size)
            if night and lit and pane["lit"]:
                glow = pygame.Color(lit)
                self.draw_glow(surface, glow, (wx, wy + size / 2), size * self.LIGHT_GLOW)
                pygame.draw.rect(surface, glow, rect)
            else:
                pygame.draw.rect(surface, window, rect)

    def draw_glow(self, surface, color, center, radius):
        # A soft warm glow, from rings made once and reused
        key = (tuple(color), round(radius))
        if key not in self.glows:
            image = pygame.Surface((int(radius * 2) + 2, int(radius * 2) + 2), pygame.SRCALPHA)
            for step in range(4):
                share = 1 - step / 4
                glow = pygame.Color(color)
                glow.a = int(255 * 0.12 * (step + 1) / 4)
                pygame.draw.circle(image, glow, (radius + 1, radius + 1), radius * share)
            self.glows[key] = image
        image = self.glows[key]
        surface.blit(image, image.get_rect(center=center))

    # ---- Smoke ----

    def update_smoke(self, cottage, dt):
        seconds = dt / 1000
        wind = self.scene.weather["wind"]
        scale = self.scale
        for puff in cottage["puffs"]:
            puff["age"] += dt
            puff["y"] -= s(self.SMOKE_RISE) * scale * seconds * (1 - 0.5 * puff["age"] / puff["life"])
            puff["x"] += s(self.SMOKE_DRIFT) * wind * scale * seconds * (puff["age"] / puff["life"] + 0.2)
        cottage["puffs"] = [puff for puff in cottage["puffs"] if puff["age"] < puff["life"]]

        cottage["next_puff"] -= dt
        if cottage["next_puff"] <= 0:
            x, y = cottage["chimney_top"]
            cottage["puffs"].append({"x": x + random.uniform(-1, 1), "y": y, "age": 0,
                                     "life": random.randint(*self.SMOKE_LIFE)})
            cottage["next_puff"] = random.randint(*self.SMOKE_EVERY)

    def draw_smoke(self, surface, palette, cottage):
        if "smoke" not in palette:
            return
        smoke = pygame.Color(palette["smoke"])
        for puff in cottage["puffs"]:
            share = puff["age"] / puff["life"]
            radius = s(self.SMOKE_SIZE[0] + (self.SMOKE_SIZE[1] - self.SMOKE_SIZE[0]) * share) * self.scale
            strength = self.SMOKE_STRENGTH * (1 - share) * min(1, share * 6)
            behind = self.scene.color_at(palette, puff["y"])
            pygame.draw.circle(surface, behind.lerp(smoke, strength), (puff["x"], puff["y"]), max(1, radius))

    # ---- Layer methods ----

    def update(self, dt):
        self.time += dt
        for thing in self.things:
            if thing["kind"] != "cottage":
                continue
            self.update_smoke(thing, dt)
            for pane in thing["windows"]:
                pane["timer"] -= dt
                if pane["timer"] <= 0:
                    pane["lit"] = not pane["lit"]
                    pane["timer"] = random.randint(*(self.LIGHT_ON if pane["lit"] else self.LIGHT_OFF))

    def draw(self, surface, palette):
        night = "window_lit" in palette

        # Shadows first, all of them, lying on the snow
        darkness = palette.get("shadow", self.SHADOW) * 2 * max(0, min(1, self.scene.weather["light"]))
        if darkness > 0.02:
            shade_color = pygame.Color(palette.get("snow_shadow", palette["muted"]))
            for thing in self.things:
                behind = self.scene.color_at(palette, thing["y"])
                self.draw_shadow(surface, thing, behind.lerp(shade_color, min(1, darkness)))

        fir = pygame.Color(palette.get("fir", palette["muted"]))
        fir_snow = pygame.Color(palette.get("fir_snow", palette.get("snow_top", palette["bg"])))
        for thing in self.things:
            if thing["kind"] == "fir":
                draw_fir(surface, thing["x"], thing["y"], thing["height"], fir, fir_snow, wobble=0)
            else:
                self.draw_cottage(surface, palette, thing, night)
        for thing in self.things:
            if thing["kind"] == "cottage":
                self.draw_smoke(surface, palette, thing)
