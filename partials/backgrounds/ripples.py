# Rings spreading out where drops land on the water

import math

import random

import pygame

from partials.config import s
from partials.backgrounds.base import Layer
from partials.backgrounds.helpers import make_jitter, ellipse_points


class Ripples(Layer):
    # Squashed rings that grow and fade, each followed by fainter echoes, with a tiny
    # splash where the drop hit. Size and squash come from the scene's perspective,
    # and the far side of each ring catches the same light as the water's glints
    #
    # Palette colors it uses:
    #   "ripple"        the ring's color when fresh
    #   "ripple_light"  the light caught on the ring's far side; it should stand out from
    #                   the water (without it: "ripple" mixed with "glint")

    LIFETIME = (1300, 2100)         # milliseconds a ripple lasts
    RADIUS = (25, 60)               # how wide a ripple grows, up close, in pixels
    LINE_WIDTH = 2                  # up close, in pixels
    ECHOES = (1, 3)                 # how many fainter rings follow the first (fewest, most)
    ECHO_DELAY = 0.2                # how far behind each echo follows, as a share of the lifetime
    ECHO_STRENGTH = 0.55            # each echo is this much as strong as the ring before it
    LIGHT = 0.5                     # without "ripple_light": how much of the glint color the far side catches
    POINTS = 24                     # points around each ring
    JITTER = 0.05                   # how far a point can wobble, as a share of the ring's size

    SPLASH_TIME = 220               # milliseconds the splash droplets are in the air
    SPLASH_HEIGHT = 9               # how high they jump, up close, in pixels
    SPLASH_SPREAD = 6               # how far sideways they land, up close, in pixels
    SPLASH_SIZE = 1.5               # droplet radius up close, in pixels

    def __init__(self, scene):
        super().__init__(scene)
        self.ripples = []

    def add(self, x, y, size=1, slow=1, strength=1, echoes=None, splash=True):
        # Start a new ripple at (x, y): called by whatever disturbs the water.
        # The extras make other kinds of ripple than a raindrop's:
        #   size        how wide it grows, compared to a raindrop's
        #   slow        how much longer it takes to spread and fade
        #   strength    how strongly it shows
        #   echoes      how many rings follow the first (None: a random number, like rain)
        #   splash      whether droplets jump up where it starts
        scale = self.scene.view.scale(y)
        self.ripples.append({
            "x": x,
            "y": y,
            "size": scale,
            "radius": s(random.randint(*self.RADIUS)) * scale * size,
            "lifetime": random.randint(*self.LIFETIME) * slow,
            "echoes": random.randint(*self.ECHOES) if echoes is None else echoes,
            "strength": strength,
            "splash": splash,
            "age": 0,
            "jitter": make_jitter(self.POINTS, self.JITTER),
        })

    def update(self, dt):
        # Age every ripple and keep only the ones still alive
        alive = []
        for ripple in self.ripples:
            ripple["age"] += dt
            if ripple["age"] < ripple["lifetime"]:
                alive.append(ripple)
        self.ripples = alive

    def wobble(self):
        # New pushes on every wobble tick, so the rings boil
        for ripple in self.ripples:
            ripple["jitter"] = make_jitter(self.POINTS, self.JITTER)

    def draw(self, surface, palette):
        view = self.scene.view
        ripple_color = pygame.Color(palette["ripple"])
        if "ripple_light" in palette:
            light_color = pygame.Color(palette["ripple_light"])
        else:
            light_color = ripple_color.lerp(pygame.Color(palette.get("glint", palette["ripple"])), self.LIGHT)

        for ripple in self.ripples:
            water = self.scene.color_at(palette, ripple["y"])     # fade into the water right under it
            clarity = view.clarity(ripple["y"]) * self.scene.keep(ripple["x"])     # fainter far away and behind the game
            progress = ripple["age"] / ripple["lifetime"]       # 0 when it lands, 1 when it's gone

            strength = clarity * ripple["strength"]
            for ring in range(1 + ripple["echoes"]):
                ring_progress = progress - ring * self.ECHO_DELAY
                if ring_progress > 0:
                    self.draw_ring(surface, ripple, ring_progress, strength, water, ripple_color, light_color)
                strength *= self.ECHO_STRENGTH

            if ripple["splash"] and ripple["age"] < self.SPLASH_TIME:
                self.draw_splash(surface, ripple, water, light_color, clarity)

    def draw_ring(self, surface, ripple, progress, strength, water, ripple_color, light_color):
        # Fast at first, slowing down, like a real ripple
        grown = 1 - (1 - progress) ** 2
        radius_x = ripple["radius"] * grown
        radius_y = radius_x * self.scene.view.flatten(ripple["y"])
        line = max(1, round(s(self.LINE_WIDTH) * ripple["size"]))
        if radius_y < line:
            return                  # too small to draw as a ring yet

        fade = (1 - progress) * strength
        near_color = water.lerp(ripple_color, fade)
        far_color = water.lerp(light_color, fade)

        points = ellipse_points(ripple["x"], ripple["y"], radius_x, radius_y, ripple["jitter"])

        # The near half of the ring (bottom on screen) is plain, the far half catches the light.
        # Two open lines that share their end points, so the ring is closed
        half = len(points) // 2
        pygame.draw.lines(surface, near_color, False, points[:half + 1], line)
        pygame.draw.lines(surface, far_color, False, points[half:] + points[:1], line)

    def draw_splash(self, surface, ripple, water, light_color, clarity):
        # Three droplets hop up out of the water and fall back in
        progress = ripple["age"] / self.SPLASH_TIME
        hop = math.sin(math.pi * progress)                  # up and back down
        size = ripple["size"]
        color = water.lerp(light_color, (1 - progress) * clarity)
        radius = max(1, s(self.SPLASH_SIZE) * size)
        for side in (-1, 0, 1):
            x = ripple["x"] + side * s(self.SPLASH_SPREAD) * size * progress
            y = ripple["y"] - s(self.SPLASH_HEIGHT) * size * hop * (0.6 if side else 1)
            pygame.draw.circle(surface, color, (x, y), radius)
