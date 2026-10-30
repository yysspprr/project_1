# The water itself: the layer at the very back

import random

import pygame

from partials.config import WIDTH, HEIGHT, s
from partials.backgrounds.base import Layer
from partials.backgrounds.helpers import make_jitter, wavy_line


class WaterSurface(Layer):
    # Painted bands of color, lighter far away (top) and darker up close (bottom),
    # with soft wavy edges that boil, and a few glints of light drifting on top.
    # The bands get thinner toward the top, following the scene's perspective
    #
    # Palette colors it uses (each falls back to "bg" if a theme doesn't have it):
    #   "water_top", "water_bottom"     the farthest and nearest band
    #   "glint"                         the brightest a glint gets

    BANDS = 8                       # how many color bands, top to bottom
    BAND_WAVE = 7                   # how far a band's edge waves up and down, in pixels up close
    BAND_POINTS = 9                 # points along each band's edge
    BAND_JITTER = 0.25              # how much the edge points move on each wobble tick, as a share of the wave

    GLINTS = 12                     # how many glints are on the water at once
    GLINT_LENGTH = (30, 90)         # how long a glint is up close, in pixels
    GLINT_LIFETIME = (3000, 6000)   # milliseconds from fading in to gone
    GLINT_DRIFT = (4, 12)           # pixels per second it slides sideways, up close
    GLINT_STRENGTH = 0.6            # how bright a glint gets at its peak (0 = invisible, 1 = full "glint" color)
    GLINT_WIDTH = 2
    GLINT_POINTS = 5                # points along each glint
    GLINT_BEND = 1.5                # how far a glint's points wobble up and down, in pixels up close
    GLINT_SPREAD = 0.6              # how much glints crowd toward the back (see Perspective.random_y)
    LIGHT = (0.35, 1.2)             # the light waxes and wanes between these: dull to bright glints
    LIGHT_TIME = (5000, 12000)      # milliseconds it takes to change

    def __init__(self, scene):
        super().__init__(scene)
        self.bands_image = None
        self.bands_palette = None   # which palette the bands image was painted with
        self.band_lines = scene.view.rows(self.BANDS)       # where each band starts, top to bottom
        self.band_edges = self.make_band_edges()
        self.light = self.swell(*self.LIGHT, self.LIGHT_TIME)

        # Start with glints already at different ages, so they don't all fade in together
        self.glints = []
        for i in range(self.GLINTS):
            glint = self.make_glint()
            glint["age"] = random.randint(0, glint["lifetime"])
            self.glints.append(glint)

    # ---- Bands ----

    def band_wave(self, index):
        # Edges far away wave less, like everything else there
        return s(self.BAND_WAVE) * self.scene.view.scale(self.band_lines[index])

    def make_band_edges(self):
        # The wavy top edge of every band but the first: a list of heights across the window
        edges = []
        for i in range(1, self.BANDS):
            heights = []
            for push in make_jitter(self.BAND_POINTS, 1):
                heights.append(self.band_lines[i] + self.band_wave(i) * push)
            edges.append(heights)
        return edges

    def nudge_band_edges(self):
        # Move every edge point a little, keeping it close to its band's line
        for i, heights in enumerate(self.band_edges):
            base_y = self.band_lines[i + 1]
            wave = self.band_wave(i + 1)
            for j in range(len(heights)):
                moved = heights[j] + wave * random.uniform(-self.BAND_JITTER, self.BAND_JITTER)
                heights[j] = max(base_y - wave, min(base_y + wave, moved))

    def band_color(self, palette, index):
        top = pygame.Color(palette.get("water_top", palette["bg"]))
        bottom = pygame.Color(palette.get("water_bottom", palette["bg"]))
        return top.lerp(bottom, index / (self.BANDS - 1))

    def paint_bands(self, palette):
        # Paint the bands once into an image; it's only repainted on a wobble tick or a new palette
        image = pygame.Surface((WIDTH, HEIGHT))
        image.fill(self.band_color(palette, 0))
        for i, heights in enumerate(self.band_edges):
            edge = wavy_line(0, WIDTH, heights)
            outline = edge + [(WIDTH, HEIGHT), (0, HEIGHT)]
            pygame.draw.polygon(image, self.band_color(palette, i + 1), outline)
        self.bands_image = image
        self.bands_palette = palette

    def color_at(self, palette, y):
        # The water's color at height y, so other layers can fade into it
        band = 0
        while band < self.BANDS - 1 and y >= self.band_lines[band + 1]:
            band += 1
        return self.band_color(palette, band)

    # ---- Glints ----

    def make_glint(self):
        view = self.scene.view
        y = view.random_y(self.GLINT_SPREAD)
        size = view.scale(y)
        return {
            "x": random.uniform(0, WIDTH),
            "y": y,
            "length": s(random.randint(*self.GLINT_LENGTH)) * size,
            "lifetime": random.randint(*self.GLINT_LIFETIME),
            "age": 0,
            "drift": s(random.uniform(*self.GLINT_DRIFT)) * size * random.choice((-1, 1)),
            "bend": make_jitter(self.GLINT_POINTS, s(self.GLINT_BEND) * size),
        }

    # ---- Layer methods ----

    def update(self, dt):
        for i, glint in enumerate(self.glints):
            glint["age"] += dt
            glint["x"] += glint["drift"] * dt / 1000
            if glint["age"] >= glint["lifetime"]:
                self.glints[i] = self.make_glint()      # a gone glint is replaced somewhere else

    def wobble(self):
        self.nudge_band_edges()
        self.bands_image = None                         # repaint on the next draw
        for glint in self.glints:
            size = self.scene.view.scale(glint["y"])
            glint["bend"] = make_jitter(self.GLINT_POINTS, s(self.GLINT_BEND) * size)

    def draw(self, surface, palette):
        if self.bands_image is None or self.bands_palette is not palette:
            self.paint_bands(palette)
        surface.blit(self.bands_image, (0, 0))

        view = self.scene.view
        glint_color = pygame.Color(palette.get("glint", palette["bg"]))
        for glint in self.glints:
            progress = glint["age"] / glint["lifetime"]
            # Fade in, hold, fade out: a soft bump that peaks in the middle
            bump = 1 - (2 * progress - 1) ** 2
            strength = min(1, bump * self.GLINT_STRENGTH * self.light.value * view.clarity(glint["y"]))
            color = self.color_at(palette, glint["y"]).lerp(glint_color, strength)
            line = max(1, round(s(self.GLINT_WIDTH) * view.scale(glint["y"])))

            # A short line, gently bent up and down
            left = glint["x"] - glint["length"] / 2
            heights = []
            for bend in glint["bend"]:
                heights.append(glint["y"] + bend)
            points = wavy_line(left, left + glint["length"], heights)
            pygame.draw.lines(surface, color, False, points, line)
