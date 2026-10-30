# One shared way of seeing the scene, so every layer agrees on how far away things are
#
# We look down at a flat surface (water, a field, a street) from an angle.
# The bottom of the window is close to us, the top is far away. Further away:
#   - things look smaller                   (scale)
#   - circles look more squashed            (flatten)
#   - colors fade a little into the haze    (clarity)
#   - evenly spaced rows look closer together

import random

from partials.config import HEIGHT


class Perspective:

    def __init__(self, far_scale=0.35, near_flatten=0.5, far_flatten=0.18, far_clarity=0.55):
        self.far_scale = far_scale          # size at the top of the window, compared to the bottom
        self.near_flatten = near_flatten    # height / width of a circle at the bottom
        self.far_flatten = far_flatten      # ... and at the top
        self.far_clarity = far_clarity      # how strongly things show at the top (1 = as strong as up close)

    def nearness(self, y):
        # 0 at the top of the window (far), 1 at the bottom (near)
        return max(0, min(1, y / HEIGHT))

    def scale(self, y):
        # How big things look at height y: 1 at the bottom, far_scale at the top.
        # Growing in a straight line toward the bottom is how a flat surface really looks
        return self.far_scale + (1 - self.far_scale) * self.nearness(y)

    def flatten(self, y):
        # How squashed a circle lying on the surface looks at height y
        return self.far_flatten + (self.near_flatten - self.far_flatten) * self.nearness(y)

    def clarity(self, y):
        return self.far_clarity + (1 - self.far_clarity) * self.nearness(y)

    def height_at(self, depth):
        # The height on the screen of a spot depth of the way from near (0) to far (1)
        # on the surface itself. Halfway back is well above the middle of the window
        size = 1 / (1 + (1 / self.far_scale - 1) * depth)
        return HEIGHT * (size - self.far_scale) / (1 - self.far_scale)

    def random_y(self, spread=1):
        # A random height for something lying on the surface.
        # spread 0: every height is equally likely (more space near us gets more things);
        # spread 1: every equally deep strip of surface is equally likely (more crowded far away)
        if random.random() < spread:
            return self.height_at(random.random())
        return random.uniform(0, HEIGHT)

    def rows(self, count):
        # Heights that split the window into count rows that are equally deep on the surface:
        # thin rows far away, tall rows up close. Returns count + 1 heights, from 0 to HEIGHT
        heights = []
        for i in range(count + 1):
            heights.append(self.height_at(1 - i / count))
        return heights
