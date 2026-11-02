# The desert's moods: heat shimmering over the horizon by day, ripples on the oasis pool,
# tumbleweed bowling across the sand, and now and then a sandstorm: the air turns thick
# and ochre, dust streams past, and then it clears again

import math

import random

import pygame

from partials.config import WIDTH, HEIGHT, s
from partials.backgrounds.base import Layer
from partials.backgrounds.helpers import Timer


class HeatShimmer(Layer):
    # By day, the strip along the horizon wavers in the heat: each row of pixels there is
    # nudged a little sideways, by a wave that rolls slowly upward. It works on whatever is
    # already drawn (sky, pyramids, far dunes), so it goes right after them. Daytime only:
    # needs "shimmer" in the palette (how strong, in pixels at the medium size)

    ABOVE = 46                      # how far above the horizon it reaches, pixels at the medium size
    BELOW = 16                      # ... and below
    WAVE = 7                        # pixels between wave crests, up the strip

    def __init__(self, scene):
        super().__init__(scene)
        self.time = 0
        self.top = int(scene.view.horizon - s(self.ABOVE))
        self.bottom = int(scene.view.horizon + s(self.BELOW))

    def update(self, dt):
        self.time += dt

    def draw(self, surface, palette):
        amount = palette.get("shimmer")
        if not amount:
            return
        strength = s(amount) * (1 - self.scene.weather.get("storm", 0))
        if strength < 0.5:
            return
        strip = surface.subsurface((0, self.top, WIDTH, self.bottom - self.top)).copy()
        horizon = self.scene.view.horizon
        for row in range(0, self.bottom - self.top, 2):
            y = self.top + row
            # Strongest right at the horizon, fading above and below it
            fade = 1 - min(1, abs(y - horizon) / (s(self.ABOVE) if y < horizon else s(self.BELOW)))
            shift = round(math.sin(y / s(self.WAVE) + self.time / 260) * strength * fade)
            if shift:
                surface.blit(strip, (shift, y), (0, row, WIDTH, 2))


class PoolRipples(Layer):
    # Life on the oasis pool: now and then a ring spreads where something touched the water
    # (a date dropping, an insect), and when the wind picks up, little ripple lines skate
    # across the surface. Others can add rings with ring(x, y)
    #
    # Palette colors it uses:
    #   "pool_ripple"           the rings and ripple lines (they fade into the water)

    EVERY = (1500, 4500)            # milliseconds between rings
    RING_LIFE = 1500
    LINES = 12

    def __init__(self, scene, oasis):
        super().__init__(scene)
        self.oasis = oasis
        self.timer = Timer(self.EVERY)
        self.rings = []
        self.lines = [self.new_line(random.uniform(0, 1)) for i in range(self.LINES)]

    def ring(self, x, y, size=1.0):
        self.rings.append({"x": x, "y": y, "age": 0.0, "size": size})

    def new_line(self, along=None):
        y = self.oasis.cy + random.uniform(-0.7, 0.7) * s(self.oasis.HALF[1])
        return {"y": y, "along": 1.0 if along is None else along, "length": s(random.uniform(8, 20)), "speed": random.uniform(0.7, 1.3)}

    def update(self, dt):
        if self.timer.tick(dt):
            x, y = self.oasis.point(random.uniform(0, 2 * math.pi), random.uniform(0, 0.8))
            self.ring(x, y)
        for ring in self.rings:
            ring["age"] += dt
        self.rings = [ring for ring in self.rings if ring["age"] < self.RING_LIFE]
        wind = self.scene.weather.get("wind", 1)
        for i, line in enumerate(self.lines):
            line["along"] -= wind * line["speed"] * dt / 4000          # the wind blows to the left
            if line["along"] < 0:
                self.lines[i] = self.new_line()

    def draw(self, surface, palette):
        ripple = pygame.Color(palette.get("pool_ripple", palette["text"]))
        oasis = self.oasis
        for ring in self.rings:
            t = ring["age"] / self.RING_LIFE
            r = (s(2) + s(12) * t) * ring["size"]
            color = oasis.water_color(palette, ring["y"]).lerp(ripple, (1 - t) * 0.8)
            pygame.draw.ellipse(surface, color, (ring["x"] - r, ring["y"] - r * 0.35, r * 2, r * 0.7), 1)
        wind = self.scene.weather.get("wind", 1)
        strength = max(0.0, min(0.7, (wind - 0.6) * 0.6))
        if strength <= 0.05:
            return
        half = s(oasis.HALF[0])
        for line in self.lines:
            x = oasis.cx - half + 2 * half * line["along"]
            if not oasis.inside(x, line["y"], 0.85) or not oasis.inside(x + line["length"], line["y"], 0.85):
                continue
            fade = math.sin(math.pi * line["along"])
            color = oasis.water_color(palette, line["y"]).lerp(ripple, strength * fade)
            pygame.draw.line(surface, color, (x, line["y"]), (x + line["length"], line["y"]), 1)


class Tumbleweed(Layer):
    # Now and then a tumbleweed comes bowling in from the right with the wind, rolling and
    # bouncing across the sand in the lower part of the window, its shadow skimming under it,
    # and rolls away out of sight on the left. More of them on windy days
    #
    # Palette colors it uses:
    #   "tumbleweed", "tumbleweed_dark"

    EVERY = (16000, 40000)          # milliseconds between tumbleweeds at a normal breeze
    SIZE = (16, 24)                 # radius, pixels at the medium size up close
    SPEED = 70                      # pixels per second at a normal breeze
    TWIGS = 22

    def __init__(self, scene):
        super().__init__(scene)
        self.timer = Timer(self.EVERY)
        self.timer.left = random.uniform(4000, self.EVERY[1])
        self.weeds = []

    def start(self):
        view = self.scene.view
        y = HEIGHT * random.uniform(0.62, 0.9)
        twigs = []
        for k in range(self.TWIGS):
            # Curved twigs inside the ball: start and end points in polar form
            twigs.append((random.uniform(0, 2 * math.pi), random.uniform(0.3, 1.0), random.uniform(0, 2 * math.pi), random.uniform(0.3, 1.0)))
        self.weeds.append({"x": WIDTH + s(30), "y": y, "r": s(random.uniform(*self.SIZE)) * view.scale(y), "spin": 0.0,
                           "hop": random.uniform(0, math.pi), "twigs": twigs, "speed": random.uniform(0.8, 1.2)})

    def update(self, dt):
        wind = self.scene.weather.get("wind", 1)
        if self.timer.tick(dt, max(0.3, wind)):
            self.start()
        seconds = dt / 1000
        for weed in self.weeds:
            speed = s(self.SPEED) * wind * weed["speed"] * self.scene.view.scale(weed["y"])
            weed["x"] -= speed * seconds
            weed["spin"] -= speed / max(weed["r"], 1) * seconds
            weed["hop"] += seconds * 3.2 * (0.6 + 0.4 * wind)
        self.weeds = [weed for weed in self.weeds if weed["x"] > -s(40)]

    def draw(self, surface, palette):
        if not self.weeds:
            return
        light = pygame.Color(palette.get("tumbleweed", palette["muted"]))
        dark = pygame.Color(palette.get("tumbleweed_dark", palette["muted"]))
        for weed in self.weeds:
            r = weed["r"]
            bounce = abs(math.sin(weed["hop"])) * r * 1.2
            x, y = weed["x"], weed["y"] - r - bounce
            shade = pygame.Surface((int(r * 2.4), int(r * 0.7)), pygame.SRCALPHA)
            pygame.draw.ellipse(shade, (0, 0, 0, int(255 * palette.get("shadow", 0.3) * 0.6 * (1 - bounce / (r * 2.5)))), shade.get_rect())
            surface.blit(shade, (weed["x"] - r * 1.2, weed["y"] - r * 0.35))
            for k, (a1, r1, a2, r2) in enumerate(weed["twigs"]):
                a1 += weed["spin"]
                a2 += weed["spin"]
                p1 = (x + math.cos(a1) * r * r1, y + math.sin(a1) * r * r1)
                p2 = (x + math.cos(a2) * r * r2, y + math.sin(a2) * r * r2)
                middle = ((p1[0] + p2[0]) / 2 + math.cos(a1 + 1) * r * 0.2, (p1[1] + p2[1]) / 2 + math.sin(a1 + 1) * r * 0.2)
                pygame.draw.lines(surface, dark if k % 3 == 0 else light, False, [p1, middle, p2], 1)


class Sandstorm(Layer):
    # When a sandstorm blows (the scene's weather "storm"), the air fills with dust: a
    # thick ochre veil, denser toward the ground, and streams of sand racing past to the
    # left. Drawn in front of the scene but behind the game, and kept a little thinner
    # in the middle so the text stays readable
    #
    # Palette colors it uses:
    #   "dust"                  the color of the air in a storm
    #   "dust_streak"           the racing streams of sand (falls back to "dust")

    THICKEST = 0.72                 # how much the veil covers the scene at the height of a storm
    STREAKS = 90
    LEVELS = 16                     # veil strengths painted ahead of time

    def __init__(self, scene):
        super().__init__(scene)
        self.streaks = [self.new_streak(random.uniform(0, WIDTH)) for i in range(self.STREAKS)]
        self.veils = None
        self.painted_palette = None

    def new_streak(self, x=None):
        return {"x": WIDTH + random.uniform(0, s(80)) if x is None else x, "y": random.uniform(0, HEIGHT),
                "length": s(random.uniform(20, 70)), "speed": random.uniform(0.6, 1.4), "pick": random.random()}

    def paint(self, palette):
        # The veil: a gradient, thinner at the top and in the middle column
        dust = pygame.Color(palette.get("dust", palette["muted"]))
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for y in range(0, HEIGHT, 2):
            depth = 0.55 + 0.45 * (y / HEIGHT)
            for x0 in range(0, WIDTH, 2):
                quiet = self.scene.keep(x0 + 1, 0.35)
                veil.fill((dust.r, dust.g, dust.b, int(255 * depth * quiet)), (x0, y, 2, 2))
        self.veils = []
        for level in range(1, self.LEVELS + 1):
            copy = veil.copy()
            copy.fill((255, 255, 255, int(255 * level / self.LEVELS)), special_flags=pygame.BLEND_RGBA_MULT)
            self.veils.append(copy)
        self.painted_palette = palette

    def update(self, dt):
        storm = self.scene.weather.get("storm", 0)
        wind = self.scene.weather.get("wind", 1)
        if storm <= 0.02:
            return
        seconds = dt / 1000
        for i, streak in enumerate(self.streaks):
            streak["x"] -= s(260) * streak["speed"] * (0.5 + 0.5 * wind) * seconds
            if streak["x"] + streak["length"] < 0:
                self.streaks[i] = self.new_streak()

    def draw(self, surface, palette):
        storm = self.scene.weather.get("storm", 0)
        if storm <= 0.02:
            return
        if self.painted_palette is not palette:
            self.paint(palette)
        level = int(storm * self.THICKEST * self.LEVELS)
        if level > 0:
            surface.blit(self.veils[min(level, self.LEVELS) - 1], (0, 0))
        dust = pygame.Color(palette.get("dust", palette["muted"]))
        streak_color = pygame.Color(palette.get("dust_streak", palette.get("dust", palette["muted"])))
        count = int(self.STREAKS * storm)
        for streak in self.streaks[:count]:
            behind = self.scene.color_at(palette, streak["y"]).lerp(dust, storm * self.THICKEST)
            color = behind.lerp(streak_color, (0.5 + 0.5 * streak["pick"]) * self.scene.keep(streak["x"], 0.5))
            y = streak["y"]
            pygame.draw.line(surface, color, (streak["x"], y), (streak["x"] + streak["length"], y + s(2)), 2 if streak["pick"] > 0.7 else 1)
