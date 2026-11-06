# The space theme's scenery: drifting through deep space alongside the Voyager probe. A
# backdrop of black space with a soft nebula across it and a small spiral galaxy far off,
# layers of stars sliding slowly past, the Sun (just a very bright star now) at the top
# right, a great ringed gas giant with a little moon in the bottom left, and Voyager itself
# on the right, its big dish and long booms turning gently as it drifts
#
# Light mode is a photographic negative of dark mode: its palette is the dark one with
# every color inverted (see negative() in themes.py). Anything that glows, which adds light
# in dark mode, takes light away in light mode instead (see shine() below), so the whole
# picture stays a true negative

import math

import random

import pygame

from partials.config import WIDTH, HEIGHT, UI_SCALE, s
from partials.backgrounds.base import Layer
from partials.backgrounds.brook_light import glow_sprite


def invert(color):
    color = pygame.Color(color)
    return pygame.Color(255 - color.r, 255 - color.g, 255 - color.b, color.a)


def shine(palette, key):
    # The color and blend for something that glows: added on in dark mode; in the negative,
    # the original (un-inverted) color taken away instead, so it shows as a darkening
    color = pygame.Color(palette[key])
    if palette.get("negative"):
        return invert(color), pygame.BLEND_RGB_SUB
    return color, pygame.BLEND_RGB_ADD


def blur(image, factor):
    # Soften an image: shrink it right down and grow it back
    size = image.get_size()
    small = pygame.transform.smoothscale(image, (max(1, size[0] // factor), max(1, size[1] // factor)))
    return pygame.transform.smoothscale(small, size)


class Backdrop(Layer):
    # The black of space, very slightly lighter low down, with a soft nebula of glowing gas
    # drifting across it from the top left (fainter behind the game's text) and a small
    # spiral galaxy far away. All painted once, so it costs one blit a frame
    #
    # Palette colors it uses:
    #   "space_top", "space_low"    the backdrop
    #   "nebula"                    a list of the nebula's colors
    #   "nebula_strength"           how strongly it shows (0-1)
    #   "galaxy", "galaxy_core"

    GALAXY = (44, 236)              # where the galaxy is, at the medium size
    GALAXY_SIZE = 26

    def __init__(self, scene):
        super().__init__(scene)
        # The nebula: a winding band of clouds, as a list of (x, y, radius, color, strength)
        self.clouds = []
        for i in range(70):
            t = random.random()
            x = -s(30) + t * (WIDTH + s(60))
            y = s(60) + t * s(250) + math.sin(t * 5 + 1) * s(50) + random.gauss(0, s(28))
            self.clouds.append((x, y, s(random.uniform(18, 55)), random.randrange(3), random.uniform(0.25, 0.7)))
        # Dark lanes of dust winding through it
        self.dust = []
        for i in range(14):
            t = random.random()
            x = -s(30) + t * (WIDTH + s(60))
            y = s(75) + t * s(250) + math.sin(t * 5 + 1) * s(50) + random.gauss(0, s(10))
            self.dust.append((x, y, s(random.uniform(8, 20))))
        # The galaxy's stars: two arms winding out from the core
        self.galaxy = []
        for arm in (0, math.pi):
            for i in range(60):
                t = random.random() ** 0.8
                a = arm + t * 3.6
                r = t * s(self.GALAXY_SIZE)
                self.galaxy.append((math.cos(a) * r + random.gauss(0, s(1.5)), math.sin(a) * r + random.gauss(0, s(1.5)), random.uniform(0.3, 1)))
        self.image = None
        self.painted_palette = None

    def color_at(self, palette, y):
        top = pygame.Color(palette["space_top"])
        return top.lerp(pygame.Color(palette["space_low"]), max(0, min(1, y / HEIGHT)))

    def paint(self, palette):
        self.image = pygame.Surface((WIDTH, HEIGHT))
        for y in range(HEIGHT):
            pygame.draw.line(self.image, self.color_at(palette, y), (0, y), (WIDTH, y))
        # The nebula, built up from soft see-through clouds at a quarter of the size, then
        # blurred and grown to fit
        scale = 4
        cloud = pygame.Surface((WIDTH // scale + 1, HEIGHT // scale + 1), pygame.SRCALPHA)
        colors = [pygame.Color(c) for c in palette["nebula"]]
        cloud.fill((colors[0].r, colors[0].g, colors[0].b, 0))
        for x, y, r, c, strength in self.clouds:
            puff = pygame.Surface((int(r * 2 / scale) + 2, int(r * 2 / scale) + 2), pygame.SRCALPHA)
            color = colors[c % len(colors)]
            puff.fill((color.r, color.g, color.b, 0))
            pygame.draw.circle(puff, (color.r, color.g, color.b, int(105 * strength)), (puff.get_width() / 2, puff.get_height() / 2), r / scale)
            cloud.blit(puff, ((x - r) / scale, (y - r) / scale))
        backdrop = self.color_at(palette, HEIGHT / 3)
        for x, y, r in self.dust:
            puff = pygame.Surface((int(r * 2 / scale) + 2, int(r * 2 / scale) + 2), pygame.SRCALPHA)
            pygame.draw.circle(puff, (backdrop.r, backdrop.g, backdrop.b, 90), (puff.get_width() / 2, puff.get_height() / 2), r / scale)
            cloud.blit(puff, ((x - r) / scale, (y - r) / scale))
        cloud = blur(cloud, 3)
        cloud = pygame.transform.smoothscale(cloud, (WIDTH, HEIGHT))
        # Fainter behind the game's text
        quiet = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for x in range(WIDTH):
            strength = palette["nebula_strength"] * self.scene.keep(x, 0.55)
            pygame.draw.line(quiet, (255, 255, 255, int(255 * strength)), (x, 0), (x, HEIGHT))
        cloud.blit(quiet, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self.image.blit(cloud, (0, 0))
        self.paint_galaxy(palette)
        self.painted_palette = palette

    def paint_galaxy(self, palette):
        # A small spiral seen at a slant: its stars on a see-through image, squashed and tilted
        size = s(self.GALAXY_SIZE) * 2 + s(8)
        image = pygame.Surface((size, size), pygame.SRCALPHA)
        star = pygame.Color(palette["galaxy"])
        image.fill((star.r, star.g, star.b, 0))
        middle = size / 2
        for x, y, strength in self.galaxy:
            pygame.draw.circle(image, (star.r, star.g, star.b, int(170 * strength)), (middle + x, middle + y), max(1, s(1)))
        core = pygame.Color(palette["galaxy_core"])
        for ring in range(5):
            pygame.draw.circle(image, (core.r, core.g, core.b, 60 + ring * 35), (middle, middle), s(7) * (1 - ring / 5))
        image = blur(image, 2)
        image = pygame.transform.smoothscale(image, (size, int(size * 0.42)))
        image = pygame.transform.rotate(image, 28)
        self.image.blit(image, image.get_rect(center=(s(self.GALAXY[0]), s(self.GALAXY[1]))))

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.image, (0, 0))


class Starfield(Layer):
    # Stars in three layers, far to near, sliding slowly to the left as we drift (the near
    # ones faster), each twinkling on its own. The nearest are bigger and catch a little
    # cross of light. They're added onto whatever's behind them, so they shine through the
    # nebula, and they dim behind the game's text
    #
    # Palette colors it uses:
    #   "star_colors"       a list of star tints

    LAYERS = (                      # (how many, size, speed in pixels a second, brightness)
        (150, 1, 0.5, (0.25, 0.6)),
        (60, 1, 1.2, (0.45, 0.9)),
        (14, 2, 2.6, (0.75, 1.0)),
    )

    def __init__(self, scene):
        super().__init__(scene)
        self.time = 0
        self.stars = []
        for layer, (count, size, speed, (dim, bright)) in enumerate(self.LAYERS):
            for i in range(count):
                self.stars.append({"x": random.uniform(0, WIDTH), "y": random.uniform(0, HEIGHT), "layer": layer, "size": size,
                                   "speed": s(speed) if speed >= 1 else speed * UI_SCALE, "strength": random.uniform(dim, bright),
                                   "tint": random.randrange(4), "period": random.uniform(1500, 5000), "phase": random.uniform(0, 6.3)})

    def update(self, dt):
        self.time += dt
        wind = self.scene.weather.get("drift", 1)
        for star in self.stars:
            star["x"] -= star["speed"] * wind * dt / 1000
            if star["x"] < -s(4):
                star["x"] += WIDTH + s(8)
                star["y"] = random.uniform(0, HEIGHT)

    def draw(self, surface, palette):
        tints = [shine({"t": c, "negative": palette.get("negative")}, "t") for c in palette["star_colors"]]
        for star in self.stars:
            twinkle = 0.7 + 0.3 * math.sin(self.time / star["period"] * 6.28 + star["phase"])
            strength = star["strength"] * twinkle * self.scene.keep(star["x"], 0.6)
            color, blend = tints[star["tint"] % len(tints)]
            add = (int(color.r * strength), int(color.g * strength), int(color.b * strength))
            x, y, size = star["x"], star["y"], star["size"]
            surface.fill(add, (x, y, max(1, s(size)), max(1, s(size))), special_flags=blend)
            if star["layer"] == 2:                               # a little cross of light
                faint = (add[0] // 3, add[1] // 3, add[2] // 3)
                reach = s(3)
                surface.fill(faint, (x - reach, y + s(size) // 2, reach * 2 + s(size), 1), special_flags=blend)
                surface.fill(faint, (x + s(size) // 2, y - reach, 1, reach * 2 + s(size)), special_flags=blend)


class Sun(Layer):
    # The Sun, seen from the edge of the solar system: no longer a disc, just the brightest
    # star in the sky, with a soft glow and long thin spikes of light
    #
    # Palette colors it uses:
    #   "sun", "sun_glow"

    PLACE = (402, 46)

    def __init__(self, scene):
        super().__init__(scene)
        self.x, self.y = s(self.PLACE[0]), s(self.PLACE[1])
        scene.weather["light_x"], scene.weather["light_y"] = self.x, self.y
        self.time = 0
        self.palette = None

    def update(self, dt):
        self.time += dt

    def draw(self, surface, palette):
        if self.palette is not palette:
            glow, self.blend = shine(palette, "sun_glow")
            self.glow = glow_sprite(s(26), glow)
            self.core, _ = shine(palette, "sun")
            self.palette = palette
        surface.blit(self.glow, self.glow.get_rect(center=(self.x, self.y)), special_flags=self.blend)
        breathe = 1 + 0.08 * math.sin(self.time / 1300)
        for angle, length in ((0, 34), (90, 34), (45, 16), (135, 16)):
            a = math.radians(angle)
            reach = s(length) * breathe
            for width, share in ((3, 0.35), (1, 1.0)):
                color = [int(c * (0.35 if width == 3 else 0.8)) for c in self.core[:3]]
                dx, dy = math.cos(a) * reach * share, math.sin(a) * reach * share
                pygame.draw.line(surface, color, (self.x - dx, self.y - dy), (self.x + dx, self.y + dy), 1)
        pygame.draw.circle(surface, self.core, (self.x, self.y), max(2, s(2.5)))


class GasGiant(Layer):
    # A great ringed planet looming in the bottom left corner: banded in creams and tans,
    # lit from the Sun at the top right with its far side in night, its wide rings tilted
    # across it (behind it at the top, in front of it below, with a dark gap in them), and a
    # little cratered moon hanging above. It turns slowly: its bands ripple along and a storm
    # spot drifts across. That's a loop of pictures, painted one per frame as they're first
    # needed, and cross-faded into each other
    #
    # Palette colors it uses:
    #   "planet", "planet_bands"    its lit surface, and a list of colors for its bands
    #   "planet_night"              its dark side
    #   "ring", "ring_dark"
    #   "moon", "moon_dark"

    CENTER = (-14, 606)             # at the medium size
    RADIUS = 122
    RING = (1.25, 1.62)             # the rings' inner and outer edge, in planet radii
    RING_FLATTEN = 0.3
    TILT = 16                       # degrees the rings are tilted, rising to the right
    MOON = (30, 438, 9)
    TURNS = 16                      # pictures in one turn
    TURN_STEP = 3000                # milliseconds from one picture to the next

    def __init__(self, scene):
        super().__init__(scene)
        self.bands = []
        y = -1.0
        while y < 1.0:
            height = random.uniform(0.05, 0.16)
            self.bands.append((y, height, random.randrange(4), random.uniform(0, 6.3)))
            y += height * random.uniform(0.9, 1.5)
        self.craters = [(random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5), random.uniform(0.12, 0.25)) for i in range(4)]
        self.time = random.uniform(0, self.TURNS * self.TURN_STEP)
        self.frames = {}
        self.painted_palette = None

    def paint_planet(self, palette, r, turn):
        # The disc with its bands and its night side, on its own see-through image
        size = r * 2 + 2
        disc = pygame.Surface((size, size), pygame.SRCALPHA)
        middle = size / 2
        disc.fill(pygame.Color(palette["planet"]))
        bands = [pygame.Color(c) for c in palette["planet_bands"]]
        for y, height, c, phase in self.bands:
            top = []
            bottom = []
            for i in range(13):
                x = size * i / 12
                wave = math.sin(i * 0.9 + phase + turn * 2 * math.pi) * r * 0.014
                top.append((x, middle + y * r + wave))
                bottom.append((x, middle + (y + height) * r - wave))
            pygame.draw.polygon(disc, bands[c % len(bands)], top + list(reversed(bottom)))
        # A storm: an oval spot in one of the bands, carried across as the planet turns
        across = -1.3 + 2.6 * ((turn + 0.6) % 1)
        squash = max(0.2, 1 - abs(across) * 0.8)                # narrower toward the edges, seen side-on
        pygame.draw.ellipse(disc, bands[0].lerp(pygame.Color(palette["ring_dark"]), 0.4),
                            (middle + across * r - r * 0.11 * squash, middle + r * 0.28, r * 0.22 * squash, r * 0.1))
        # Night: the side away from the Sun, fading across the terminator
        light = (math.cos(math.radians(-45 + self.TILT)), math.sin(math.radians(-45 + self.TILT)))
        night = pygame.Color(palette["planet_night"])
        shade = pygame.Surface((size, size), pygame.SRCALPHA)
        shade.fill((night.r, night.g, night.b, 235))
        steps = 9
        for i in range(steps):
            share = (i + 1) / steps
            centre = (middle + light[0] * r * (0.35 + 0.3 * share), middle + light[1] * r * (0.35 + 0.3 * share))
            pygame.draw.circle(shade, (night.r, night.g, night.b, int(235 * (1 - share))), centre, r * (1.15 - 0.25 * share))
        disc.blit(shade, (0, 0))
        # Darker toward the edge, where we look through more of its air
        limb = pygame.Surface((size, size), pygame.SRCALPHA)
        for i in range(6):
            pygame.draw.circle(limb, (night.r, night.g, night.b, 22), (middle, middle), r, max(1, int(r * (0.04 + i * 0.03))))
        disc.blit(limb, (0, 0))
        mask = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(mask, (255, 255, 255, 255), (middle, middle), r)
        disc.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        return disc

    def paint_ring(self, palette, r, half):
        # The rings as an ellipse band, only its top half (behind the planet) or bottom half
        outer, inner = r * self.RING[1], r * self.RING[0]
        w, h = outer * 2 + 2, outer * 2 * self.RING_FLATTEN + 2
        ring = pygame.Surface((w, h), pygame.SRCALPHA)
        color = pygame.Color(palette["ring"])
        dark = pygame.Color(palette["ring_dark"])
        steps = 7
        for i in range(steps):
            t = i / steps
            radius = outer - (outer - inner) * t
            band = color if i % 3 else dark
            rect = pygame.Rect(0, 0, radius * 2, radius * 2 * self.RING_FLATTEN)
            rect.center = (w / 2, h / 2)
            pygame.draw.ellipse(ring, band, rect)
        gap = pygame.Rect(0, 0, (outer - (outer - inner) * 0.35) * 2, (outer - (outer - inner) * 0.35) * 2 * self.RING_FLATTEN)
        gap.center = (w / 2, h / 2)
        pygame.draw.ellipse(ring, (0, 0, 0, 0), gap, max(1, s(2)))                     # the dark gap in the rings
        hole = pygame.Rect(0, 0, inner * 2, inner * 2 * self.RING_FLATTEN)
        hole.center = (w / 2, h / 2)
        pygame.draw.ellipse(ring, (0, 0, 0, 0), hole)
        if half == "back":
            pygame.draw.rect(ring, (0, 0, 0, 0), (0, h / 2, w, h / 2 + 1))
        else:
            pygame.draw.rect(ring, (0, 0, 0, 0), (0, 0, w, h / 2))
        return ring

    def paint(self, palette):
        self.frames = {}
        self.paint_moon(palette)
        here = self.frame_at()[0]
        self.frames[here] = self.paint_frame(palette, here)
        self.painted_palette = palette

    def frame_at(self):
        # The picture we're on, the next one, and how far between them
        step = self.time / self.TURN_STEP
        here = int(step) % self.TURNS
        return here, (here + 1) % self.TURNS, step - int(step)

    def update(self, dt):
        self.time += dt

    def paint_frame(self, palette, n):
        turn = n / self.TURNS
        r = s(self.RADIUS)
        outer = r * self.RING[1]
        size = int(outer * 2 + s(10))
        image = pygame.Surface((size, size), pygame.SRCALPHA)
        middle = size / 2
        back = self.paint_ring(palette, r, "back")
        image.blit(back, back.get_rect(center=(middle, middle)))
        disc = self.paint_planet(palette, r, turn)
        image.blit(disc, disc.get_rect(center=(middle, middle)))
        # The rings' shadow falling across the planet, just below them
        shadow = pygame.Surface((size, size), pygame.SRCALPHA)
        night = pygame.Color(palette["planet_night"])
        band = pygame.Rect(0, 0, r * self.RING[0] * 2.05, r * self.RING[0] * 2 * self.RING_FLATTEN)
        band.center = (middle, middle + r * 0.1)
        pygame.draw.ellipse(shadow, (night.r, night.g, night.b, 110), band, max(2, s(5)))
        planet_mask = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(planet_mask, (255, 255, 255, 255), (middle, middle), r)
        shadow.blit(planet_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        image.blit(shadow, (0, 0))
        front = self.paint_ring(palette, r, "front")
        image.blit(front, front.get_rect(center=(middle, middle)))
        return pygame.transform.rotozoom(image, self.TILT, 1)

    def paint_moon(self, palette):
        mx, my, mr = self.MOON
        r = s(mr)
        size = r * 2 + 2
        moon = pygame.Surface((size, size), pygame.SRCALPHA)
        middle = size / 2
        pygame.draw.circle(moon, pygame.Color(palette["moon"]), (middle, middle), r)
        dark = pygame.Color(palette["moon_dark"])
        for cx, cy, cr in self.craters:
            pygame.draw.circle(moon, pygame.Color(palette["moon"]).lerp(dark, 0.4), (middle + cx * r, middle + cy * r), cr * r)
        shade = pygame.Surface((size, size), pygame.SRCALPHA)
        night = pygame.Color(palette["planet_night"])
        shade.fill((night.r, night.g, night.b, 230))
        pygame.draw.circle(shade, (0, 0, 0, 0), (middle + r * 0.45, middle - r * 0.45), r * 1.05)
        moon.blit(shade, (0, 0))
        mask = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(mask, (255, 255, 255, 255), (middle, middle), r)
        moon.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        self.moon = moon

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        here, after, between = self.frame_at()
        for n in (here, after):
            if n not in self.frames:                            # paint one missing picture a frame
                self.frames[n] = self.paint_frame(palette, n)
                break
        place = self.frames[here].get_rect(center=(s(self.CENTER[0]), s(self.CENTER[1])))
        self.frames[here].set_alpha(255)
        surface.blit(self.frames[here], place)
        if after in self.frames:
            self.frames[after].set_alpha(int(255 * between))
            surface.blit(self.frames[after], place)
            self.frames[after].set_alpha(255)
        surface.blit(self.moon, self.moon.get_rect(center=(s(self.MOON[0]), s(self.MOON[1]))))


class Voyager(Layer):
    # The Voyager probe, drifting along on the right: its great white dish antenna on top
    # (lit from the Sun on its right), the gold-foiled body with the Golden Record on its side,
    # the long magnetometer boom reaching off to the lower left, the boom of power generators
    # and the boom with the camera platform to the right, and two long thin antennas trailing
    # below. It turns and bobs very slowly as it drifts
    #
    # Palette colors it uses:
    #   "dish", "dish_shade"        the dish antenna
    #   "probe", "foil", "boom"     its body, the gold foil, and the booms and struts
    #   "record"                    the Golden Record

    PLACE = (372, 462)              # at the medium size
    SIZE = 1.7                      # how big, as a multiple of the medium size

    def __init__(self, scene):
        super().__init__(scene)
        self.time = random.uniform(0, 60000)
        self.x, self.y = s(self.PLACE[0]), s(self.PLACE[1])

    def update(self, dt):
        self.time += dt

    def angle(self):
        return math.sin(self.time / 9000) * 0.14 + math.sin(self.time / 23000) * 0.06

    def at(self, u, v):
        # A point on the probe (u right, v down, in its own units) on the screen
        a = self.angle()
        k = self.SIZE * UI_SCALE
        cos, sin = math.cos(a), math.sin(a)
        bob = math.sin(self.time / 4000) * s(3)
        return (self.x + (u * cos - v * sin) * k, self.y + bob + (u * sin + v * cos) * k)

    def oval(self, cx, cy, rx, ry, start=0, end=2 * math.pi, count=24):
        return [self.at(cx + math.cos(start + (end - start) * i / count) * rx, cy + math.sin(start + (end - start) * i / count) * ry)
                for i in range(count + 1)]

    def draw(self, surface, palette):
        dish = pygame.Color(palette["dish"])
        dish_shade = pygame.Color(palette["dish_shade"])
        probe = pygame.Color(palette["probe"])
        foil = pygame.Color(palette["foil"])
        boom = pygame.Color(palette["boom"])
        record = pygame.Color(palette["record"])
        k = self.SIZE * UI_SCALE
        width = max(1, int(1.2 * k))
        # The long thin antennas trailing below, and the magnetometer boom to the lower left
        for end in ((-16, 46), (16, 46)):
            pygame.draw.line(surface, boom, self.at(0, 6), self.at(*end), 1)
        magnetometer = [self.at(-6, 4), self.at(-60, 30)]
        pygame.draw.line(surface, boom, *magnetometer, width)
        for n in range(1, 8):                                    # its lattice, in segments
            t = n / 8
            px, py = magnetometer[0][0] + (magnetometer[1][0] - magnetometer[0][0]) * t, magnetometer[0][1] + (magnetometer[1][1] - magnetometer[0][1]) * t
            pygame.draw.circle(surface, boom, (px, py), max(1, 0.8 * k))
        pygame.draw.circle(surface, boom, magnetometer[1], max(1, 1.4 * k))
        # The power boom to the lower right, with its three generators
        pygame.draw.line(surface, boom, self.at(6, 4), self.at(24, 14), width)
        for n in range(3):
            u, v = 12 + n * 4.5, 7.5 + n * 2.5
            pygame.draw.polygon(surface, probe.lerp(boom, 0.5), [self.at(u - 2, v - 2), self.at(u + 2, v), self.at(u + 1, v + 2.5), self.at(u - 3, v + 0.5)])
        # The science boom to the right, with the camera platform at the end
        pygame.draw.line(surface, boom, self.at(6, -1), self.at(26, -4), width)
        pygame.draw.polygon(surface, probe, [self.at(24, -8), self.at(31, -8), self.at(31, -1), self.at(24, -1)])
        pygame.draw.line(surface, boom, self.at(31, -6), self.at(36, -7), max(1, int(1.5 * k)))
        pygame.draw.line(surface, boom, self.at(31, -3), self.at(35, -3), max(1, int(1.5 * k)))
        # The body: ten-sided, wrapped in gold foil, with the Golden Record on its side
        body = [self.at(-8, -2), self.at(8, -2), self.at(9, 3), self.at(6, 7), self.at(-6, 7), self.at(-9, 3)]
        pygame.draw.polygon(surface, foil, body)
        pygame.draw.lines(surface, foil.lerp(boom, 0.5), True, body, 1)
        pygame.draw.line(surface, foil.lerp(boom, 0.4), self.at(-3, -2), self.at(-3, 7), 1)
        pygame.draw.line(surface, foil.lerp(boom, 0.4), self.at(3, -2), self.at(3, 7), 1)
        pygame.draw.circle(surface, record, self.at(5.5, 2.5), max(1, 2.2 * k))
        pygame.draw.circle(surface, record.lerp(boom, 0.5), self.at(5.5, 2.5), max(1, 0.6 * k))
        # The dish: a big shallow bowl tipped toward us, so we look into it: its rim, the curve
        # of its back below, and the inside, shaded on the left away from the Sun
        back = self.oval(0, -9, 21, 6, 0, math.pi, 12) + self.oval(0, -4, 8, 4, math.pi, 0, 8)
        pygame.draw.polygon(surface, dish_shade, back)                                               # its curved back
        bowl = self.oval(0, -11, 21, 10)
        pygame.draw.polygon(surface, dish, bowl)
        pygame.draw.polygon(surface, dish.lerp(dish_shade, 0.55), self.oval(-3, -11.5, 16, 7.5, math.pi * 0.5, math.pi * 1.5, 12))
        pygame.draw.polygon(surface, dish.lerp(dish_shade, 0.25), self.oval(0, -10.5, 7, 3.5))      # the hollow in the middle
        for ring in (0.45, 0.75):                                                                   # its panels
            pygame.draw.lines(surface, dish.lerp(dish_shade, 0.4), True, self.oval(0, -11, 21 * ring, 10 * ring), 1)
        pygame.draw.lines(surface, dish_shade, True, bowl, width)
        # The feed held out in front of the middle on three struts
        feed = self.at(1, -22)
        for u, v in ((-16, -6), (16, -6), (0, -21)):
            pygame.draw.line(surface, boom, self.at(u, v), feed, 1)
        pygame.draw.circle(surface, probe, feed, max(1, 1.6 * k))
