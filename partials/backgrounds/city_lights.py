# The city's lights. At night: windows lighting up and going dark all over the skyline
# (with the odd one flickering blue with a television), red warning lights blinking on the
# masts and spires, a neon hotel sign buzzing on the right, car lights streaming over a far
# bridge, and now and then fireworks bursting over the rooftops. By day the glass glints
# in the sun and the bridge carries little bright cars

import math

import random

import pygame

from partials.config import WIDTH, HEIGHT, FONT_PATH, UI_SCALE, s
from partials.backgrounds.base import Layer
from partials.backgrounds.helpers import Timer
from partials.backgrounds.brook_light import glow_sprite


class WindowLights(Layer):
    # The lit windows in one row of buildings. At night about share of them are lit, in warm
    # colors, and every so often one goes dark or another comes on; a few flicker blue with
    # a television. They fade into the haze like the buildings, but less, since lights shine
    # through it. By day, now and then a window glints in the sun instead
    #
    # Palette colors it uses:
    #   "window_lit"        a list of colors for lit windows (none lit without it)
    #   "tv"                a television's blue flicker
    #   "glint"             a window catching the sun, by day (no glints without it)
    #   "haze"

    FLIP = (250, 1100)              # milliseconds between one window changing and the next
    TVS = 3
    GLINTS = (1500, 5000)           # milliseconds between glints
    GLINT_TIME = 700

    def __init__(self, scene, row, share):
        super().__init__(scene)
        self.row = row
        self.share = share
        self.windows = row.lights
        count = len(self.windows)
        self.on = set(random.sample(range(count), int(count * share))) if count else set()
        self.colors = [random.randrange(4) for i in range(count)]
        on = list(self.on)
        self.tvs = random.sample(on, min(self.TVS, len(on)))
        self.changed = []
        self.flip = Timer(self.FLIP)
        self.glint_timer = Timer(self.GLINTS)
        self.glints = []
        self.time = 0
        self.image = None
        self.palette = None

    def strength(self, x, y):
        # How strongly a light at (x, y) shows through the haze and the quiet column
        return (1 - 0.65 * self.row.fade_at(y)) * self.scene.keep(x, 0.5)

    def paint_window(self, i, palette):
        x, y, w, h = self.windows[i]
        spot = (x, y - self.row.high, w, h)
        if i in self.on:
            lit = palette["window_lit"]
            color = pygame.Color(palette["haze"]).lerp(pygame.Color(lit[self.colors[i] % len(lit)]), self.strength(x, y))
            pygame.draw.rect(self.image, color, spot)
        else:
            pygame.draw.rect(self.image, (0, 0, 0, 0), spot)

    def paint(self, palette):
        self.image = pygame.Surface((WIDTH, max(1, self.row.bottom - self.row.high + s(120))), pygame.SRCALPHA)
        if "window_lit" in palette:
            for i in self.on:
                self.paint_window(i, palette)
        self.changed = []
        self.palette = palette

    def update(self, dt):
        self.time += dt
        if self.windows and self.flip.tick(dt):
            # Keep about the right share lit: switch one off if there are too many, on if too few
            want = len(self.windows) * self.share
            if len(self.on) > want * random.uniform(0.9, 1.1):
                i = random.choice(list(self.on))
                if i not in self.tvs:
                    self.on.discard(i)
                    self.changed.append(i)
            else:
                i = random.randrange(len(self.windows))
                if i not in self.on:
                    self.on.add(i)
                    self.colors[i] = random.randrange(4)
                    self.changed.append(i)
        if self.windows and self.glint_timer.tick(dt):
            self.glints.append({"i": random.randrange(len(self.windows)), "age": 0.0})
        for g in self.glints:
            g["age"] += dt
        self.glints = [g for g in self.glints if g["age"] < self.GLINT_TIME]

    def draw(self, surface, palette):
        if self.palette is not palette:
            self.paint(palette)
        if "window_lit" in palette:
            for i in self.changed:
                self.paint_window(i, palette)
            self.changed = []
            surface.blit(self.image, (0, self.row.high))
            # Televisions: a cold blue light, flickering as the picture changes
            tv = pygame.Color(palette["tv"])
            haze = pygame.Color(palette["haze"])
            for n, i in enumerate(self.tvs):
                x, y, w, h = self.windows[i]
                flicker = 0.6 + 0.4 * abs(math.sin(self.time / 170 + n * 2) * math.sin(self.time / 410 + n))
                surface.fill(haze.lerp(tv, self.strength(x, y) * flicker), (x, y, w, h))
        elif "glint" in palette:
            glint = pygame.Color(palette["glint"])
            for g in self.glints:
                x, y, w, h = self.windows[g["i"]]
                t = g["age"] / self.GLINT_TIME
                strength = math.sin(math.pi * t) * self.strength(x, y)
                cx, cy = x + w / 2, y + h / 2
                color = pygame.Color(palette["haze"]).lerp(glint, strength)
                reach = s(3) * strength + 1
                surface.fill(color, (x, y, w, h))
                pygame.draw.line(surface, color, (cx - reach, cy), (cx + reach, cy), 1)
                pygame.draw.line(surface, color, (cx, cy - reach), (cx, cy + reach), 1)


class Beacons(Layer):
    # Red warning lights on the tops of the spires, the masts and the tallest towers, each
    # blinking on its own slow beat, with a soft red glow at night
    #
    # Palette colors it uses:
    #   "beacon"                    the light
    #   "beacon_glow"               its glow, at night (no glow without it)

    def __init__(self, scene, rows):
        super().__init__(scene)
        self.rows = rows
        self.time = 0
        self.phases = {}
        self.palette = None

    def update(self, dt):
        self.time += dt

    def draw(self, surface, palette):
        if self.palette is not palette:
            self.glow = glow_sprite(s(7), pygame.Color(palette["beacon_glow"])) if "beacon_glow" in palette else None
            self.palette = palette
        beacon = pygame.Color(palette["beacon"])
        for row in self.rows:
            for x, y, landmark in row.tips:
                key = (int(x), int(y))
                if key not in self.phases:
                    self.phases[key] = (random.uniform(0, 3000), random.uniform(1800, 3000))
                phase, period = self.phases[key]
                t = ((self.time + phase) % period) / period
                if t > 0.35 and not landmark:
                    continue                                    # most blink; the landmarks' lights pulse
                strength = math.sin(math.pi * min(1, t / 0.35)) if t <= 0.35 else 0.35
                strength *= self.scene.keep(x, 0.4)
                if strength <= 0.05:
                    continue
                behind = self.scene.color_at(palette, y)
                pygame.draw.circle(surface, behind.lerp(beacon, strength), (x, y), max(1, s(1.3)))
                if self.glow is not None:
                    glow = self.glow.copy()
                    glow.fill([int(255 * strength)] * 3, special_flags=pygame.BLEND_RGB_MULT)
                    surface.blit(glow, glow.get_rect(center=(x, y)), special_flags=pygame.BLEND_RGB_ADD)


class NeonSign(Layer):
    # A tall hotel sign hanging off the side of a building on the right, its letters in neon
    # tubes down a dark board. At night they glow pink, buzzing, and now and then one letter
    # stutters off and on; by day the tubes are pale and unlit
    #
    # Palette colors it uses:
    #   "sign"              the board
    #   "neon"              the tubes (lit at night, pale by day)
    #   "neon_glow"         the glow around them, at night (unlit without it)

    WORD = "HOTEL"
    PLACE = (414, 318)              # the board's top middle, at the medium size
    SIZE = (16, 76)

    def __init__(self, scene):
        super().__init__(scene)
        self.time = 0
        self.x, self.y = s(self.PLACE[0]), s(self.PLACE[1])
        self.w, self.h = s(self.SIZE[0]), s(self.SIZE[1])
        try:
            self.font = pygame.font.Font(FONT_PATH, max(8, s(14)))     # the game's own hand-drawn letters
        except (FileNotFoundError, OSError):
            self.font = pygame.font.Font(None, max(10, s(18)))
        self.stutter = None
        self.stutter_timer = Timer((4000, 12000))
        self.palette = None

    def update(self, dt):
        self.time += dt
        if self.stutter is None:
            if self.stutter_timer.tick(dt):
                self.stutter = {"letter": random.randrange(len(self.WORD)), "age": 0.0, "time": random.uniform(400, 1500)}
        else:
            self.stutter["age"] += dt
            if self.stutter["age"] > self.stutter["time"]:
                self.stutter = None

    def paint(self, palette):
        neon = pygame.Color(palette["neon"])
        self.letters = [self.font.render(letter, True, neon) for letter in self.WORD]
        self.glow = glow_sprite(s(11), pygame.Color(palette["neon_glow"])) if "neon_glow" in palette else None
        self.palette = palette

    def draw(self, surface, palette):
        if self.palette is not palette:
            self.paint(palette)
        board = pygame.Color(palette["sign"])
        rect = pygame.Rect(0, 0, self.w, self.h)
        rect.midtop = (self.x, self.y)
        # The brackets holding it off the wall, and the board
        pygame.draw.line(surface, board, (rect.right, rect.top + s(6)), (rect.right + s(14), rect.top + s(6)), max(1, s(2)))
        pygame.draw.line(surface, board, (rect.right, rect.bottom - s(6)), (rect.right + s(14), rect.bottom - s(6)), max(1, s(2)))
        pygame.draw.rect(surface, board, rect, border_radius=s(3))
        lit = self.glow is not None
        step = self.h / len(self.WORD)
        for n, image in enumerate(self.letters):
            on = True
            if lit and self.stutter is not None and self.stutter["letter"] == n:
                on = math.sin(self.stutter["age"] / 35) > 0.2         # buzzing off and on
            cy = rect.top + step * (n + 0.5)
            if lit and on:
                strength = 0.75 + 0.1 * math.sin(self.time / 60 + n)
                glow = self.glow.copy()
                glow.fill([int(255 * strength)] * 3, special_flags=pygame.BLEND_RGB_MULT)
                surface.blit(glow, glow.get_rect(center=(rect.centerx, cy)), special_flags=pygame.BLEND_RGB_ADD)
            image.set_alpha(255 if (on or not lit) else 70)
            surface.blit(image, image.get_rect(center=(rect.centerx, cy)))


class BridgeTraffic(Layer):
    # A suspension bridge far off on the left, half hidden behind the buildings: two towers
    # and the long swoop of its cables, with traffic streaming across. At night it's two
    # rivers of light, white headlights one way and red taillights the other; by day,
    # little bright cars
    #
    # Palette colors it uses:
    #   "bridge"                    the bridge (faded into the haze with distance)
    #   "car_head", "car_tail"      car lights, at night
    #   "cars"                      a list of car colors, by day
    #   "haze"

    DECK = 210                      # the deck's height, at the medium size
    LEFT, RIGHT = -20, 175          # where it runs, medium x
    TOWERS = (25, 130)
    TOWER_HEIGHT = 34
    DISTANCE = 0.45
    SPEED = 22                      # pixels a second
    CARS = 9                        # in each direction

    def __init__(self, scene):
        super().__init__(scene)
        self.y = s(self.DECK)
        self.left, self.right = s(self.LEFT), s(self.RIGHT)
        self.cars = []
        for lane in (0, 1):
            for i in range(self.CARS):
                self.cars.append({"lane": lane, "x": random.uniform(self.left, self.right), "speed": random.uniform(0.8, 1.2),
                                  "color": random.randrange(5)})
        self.image = None
        self.palette = None

    def paint(self, palette):
        haze = pygame.Color(palette["haze"])
        color = pygame.Color(palette["bridge"]).lerp(haze, self.DISTANCE)
        top = self.y - s(self.TOWER_HEIGHT) - s(4)
        self.image = pygame.Surface((WIDTH, s(self.TOWER_HEIGHT) + s(12)), pygame.SRCALPHA)
        y = self.y - top
        pygame.draw.rect(self.image, color, (self.left, y, self.right - self.left, max(2, s(3))))
        towers = [s(t) for t in self.TOWERS]
        for tx in towers:
            pygame.draw.rect(self.image, color, (tx - s(2), y - s(self.TOWER_HEIGHT), s(4), s(self.TOWER_HEIGHT) + s(8)))
            pygame.draw.line(self.image, color, (tx - s(2), y - s(self.TOWER_HEIGHT) * 0.6), (tx + s(2), y - s(self.TOWER_HEIGHT) * 0.6), 1)
        # The main cables: swooping between the towers, and down to the ends
        cable = []
        for i in range(25):
            t = i / 24
            x = towers[0] + (towers[1] - towers[0]) * t
            cable.append((x, y - s(self.TOWER_HEIGHT) + s(2) + math.sin(math.pi * t) * s(self.TOWER_HEIGHT - 6)))
        pygame.draw.lines(self.image, color, False, cable, 1)
        pygame.draw.line(self.image, color, (towers[0], y - s(self.TOWER_HEIGHT) + s(2)), (self.left, y - s(4)), 1)
        pygame.draw.line(self.image, color, (towers[1], y - s(self.TOWER_HEIGHT) + s(2)), (self.right, y - s(2)), 1)
        for x, cy in cable[2:-2:2]:                            # hangers down to the deck
            pygame.draw.line(self.image, color, (x, cy), (x, y), 1)
        self.top = top
        self.palette = palette

    def update(self, dt):
        for car in self.cars:
            way = 1 if car["lane"] == 0 else -1
            car["x"] += way * s(self.SPEED) * car["speed"] * dt / 1000
            if car["x"] > self.right:
                car["x"] = self.left
            elif car["x"] < self.left:
                car["x"] = self.right

    def draw(self, surface, palette):
        if self.palette is not palette:
            self.paint(palette)
        surface.blit(self.image, (0, self.top))
        haze = pygame.Color(palette["haze"])
        night = "car_head" in palette
        for car in self.cars:
            x = car["x"]
            y = self.y - (1 if car["lane"] == 0 else 0)
            fade = self.scene.keep(x, 0.6) * (1 - self.DISTANCE * 0.5)
            if night:
                color = palette["car_head"] if car["lane"] == 0 else palette["car_tail"]
                surface.fill(haze.lerp(pygame.Color(color), fade), (x, y, max(1, s(2)), 1))
            else:
                cars = palette["cars"]
                surface.fill(haze.lerp(pygame.Color(cars[car["color"] % len(cars)]), fade * 0.8), (x, y - 1, max(2, s(3)), max(1, s(1.5))))


class Fireworks(Layer):
    # Every few minutes, at night, a show of fireworks over the city: rockets streak up from
    # the rooftops at the sides and burst into spheres of colored sparks that droop, fade and
    # twinkle out, a few at a time, then quiet again
    #
    # Palette colors it uses:
    #   "fireworks"         a list of colors (no fireworks without it, so none by day)

    WAIT = (120000, 260000)         # milliseconds between shows
    FIRST = (40000, 100000)
    SHOW = (12000, 20000)           # how long a show lasts
    LAUNCH = (500, 1600)            # milliseconds between rockets during a show
    SPARKS = 34
    GRAVITY = 26                    # pixels a second per second, at the medium size

    def __init__(self, scene):
        super().__init__(scene)
        self.timer = Timer(self.WAIT)
        self.timer.left = random.uniform(*self.FIRST)
        self.show = None
        self.rockets = []
        self.sparks = []
        self.palette = None
        self.glows = {}

    def start(self):
        self.show = {"age": 0.0, "time": random.uniform(*self.SHOW), "next": 0.0}

    def launch(self):
        side = random.choice((-1, 1))
        x = s(random.uniform(20, 95)) if side < 0 else WIDTH - s(random.uniform(20, 95))
        self.rockets.append({"x": x, "y": s(330), "vx": random.uniform(-s(6), s(6)), "vy": -s(random.uniform(150, 190)),
                             "burst": s(random.uniform(45, 130)), "color": random.randrange(8)})

    def burst(self, rocket):
        speed = s(random.uniform(55, 80))
        for i in range(self.SPARKS):
            a = 2 * math.pi * i / self.SPARKS + random.uniform(-0.1, 0.1)
            v = speed * random.uniform(0.75, 1.0)
            self.sparks.append({"x": rocket["x"], "y": rocket["y"], "vx": math.cos(a) * v, "vy": math.sin(a) * v, "age": 0.0,
                                "life": random.uniform(1300, 2000), "color": rocket["color"], "twinkle": random.uniform(0, 6)})

    def update(self, dt):
        if self.show is None:
            if self.timer.tick(dt) and self.palette is not None and "fireworks" in self.palette:
                self.start()
        else:
            self.show["age"] += dt
            self.show["next"] -= dt
            if self.show["next"] <= 0 and self.show["age"] < self.show["time"]:
                self.show["next"] = random.uniform(*self.LAUNCH)
                self.launch()
            if self.show["age"] > self.show["time"] and not self.rockets and not self.sparks:
                self.show = None
        seconds = dt / 1000
        for r in self.rockets:
            r["x"] += r["vx"] * seconds
            r["y"] += r["vy"] * seconds
            r["vy"] += s(self.GRAVITY) * seconds
        for r in [r for r in self.rockets if r["y"] < r["burst"] or r["vy"] > -s(30)]:
            self.rockets.remove(r)
            self.burst(r)
        for p in self.sparks:
            p["age"] += dt
            p["x"] += p["vx"] * seconds
            p["y"] += p["vy"] * seconds
            p["vx"] *= 1 - 1.4 * seconds                        # air slows them
            p["vy"] = p["vy"] * (1 - 1.4 * seconds) + s(self.GRAVITY) * seconds
        self.sparks = [p for p in self.sparks if p["age"] < p["life"]]

    def draw(self, surface, palette):
        self.palette = palette
        if "fireworks" not in palette or (not self.rockets and not self.sparks):
            return
        colors = [pygame.Color(c) for c in palette["fireworks"]]
        for r in self.rockets:
            behind = self.scene.color_at(palette, r["y"])
            pygame.draw.line(surface, behind.lerp(pygame.Color(palette["fireworks"][0]), 0.6), (r["x"], r["y"]),
                             (r["x"] - r["vx"] * 0.06, r["y"] - r["vy"] * 0.06), 1)
        for p in self.sparks:
            t = p["age"] / p["life"]
            strength = (1 - t ** 1.5) * ((0.5 + 0.5 * math.sin(p["age"] / 45 + p["twinkle"])) if t > 0.6 else 1)
            strength *= self.scene.keep(p["x"], 0.4)
            color = colors[p["color"] % len(colors)]
            add = [int(c * strength) for c in color[:3]]
            size = max(2, s(2.5)) if t < 0.3 else max(1, s(2))
            surface.fill(add, (p["x"] - size / 2, p["y"] - size / 2, size, size), special_flags=pygame.BLEND_RGB_ADD)
            # A trail behind each spark, fading back along its path
            for n, back in enumerate((0.04, 0.08, 0.12)):
                surface.fill([c // (2 + n) for c in add], (p["x"] - p["vx"] * back, p["y"] - p["vy"] * back, max(1, s(1.5)), max(1, s(1.5))),
                             special_flags=pygame.BLEND_RGB_ADD)
