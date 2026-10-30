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

    def tick(self, dt, rate=1):
        # True once each time the countdown runs out.
        # rate speeds the countdown up (above 1) or slows it down (below 1)
        self.left -= dt * rate
        if self.left <= 0:
            self.left = random.randint(*self.wait_range)
            return True
        return False


class Swell:
    # A number that slowly waxes and wanes on its own, for things that should
    # come and go: how hard it rains, how strong the wind is, how bright the light is.
    # Every now and then it picks a new random target and glides there smoothly
    #
    #   swell = Swell(0.3, 1.5, (4000, 9000))
    #   swell.update(dt) every frame, then use swell.value

    def __init__(self, low, high, glide_time, start=None):
        self.low = low
        self.high = high
        self.glide_time = glide_time        # (shortest, longest) milliseconds to reach a new target
        self.value = start if start is not None else random.uniform(low, high)
        self.pick_target()

    def pick_target(self):
        self.start = self.value
        self.target = random.uniform(self.low, self.high)
        self.time = random.randint(*self.glide_time)
        self.age = 0

    def update(self, dt):
        self.age += dt
        if self.age >= self.time:
            self.value = self.target
            self.pick_target()
            return
        # Ease in and out, so it never jerks into a change
        t = self.age / self.time
        smooth = t * t * (3 - 2 * t)
        self.value = self.start + (self.target - self.start) * smooth

    def share(self):
        # Where the value sits between low (0) and high (1)
        return (self.value - self.low) / (self.high - self.low)


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


def wavy_line(left, right, heights):
    # Points spread evenly from left to right, one for each height
    count = len(heights)
    points = []
    for i in range(count):
        x = left + (right - left) * i / (count - 1)
        points.append((x, heights[i]))
    return points


def draw_wobbly_ring(surface, color, points, width):
    # A closed outline through the points, with round joins so the corners don't show
    pygame.draw.lines(surface, color, True, points, width)
    for point in points:
        pygame.draw.circle(surface, color, point, width / 2)
