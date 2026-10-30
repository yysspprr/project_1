# Rings spreading out where drops land on the water

import random

import pygame

from partials.config import s
from partials.backgrounds.base import Layer
from partials.backgrounds.helpers import make_jitter, ellipse_points, draw_wobbly_ring


class Ripples(Layer):
    # Flattened rings that grow and fade, each followed by a fainter echo

    LIFETIME = (1600, 2600)         # milliseconds a ripple lasts
    RADIUS = (25, 60)               # how wide a ripple grows, at the medium size
    FLATTEN = 0.35                  # rings are squashed: we see the water from an angle
    LINE_WIDTH = 2
    ECHO_DELAY = 0.25               # how far behind the second ring follows
    POINTS = 24                     # points around each ring
    JITTER = 0.05                   # how far a point can wobble, as a share of the ring's size

    def __init__(self, scene):
        super().__init__(scene)
        self.ripples = []

    def add(self, x, y):
        # Start a new ripple at (x, y): called by whatever makes the drops
        self.ripples.append({
            "x": x,
            "y": y,
            "radius": s(random.randint(*self.RADIUS)),
            "lifetime": random.randint(*self.LIFETIME),
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
        bg = pygame.Color(palette["bg"])
        ripple_color = pygame.Color(palette["ripple"])

        for ripple in self.ripples:
            progress = ripple["age"] / ripple["lifetime"]       # 0 when it lands, 1 when it's gone
            self.draw_ring(surface, ripple, progress, 1, bg, ripple_color)

            echo = progress - self.ECHO_DELAY
            if echo > 0:
                self.draw_ring(surface, ripple, echo, 0.5, bg, ripple_color)

    def draw_ring(self, surface, ripple, progress, strength, bg, ripple_color):
        # Fast at first, slowing down, like a real ripple
        grown = 1 - (1 - progress) ** 2
        radius_x = ripple["radius"] * grown
        radius_y = radius_x * self.FLATTEN
        line = s(self.LINE_WIDTH)
        if radius_y < line:
            return                  # too small to draw as a ring yet

        fade = (1 - progress) * strength
        color = bg.lerp(ripple_color, fade)

        points = ellipse_points(ripple["x"], ripple["y"], radius_x, radius_y, ripple["jitter"])
        draw_wobbly_ring(surface, color, points, line)
