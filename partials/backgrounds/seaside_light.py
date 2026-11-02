# Light at the seaside: a path of glitter on the water toward the sun or moon, the far
# lighthouse's beam sweeping round at night, and on dark nights the breaking waves glowing
# blue-green where the surf stirs up the plankton

import math

import random

import pygame

from partials.config import WIDTH, HEIGHT, s
from partials.backgrounds.base import Layer
from partials.backgrounds.brook_light import glow_sprite
from partials.backgrounds.beach import SHORE


class GlitterPath(Layer):
    # Sparkles dancing on the sea in a path from the horizon below the sun (or moon) toward
    # the shore, narrow far off and widening as it comes closer, each one flashing briefly.
    # A soft sheen lies under them
    #
    # Palette colors it uses:
    #   "glitter"               the sparkles at their brightest

    COUNT = 130

    def __init__(self, scene, sky, sea):
        super().__init__(scene)
        self.sky = sky
        self.sea = sea
        self.time = 0
        self.horizon = scene.view.horizon
        self.sparks = []
        for i in range(self.COUNT):
            t = random.random() ** 1.4                      # more of them far off, where they crowd together
            self.sparks.append({"t": t, "across": random.gauss(0, 0.45), "period": random.uniform(500, 1500),
                                "phase": random.uniform(0, 6)})

    def update(self, dt):
        self.time += dt

    def draw(self, surface, palette):
        if "glitter" not in palette:
            return
        glitter = pygame.Color(palette["glitter"])
        light = min(1.2, self.scene.weather.get("light", 1))
        x0 = self.sky.body_x
        bottom = s(SHORE) - s(10)
        for p in self.sparks:
            y = self.horizon + 2 + (bottom - self.horizon) * p["t"]
            width = s(8) + s(80) * p["t"]
            x = x0 + p["across"] * width + math.sin(self.time / 900 + p["phase"]) * s(2)
            flash = max(0.0, math.sin(self.time / p["period"] + p["phase"])) ** 2
            strength = flash * light * self.scene.keep(x, 0.5) * (1 - 0.5 * abs(p["across"]))
            if strength < 0.08:
                continue
            half = s(1.5) + s(4) * p["t"]
            behind = self.sea.sea_color(palette, y)
            pygame.draw.line(surface, behind.lerp(glitter, min(1.0, strength)), (x - half, y), (x + half, y), 1)


class LighthouseBeam(Layer):
    # At night the lighthouse on the headland is lit: a steady glow at its lamp, and a beam
    # sweeping round, stretching out across the sky as it turns side-on and shrinking as it
    # swings toward or away from us, with a bright flash each time it points our way.
    # Night only: needs "beam" in the palette
    #
    # Palette colors it uses:
    #   "beam"

    TURN = 9000                     # milliseconds for one full turn
    LENGTH = 190                    # how far the beam reaches side-on, pixels at the medium size

    def __init__(self, scene, sea):
        super().__init__(scene)
        self.sea = sea
        self.time = 0
        self.glow = None
        self.painted_palette = None

    def paint(self, palette):
        c = pygame.Color(palette["beam"])
        self.glow = glow_sprite(s(18), (c.r * 0.6, c.g * 0.55, c.b * 0.4), 1.0, 8)
        self.flash = glow_sprite(s(46), (c.r * 0.7, c.g * 0.65, c.b * 0.5), 1.0, 10)
        self.painted_palette = palette

    def update(self, dt):
        self.time += dt

    def draw(self, surface, palette):
        if "beam" not in palette:
            return
        if self.painted_palette is not palette:
            self.paint(palette)
        r = self.sea.tower_rect
        lamp = (r.centerx, r.top - s(2))
        angle = self.time / self.TURN * 2 * math.pi
        side = math.cos(angle)                              # +1 pointing right, -1 left
        toward = math.sin(angle)                            # +1 toward us
        c = pygame.Color(palette["beam"])
        length = s(self.LENGTH) * abs(side)
        if length > s(6):
            beam = pygame.Surface((int(length) + 2, s(24)), pygame.SRCALPHA)
            spread = s(4) + s(8) * abs(side)
            strength = 0.32 * (0.6 + 0.4 * max(0.0, toward + 0.3))
            for k in range(4):
                share = 1 - k / 4
                points = [(0, beam.get_height() / 2 - s(1.5)), (length * share, beam.get_height() / 2 - spread * share),
                          (length * share, beam.get_height() / 2 + spread * share), (0, beam.get_height() / 2 + s(1.5))]
                pygame.draw.polygon(beam, (c.r, c.g, c.b, int(255 * strength * 0.3)), points)
            if side < 0:
                beam = pygame.transform.flip(beam, True, False)
                surface.blit(beam, (lamp[0] - length, lamp[1] - beam.get_height() / 2))
            else:
                surface.blit(beam, (lamp[0], lamp[1] - beam.get_height() / 2))
        surface.blit(self.glow, self.glow.get_rect(center=lamp), special_flags=pygame.BLEND_RGB_ADD)
        if toward > 0.9:
            flash = self.flash.copy()
            level = int(255 * (toward - 0.9) / 0.1)
            flash.fill((level, level, level), special_flags=pygame.BLEND_RGB_MULT)
            surface.blit(flash, flash.get_rect(center=lamp), special_flags=pygame.BLEND_RGB_ADD)
        pygame.draw.circle(surface, c, lamp, max(1, s(1.6)))


class GlowingSurf(Layer):
    # On dark nights the breaking waves glow blue-green: the crest lights up as it breaks,
    # and the foamy edge of the water glows as it runs up the sand, fading as it draws back.
    # Night only: needs "surf_glow" in the palette
    #
    # Palette colors it uses:
    #   "surf_glow"

    def __init__(self, scene, waves):
        super().__init__(scene)
        self.waves = waves
        self.sprite = None
        self.painted_palette = None

    def draw(self, surface, palette):
        if "surf_glow" not in palette:
            return
        if self.painted_palette is not palette:
            c = pygame.Color(palette["surf_glow"])
            self.sprites = [glow_sprite(s(9), (c.r * k / 4, c.g * k / 4, c.b * k / 4), 0.6, 5) for k in range(1, 5)]
            self.painted_palette = palette
        if self.waves.crest is not None:
            points, strength = self.waves.crest
            self.glow_along(surface, points, (strength - 0.55) / 0.45)
        elif self.waves.edge is not None:
            points, strength = self.waves.edge
            self.glow_along(surface, points, strength * 0.8)

    def glow_along(self, surface, points, strength):
        if strength <= 0.05:
            return
        for i in range(0, len(points), 2):
            x, y = points[i]
            level = strength * self.scene.keep(x, 0.5) * (0.6 + 0.4 * math.sin(i * 1.3))
            if level < 0.1:
                continue
            sprite = self.sprites[min(3, int(level * 4))]
            surface.blit(sprite, sprite.get_rect(center=(int(x), int(y))), special_flags=pygame.BLEND_RGB_ADD)
