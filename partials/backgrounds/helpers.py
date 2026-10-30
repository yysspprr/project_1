# Small tools shared by the layers

import math

import random

import pygame


class Timer:
    # Counts down and says when it's time for the next event,
    # waiting a random number of milliseconds between events

    def __init__(self, wait_range):
        self.wait_range = wait_range        # (shortest, longest) in milliseconds
        self.left = 0                       # milliseconds until the next event

    def tick(self, dt):
        # True once each time the countdown runs out
        self.left -= dt
        if self.left <= 0:
            self.left = random.randint(*self.wait_range)
            return True
        return False


def make_jitter(count, amount):
    # A small random push in or out for each of count points
    jitter = []
    for i in range(count):
        jitter.append(random.uniform(-amount, amount))
    return jitter


def ellipse_points(x, y, radius_x, radius_y, jitter):
    # Points around an ellipse, each pushed in or out by its jitter
    count = len(jitter)
    points = []
    for i in range(count):
        angle = 2 * math.pi * i / count
        push = 1 + jitter[i]
        points.append((x + radius_x * math.cos(angle) * push,
                       y + radius_y * math.sin(angle) * push))
    return points


def draw_wobbly_ring(surface, color, points, width):
    # A closed outline through the points, with round joins so the corners don't show
    pygame.draw.lines(surface, color, True, points, width)
    for point in points:
        pygame.draw.circle(surface, color, point, width / 2)
