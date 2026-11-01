# The sky above the horizon: a soft gradient, the sun or the moon, stars at night,
# and clouds drifting with the wind. Day or night comes from the palette, so light
# mode gets the sun and dark mode the moon without the game having to say anything

import math

import random

import pygame

from partials.config import WIDTH, CENTER_X, s
from partials.backgrounds.base import Layer
from partials.backgrounds.helpers import make_jitter


class Sky(Layer):
    # Fills everything above the view's horizon. It reads the scene's weather:
    # "light" makes the sun or moon brighter or dimmer, "storm" thickens the clouds
    # and hides the stars, "wind" moves the clouds along
    #
    # Palette colors it uses:
    #   "sky_top", "sky_low"    the top of the window and just above the horizon
    #   "sky_body"              "sun", "moon", or leave it out for neither
    #   "body", "body_glow"     the sun or moon, and the glow around it
    #   "cloud"                 the clouds (no clouds without it)
    #   "star"                  the stars (no stars without it: leave it out for daytime)

    BODY_SIZE = 11                  # sun or moon radius, in pixels at the medium size
    BODY_HEIGHT = 0.4               # how far down the sky it sits (0 = top of the window, 1 = horizon)
    GLOW = 3.4                      # how far its glow reaches, in body radii
    GLOW_STEPS = 6                  # rings in the glow, from faint to strong
    MOON_BITE = 0.65                # how far the shadow over the moon is shifted, in radii (crescent)

    CLOUDS = 4
    CLOUD_WIDTH = (50, 95)          # pixels at the medium size
    CLOUD_PUFFS = (4, 6)            # round lumps that make up a cloud
    CLOUD_SPEED = 4                 # pixels per second at a normal breeze
    CLOUD_SHOW = (0.45, 0.85)       # how strongly clouds show: calm, full storm
    CLOUD_JITTER = 0.06             # how much the lumps wobble, as a share of their size

    STARS = 30
    STAR_TWINKLE = (1500, 4500)     # milliseconds for one twinkle
    STAR_STRENGTH = (0.35, 1)       # dimmest and brightest a star gets
    STAR_QUIET = 0.6                # how much they fade behind the game's text (0 = not at all)

    def __init__(self, scene):
        super().__init__(scene)
        self.horizon = scene.view.horizon
        self.time = 0

        # The sun or moon sits over the right-hand margin, out of the game's way
        margin = CENTER_X - scene.QUIET_WIDTH
        self.body_x = WIDTH - margin / 2
        self.body_y = self.horizon * self.BODY_HEIGHT
        scene.weather["light_x"] = self.body_x      # so the water knows where to put its reflection,
        scene.weather["light_y"] = self.body_y      # and shadows know which way to fall

        self.stars = []
        for i in range(self.STARS):
            self.stars.append({
                "x": random.uniform(0, WIDTH),
                "y": random.uniform(0, self.horizon * 0.85),
                "period": random.randint(*self.STAR_TWINKLE),
                "phase": random.uniform(0, 2 * math.pi),
                "big": random.random() < 0.2,
            })

        self.clouds = []
        for i in range(self.CLOUDS):
            self.clouds.append(self.make_cloud(random.uniform(0, WIDTH)))

        self.sky_image = None
        self.glow_image = None
        self.painted_palette = None
        self.disc = None
        self.disc_light = None              # the light the disc was painted for

    # ---- Clouds ----

    def make_cloud(self, x):
        width = s(random.randint(*self.CLOUD_WIDTH))
        puffs = []
        count = random.randint(*self.CLOUD_PUFFS)
        for i in range(count):
            # Round lumps sitting on a flat bottom, spread evenly, bigger in the middle
            along = -0.4 + 0.8 * i / (count - 1) + random.uniform(-0.06, 0.06)
            size = (1 - abs(along) * 1.1) * random.uniform(0.2, 0.28)
            puffs.append((along, size))
        return {
            "x": x,
            "y": random.uniform(self.horizon * 0.15, self.horizon * 0.7),
            "width": width,
            "puffs": puffs,
            "jitter": make_jitter(len(puffs) * 2, self.CLOUD_JITTER),
            "image": None,
        }

    def paint_cloud(self, cloud, palette):
        # Flat lumps in one color on a see-through image; repainted when it wobbles
        width = cloud["width"]
        height = int(width * 0.6)
        image = pygame.Surface((int(width * 1.2), height), pygame.SRCALPHA)
        color = pygame.Color(palette["cloud"])
        base = height - 2                                   # the flat bottom line
        middle = image.get_width() / 2
        for i, (along, size) in enumerate(cloud["puffs"]):
            push_x = 1 + cloud["jitter"][i * 2]
            push_y = 1 + cloud["jitter"][i * 2 + 1]
            radius = size * width * push_y
            x = middle + along * width * push_x
            pygame.draw.circle(image, color, (x, base - radius * 0.75), radius)
        # A low flat lump along the bottom ties them together and cuts the circles off flat
        pygame.draw.ellipse(image, color, (middle - width * 0.52, base - width * 0.12, width * 1.04, width * 0.12))
        pygame.draw.rect(image, (0, 0, 0, 0), (0, base, image.get_width(), height - base))
        cloud["image"] = image

    # ---- Painting what stays still ----

    def sky_color(self, palette, y):
        top = pygame.Color(palette.get("sky_top", palette["bg"]))
        low = pygame.Color(palette.get("sky_low", palette["bg"]))
        return top.lerp(low, max(0, min(1, y / max(self.horizon, 1))))

    def paint(self, palette):
        # The gradient and the glow only change with the palette, so they're painted once
        self.sky_image = pygame.Surface((WIDTH, max(1, int(self.horizon) + 1)))
        for y in range(self.sky_image.get_height()):
            pygame.draw.line(self.sky_image, self.sky_color(palette, y), (0, y), (WIDTH, y))

        self.glow_image = None
        if palette.get("sky_body"):
            radius = s(self.BODY_SIZE) * self.GLOW
            self.glow_image = pygame.Surface((int(radius * 2), int(radius * 2)), pygame.SRCALPHA)
            glow = pygame.Color(palette.get("body_glow", palette["body"]))
            # Rings from the outside in, each a little stronger: a soft glow without blurring
            for step in range(self.GLOW_STEPS):
                share = 1 - step / self.GLOW_STEPS
                glow.a = int(255 * (step + 1) / self.GLOW_STEPS * 0.35)
                ring = pygame.Surface(self.glow_image.get_size(), pygame.SRCALPHA)
                pygame.draw.circle(ring, glow, (radius, radius), radius * share)
                self.glow_image.blit(ring, (0, 0))

        for cloud in self.clouds:
            cloud["image"] = None
        self.disc = None
        self.painted_palette = palette

    def paint_disc(self, palette, light):
        # The sun or moon on its own see-through image, so the moon's shadow can be cut
        # out of it (painting the shadow in sky color would cover the glow behind it)
        radius = s(self.BODY_SIZE)
        behind = self.sky_color(palette, self.body_y)
        body = behind.lerp(pygame.Color(palette["body"]), 0.55 + 0.45 * light)
        self.disc = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
        middle = (radius + 1, radius + 1)
        pygame.draw.circle(self.disc, body, middle, radius)
        if palette["sky_body"] == "moon":
            bite = (middle[0] + radius * self.MOON_BITE, middle[1] - radius * 0.2)
            pygame.draw.circle(self.disc, (0, 0, 0, 0), bite, radius)
        self.disc_light = light

    def star_strength(self, dot):
        # How bright a star is right now: it twinkles, and a storm hides it
        twinkle = 0.5 + 0.5 * math.sin(self.time / dot["period"] * 2 * math.pi + dot["phase"])
        strength = self.STAR_STRENGTH[0] + (self.STAR_STRENGTH[1] - self.STAR_STRENGTH[0]) * twinkle
        return strength * (1 - self.scene.weather["storm"])

    def color_at(self, palette, y):
        if y >= self.horizon:
            return None
        return self.sky_color(palette, y)

    # ---- Layer methods ----

    def update(self, dt):
        self.time += dt
        wind = self.scene.weather["wind"]
        for i, cloud in enumerate(self.clouds):
            cloud["x"] += s(self.CLOUD_SPEED) * wind * dt / 1000
            if cloud["x"] - cloud["width"] > WIDTH:
                self.clouds[i] = self.make_cloud(-cloud["width"])   # drifted off: a new one comes in

    def wobble(self):
        for cloud in self.clouds:
            cloud["jitter"] = make_jitter(len(cloud["puffs"]) * 2, self.CLOUD_JITTER)
            cloud["image"] = None

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.sky_image, (0, 0))

        weather = self.scene.weather
        light = max(0, min(1.2, weather["light"]))
        storm = weather["storm"]

        # Stars: twinkling, fading behind the game's text, hidden by a storm
        if palette.get("star"):
            star = pygame.Color(palette["star"])
            for dot in self.stars:
                strength = self.star_strength(dot) * self.scene.keep(dot["x"], self.STAR_QUIET)
                color = self.sky_color(palette, dot["y"]).lerp(star, max(0, min(1, strength)))
                pygame.draw.circle(surface, color, (dot["x"], dot["y"]), s(1.2) if dot["big"] else 1)

        # The sun or moon, dimmer when it clouds over
        if palette.get("sky_body"):
            if self.glow_image is not None:
                self.glow_image.set_alpha(int(255 * min(1, light)))
                surface.blit(self.glow_image, self.glow_image.get_rect(center=(self.body_x, self.body_y)))
            # Repainted only when the light has changed enough to see
            rounded = round(min(1, light), 2)
            if self.disc is None or self.disc_light != rounded:
                self.paint_disc(palette, rounded)
            surface.blit(self.disc, self.disc.get_rect(center=(self.body_x, self.body_y)))

        # Clouds in front of it all, thicker in a storm
        if palette.get("cloud"):
            show = self.CLOUD_SHOW[0] + (self.CLOUD_SHOW[1] - self.CLOUD_SHOW[0]) * storm
            for cloud in self.clouds:
                if cloud["image"] is None:
                    self.paint_cloud(cloud, palette)
                cloud["image"].set_alpha(int(255 * show))
                surface.blit(cloud["image"], cloud["image"].get_rect(midbottom=(cloud["x"], cloud["y"])))
