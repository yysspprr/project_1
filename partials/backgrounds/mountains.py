# Far away on the horizon: a range of snow-capped mountains, with a row of snowy fir
# trees in front of them. Painted once into an image and only repainted when it wobbles

import math

import random

import pygame

from partials.config import WIDTH, s
from partials.backgrounds.base import Layer
from partials.backgrounds.helpers import make_jitter


class SnowyRange(Layer):
    # Kept soft, close to the sky's colors, so it reads as far away and never fights the
    # game's text. In a storm it fades into the snow haze
    #
    # Palette colors it uses:
    #   "mountain", "mountain_snow"     the rock and the snow on top (no mountains without "mountain")
    #   "fir", "fir_snow"               the trees and the snow on their branches (no trees without "fir")

    PEAKS = (4, 6)                  # how many peaks across the window
    PEAK_HEIGHT = (38, 68)          # pixels at the medium size
    CAP = (0.3, 0.45)               # how far down a peak its snow cap reaches, as a share of its height
    FIR_HEIGHT = (9, 17)
    FIR_WIDTH = 0.55                # a fir's width, as a share of its height
    FIR_TIERS = 3                   # layers of branches on each fir
    JITTER = 0.6                    # outline wobble, in pixels
    STORM_HAZE = 0.6                # how much a full storm hides it (0 = not at all, 1 = gone)

    def __init__(self, scene):
        super().__init__(scene)
        self.horizon = scene.view.horizon
        self.peaks = self.make_peaks()
        self.firs = self.make_firs()
        self.image = None
        self.trees_image = None     # the firs are too small for their boil to show: painted once
        self.painted_palette = None

    def make_peaks(self):
        # Peaks spread across the window, each a top point with a rough slope either side
        count = random.randint(*self.PEAKS)
        peaks = []
        for i in range(count):
            x = WIDTH * (i + random.uniform(0.2, 0.8)) / count
            height = s(random.randint(*self.PEAK_HEIGHT))
            peaks.append({"x": x, "height": height, "cap": random.uniform(*self.CAP),
                          "width": height * random.uniform(1.6, 2.4)})
        return peaks

    def make_firs(self):
        firs = []
        x = -s(6)
        while x < WIDTH + s(6):
            height = s(random.randint(*self.FIR_HEIGHT))
            firs.append({"x": x, "height": height})
            x += height * self.FIR_WIDTH * random.uniform(0.45, 0.85)
        return firs

    def ridge(self):
        # The skyline of all the peaks together: the highest slope at each step across
        points = []
        step = s(4)
        for x in range(-step, WIDTH + step * 2, step):
            top = 0
            for peak in self.peaks:
                slope = 1 - abs(x - peak["x"]) / (peak["width"] / 2)
                top = max(top, peak["height"] * slope)
            points.append((x, self.horizon - top + random.uniform(-1, 1) * self.JITTER * 2))
        return points

    def paint(self, palette):
        top = int(self.horizon - s(self.PEAK_HEIGHT[1]) - s(6))
        image = pygame.Surface((WIDTH, int(self.horizon) - top + 2), pygame.SRCALPHA)
        def up(points):
            return [(x, y - top) for x, y in points]

        if palette.get("mountain"):
            ridge = self.ridge()
            pygame.draw.polygon(image, pygame.Color(palette["mountain"]),
                                up([(ridge[0][0], self.horizon + 1)] + ridge + [(ridge[-1][0], self.horizon + 1)]))
            # Snow caps: each peak's top, down to a ragged snow line
            snow = pygame.Color(palette.get("mountain_snow", palette["mountain"]))
            for peak in self.peaks:
                drop = peak["height"] * peak["cap"]
                half = peak["width"] / 2 * peak["cap"]
                tip = (peak["x"], self.horizon - peak["height"])
                cap = [tip]
                steps = 6
                for k in range(steps + 1):
                    across = half - 2 * half * k / steps
                    ragged = drop * (1 + random.uniform(-0.12, 0.12))
                    cap.append((peak["x"] + across, tip[1] + ragged * (1 - abs(across) / half * 0.15)))
                pygame.draw.polygon(image, snow, up(cap))

        if palette.get("fir"):
            if self.trees_image is None or self.painted_palette is not palette:
                self.trees_image = pygame.Surface(image.get_size(), pygame.SRCALPHA)
                fir = pygame.Color(palette["fir"])
                fir_snow = pygame.Color(palette.get("fir_snow", palette["fir"]))
                for tree in self.firs:
                    self.paint_fir(self.trees_image, tree, fir, fir_snow, top)
            image.blit(self.trees_image, (0, 0))

        self.image = image
        self.top = top
        self.painted_palette = palette

    def paint_fir(self, image, tree, fir, fir_snow, top):
        # Tiers of triangles, each with a line of snow along its upper edges
        height = tree["height"]
        width = height * self.FIR_WIDTH
        base = self.horizon + 1 - top
        jitter = make_jitter(self.FIR_TIERS * 3, self.JITTER)
        for tier in range(self.FIR_TIERS):
            share = tier / self.FIR_TIERS
            tier_bottom = base - height * share * 0.75
            tier_top = base - height * (share * 0.75 + 0.45)
            half = width / 2 * (1 - share * 0.55)
            left = (tree["x"] - half + jitter[tier * 3], tier_bottom)
            right = (tree["x"] + half + jitter[tier * 3 + 1], tier_bottom)
            tip = (tree["x"] + jitter[tier * 3 + 2], tier_top)
            pygame.draw.polygon(image, fir, [left, tip, right])
            pygame.draw.lines(image, fir_snow, False, [left, tip, right], 1)

    def wobble(self):
        self.image = None

    def draw(self, surface, palette):
        if self.image is None or self.painted_palette is not palette:
            self.paint(palette)
        self.image.set_alpha(int(255 * (1 - self.STORM_HAZE * self.scene.weather["storm"])))
        surface.blit(self.image, (0, self.top))
