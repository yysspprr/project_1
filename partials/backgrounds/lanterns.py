# Paper lanterns in the garden: a few hanging from bamboo poles beside the stepping-stone
# path, swaying a little in the breeze and glowing at night, and now and then on a night
# a sky lantern rising from the garden and drifting away into the dark

import math

import random

import pygame

from partials.config import WIDTH, HEIGHT, s
from partials.backgrounds.base import Layer
from partials.backgrounds.helpers import Timer
from partials.backgrounds.brook_light import glow_sprite


class PathLanterns(Layer):
    # Round paper lanterns hung from crooked bamboo poles along the left side of the path:
    # ribbed paper between dark caps, on a short cord from the pole's arm, so they swing in
    # the wind. By day they're plain red paper; at night they glow warm, light the ground
    # under them, and flicker
    #
    # Palette colors it uses:
    #   "paper_lantern"             the paper (lit or not)
    #   "paper_lantern_rib"         the ribs and caps
    #   "branch"                    the bamboo poles
    #   "lantern_glow"              their glow at night (unlit without it)

    STONES = (1, 3, 5)              # which stepping stones of the path they stand beside
    OFF_PATH = 34                   # how far left of the stone, pixels at the medium size
    POLE = 66                       # pole height
    ARM = 13
    CORD = 7
    SIZE = (15, 19)                 # the lantern's width and height
    SWING = 0.14                    # radians they swing at a normal breeze
    GLOW = 46                       # glow radius at night

    def __init__(self, scene, garden):
        super().__init__(scene)
        self.time = 0
        self.lanterns = []
        for k in self.STONES:
            x, y, size, turn = garden.path[k]
            scale = scene.view.scale(y)
            self.lanterns.append({"x": x - s(self.OFF_PATH) * scale, "y": y, "scale": scale,
                                  "phase": random.uniform(0, 2 * math.pi), "flicker": random.uniform(0, 100)})
        self.lanterns.sort(key=lambda lantern: lantern["y"])
        self.glows = None
        self.painted_palette = None

    def paint(self, palette):
        self.glows = None
        if "lantern_glow" in palette:
            color = pygame.Color(palette["lantern_glow"])
            self.glows = {}
            for lantern in self.lanterns:
                r = s(self.GLOW) * lantern["scale"]
                self.glows[id(lantern)] = (glow_sprite(r, (color.r * 0.55, color.g * 0.5, color.b * 0.4), 1.0, 12),
                                           glow_sprite(r * 0.9, (color.r * 0.3, color.g * 0.27, color.b * 0.2), 0.35, 8))
        self.painted_palette = palette

    def update(self, dt):
        self.time += dt

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        paper = pygame.Color(palette.get("paper_lantern", palette["accent"]))
        rib = pygame.Color(palette.get("paper_lantern_rib", palette["text"]))
        pole = pygame.Color(palette.get("branch", palette["text"]))
        wind = self.scene.weather.get("wind", 1)
        for lantern in self.lanterns:
            k = lantern["scale"]
            x, ground = lantern["x"], lantern["y"]
            top = ground - s(self.POLE) * k
            # The pole, with a few bamboo joints, and its arm reaching out over the path
            pygame.draw.line(surface, pole, (x, ground), (x, top), max(1, int(s(2.4) * k)))
            for j in range(1, 4):
                jy = ground - s(self.POLE) * k * j / 4
                pygame.draw.line(surface, pole.lerp((255, 255, 255), 0.15), (x - s(1.6) * k, jy), (x + s(1.6) * k, jy), 1)
            hook = (x + s(self.ARM) * k, top + s(2) * k)
            pygame.draw.lines(surface, pole, False, [(x, top + s(4) * k), (x + s(self.ARM) * k * 0.6, top), hook], max(1, int(s(1.6) * k)))
            # It swings from the arm on its cord
            swing = math.sin(self.time / 1300 + lantern["phase"]) * self.SWING * wind + (wind - 1) * 0.08
            cord = s(self.CORD) * k
            w, h = s(self.SIZE[0]) * k, s(self.SIZE[1]) * k
            cx = hook[0] + math.sin(swing) * (cord + h / 2)
            cy = hook[1] + math.cos(swing) * (cord + h / 2)
            pygame.draw.line(surface, rib, hook, (hook[0] + math.sin(swing) * cord, hook[1] + math.cos(swing) * cord), 1)
            lit = self.glows is not None
            flicker = 1.0
            if lit:
                t = self.time / 1000 + lantern["flicker"]
                flicker = 0.85 + 0.1 * math.sin(t * 7.3) + 0.05 * math.sin(t * 17.1)
                glow, pool = self.glows[id(lantern)]
                level = int(255 * flicker)
                for sprite, at in ((pool, (cx, ground)), (glow, (cx, cy))):
                    sprite = sprite.copy()
                    sprite.fill((level, level, level), special_flags=pygame.BLEND_RGB_MULT)
                    surface.blit(sprite, sprite.get_rect(center=(int(at[0]), int(at[1]))), special_flags=pygame.BLEND_RGB_ADD)
            body = pygame.Rect(0, 0, w, h)
            body.center = (cx, cy)
            pygame.draw.ellipse(surface, paper, body)
            if not lit:
                pygame.draw.ellipse(surface, paper.lerp((255, 255, 255), 0.3), (body.x + w * 0.18, body.y + h * 0.15, w * 0.3, h * 0.55))
            for r in (-0.25, 0, 0.25):
                ry = cy + r * h
                half = w / 2 * math.sqrt(max(0, 1 - (2 * r) ** 2)) * 0.95
                pygame.draw.line(surface, paper.lerp(rib, 0.35), (cx - half, ry), (cx + half, ry), 1)
            for edge in (-1, 1):
                cap = pygame.Rect(0, 0, w * 0.55, max(2, h * 0.14))
                cap.center = (cx, cy + edge * h * 0.47)
                pygame.draw.rect(surface, rib, cap)
            pygame.draw.ellipse(surface, rib, body, 1)


class SkyLanterns(Layer):
    # Now and then on a night, one to three paper sky lanterns rise from the garden: glowing
    # warm, flickering, drifting with the breeze and swaying as they go, getting smaller as
    # they float off into the distance, and fading out high in the sky. Night only: needs
    # "sky_lantern" in the palette
    #
    # Palette colors it uses:
    #   "sky_lantern"               their glowing paper

    EVERY = (35000, 80000)          # milliseconds between launches
    FIRST = (8000, 20000)
    RISE = 17                       # pixels per second, at the medium size
    SIZE = 10                       # half its width up close
    GLOW = 30
    FADE_AT = 0.14                  # they fade out over the top of the window, as a share of its height

    def __init__(self, scene):
        super().__init__(scene)
        self.timer = Timer(self.EVERY)
        self.timer.left = random.uniform(*self.FIRST)
        self.lanterns = []
        self.time = 0
        self.sprite = None
        self.painted_palette = None

    def launch(self):
        # From the left side, so the breeze (blowing right) carries them across the sky
        x0 = random.uniform(s(15), s(70))
        for k in range(random.choice((1, 1, 2, 3))):
            y = HEIGHT * random.uniform(0.55, 0.85) + k * s(30)
            self.lanterns.append({"x": x0 + random.uniform(-s(30), s(30)), "y": y, "start": y,
                                  "phase": random.uniform(0, 2 * math.pi), "speed": random.uniform(0.8, 1.2)})

    def update(self, dt):
        self.time += dt
        if self.painted_palette is not None and "sky_lantern" in self.painted_palette and self.timer.tick(dt):
            self.launch()
        wind = self.scene.weather.get("wind", 1)
        seconds = dt / 1000
        for lantern in self.lanterns:
            far = self.distance(lantern)
            lantern["y"] -= s(self.RISE) * lantern["speed"] * (1 - 0.6 * far) * seconds
            lantern["x"] += (s(3) * wind + math.sin(self.time / 1700 + lantern["phase"]) * s(4)) * (1 - 0.5 * far) * seconds
        self.lanterns = [lantern for lantern in self.lanterns if lantern["y"] > -s(10) and lantern["x"] < WIDTH + s(20)]

    def distance(self, lantern):
        # 0 just launched, toward 1 as it rises out of sight
        return max(0.0, min(1.0, (lantern["start"] - lantern["y"]) / max(lantern["start"], 1)))

    def draw(self, surface, palette):
        self.painted_palette = palette
        if "sky_lantern" not in palette or not self.lanterns:
            return
        color = pygame.Color(palette["sky_lantern"])
        if self.sprite is None:
            self.sprite = glow_sprite(s(self.GLOW), (color.r * 0.5, color.g * 0.42, color.b * 0.3), 1.0, 10)
        for lantern in self.lanterns:
            far = self.distance(lantern)
            size = s(self.SIZE) * (1 - 0.7 * far)
            fade = min(1.0, lantern["y"] / (HEIGHT * self.FADE_AT)) * self.scene.keep(lantern["x"], 0.4)
            flicker = 0.85 + 0.15 * math.sin(self.time / 110 + lantern["phase"] * 3)
            strength = max(0.0, fade * flicker)
            if strength < 0.05:
                continue
            x, y = lantern["x"], lantern["y"]
            glow = pygame.transform.smoothscale(self.sprite, (max(2, int(self.sprite.get_width() * (1 - 0.6 * far))),) * 2)
            level = int(255 * strength)
            glow.fill((level, level, level), special_flags=pygame.BLEND_RGB_MULT)
            surface.blit(glow, glow.get_rect(center=(int(x), int(y))), special_flags=pygame.BLEND_RGB_ADD)
            behind = self.scene.color_at(palette, y)
            paper = behind.lerp(color, strength)
            # A paper bag: wider at the top, open and brightest at the bottom
            body = [(x - size * 0.75, y - size), (x + size * 0.75, y - size), (x + size * 0.55, y + size * 0.8), (x - size * 0.55, y + size * 0.8)]
            pygame.draw.polygon(surface, paper, body)
            pygame.draw.line(surface, behind.lerp(color.lerp((255, 255, 255), 0.6), strength),
                             (x - size * 0.45, y + size * 0.75), (x + size * 0.45, y + size * 0.75), max(1, int(size * 0.3)))
