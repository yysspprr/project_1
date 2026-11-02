# The weather outside the home's window. Each game it picks one (clear, rain, snow or fog),
# and every few minutes it may drift to another, the old one fading out before the new one
# fades in. Everything is drawn on the window's glass, inside its frame

import math

import random

import pygame

from partials.config import s
from partials.backgrounds.base import Layer


class WindowWeather(Layer):
    # Rain: the sky goes grey, rain streaks past outside, and drops gather on the glass, now and
    # then one running down and leaving a trail. Snow: flakes drifting down outside, snow
    # slowly piling up along the bottom of the panes, frost creeping in at the corners.
    # Fog: the view outside fades into a soft white haze with slow drifting bands. Clear: none
    # of it. Draws itself on the glass when the window asks it to (draw_on_glass)
    #
    # Palette colors it uses:
    #   "overcast"              the grey over the sky when it rains or snows
    #   "rain", "raindrop"      the streaks outside and the drops on the glass
    #   "snow", "frost"         the flakes and the snow on the panes, and the frost
    #   "fog"                   the haze

    KINDS = (("clear", 0.35), ("rain", 0.3), ("snow", 0.2), ("fog", 0.15))
    CHANGE = (120000, 260000)       # milliseconds between chances to change
    FADE = 9000                     # milliseconds to fade out (or in)
    STREAKS = 40
    DROPS = 34
    FLAKES = 45
    PILE = 12                       # how high the snow piles at most, pixels at the medium size
    PILE_TIME = 90000               # milliseconds to pile up that high

    def __init__(self, scene, window):
        super().__init__(scene)
        self.window = window
        window.outside = self
        self.rect = window.glass()
        self.kind = self.pick()
        self.amount = 1.0                    # how strongly the current weather shows
        self.fading = None                   # the weather fading in next, while the current one fades out
        self.change = random.uniform(*self.CHANGE)
        self.time = 0
        self.pile = 0.0
        r = self.rect
        self.streaks = [(random.uniform(0, r.width), random.uniform(0, r.height), random.uniform(0.7, 1.3)) for i in range(self.STREAKS)]
        self.drops = [self.new_drop() for i in range(self.DROPS)]
        self.flakes = [(random.uniform(0, r.width), random.uniform(0, r.height), random.uniform(0.6, 1.4), random.uniform(0, 6)) for i in range(self.FLAKES)]
        self.frost = None
        self.painted_palette = None

    def pick(self, other_than=None):
        kinds = [(kind, weight) for kind, weight in self.KINDS if kind != other_than]
        roll = random.uniform(0, sum(w for k, w in kinds))
        for kind, weight in kinds:
            roll -= weight
            if roll <= 0:
                return kind
        return kinds[-1][0]

    def new_drop(self):
        r = self.rect
        return {"x": random.uniform(2, r.width - 2), "y": random.uniform(2, r.height - 2), "size": random.uniform(0.6, 1.4),
                "grow": random.uniform(0, 1), "run": None, "trail": []}

    def cover(self):
        # How much the weather hides the clear sky (0 clear, 1 fully grey or white)
        if self.kind == "clear":
            return 0.0
        return self.amount * (0.95 if self.kind == "fog" else 0.75)

    def update(self, dt):
        self.time += dt
        # Changing weather: fade out, swap, fade in
        if self.fading is not None:
            self.amount -= dt / self.FADE
            if self.amount <= 0:
                self.kind, self.fading, self.amount = self.fading, None, 0.0
                self.pile = 0.0
        elif self.amount < 1:
            self.amount = min(1.0, self.amount + dt / self.FADE)
        else:
            self.change -= dt
            if self.change <= 0:
                self.change = random.uniform(*self.CHANGE)
                if random.random() < 0.6:
                    self.fading = self.pick(self.kind)
        seconds = dt / 1000
        r = self.rect
        wind = self.scene.weather.get("wind", 1)
        if self.kind == "rain":
            self.streaks = [((x + s(30) * wind * seconds) % r.width, (y + s(260) * speed * seconds) % r.height, speed) for x, y, speed in self.streaks]
            for i, drop in enumerate(self.drops):
                drop["grow"] = min(1.0, drop["grow"] + seconds * 0.25)
                if drop["run"] is None and drop["grow"] >= 1 and random.random() < seconds * 0.08:
                    drop["run"] = random.uniform(20, 45)
                if drop["run"] is not None:
                    drop["trail"].append((drop["x"], drop["y"]))
                    drop["trail"] = drop["trail"][-14:]
                    drop["y"] += s(drop["run"]) * seconds
                    drop["x"] += math.sin(drop["y"] / s(6)) * s(4) * seconds
                    if drop["y"] > r.height:
                        self.drops[i] = self.new_drop()
                        self.drops[i]["grow"] = 0.0
        elif self.kind == "snow":
            self.flakes = [((x + (s(8) * wind + math.sin(self.time / 800 + phase) * s(6)) * seconds) % r.width,
                            (y + s(18) * speed * seconds) % r.height, speed, phase) for x, y, speed, phase in self.flakes]
            self.pile = min(1.0, self.pile + dt / self.PILE_TIME * self.amount)

    def paint(self, palette):
        # Frost in the corners of the panes: feathery fans of white, painted once
        r = self.rect
        frost = pygame.Color(palette.get("frost", palette.get("snow", palette["text"])))
        image = pygame.Surface(r.size, pygame.SRCALPHA)
        rng = random.Random(4)
        cols, rows = self.window.PANES
        for c in range(cols):
            for k in range(rows):
                pane = pygame.Rect(r.width * c / cols, r.height * k / rows, r.width / cols, r.height / rows)
                for corner in (pane.topleft, pane.topright, pane.bottomleft, pane.bottomright):
                    for n in range(9):
                        a = rng.uniform(0, 2 * math.pi)
                        length = s(rng.uniform(3, 10))
                        tip = (corner[0] + math.cos(a) * length, corner[1] + math.sin(a) * length)
                        image.fill((0, 0, 0, 0), None)
                        pygame.draw.line(image, (frost.r, frost.g, frost.b, 120), corner, tip, 1)
                        for b in (-0.6, 0.6):
                            mid = (corner[0] + math.cos(a) * length * 0.6, corner[1] + math.sin(a) * length * 0.6)
                            pygame.draw.line(image, (frost.r, frost.g, frost.b, 90), mid,
                                             (mid[0] + math.cos(a + b) * length * 0.35, mid[1] + math.sin(a + b) * length * 0.35), 1)
        self.frost = image
        self.painted_palette = palette

    def draw_on_glass(self, surface, palette):
        if self.kind == "clear" or self.amount <= 0.01:
            return
        if self.painted_palette is not palette:
            self.paint(palette)
        r = self.rect
        clip = surface.get_clip()
        surface.set_clip(r)
        amount = self.amount
        if self.kind in ("rain", "snow"):
            grey = pygame.Color(palette.get("overcast", palette["muted"]))
            veil = pygame.Surface(r.size, pygame.SRCALPHA)
            veil.fill((grey.r, grey.g, grey.b, int(255 * 0.7 * amount)))
            surface.blit(veil, r.topleft)
        if self.kind == "rain":
            rain = pygame.Color(palette.get("rain", palette["text"]))
            behind = pygame.Color(palette.get("overcast", palette["muted"]))
            streak = behind.lerp(rain, 0.7 * amount)
            wind = self.scene.weather.get("wind", 1)
            for x, y, speed in self.streaks:
                pygame.draw.line(surface, streak, (r.left + x, r.top + y), (r.left + x - s(2) * wind, r.top + y - s(10) * speed), 1)
            drop = pygame.Color(palette.get("raindrop", palette["text"]))
            for d in self.drops:
                size = s(2.2) * d["size"] * d["grow"]
                if size < 0.5:
                    continue
                if len(d["trail"]) > 1:
                    trail = [(r.left + x, r.top + y) for x, y in d["trail"]]
                    pygame.draw.lines(surface, behind.lerp(drop, 0.35 * amount), False, trail, 1)
                x, y = r.left + d["x"], r.top + d["y"]
                pygame.draw.circle(surface, behind.lerp(drop, 0.55 * amount), (x, y), size)
                pygame.draw.circle(surface, behind.lerp((255, 255, 255), 0.7 * amount), (x - size * 0.35, y - size * 0.35), max(1, size * 0.35))
        elif self.kind == "snow":
            snow = pygame.Color(palette.get("snow", palette["text"]))
            behind = pygame.Color(palette.get("overcast", palette["muted"]))
            for x, y, speed, phase in self.flakes:
                pygame.draw.circle(surface, behind.lerp(snow, 0.9 * amount), (r.left + x, r.top + y), max(1, s(1.2) * speed))
            # Snow piling along the bottom of each row of panes, and frost in the corners
            cols, rows = self.window.PANES
            height = s(self.PILE) * self.pile
            if height >= 1:
                for k in range(1, rows + 1):
                    bottom = r.top + r.height * k / rows
                    for c in range(cols):
                        left, right = r.left + r.width * c / cols, r.left + r.width * (c + 1) / cols
                        mound = [(left, bottom)]
                        for n in range(9):
                            u = n / 8
                            mound.append((left + (right - left) * u, bottom - height * (0.6 + 0.4 * math.sin(u * math.pi)) * (1 if k == rows else 0.45)))
                        mound.append((right, bottom))
                        pygame.draw.polygon(surface, snow, mound)
            self.frost.set_alpha(int(255 * amount))
            surface.blit(self.frost, r.topleft)
        elif self.kind == "fog":
            fog = pygame.Color(palette.get("fog", palette["text"]))
            veil = pygame.Surface(r.size, pygame.SRCALPHA)
            veil.fill((fog.r, fog.g, fog.b, int(255 * 0.78 * amount)))
            surface.blit(veil, r.topleft)
            for k in range(4):
                y = r.top + r.height * (0.2 + 0.2 * k) + math.sin(self.time / 4000 + k) * s(6)
                band = pygame.Surface((r.width, s(10)), pygame.SRCALPHA)
                band.fill((fog.r, fog.g, fog.b, int(255 * 0.25 * amount)))
                surface.blit(band, (r.left + math.sin(self.time / 6000 + k * 2) * s(10), y))
        surface.set_clip(clip)
