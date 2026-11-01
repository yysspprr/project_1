# The far side of the water: faint hills and a treeline sitting on the horizon,
# and their reflection in the water, broken up into strips by the ripples.
# Also the reflections of the sky's clouds, if the scene has a sky

import math

import random

import pygame

from partials.config import WIDTH, s
from partials.backgrounds.base import Layer
from partials.backgrounds.helpers import make_jitter


class FarShore(Layer):
    # Draw it after the water (its reflection lies on top of the water) and before
    # anything floating on it. Kept low and soft so it never fights with the game's text.
    # In a storm it fades into the rain haze
    #
    # Palette colors it uses:
    #   "trees"         the treeline (falls back to "muted")
    #   "far_hill"      the hills behind it (no hills without it)

    TREE_HEIGHT = 14                # tallest treetops, in pixels at the medium size
    TREE_WIDTH = (8, 17)            # how wide one tree's crown is
    FIRS = 0.25                     # share of the trees that are pointed firs
    HILL_HEIGHT = 22                # tallest hilltop
    JITTER = 0.6                    # how far outline points wobble, in pixels

    REFLECT_DEPTH = 0.75            # how tall the reflection is, compared to the shore itself
    REFLECT_STRENGTH = 0.45         # how strongly it shows in the water (0 = invisible, 1 = as dark as the trees)
    STRIP = (1.5, 3)                # height of each unbroken strip of reflection, in pixels
    STRIP_GAP = (0.5, 1.5)          # gap between strips near the shore; the gaps grow further down
    STRIP_SHIFT = 3                 # how far a strip slides sideways, in pixels
    STORM_HAZE = 0.7                # how much a full storm hides the shore (0 = not at all, 1 = gone)

    CLOUD_REFLECT = 0.22            # how strongly the clouds show in the water (0 = not at all)
    CLOUD_SQUASH = 0.45             # the reflections are flatter than the clouds
    CLOUD_DEPTH = 0.8               # how far below the horizon they land, compared to how high the cloud is

    def __init__(self, scene, sky=None):
        super().__init__(scene)
        self.sky = sky              # the sky layer, for reflecting its clouds (optional)
        self.horizon = scene.view.horizon
        self.trees = self.make_treeline()
        self.hills = self.make_hills()
        self.jitter = make_jitter(len(self.trees) + len(self.hills), 1)
        self.strips = self.make_strips()
        self.shore_image = None
        self.reflect_image = None
        self.painted_palette = None
        self.cloud_images = []      # (cloud image, its reflection) pairs, so each is only flipped once

    # ---- Shapes ----

    def make_treeline(self):
        # The tops of a row of trees along the horizon, left to right
        height = s(self.TREE_HEIGHT)
        top = []
        x = -s(10)
        while x < WIDTH + s(10):
            width = s(random.uniform(*self.TREE_WIDTH))
            tall = height * random.uniform(0.55, 1)
            if random.random() < self.FIRS:
                top += [(x, self.horizon - tall * 0.45), (x + width / 2, self.horizon - tall * 1.15),
                        (x + width, self.horizon - tall * 0.45)]
            else:
                for k in range(6):
                    angle = math.pi * (1 - k / 5)
                    top.append((x + width / 2 + math.cos(angle) * width / 2,
                                self.horizon - tall * 0.6 - math.sin(angle) * tall * 0.4))
            x += width * random.uniform(0.6, 0.9)
        return top

    def make_hills(self):
        height = s(self.HILL_HEIGHT)
        wave = random.uniform(0, 2 * math.pi)
        top = []
        for x in range(-s(10), WIDTH + s(30), s(20)):
            rise = 0.5 + 0.3 * math.sin(x / s(80) + wave) + 0.2 * math.sin(x / s(37) + wave * 2)
            top.append((x, self.horizon - height * rise))
        return top

    def make_strips(self):
        # Where the reflection is broken: (top, height, sideways shift) for each unbroken strip
        strips = []
        depth = (s(self.TREE_HEIGHT) * 1.15 + 2) * self.REFLECT_DEPTH
        y = 0
        while y < depth:
            tall = random.uniform(*self.STRIP)
            strips.append((y, tall, random.uniform(-1, 1) * self.STRIP_SHIFT))
            y += tall + random.uniform(*self.STRIP_GAP) * (1 + y / 6)
        return strips

    # ---- Painting ----

    def outline(self, top, offset):
        # The shape under a line of tops, with each point wobbled a little
        points = [(top[0][0], self.horizon + 1)]
        for i, (x, y) in enumerate(top):
            points.append((x, y + self.jitter[offset + i] * self.JITTER))
        points.append((top[-1][0], self.horizon + 1))
        return points

    def paint(self, palette):
        tree_color = pygame.Color(palette.get("trees", palette["muted"]))
        top = self.horizon - s(self.HILL_HEIGHT) - s(4)
        height = int(self.horizon - top) + 2

        # The shore: only what sticks up above the horizon, on a see-through image
        shore = pygame.Surface((WIDTH, height), pygame.SRCALPHA)
        def shifted(points):
            return [(x, y - top) for x, y in points]
        if palette.get("far_hill"):
            pygame.draw.polygon(shore, pygame.Color(palette["far_hill"]),
                                shifted(self.outline(self.hills, len(self.trees))))
        pygame.draw.polygon(shore, tree_color, shifted(self.outline(self.trees, 0)))
        self.shore_image = shore
        self.shore_top = top

        # The reflection: the treeline upside down and squashed, in a color between
        # the water and the trees
        water = self.scene.color_at(palette, self.horizon + 1)
        reflect_color = water.lerp(tree_color, self.REFLECT_STRENGTH)
        depth = int((s(self.TREE_HEIGHT) * 1.15 + 2) * self.REFLECT_DEPTH) + 2
        reflection = pygame.Surface((WIDTH, depth), pygame.SRCALPHA)
        flipped = []
        for x, y in self.outline(self.trees, 0):
            flipped.append((x, (self.horizon - y) * self.REFLECT_DEPTH))
        pygame.draw.polygon(reflection, reflect_color, flipped)
        self.reflect_image = reflection
        self.painted_palette = palette

    def reflect_cloud(self, image):
        # A cloud's image turned upside down and flattened
        flipped = pygame.transform.flip(image, False, True)
        height = max(1, int(image.get_height() * self.CLOUD_SQUASH))
        return pygame.transform.scale(flipped, (image.get_width(), height))

    # ---- Layer methods ----

    def wobble(self):
        self.jitter = make_jitter(len(self.trees) + len(self.hills), 1)
        self.strips = self.make_strips()        # the ripples break the reflection up differently
        self.shore_image = None

    def draw(self, surface, palette):
        if self.shore_image is None or self.painted_palette is not palette:
            self.paint(palette)

        # Rain haze: the shore and its reflection fade into the sky and water in a storm
        clear = 1 - self.STORM_HAZE * self.scene.weather["storm"]
        alpha = int(255 * clear)

        # Clouds' reflections first: they're the furthest things the water shows
        if self.sky is not None and palette.get("cloud"):
            used = []
            for cloud in self.sky.clouds:
                image = cloud["image"]
                if image is None:
                    continue
                reflected = None
                for source, made in self.cloud_images:
                    if source is image:
                        reflected = made
                if reflected is None:
                    reflected = self.reflect_cloud(image)
                used.append((image, reflected))
                reflected.set_alpha(int(255 * self.CLOUD_REFLECT * clear))
                below = (self.horizon - cloud["y"]) * self.CLOUD_DEPTH
                surface.blit(reflected, reflected.get_rect(midtop=(cloud["x"], self.horizon + below)))
            self.cloud_images = used            # forget the ones that are gone

        self.shore_image.set_alpha(alpha)
        surface.blit(self.shore_image, (0, self.shore_top))

        # The reflection, strip by strip, each slid a little sideways
        self.reflect_image.set_alpha(alpha)
        width = self.reflect_image.get_width()
        for top, tall, shift in self.strips:
            area = pygame.Rect(0, int(top), width, max(1, round(tall)))
            surface.blit(self.reflect_image, (shift, self.horizon + int(top)), area)
