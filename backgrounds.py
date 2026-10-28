# Animated backgrounds: each one is a class with update() and draw()

import random

import pygame

from config import WIDTH, HEIGHT, s


class RainBackground:
    # Raindrops landing on still water: flattened rings that grow and fade

    SPAWN_TIME = (150, 500)         # milliseconds between drops (shortest, longest)
    LIFETIME = (1600, 2600)         # milliseconds a ripple lasts
    RADIUS = (25, 60)               # how wide a ripple grows, at the medium size
    FLATTEN = 0.35                  # rings are squashed: we see the water from an angle
    LINE_WIDTH = 2
    ECHO_DELAY = 0.25               # how far behind the second ring follows

    def __init__(self):
        self.ripples = []
        self.next_drop = 0          # milliseconds until the next drop lands

    def update(self, dt):
        # Age every ripple and keep only the ones still alive
        alive = []
        for ripple in self.ripples:
            ripple["age"] += dt
            if ripple["age"] < ripple["lifetime"]:
                alive.append(ripple)
        self.ripples = alive

        # Count down to the next drop
        self.next_drop -= dt
        if self.next_drop <= 0:
            self.add_drop()
            self.next_drop = random.randint(*self.SPAWN_TIME)

    def add_drop(self):
        self.ripples.append({
            "x": random.randint(0, WIDTH),
            "y": random.randint(0, HEIGHT),
            "radius": s(random.randint(*self.RADIUS)),
            "lifetime": random.randint(*self.LIFETIME),
            "age": 0,
        })

    def draw(self, surface, palette):
        surface.fill(palette["bg"])
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
        width = round(ripple["radius"] * 2 * grown)
        height = round(width * self.FLATTEN)
        line = s(self.LINE_WIDTH)
        if height < line * 2:
            return                  # too small to draw as a ring yet

        ring = pygame.Rect(0, 0, width, height)
        ring.center = (ripple["x"], ripple["y"])
        fade = (1 - progress) * strength
        pygame.draw.ellipse(surface, bg.lerp(ripple_color, fade), ring, line)


# Which background goes with which theme (themes without one use a plain color)
BACKGROUNDS = {
    "rain": RainBackground,
}

def make_background(theme):
    if theme in BACKGROUNDS:
        return BACKGROUNDS[theme]()
    return None