# The far side of the water: faint hills and a treeline sitting on the horizon,
# and their reflection in the water, broken up into strips by the ripples.
# If the scene has a sky, the water also reflects what's in it: the clouds,
# the sun or moon, and the stars

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
    HILL_HEIGHT = 32                # tallest hilltop
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

    # The sun or moon on rippled water: not a neat mirror image, but a long column of
    # broken bands stretching toward us, narrower and fainter the further it reaches
    BODY_REFLECT = 0.8              # how strongly the bands show right under the sun or moon
    BODY_GLOW_REFLECT = 0.4         # how strongly its glow shows in the water
    BODY_LENGTH = 9                 # how far the column reaches, in sun or moon radii
    BODY_TAPER = 0.3                # how wide the bands are at the far end, compared to the start
    BODY_BAND = (1, 2.5)            # how tall each band is, in pixels
    BODY_BAND_GAP = (1.2, 3)        # the gaps between bands; they grow further down
    BODY_SHIFT = (2, 7)             # how far bands slide sideways: at the top, at the far end
    BODY_SPLIT = 0.4                # chance a band is broken into two pieces
    BODY_GLOW_STRETCH = 2.2         # the glow's reflection is this many times taller than the glow

    STAR_REFLECT = 0.55             # how strongly the stars show in the water
    STAR_DEPTH = 0.85               # how far below the horizon they land, compared to how high the star is
    STAR_SHIMMER = 1.5              # how far a reflected star jumps sideways on each wobble
    STAR_BROKEN = 0.2               # chance a reflected star is broken up by a ripple on each wobble
    STAR_QUIET = 0.6                # how much they fade behind the game's text

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
        self.body_images = []       # the same for the sun or moon and its glow
        self.body_strips = []
        self.star_shimmer = []
        self.shake_reflections()

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

    def reflect(self, image, squash):
        # An image turned upside down and flattened
        flipped = pygame.transform.flip(image, False, True)
        height = max(1, int(image.get_height() * squash))
        return pygame.transform.scale(flipped, (image.get_width(), height))

    def reflected(self, image, squash, cache):
        # The reflection of image, made once and kept while the image stays the same
        for source, made in cache:
            if source is image:
                return made
        made = self.reflect(image, squash)
        cache.append((image, made))
        if len(cache) > 8:
            del cache[0]
        return made

    def shake_reflections(self):
        # New breaks in the sun or moon's reflection, and new shimmer for the stars.
        # Each band piece: how far down the column it is (0-1), its height, its sideways
        # shift (as a share of the most it can move there) and its width (as a share of the most)
        self.body_strips = []
        if self.sky is not None:
            length = s(self.sky.BODY_SIZE) * self.BODY_LENGTH
            y = 0
            while y < length:
                share = y / length
                tall = random.uniform(*self.BODY_BAND)
                shift = random.uniform(-1, 1)
                width = random.uniform(0.3, 1)
                if random.random() < self.BODY_SPLIT:
                    # Broken in two: a piece either side, with a gap in the middle
                    self.body_strips.append((share, tall, shift - width * 0.6, width * 0.45))
                    self.body_strips.append((share, tall, shift + width * 0.6, width * 0.35))
                else:
                    self.body_strips.append((share, tall, shift, width))
                y += tall + random.uniform(*self.BODY_BAND_GAP) * (1 + share * 1.5)
        count = len(self.sky.stars) if self.sky is not None else 0
        self.star_shimmer = []
        for i in range(count):
            broken = random.random() < self.STAR_BROKEN
            self.star_shimmer.append(None if broken else random.uniform(-1, 1) * self.STAR_SHIMMER)

    def draw_body_reflection(self, surface, palette, clear):
        # The sun or moon's reflection: its glow stretched long, with a column of broken
        # bands on top, starting where the mirror image of the sun or moon would be
        sky = self.sky
        light = max(0, min(1, self.scene.weather["light"]))
        radius = s(sky.BODY_SIZE)
        length = radius * self.BODY_LENGTH
        mirror_y = self.horizon + (self.horizon - sky.body_y) * self.CLOUD_DEPTH
        top = mirror_y - radius * 0.6

        if sky.glow_image is not None:
            glow = self.reflected(sky.glow_image, self.BODY_GLOW_STRETCH, self.body_images)
            glow.set_alpha(int(255 * self.BODY_GLOW_REFLECT * light * clear))
            surface.blit(glow, glow.get_rect(center=(sky.body_x, top + length * 0.3)))

        body = pygame.Color(palette["body"])
        for share, tall, shift, width in self.body_strips:
            y = top + share * length
            fade = 1 - 0.75 * share
            strength = self.BODY_REFLECT * fade * (0.5 + 0.5 * light) * clear
            color = self.scene.color_at(palette, y).lerp(body, max(0, min(1, strength)))
            band_width = radius * 2 * (1 - (1 - self.BODY_TAPER) * share) * width
            slide = shift * (s(self.BODY_SHIFT[0]) + (s(self.BODY_SHIFT[1]) - s(self.BODY_SHIFT[0])) * share)
            x = sky.body_x + slide - band_width / 2
            band = pygame.Rect(round(x), round(y), max(1, round(band_width)), max(1, round(tall)))
            pygame.draw.rect(surface, color, band, border_radius=max(1, round(tall / 2)))

    def draw_star_reflections(self, surface, palette, clear):
        # Each star mirrored below the horizon as a short dash, twinkling with its star;
        # on every wobble they shimmer sideways and a few are broken up by ripples
        sky = self.sky
        star = pygame.Color(palette["star"])
        for dot, shimmer in zip(sky.stars, self.star_shimmer):
            if shimmer is None:
                continue
            y = self.horizon + (self.horizon - dot["y"]) * self.STAR_DEPTH
            x = dot["x"] + shimmer
            strength = sky.star_strength(dot) * self.STAR_REFLECT * clear * self.scene.keep(x, self.STAR_QUIET)
            if strength <= 0.02:
                continue
            water = self.scene.color_at(palette, y)
            half = s(1.5) * self.scene.view.scale(y) + 0.5
            pygame.draw.line(surface, water.lerp(star, min(1, strength)), (x - half, y), (x + half, y))

    # ---- Layer methods ----

    def wobble(self):
        self.jitter = make_jitter(len(self.trees) + len(self.hills), 1)
        self.strips = self.make_strips()        # the ripples break the reflection up differently
        self.shake_reflections()
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
                    reflected = self.reflect(image, self.CLOUD_SQUASH)
                used.append((image, reflected))
                reflected.set_alpha(int(255 * self.CLOUD_REFLECT * clear))
                below = (self.horizon - cloud["y"]) * self.CLOUD_DEPTH
                surface.blit(reflected, reflected.get_rect(midtop=(cloud["x"], self.horizon + below)))
            self.cloud_images = used            # forget the ones that are gone

        if self.sky is not None and palette.get("star"):
            self.draw_star_reflections(surface, palette, clear)
        if self.sky is not None and palette.get("sky_body"):
            self.draw_body_reflection(surface, palette, clear)

        self.shore_image.set_alpha(alpha)
        surface.blit(self.shore_image, (0, self.shore_top))

        # The reflection, strip by strip, each slid a little sideways
        self.reflect_image.set_alpha(alpha)
        width = self.reflect_image.get_width()
        for top, tall, shift in self.strips:
            area = pygame.Rect(0, int(top), width, max(1, round(tall)))
            surface.blit(self.reflect_image, (shift, self.horizon + int(top)), area)
