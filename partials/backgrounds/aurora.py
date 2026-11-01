# The northern lights: slow curtains of light hanging in the night sky

import math

import random

import pygame

from partials.config import WIDTH, s
from partials.backgrounds.base import Layer


class Aurora(Layer):
    # Each curtain is a row of thin vertical rays: brightest at its lower edge, fading
    # upward from one color to another. The curtains ripple slowly along their length,
    # brighter patches drift along them, and the whole show comes and goes on its own swell.
    # Falling snow (the scene's weather["storm"]) hides it, and it stays faint behind the
    # game's text. Only drawn when the palette has aurora colors, so: only at night.
    # It's painted into an image a few times a second (it moves slowly), and other layers
    # can borrow that image upside down as a reflection: see reflection()
    #
    # Palette colors it uses:
    #   "aurora_low", "aurora_high"     the bottom and top of the curtains (no aurora without them)

    CURTAINS = 3
    STEP = 3                        # pixels between rays
    RAY_HEIGHT = (16, 44)           # pixels at the medium size
    BASE = (0.4, 0.8)               # where the curtains' lower edges sit: share of the way down the sky
    WAVE = 12                       # how far a curtain's lower edge ripples up and down, in pixels
    STRENGTH = 0.55                 # brightest it gets (0 = invisible, 1 = solid color)
    QUIET = 0.6                     # how much it fades behind the game's text (0 = not at all)
    SHOW = (0.15, 1)                # the whole show waxes and wanes between these
    SHOW_TIME = (9000, 22000)
    REPAINT = 90                    # milliseconds between repaints: it moves slowly
    HEIGHT_STEP = 2                 # ray heights are rounded to this, so each size is only made once

    def __init__(self, scene):
        super().__init__(scene)
        self.horizon = scene.view.horizon
        self.show = self.swell(*self.SHOW, self.SHOW_TIME)
        self.time = 0
        self.since_paint = self.REPAINT
        self.curtains = []
        for i in range(self.CURTAINS):
            self.curtains.append({
                "base": random.uniform(*self.BASE),
                "length": random.uniform(0.8, 1.6),         # how long its ripples are, in window widths
                "speed": random.uniform(-0.05, 0.05),       # how fast they travel, window widths per second
                "phase": random.uniform(0, 2 * math.pi),
                "glow_length": random.uniform(0.3, 0.6),    # the bright patches drifting along it
                "glow_speed": random.uniform(0.03, 0.08) * random.choice((-1, 1)),
                "height": s(random.randint(*self.RAY_HEIGHT)),
            })
        self.image = None
        self.flipped = None
        self.painted_palette = None
        self.rays = {}              # ready-made rays, by height
        self.version = 0            # goes up on every repaint, so borrowers know when to update

    def make_ray(self, palette, height):
        # One ray: a thin strip, fading from the low color at the bottom to the high color
        # at the top, see-through at the top and quickly fading at the very bottom edge
        low = pygame.Color(palette["aurora_low"])
        high = pygame.Color(palette["aurora_high"])
        strip = pygame.Surface((1, height), pygame.SRCALPHA)
        for y in range(height):
            up = 1 - y / max(height - 1, 1)                 # 0 at the bottom, 1 at the top
            color = low.lerp(high, up)
            fade = (1 - up) ** 1.6
            if up < 0.08:
                fade *= 0.5 + up / 0.16                     # a soft lower edge, not a hard line
            color.a = int(255 * fade)
            strip.set_at((0, y), color)
        return pygame.transform.scale(strip, (self.STEP + 1, height))

    def ray(self, palette, height):
        height = max(self.HEIGHT_STEP, round(height / self.HEIGHT_STEP) * self.HEIGHT_STEP)
        if height not in self.rays:
            self.rays[height] = self.make_ray(palette, height)
        return self.rays[height]

    def paint(self, palette):
        image = pygame.Surface((WIDTH, int(self.horizon) + 1), pygame.SRCALPHA)
        seconds = self.time / 1000
        show = self.show.value * (1 - self.scene.weather["storm"])

        if show > 0.02:
            for curtain in self.curtains:
                for x in range(0, WIDTH, self.STEP):
                    across = x / WIDTH
                    ripple = math.sin((across / curtain["length"] + seconds * curtain["speed"]) * 2 * math.pi
                                      + curtain["phase"])
                    glow = 0.5 + 0.5 * math.sin((across / curtain["glow_length"] + seconds * curtain["glow_speed"])
                                                * 2 * math.pi + curtain["phase"] * 2)
                    base = self.horizon * curtain["base"] + s(self.WAVE) * ripple
                    height = curtain["height"] * (0.6 + 0.4 * glow)
                    strength = self.STRENGTH * show * (0.25 + 0.75 * glow) * self.scene.keep(x, self.QUIET)
                    if strength < 0.02:
                        continue
                    ray = self.ray(palette, height)
                    ray.set_alpha(int(255 * strength))
                    image.blit(ray, (x, base - ray.get_height()))

        self.image = image
        self.flipped = None
        self.version += 1

    def reflection(self):
        # The aurora upside down, for water or ice to show (None when there's nothing to show)
        if self.image is None:
            return None
        if self.flipped is None:
            self.flipped = pygame.transform.flip(self.image, False, True)
        return self.flipped

    def update(self, dt):
        self.time += dt
        self.since_paint += dt

    def draw(self, surface, palette):
        if "aurora_low" not in palette or "aurora_high" not in palette:
            self.image = None                               # daytime: no aurora, nothing to reflect
            return
        if self.painted_palette is not palette:
            self.rays = {}
            self.painted_palette = palette
            self.since_paint = self.REPAINT
        if self.since_paint >= self.REPAINT or self.image is None:
            self.paint(palette)
            self.since_paint = 0
        surface.blit(self.image, (0, 0))
