# The ground in a snowy scene: drifts of snow, and a frozen pond lying in them

import math

import random

import pygame

from partials.config import WIDTH, HEIGHT, CENTER_X, s
from partials.backgrounds.base import Layer
from partials.backgrounds.helpers import make_jitter, wavy_line, vertical_gradient


class SnowField(Layer):
    # Snow from the horizon down to us, in bands that follow the perspective: thin far away,
    # tall up close. Each band is a drift: brightest at its crest where the light catches it,
    # shading down its slope toward the next one, with a soft blue shadow tucked in just
    # below the crest in front of it. So the ground rolls instead of lying flat. The crests
    # boil gently
    #
    # Palette colors it uses:
    #   "snow_top", "snow_bottom"   the snow far away and up close
    #   "snow_lit"                  the bright snow on the crests (falls back to "snow_top")
    #   "snow_shadow"               the shadow behind each drift (falls back to a darker snow)

    BANDS = 6
    WAVE = 20                       # how far the crests rise and fall, in pixels up close
    POINTS = 24                     # points along each crest
    SWELLS = 3                      # overlapping gentle waves that shape each crest
    JITTER = 0.03                   # how much crest points move on each wobble, as a share of the wave
    SHADOW_DEPTH = 16               # how far the shadow behind a crest reaches, in pixels up close
    SHADOW = 0.75                   # how strong it is (0 = none, 1 = full "snow_shadow")
    LIT = 0.7                       # how bright a crest gets (0 = plain band color, 1 = full "snow_lit")
    SLOPE = 0.35                    # how far down its slope a drift darkens, toward "snow_shadow"

    def __init__(self, scene):
        super().__init__(scene)
        self.lines = scene.view.rows(self.BANDS)
        self.crests = []
        for i in range(1, self.BANDS):
            self.crests.append(self.make_crest(i))
        self.jitter = [make_jitter(self.POINTS, self.JITTER) for crest in self.crests]
        self.image = None
        self.painted_palette = None
        self.gradients = {}         # each drift's shading, by band: only the shape cut from it changes

    def make_crest(self, index):
        # A smooth rolling line: a few gentle waves of different lengths added together
        swells = []
        for k in range(self.SWELLS):
            swells.append((random.uniform(0.6, 2.2) * (k + 1), random.uniform(0, 2 * math.pi),
                           random.uniform(0.5, 1) / (k + 1)))
        total = sum(size for length, phase, size in swells)
        heights = []
        for p in range(self.POINTS):
            across = p / (self.POINTS - 1)
            rise = 0
            for length, phase, size in swells:
                rise += math.sin(across * length * math.pi + phase) * size
            heights.append(self.lines[index] - self.wave(index) * rise / total)
        return heights

    def wave(self, index):
        return s(self.WAVE) * self.scene.view.scale(self.lines[index])

    def band_color(self, palette, index):
        top = pygame.Color(palette.get("snow_top", palette["bg"]))
        bottom = pygame.Color(palette.get("snow_bottom", palette["bg"]))
        return top.lerp(bottom, index / (self.BANDS - 1))

    def color_at(self, palette, y):
        if y < self.lines[0]:
            return None
        band = 0
        while band < self.BANDS - 1 and y >= self.lines[band + 1]:
            band += 1
        return self.band_color(palette, band)

    def paint(self, palette):
        top = self.lines[0]
        image = pygame.Surface((WIDTH, int(HEIGHT - top) + 1))
        image.fill(self.band_color(palette, 0))
        shadow = pygame.Color(palette.get("snow_shadow", palette.get("snow_bottom", palette["bg"])))
        view = self.scene.view

        lit = pygame.Color(palette.get("snow_lit", palette.get("snow_top", palette["bg"])))
        for i, base_heights in enumerate(self.crests):
            band = self.band_color(palette, i + 1)
            wave = self.wave(i + 1)
            heights = [h + wave * j for h, j in zip(base_heights, self.jitter[i])]
            crest = wavy_line(0, WIDTH, [h - top for h in heights])
            # The drift: bright at the crest, shading down its slope to where the next one starts.
            # The shading starts at the highest the crest can ever reach, so it can be kept
            start = int(self.lines[i + 1] - wave * (1 + self.JITTER) - top) - 1
            end = int(self.lines[i + 2] - top) if i + 2 < len(self.lines) else image.get_height()
            end = max(end, start + 2)
            if i not in self.gradients:
                def shade(share, band=band):
                    return band.lerp(lit, self.LIT * (1 - share) ** 2).lerp(shadow, self.SLOPE * share * share)
                self.gradients[i] = vertical_gradient(WIDTH, end - start, shade)
            slope = self.gradients[i].copy()
            shape = pygame.Surface(slope.get_size(), pygame.SRCALPHA)
            pygame.draw.polygon(shape, (255, 255, 255, 255),
                                [(x, y - start) for x, y in crest] + [(WIDTH, end - start), (0, end - start)])
            slope.blit(shape, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            pygame.draw.polygon(image, band, crest + [(WIDTH, HEIGHT - top), (0, HEIGHT - top)])
            image.blit(slope, (0, start))
            # Its shadow: a strip just below the crest, thickest where the crest is highest
            depth = s(self.SHADOW_DEPTH) * view.scale(self.lines[i + 1])
            under = []
            for k, (x, y) in enumerate(crest):
                rise = (self.lines[i + 1] - heights[k]) / max(self.wave(i + 1), 1)   # -1 to 1
                under.append((x, y + depth * (0.6 + 0.4 * rise)))
            pygame.draw.polygon(image, band.lerp(shadow, self.SHADOW), crest + under[::-1])

        self.image = image
        self.painted_palette = palette

    def wobble(self):
        self.jitter = [make_jitter(self.POINTS, self.JITTER) for crest in self.crests]
        self.image = None

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.gradients = {}         # new colors: the shading has to be made again
        if self.image is None or self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.image, (0, self.lines[0]))


class FrozenPond(Layer):
    # An ice-covered pond lying in the snow, right behind the game: smooth and calm, which
    # makes it a quiet backdrop for the text. A rim of snow around its edge, a few cracks,
    # and patches of snow dusted over the ice. Other layers can draw reflections on it,
    # using inside() to stay on the ice
    #
    # Palette colors it uses:
    #   "ice_far", "ice_near"       the ice, at its far and near edge
    #   "ice_rim"                   the snow around the edge (falls back to "snow_top")
    #   "ice_crack"                 the cracks (falls back to "ice_rim")

    DEPTH = 0.42                    # where its middle lies, as a share of the way down the ground
    WIDTH_SHARE = 0.86              # how wide it is, as a share of the window
    POINTS = 36                     # points around its edge
    JITTER = 0.008                  # how much its edge wobbles, as a share of its size
    RIM = 3                         # rim thickness, up close in pixels
    CRACKS = 4
    DUST = 5                        # patches of snow on the ice

    def __init__(self, scene):
        super().__init__(scene)
        view = scene.view
        self.center_y = view.horizon + (HEIGHT - view.horizon) * self.DEPTH
        self.half_w = WIDTH * self.WIDTH_SHARE / 2
        self.half_h = self.half_w * view.flatten(self.center_y)
        self.shape = self.make_shape()                              # its own gently lobed outline
        self.jitter = make_jitter(self.POINTS, self.JITTER)         # plus a wobble that boils
        self.cracks = self.make_cracks()
        self.dust = self.make_dust()
        self.image = None
        self.painted_palette = None

    def make_shape(self):
        # A few smooth bulges around the edge, so it's a natural pond and not a perfect oval
        waves = [(k, random.uniform(0, 2 * math.pi), random.uniform(0.03, 0.08) / k * 2) for k in (2, 3, 5)]
        shape = []
        for i in range(self.POINTS):
            angle = 2 * math.pi * i / self.POINTS
            shape.append(sum(math.sin(angle * k + phase) * size for k, phase, size in waves))
        return shape

    def outline(self):
        points = []
        for i in range(self.POINTS):
            angle = 2 * math.pi * i / self.POINTS
            push = 1 + self.shape[i] + self.jitter[i]
            points.append((CENTER_X + math.cos(angle) * self.half_w * push,
                           self.center_y + math.sin(angle) * self.half_h * push))
        return points

    def inside(self, x, y, margin=0.9):
        # Whether (x, y) is on the ice (well inside its edge)
        dx = (x - CENTER_X) / (self.half_w * margin)
        dy = (y - self.center_y) / (self.half_h * margin)
        return dx * dx + dy * dy < 1

    def make_cracks(self):
        # Short jagged lines starting somewhere on the ice, heading off in a random direction
        cracks = []
        for i in range(self.CRACKS):
            angle = random.uniform(0, 2 * math.pi)
            reach = random.uniform(0.15, 0.45)
            x = CENTER_X + math.cos(angle) * self.half_w * reach
            y = self.center_y + math.sin(angle) * self.half_h * reach
            heading = random.uniform(0, 2 * math.pi)
            line = [(x, y)]
            for k in range(random.randint(3, 5)):
                heading += random.uniform(-0.7, 0.7)
                step = s(random.uniform(8, 18))
                x += math.cos(heading) * step
                y += math.sin(heading) * step * self.scene.view.flatten(y)
                if not self.inside(x, y):
                    break
                line.append((x, y))
            if len(line) > 1:
                cracks.append(line)
        return cracks

    def make_dust(self):
        dust = []
        for i in range(self.DUST):
            angle = random.uniform(0, 2 * math.pi)
            reach = random.uniform(0.55, 0.95)
            dust.append((CENTER_X + math.cos(angle) * self.half_w * reach,
                         self.center_y + math.sin(angle) * self.half_h * reach,
                         s(random.uniform(14, 30)), random.uniform(0.35, 0.7)))
        return dust

    def paint(self, palette):
        # The ice, painted once: a gradient cut to the pond's shape, then rim, dust and cracks
        outline = self.outline()
        left = int(min(x for x, y in outline)) - s(6)
        top = int(min(y for x, y in outline)) - s(6)
        width = int(max(x for x, y in outline)) - left + s(12)
        height = int(max(y for x, y in outline)) - top + s(12)
        local = [(x - left, y - top) for x, y in outline]

        far = pygame.Color(palette.get("ice_far", palette["bg"]))
        near = pygame.Color(palette.get("ice_near", palette["bg"]))
        ice = vertical_gradient(width, height, lambda share: far.lerp(near, share))
        cutout = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.polygon(cutout, (255, 255, 255, 255), local)
        ice.blit(cutout, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        view = self.scene.view
        rim = pygame.Color(palette.get("ice_rim", palette.get("snow_top", palette["bg"])))
        for x, y, size, flatness in self.dust:
            dust = near.lerp(rim, 0.55)
            pygame.draw.ellipse(ice, dust, (x - left - size, y - top - size * flatness * 0.5,
                                            size * 2, size * flatness))
        # Snow dusted near the edge must stay inside it: cut again
        ice.blit(cutout, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        crack = pygame.Color(palette.get("ice_crack", palette.get("ice_rim", palette["bg"])))
        for line in self.cracks:
            pygame.draw.lines(ice, near.lerp(crack, 0.7), False, [(x - left, y - top) for x, y in line], 1)

        thickness = max(2, round(s(self.RIM) * view.scale(self.center_y)))
        pygame.draw.lines(ice, rim, True, local, thickness)
        for point in local:
            pygame.draw.circle(ice, rim, point, thickness / 2)

        self.image = ice
        self.image_at = (left, top)
        self.painted_palette = palette

    def wobble(self):
        self.jitter = make_jitter(self.POINTS, self.JITTER)
        self.image = None

    def draw(self, surface, palette):
        if self.image is None or self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.image, self.image_at)
