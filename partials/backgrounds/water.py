# The water itself: the layer at the very back

import random

import pygame

from partials.config import WIDTH, HEIGHT, s
from partials.backgrounds.base import Layer
from partials.backgrounds.helpers import make_jitter, wavy_line


class WaterSurface(Layer):
    # Painted bands of color, lighter far away (top) and darker up close (bottom),
    # with soft wavy edges that boil, and a few glints of light drifting on top.
    # The bands get thinner toward the top, following the scene's perspective.
    # A storm (the scene's weather["storm"]) churns the water, and the glints follow the
    # scene's weather["light"]. If the view has a horizon, the water starts there.
    # If something in the sky gives off light (the scene's weather["light_x"]), some of
    # the glints gather into a shimmering column below it: its reflection on the water
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
    COLUMN_GLINTS = 16              # extra glints in the column under the sun or moon
    COLUMN_LENGTH = (6, 22)         # shorter than the loose glints, up close in pixels
    COLUMN_WIDTH = (4, 30)          # how far the column spreads sideways: at the horizon, up close
    COLUMN_REACH = 0.6              # how far down the water it reaches (1 = to the bottom of the window)
    COLUMN_STRENGTH = 0.95          # brightest a column glint gets, right below the light
    STORM_ROUGH = 2.5               # how much faster the band edges churn in a full storm

    def __init__(self, scene):
        super().__init__(scene)
        self.bands_image = None
        self.bands_palette = None   # which palette the bands image was painted with
        self.band_lines = scene.view.rows(self.BANDS)       # where each band starts, top to bottom
        self.band_edges = self.make_band_edges()

        # Start with glints already at different ages, so they don't all fade in together
        self.glints = []
        for i in range(self.GLINTS + self.COLUMN_GLINTS):
            glint = self.make_glint(column=i >= self.GLINTS)
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
        # Move every edge point a little, keeping it close to its band's line. Rougher in a storm
        jitter = self.BAND_JITTER * (1 + (self.STORM_ROUGH - 1) * self.scene.weather["storm"])
        for i, heights in enumerate(self.band_edges):
            base_y = self.band_lines[i + 1]
            wave = self.band_wave(i + 1)
            for j in range(len(heights)):
                moved = heights[j] + wave * random.uniform(-jitter, jitter)
                heights[j] = max(base_y - wave, min(base_y + wave, moved))

    def band_color(self, palette, index):
        top = pygame.Color(palette.get("water_top", palette["bg"]))
        bottom = pygame.Color(palette.get("water_bottom", palette["bg"]))
        return top.lerp(bottom, index / (self.BANDS - 1))

    def paint_bands(self, palette):
        # Paint the bands once into an image; it's only repainted on a wobble tick or a new palette
        # Only the part below the horizon: the image starts there, so everything moves up by top
        top = self.band_lines[0]
        image = pygame.Surface((WIDTH, HEIGHT - top))
        image.fill(self.band_color(palette, 0))
        for i, heights in enumerate(self.band_edges):
            edge = wavy_line(0, WIDTH, [h - top for h in heights])
            outline = edge + [(WIDTH, HEIGHT - top), (0, HEIGHT - top)]
            pygame.draw.polygon(image, self.band_color(palette, i + 1), outline)
        self.bands_image = image
        self.bands_palette = palette

    def color_at(self, palette, y):
        # The water's color at height y, so other layers can fade into it (None above the water)
        if y < self.band_lines[0]:
            return None
        band = 0
        while band < self.BANDS - 1 and y >= self.band_lines[band + 1]:
            band += 1
        return self.band_color(palette, band)

    # ---- Glints ----

    def make_glint(self, column=False):
        view = self.scene.view
        light_x = self.scene.weather.get("light_x")
        if column and light_x is not None:
            # In the column: crowded near the horizon, spreading wider as it comes closer
            top = view.horizon
            y = top + (HEIGHT - top) * self.COLUMN_REACH * random.random() ** 1.6
            spread = s(self.COLUMN_WIDTH[0]) + (s(self.COLUMN_WIDTH[1]) - s(self.COLUMN_WIDTH[0])) * view.nearness(y)
            x = light_x + random.gauss(0, 0.5) * spread
            length = s(random.randint(*self.COLUMN_LENGTH))
        else:
            column = False
            y = view.random_y(self.GLINT_SPREAD)
            x = random.uniform(0, WIDTH)
            length = s(random.randint(*self.GLINT_LENGTH))
        size = view.scale(y)
        if column:
            size = 0.35 + 0.65 * size       # the column stays visible right up to the horizon
        return {
            "column": column,
            "x": x,
            "y": y,
            "length": length * size,
            "lifetime": random.randint(*self.GLINT_LIFETIME),
            "age": 0,
            "drift": s(random.uniform(*self.GLINT_DRIFT)) * size * random.choice((-1, 1)) * (0.2 if column else 1),
            "bend": make_jitter(self.GLINT_POINTS, s(self.GLINT_BEND) * size),
        }

    # ---- Layer methods ----

    def update(self, dt):
        for i, glint in enumerate(self.glints):
            glint["age"] += dt
            glint["x"] += glint["drift"] * dt / 1000
            if glint["age"] >= glint["lifetime"]:
                self.glints[i] = self.make_glint(glint["column"])   # replaced somewhere else

    def wobble(self):
        self.nudge_band_edges()
        self.bands_image = None                         # repaint on the next draw
        for glint in self.glints:
            size = self.scene.view.scale(glint["y"])
            glint["bend"] = make_jitter(self.GLINT_POINTS, s(self.GLINT_BEND) * size)

    def draw(self, surface, palette):
        if self.bands_image is None or self.bands_palette is not palette:
            self.paint_bands(palette)
        surface.blit(self.bands_image, (0, self.band_lines[0]))

        view = self.scene.view
        glint_color = pygame.Color(palette.get("glint", palette["bg"]))
        light = self.scene.weather["light"]
        for glint in self.glints:
            progress = glint["age"] / glint["lifetime"]
            # Fade in, hold, fade out: a soft bump that peaks in the middle
            bump = 1 - (2 * progress - 1) ** 2
            if glint["column"]:
                # Brightest right under the light, fading as the column comes closer
                peak = self.COLUMN_STRENGTH * (1 - 0.6 * view.nearness(glint["y"]))
            else:
                peak = self.GLINT_STRENGTH
            strength = min(1, bump * peak * light * view.clarity(glint["y"]) * self.scene.keep(glint["x"]))
            color = self.color_at(palette, glint["y"]).lerp(glint_color, strength)
            line = max(1, round(s(self.GLINT_WIDTH) * view.scale(glint["y"])))

            # A short line, gently bent up and down
            left = glint["x"] - glint["length"] / 2
            heights = []
            for bend in glint["bend"]:
                heights.append(glint["y"] + bend)
            points = wavy_line(left, left + glint["length"], heights)
            pygame.draw.lines(surface, color, False, points, line)
