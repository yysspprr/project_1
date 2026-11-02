# Life around the brook. Regulars: dragonflies darting and hovering over the water and
# butterflies fluttering along the banks (by day), and a frog that sits on a stone or the
# log and now and then hops into the water. Rare visitors, one at a time, every few
# minutes: a kingfisher flashing down the brook (by day), a paper boat drifting past,
# or a deer stepping down to drink.
#
# Things that fly or hover are drawn above their spot on the ground, with a soft shadow
# on the spot itself, so they read as being in the air

import math

import random

import pygame

from partials.config import WIDTH, HEIGHT, CENTER_X, s
from partials.backgrounds.base import Layer
from partials.backgrounds.helpers import Timer
from partials.backgrounds.brook_flow import flow_speed


def place(points, x, y, heading, size, squash):
    # Points of a little shape in its own units (pointing along +u) turned to face
    # heading, sized, and laid on the ground (squashed up and down like the view)
    cos, sin = math.cos(heading), math.sin(heading)
    return [(x + (u * cos - v * sin) * size, y + (u * sin + v * cos) * size * squash) for u, v in points]


def ellipse_shape(length, width, count=10):
    return [(math.cos(2 * math.pi * i / count) * length, math.sin(2 * math.pi * i / count) * width) for i in range(count)]


_shadows = {}

def draw_shadow(surface, x, y, width, height, strength):
    # A soft dark oval on the ground under something in the air (or standing on it)
    key = (max(2, int(width)), max(2, int(height)), int(strength * 20))
    if key not in _shadows:
        sprite = pygame.Surface(key[:2], pygame.SRCALPHA)
        alpha = int(255 * key[2] / 20)
        pygame.draw.ellipse(sprite, (0, 0, 0, alpha // 2), sprite.get_rect())
        pygame.draw.ellipse(sprite, (0, 0, 0, alpha), sprite.get_rect().inflate(-key[0] * 0.35, -key[1] * 0.35))
        if len(_shadows) > 300:
            _shadows.clear()
        _shadows[key] = sprite
    sprite = _shadows[key]
    surface.blit(sprite, (x - sprite.get_width() / 2, y - sprite.get_height() / 2))


def daytime(palette):
    return "sunlight" in palette


class BrookRings(Layer):
    # Rings spreading on the water where something touches it: a frog plopping in, a
    # kingfisher dipping, a deer drinking. Others call add(x, y, size)
    #
    # Palette colors it uses:
    #   "ripple"                the rings when fresh (they fade into the water)

    LIFE = 1400                     # milliseconds a ring lasts

    def __init__(self, scene, water):
        super().__init__(scene)
        self.water = water
        self.rings = []

    def add(self, x, y, size, count=2):
        for k in range(count):
            self.rings.append({"x": x, "y": y, "size": size, "age": -k * 260.0})

    def update(self, dt):
        for ring in self.rings:
            ring["age"] += dt
        self.rings = [ring for ring in self.rings if ring["age"] < self.LIFE]

    def draw(self, surface, palette):
        ripple = pygame.Color(palette.get("ripple", palette.get("shallows", palette["text"])))
        view = self.scene.view
        for ring in self.rings:
            if ring["age"] < 0:
                continue
            t = ring["age"] / self.LIFE
            radius = ring["size"] * (0.4 + 1.6 * t)
            flat = view.flatten(ring["y"]) / view.near_flatten * 0.55
            color = self.water.water_color(palette, ring["x"], ring["y"]).lerp(ripple, (1 - t) * 0.9)
            pygame.draw.ellipse(surface, color, (ring["x"] - radius, ring["y"] - radius * flat, radius * 2, radius * 2 * flat), 1)


class Dragonflies(Layer):
    # Dragonflies over the water: they hover in one spot, wings a blur, then dart to
    # another in a quick straight dash. Daytime only
    #
    # Palette colors it uses:
    #   "dragonfly"             their bodies (a list: one each)
    #   "wing"                  their wings

    COUNT = 2
    HOVER = (900, 3200)             # milliseconds they hover in one spot
    DART_TIME = (220, 480)          # milliseconds a dart takes
    DART = (40, 130)                # how far a dart goes, pixels at the medium size
    HEIGHT_ABOVE = 16               # how high above the water they hover
    SIZE = 9                        # half a body's length, pixels at the medium size

    BODY = [(1.0, 0), (-1.0, 0)]
    WINGS = [(0.45, 1.25), (0.45, -1.25), (0.1, 1.1), (0.1, -1.1)]

    def __init__(self, scene, course):
        super().__init__(scene)
        self.course = course
        self.time = 0
        self.flies = []
        for i in range(self.COUNT):
            x, y = self.spot()
            self.flies.append({"x": x, "y": y, "from": (x, y), "to": (x, y), "heading": random.uniform(0, 2 * math.pi),
                               "dart": 0, "dart_time": 1, "wait": random.uniform(*self.HOVER), "pick": i})

    def spot(self, near=None):
        # Somewhere over the water, near a point if given
        for attempt in range(20):
            if near:
                angle = random.uniform(0, 2 * math.pi)
                reach = s(random.uniform(*self.DART))
                x, y = near[0] + math.cos(angle) * reach, near[1] + math.sin(angle) * reach * 0.7
            else:
                y = random.uniform(s(30), HEIGHT - s(30))
                x = self.course.center(y) + random.uniform(-0.8, 0.8) * self.course.half_width(y)
            if s(20) < y < HEIGHT - s(20) and self.course.inside(x, y, 0.9):
                return x, y
        y = random.uniform(s(30), HEIGHT - s(30))
        return self.course.center(y), y

    def update(self, dt):
        self.time += dt
        for fly in self.flies:
            if fly["dart"] > 0:
                fly["dart"] -= dt
                t = 1 - max(0, fly["dart"]) / fly["dart_time"]
                t = t * t * (3 - 2 * t)
                fly["x"] = fly["from"][0] + (fly["to"][0] - fly["from"][0]) * t
                fly["y"] = fly["from"][1] + (fly["to"][1] - fly["from"][1]) * t
            else:
                fly["wait"] -= dt
                if fly["wait"] <= 0:
                    fly["from"] = (fly["x"], fly["y"])
                    fly["to"] = self.spot((fly["x"], fly["y"]))
                    fly["heading"] = math.atan2(fly["to"][1] - fly["y"], fly["to"][0] - fly["x"])
                    fly["dart_time"] = fly["dart"] = random.uniform(*self.DART_TIME)
                    fly["wait"] = random.uniform(*self.HOVER)

    def draw(self, surface, palette):
        if "dragonfly" not in palette:
            return
        view = self.scene.view
        wing = pygame.Color(palette.get("wing", palette["text"]))
        for fly in self.flies:
            body = pygame.Color(palette["dragonfly"][fly["pick"] % len(palette["dragonfly"])])
            scale = view.scale(fly["y"])
            squash = view.flatten(fly["y"]) / view.near_flatten
            size = s(self.SIZE) * scale
            draw_shadow(surface, fly["x"], fly["y"], size * 2.2, size * 0.8 * squash, 0.18)
            # Hovering bobs it gently up and down
            x = fly["x"]
            y = fly["y"] - s(self.HEIGHT_ABOVE) * scale + math.sin(self.time / 170 + fly["pick"]) * s(1)
            beat = 0.75 + 0.25 * math.sin(self.time / 18 + fly["pick"])      # wings a flickering blur
            root = place([(0.35, 0), (0.05, 0)], x, y, fly["heading"], size, squash)
            tips = place([(u, v * beat) for u, v in self.WINGS], x, y, fly["heading"], size, squash)
            for k, tip in enumerate(tips):
                pygame.draw.line(surface, wing, root[k // 2], tip, max(1, s(2)))
            a, b = place(self.BODY, x, y, fly["heading"], size, squash)
            pygame.draw.line(surface, body, a, b, max(1, s(1.6)))
            pygame.draw.circle(surface, body, a, max(1, s(1.8) * scale))


class Butterflies(Layer):
    # Butterflies fluttering along the banks: a bobbing, wandering flight, wings flapping,
    # sometimes settling on the moss for a few seconds with their wings slowly opening and
    # closing. They turn back before they get far over the water. Daytime only
    #
    # Palette colors it uses:
    #   "butterfly"             a list of wing colors
    #   "butterfly_edge"        the dark edge of their wings and their bodies

    COUNT = 3
    SPEED = 28                      # pixels per second, at the medium size
    SIZE = 7                        # a wing's reach, pixels at the medium size
    FLY = (5000, 12000)             # milliseconds between rests
    REST = (2500, 6000)             # milliseconds a rest lasts
    HEIGHT_ABOVE = 14

    def __init__(self, scene, course):
        super().__init__(scene)
        self.course = course
        self.time = 0
        self.flies = []
        for i in range(self.COUNT):
            self.flies.append({"x": scene.margin_x(), "y": random.uniform(s(20), HEIGHT - s(20)),
                               "heading": random.uniform(0, 2 * math.pi), "pick": random.randrange(10),
                               "phase": random.uniform(0, 2 * math.pi), "resting": 0,
                               "until_rest": random.uniform(*self.FLY), "lift": 1.0})

    def update(self, dt):
        self.time += dt
        course = self.course
        for fly in self.flies:
            if fly["resting"] > 0:
                fly["resting"] -= dt
                fly["lift"] = max(0.0, fly["lift"] - dt / 400)
                continue
            fly["lift"] = min(1.0, fly["lift"] + dt / 400)
            fly["until_rest"] -= dt
            if fly["until_rest"] <= 0 and not course.inside(fly["x"], fly["y"], 1.6):
                fly["resting"] = random.uniform(*self.REST)
                fly["until_rest"] = random.uniform(*self.FLY)
                continue
            fly["heading"] += random.uniform(-3, 3) * dt / 1000
            # Over the water, or off the window: turn back toward the nearer bank's middle
            side = -1 if fly["x"] < course.center(fly["y"]) else 1
            if course.inside(fly["x"], fly["y"], 1.15) or not (s(8) < fly["x"] < WIDTH - s(8)):
                home = course.bank(fly["y"], side) + side * s(70)
                want = math.atan2(0, home - fly["x"])
                fly["heading"] += math.sin(want - fly["heading"]) * 4 * dt / 1000
            if not (s(10) < fly["y"] < HEIGHT - s(10)):
                want = math.atan2(HEIGHT / 2 - fly["y"], 0)
                fly["heading"] += math.sin(want - fly["heading"]) * 4 * dt / 1000
            step = s(self.SPEED) * self.scene.view.scale(fly["y"]) * dt / 1000
            fly["x"] += math.cos(fly["heading"]) * step
            fly["y"] += math.sin(fly["heading"]) * step * 0.7

    def draw(self, surface, palette):
        if "butterfly" not in palette:
            return
        view = self.scene.view
        edge = pygame.Color(palette.get("butterfly_edge", palette["text"]))
        for fly in self.flies:
            color = pygame.Color(palette["butterfly"][fly["pick"] % len(palette["butterfly"])])
            scale = view.scale(fly["y"])
            squash = view.flatten(fly["y"]) / view.near_flatten
            size = s(self.SIZE) * scale
            lift = fly["lift"]
            bob = math.sin(self.time / 260 + fly["phase"]) * s(3) * lift
            x, y = fly["x"], fly["y"] - (s(self.HEIGHT_ABOVE) * lift + bob) * scale
            draw_shadow(surface, fly["x"], fly["y"], size * 2.4, size * 1.0 * squash, 0.08 + 0.12 * (1 - lift))
            # Flapping fast in flight, slowly opening and closing at rest
            speed = 45 if lift > 0.2 else 700
            open_wings = 0.25 + 0.75 * abs(math.sin(self.time / speed + fly["phase"]))
            heading = fly["heading"]
            for side in (-1, 1):
                fore = place([(0.2, 0), (0.9, side * 1.15 * open_wings), (-0.1, side * 1.2 * open_wings)], x, y, heading, size, squash)
                hind = place([(-0.1, 0), (-0.3, side * 0.95 * open_wings), (-0.85, side * 0.6 * open_wings)], x, y, heading, size, squash)
                for wing in (hind, fore):
                    pygame.draw.polygon(surface, color, wing)
                    pygame.draw.lines(surface, edge, True, wing, 1)
            a, b = place([(0.55, 0), (-0.6, 0)], x, y, heading, size, squash)
            pygame.draw.line(surface, edge, a, b, max(1, s(1.4)))


class Frog(Layer):
    # A frog sitting on one of the stones in the water (or on the log, when there is
    # one), its throat pulsing. Now and then it hops into the water with a plop and a
    # ring of ripples, stays under a while, then pops up by another stone and climbs
    # back out
    #
    # Palette colors it uses:
    #   "frog", "frog_dark", "frog_light"   its back, its spots and outline, its eyes' glint

    SIZE = 10                       # half its body length, pixels at the medium size
    SIT = (12000, 30000)            # milliseconds between hops
    UNDER = (5000, 14000)           # milliseconds it stays under water
    HOP_TIME = 480
    HOP_HEIGHT = 16                 # how high a hop goes, pixels at the medium size

    # Its shape from above, in body half-lengths, nose pointing along +u
    BODY = [(1.2, 0), (1.0, 0.55), (0.3, 0.78), (-0.6, 0.72), (-1.0, 0.38), (-1.08, 0),
            (-1.0, -0.38), (-0.6, -0.72), (0.3, -0.78), (1.0, -0.55)]
    THIGH = [(-0.75, 0.55), (-0.1, 1.05), (0.25, 0.95), (-0.35, 0.45)]      # folded back leg, left side
    FOOT = [(-0.1, 1.05), (-0.85, 1.15), (-1.15, 0.95), (-0.55, 0.85)]
    ARM = [(0.45, 0.68), (0.8, 1.02)]
    EYE = (0.72, 0.5)

    def __init__(self, scene, course, rocks, log, rings):
        super().__init__(scene)
        self.course = course
        self.rings = rings
        # Where it can sit: on top of a stone in the water, or along the log
        self.perches = []
        for stone in rocks.rocks:
            if stone["wet"] and stone["size"] > s(10) * scene.view.scale(stone["y"]):
                self.perches.append((stone["x"] - stone["size"] * 0.1, stone["y"] - stone["size"] * 0.1 * stone["squash"]))
        if log.present:
            for t in (0.3, 0.4, 0.6, 0.7):
                self.perches.append(log.along(t, -0.35))
        # Prefer perches out of the way of the text, when there are any
        clear = [perch for perch in self.perches if scene.keep(perch[0]) > 0.8]
        self.perches = clear or self.perches
        self.state = "sit"
        self.wait = random.uniform(*self.SIT)
        self.spot = random.choice(self.perches) if self.perches else None
        self.heading = random.uniform(0, 2 * math.pi)
        self.time = 0
        self.hop = None

    def water_spot(self, near):
        for attempt in range(20):
            angle = random.uniform(0, 2 * math.pi)
            x, y = near[0] + math.cos(angle) * s(28), near[1] + math.sin(angle) * s(18)
            if self.course.inside(x, y, 0.85):
                return (x, y)
        return (self.course.center(near[1]), near[1])

    def update(self, dt):
        if self.spot is None:
            return
        self.time += dt
        if self.state in ("sit", "under"):
            self.wait -= dt
            if self.wait > 0:
                return
            if self.state == "sit":
                start, end = self.spot, self.water_spot(self.spot)
            else:
                end = random.choice(self.perches)
                start = self.water_spot(end)
                self.rings.add(start[0], start[1], s(6) * self.scene.view.scale(start[1]), 1)
            self.hop = {"from": start, "to": end, "age": 0.0}
            self.heading = math.atan2(end[1] - start[1], end[0] - start[0])
            self.state = "out" if self.state == "sit" else "in"
        else:
            self.hop["age"] += dt
            if self.hop["age"] >= self.HOP_TIME:
                if self.state == "out":
                    x, y = self.hop["to"]
                    self.rings.add(x, y, s(9) * self.scene.view.scale(y), 3)
                    self.state, self.wait = "under", random.uniform(*self.UNDER)
                else:
                    self.spot = self.hop["to"]
                    self.state, self.wait = "sit", random.uniform(*self.SIT)
                    self.heading += random.uniform(-0.8, 0.8)

    def draw(self, surface, palette):
        if self.spot is None or self.state == "under":
            return
        view = self.scene.view
        back = pygame.Color(palette.get("frog", palette["muted"]))
        dark = pygame.Color(palette.get("frog_dark", palette["text"]))
        light = pygame.Color(palette.get("frog_light", palette["text"]))
        if self.hop and self.state in ("out", "in"):
            t = self.hop["age"] / self.HOP_TIME
            (x0, y0), (x1, y1) = self.hop["from"], self.hop["to"]
            gx, gy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            lift = math.sin(math.pi * t) * s(self.HOP_HEIGHT) * view.scale(gy)
            stretch = 1 + 0.5 * math.sin(math.pi * t)
        else:
            gx, gy = self.spot
            lift, stretch = 0, 1
        scale = view.scale(gy)
        squash = view.flatten(gy) / view.near_flatten
        size = s(self.SIZE) * scale
        x, y = gx, gy - lift
        draw_shadow(surface, gx + size * 0.2, gy + size * 0.3, size * 2.4, size * 1.2 * squash, 0.25)
        heading = self.heading
        width = max(1, s(1))

        def shape(points, side=1):
            # Left-side parts mirror to the right; a hop kicks the back legs out behind
            moved = []
            for u, v in points:
                if stretch > 1 and v * side > 0.4 and u < 0.3:
                    u -= (stretch - 1) * 2.2
                moved.append((u, v * side))
            return place(moved, x, y, heading, size, squash)

        for side in (1, -1):
            for part in (self.FOOT, self.THIGH):
                points = shape(part, side)
                pygame.draw.polygon(surface, back.lerp(dark, 0.25), points)
                pygame.draw.lines(surface, dark, True, points, 1)
            a, b = shape(self.ARM, side)
            pygame.draw.line(surface, dark, a, b, width)
        body = place([(u * (1 + (stretch - 1) * 0.3), v) for u, v in self.BODY], x, y, heading, size, squash)
        pygame.draw.polygon(surface, back, body)
        pygame.draw.lines(surface, dark, True, body, 1)
        # A pale stripe down its back, a few spots, and its eyes bulging at the front corners
        a, b = place([(0.9, 0), (-0.8, 0)], x, y, heading, size, squash)
        pygame.draw.line(surface, back.lerp(light, 0.45), a, b, max(1, int(size * 0.18)))
        for u, v in ((-0.35, 0.38), (0.15, -0.42), (-0.55, -0.25)):
            px, py = place([(u, v)], x, y, heading, size, squash)[0]
            pygame.draw.circle(surface, dark, (px, py), max(1, size * 0.13))
        for side in (1, -1):
            ex, ey = place([(self.EYE[0], self.EYE[1] * side)], x, y, heading, size, squash)[0]
            pygame.draw.circle(surface, back, (ex, ey), max(1.5, size * 0.3))
            pygame.draw.circle(surface, dark, (ex, ey), max(1.5, size * 0.3), 1)
            pygame.draw.circle(surface, dark, (ex, ey), max(1, size * 0.15))
            pygame.draw.circle(surface, light, (ex - size * 0.06, ey - size * 0.06), max(1, size * 0.06))
        if self.state == "sit":
            pulse = max(0, math.sin(self.time / 140)) ** 2
            if pulse > 0.3:
                tx, ty = place([(1.05, 0)], x, y, heading, size, squash)[0]
                pygame.draw.circle(surface, back.lerp(light, 0.4), (tx, ty + size * 0.2), size * 0.18 * pulse)


class Visits:
    # Takes turns between the rare visitors, so only one comes at a time, every few minutes.
    # Each visitor has can_come(palette) (it may only come by day) and start()

    EVERY = (70000, 170000)         # milliseconds between visits
    FIRST = (25000, 60000)          # ... and before the first one

    def __init__(self):
        self.visitors = []
        self.wait = random.uniform(*self.FIRST)
        self.palette = None

    def join(self, visitor):
        self.visitors.append(visitor)
        visitor.visits = self
        return visitor

    def busy(self):
        return any(visitor.active for visitor in self.visitors)

    def update(self, dt):
        if self.palette is None or self.busy():
            return
        self.wait -= dt
        if self.wait <= 0:
            choices = [visitor for visitor in self.visitors if visitor.can_come(self.palette)]
            if choices:
                random.choice(choices).start()
            self.wait = random.uniform(*self.EVERY)


class Visitor(Layer):
    # A rare visitor: does nothing until Visits starts it, then plays out its visit once

    def __init__(self, scene):
        super().__init__(scene)
        self.active = False
        self.visits = None

    def can_come(self, palette):
        return True

    def start(self):
        self.active = True


class VisitClock(Layer):
    # Puts Visits in the scene: ticks it, and tells it the current palette
    def __init__(self, scene, visits):
        super().__init__(scene)
        self.visits = visits

    def update(self, dt):
        self.visits.update(dt)

    def draw(self, surface, palette):
        self.visits.palette = palette


class Kingfisher(Visitor):
    # A flash of blue and orange: a kingfisher flying fast and low down the brook (or up
    # it), following its bends, dipping to the water once on the way. Daytime only
    #
    # Palette colors it uses:
    #   "kingfisher", "kingfisher_breast"   its back and its orange cheeks
    #   "butterfly_edge"                    its beak

    SPEED = 240                     # pixels per second, at the medium size
    SIZE = 9
    HEIGHT_ABOVE = 18

    def __init__(self, scene, course, rings):
        super().__init__(scene)
        self.course = course
        self.rings = rings

    def can_come(self, palette):
        return "kingfisher" in palette

    def start(self):
        super().start()
        self.down = random.random() < 0.65
        self.y = -s(20) if self.down else HEIGHT + s(20)
        self.offset = random.uniform(-0.3, 0.3)
        self.dip_at = random.uniform(HEIGHT * 0.25, HEIGHT * 0.75)
        self.dipped = False
        self.time = 0

    def update(self, dt):
        if not self.active:
            return
        self.time += dt
        step = s(self.SPEED) * self.scene.view.scale(self.y) * dt / 1000
        self.y += step if self.down else -step
        if not self.dipped and abs(self.y - self.dip_at) < step:
            self.dipped = True
            self.rings.add(self.x(), self.y, s(7) * self.scene.view.scale(self.y), 2)
        if self.y > HEIGHT + s(30) or self.y < -s(30):
            self.active = False

    def x(self):
        return self.course.center(self.y) + self.offset * self.course.half_width(self.y)

    def draw(self, surface, palette):
        if not self.active or "kingfisher" not in palette:
            return
        view = self.scene.view
        blue = pygame.Color(palette["kingfisher"])
        orange = pygame.Color(palette.get("kingfisher_breast", palette["accent"]))
        beak = pygame.Color(palette.get("butterfly_edge", palette["text"]))
        scale = view.scale(self.y)
        squash = view.flatten(self.y) / view.near_flatten
        size = s(self.SIZE) * scale
        gx, gy = self.x(), self.y
        dip = max(0, 1 - abs(self.y - self.dip_at) / s(40))          # swoops low to touch the water
        x, y = gx, gy - s(self.HEIGHT_ABOVE) * scale * (1 - 0.8 * dip)
        draw_shadow(surface, gx, gy, size * 2.6, size * 1.0 * squash, 0.2)
        step = self.course.direction(self.y)
        heading = math.atan2(step[1], step[0]) if self.down else math.atan2(-step[1], -step[0])
        beat = math.sin(self.time / 35)
        for side in (-1, 1):
            wing = place([(0.4, 0), (0.1, side * (1.0 + 0.5 * beat)), (-0.5, side * (0.8 + 0.4 * beat)), (-0.3, 0)],
                         x, y, heading, size, squash)
            pygame.draw.polygon(surface, blue.lerp((0, 0, 0), 0.2), wing)
        body = place(ellipse_shape(0.9, 0.38, 10), x, y, heading, size, squash)
        pygame.draw.polygon(surface, blue, body)
        for side in (-1, 1):
            cheek = place([(0.55, side * 0.3)], x, y, heading, size, squash)[0]
            pygame.draw.circle(surface, orange, cheek, max(1, size * 0.18))
        a, b = place([(0.85, 0), (1.55, 0)], x, y, heading, size, squash)
        pygame.draw.line(surface, beak, a, b, max(1, s(1.5)))
        tail = place([(-0.8, 0.15), (-1.3, 0), (-0.8, -0.15)], x, y, heading, size, squash)
        pygame.draw.polygon(surface, blue, tail)


class PaperBoat(Visitor):
    # A folded paper boat someone set off upstream, riding the current all the way down,
    # rocking a little and nudged around the stones. Drawn under the log, so it slips
    # beneath it
    #
    # Palette colors it uses:
    #   "paper", "paper_shade"      the paper, and its folds and shaded side

    SIZE = 13
    SPEED = 0.6                     # share of the current's speed it rides at

    HULL = [(1.0, 0), (0.55, 0.42), (-0.55, 0.42), (-1.0, 0), (-0.55, -0.42), (0.55, -0.42)]
    SAIL = [(0.55, 0), (0, 0.18), (-0.55, 0), (0, -0.18)]

    def __init__(self, scene, course, rocks):
        super().__init__(scene)
        self.course = course
        self.stones = [stone for stone in rocks.rocks if stone["wet"]]

    def start(self):
        super().start()
        self.y = -s(20)
        self.across = random.uniform(-0.35, 0.35)
        self.time = 0

    def update(self, dt):
        if not self.active:
            return
        self.time += dt
        course = self.course
        x = course.center(self.y) + self.across * course.half_width(self.y)
        self.y += flow_speed(course, x, self.y, self.scene.weather.get("wind", 1)) * self.SPEED * dt / 1000
        size = s(self.SIZE) * self.scene.view.scale(self.y)
        for stone in self.stones:
            gap = stone["size"] * 1.3 + size
            ahead = stone["y"] - self.y
            if -gap * 0.5 < ahead < gap * 1.6 and abs(stone["x"] - x) < gap:
                self.across += (1 if x >= stone["x"] else -1) * 0.8 * dt / 1000
        self.across = max(-0.75, min(0.75, self.across))
        if self.y > HEIGHT + s(30):
            self.active = False

    def draw(self, surface, palette):
        if not self.active:
            return
        view = self.scene.view
        paper = pygame.Color(palette.get("paper", palette["text"]))
        shade = pygame.Color(palette.get("paper_shade", palette["muted"]))
        course = self.course
        x = course.center(self.y) + self.across * course.half_width(self.y)
        y = self.y
        scale = view.scale(y)
        squash = view.flatten(y) / view.near_flatten
        size = s(self.SIZE) * scale
        step = course.direction(y)
        heading = math.atan2(step[1], step[0]) + math.sin(self.time / 900) * 0.25
        rock = math.sin(self.time / 520) * 0.12
        draw_shadow(surface, x + size * 0.25, y + size * 0.35, size * 2.3, size * 1.0 * squash, 0.25)
        hull = place(self.HULL, x, y, heading, size, squash)
        pygame.draw.polygon(surface, paper.lerp(shade, 0.35), hull)
        pygame.draw.lines(surface, shade.lerp((0, 0, 0), 0.25), True, hull, 1)
        # The folded sail standing up in the middle: a tent of paper, one face lit and one
        # in shade, rocking a little from side to side
        lift = size * 0.75
        front, back = place([(0.6, rock), (-0.6, rock)], x, y, heading, size, squash)
        ridge = [(front[0], front[1] - lift), (back[0], back[1] - lift)]
        for side, color in ((-1, paper), (1, shade)):
            foot = place([(0.05, side * 0.32)], x, y, heading, size, squash)[0]
            pygame.draw.polygon(surface, color, [front, ridge[0], ridge[1], back, foot])
        pygame.draw.line(surface, shade.lerp((0, 0, 0), 0.25), ridge[0], ridge[1], 1)
        pygame.draw.line(surface, shade.lerp((0, 0, 0), 0.25), front, ridge[0], 1)
        pygame.draw.line(surface, shade.lerp((0, 0, 0), 0.25), back, ridge[1], 1)


class Deer(Visitor):
    # A deer stepping in from the side of the window, walking down the bank to the water,
    # lowering its head to drink (with little rings where its muzzle touches), then
    # lifting its head, turning and walking away. Seen from above and a little to the
    # side: its body, legs and neck, squashed like everything else
    #
    # Palette colors it uses:
    #   "deer", "deer_light", "deer_dark"   its coat, its pale rump and belly, its legs, nose and outline

    SIZE = 22                       # half its body length, pixels at the medium size
    SPEED = 26                      # walking speed, pixels per second at the medium size
    DRINK = (5000, 9000)            # milliseconds it drinks
    SIP = (900, 1800)               # milliseconds between sips (each one rings the water)

    def __init__(self, scene, course, rings, rocks):
        super().__init__(scene)
        self.course = course
        self.rings = rings
        self.busy_rows = rocks.clear_rows + [(course.crossing_y - s(40), course.crossing_y + s(40))]

    def start(self):
        super().start()
        course = self.course
        for attempt in range(30):
            y = random.uniform(s(70), HEIGHT - s(70))
            if not any(top < y < bottom for top, bottom in self.busy_rows):
                break
        self.y = y
        self.side = random.choice((-1, 1))                  # which bank it comes down
        size = s(self.SIZE) * self.scene.view.scale(y)
        self.x = -size * 3 if self.side < 0 else WIDTH + size * 3
        self.stop = course.edge(y, self.side) + self.side * size * 1.85    # close enough to reach the water
        self.facing = -self.side                            # toward the water
        self.state = "walk in"
        self.drink = random.uniform(*self.DRINK)
        self.sip = Timer(self.SIP)
        self.head = 0.0                                     # 0 up, 1 down drinking
        self.stride = 0.0

    def update(self, dt):
        if not self.active:
            return
        size = s(self.SIZE) * self.scene.view.scale(self.y)
        speed = s(self.SPEED) * self.scene.view.scale(self.y) * dt / 1000
        if self.state == "walk in":
            self.x += self.facing * speed
            self.stride += dt
            if (self.x - self.stop) * self.facing >= 0:
                self.state = "drink"
        elif self.state == "drink":
            self.head = min(1.0, self.head + dt / 900)
            self.drink -= dt
            if self.head >= 1 and self.sip.tick(dt):
                mx, my = self.muzzle(size)
                self.rings.add(mx, my + size * 0.1, s(5) * self.scene.view.scale(self.y), 1)
            if self.drink <= 0:
                self.state = "turn"
        elif self.state == "turn":
            self.head = max(0.0, self.head - dt / 700)
            if self.head <= 0:
                self.facing = -self.facing
                self.state = "walk out"
        else:
            self.x += self.facing * speed
            self.stride += dt
            if not (-size * 4 < self.x < WIDTH + size * 4):
                self.active = False

    def muzzle(self, size):
        # Where its nose is: up and ahead when walking, down at the water when drinking
        squash = self.scene.view.flatten(self.y) / self.scene.view.near_flatten
        legs = size * 1.0 * squash
        up = (self.x + self.facing * size * 1.55, self.y - legs - size * 1.2 * squash)
        down = (self.x + self.facing * size * 2.15, self.y - size * 0.05)
        h = self.head * self.head * (3 - 2 * self.head)
        return (up[0] + (down[0] - up[0]) * h, up[1] + (down[1] - up[1]) * h)

    def draw(self, surface, palette):
        if not self.active:
            return
        view = self.scene.view
        coat = pygame.Color(palette.get("deer", palette["muted"]))
        pale = pygame.Color(palette.get("deer_light", palette["muted"]))
        dark = pygame.Color(palette.get("deer_dark", palette["text"]))
        scale = view.scale(self.y)
        squash = view.flatten(self.y) / view.near_flatten
        size = s(self.SIZE) * scale
        f = self.facing
        x, ground = self.x, self.y
        legs = size * 1.0 * squash                          # how far its body is above the ground
        body_y = ground - legs - size * 0.25 * squash
        draw_shadow(surface, x, ground, size * 2.8, size * 0.9 * squash, 0.28)
        # Legs: four, swinging while it walks
        walking = self.state in ("walk in", "walk out")
        for k, u in enumerate((0.75, 0.55, -0.6, -0.8)):
            swing = math.sin(self.stride / 160 + k * math.pi / 2) * size * 0.25 if walking else 0
            top = (x + f * u * size, body_y + size * 0.2 * squash)
            foot = (x + f * u * size + swing, ground)
            pygame.draw.line(surface, dark if k % 2 else coat.lerp(dark, 0.4), top, foot, max(1, int(size * 0.14)))
        # Body, its pale rump and belly, and a little tail
        body = pygame.Rect(0, 0, size * 2.1, size * 0.9 * squash + 2)
        body.center = (x, body_y)
        pygame.draw.ellipse(surface, coat, body)
        belly = pygame.Rect(0, 0, size * 1.4, size * 0.3 * squash + 1)
        belly.center = (x, body_y + size * 0.28 * squash)
        pygame.draw.ellipse(surface, pale, belly)
        pygame.draw.circle(surface, pale, (x - f * size * 0.95, body_y - size * 0.05), size * 0.28)
        pygame.draw.ellipse(surface, dark, body, 1)
        # Neck and head, reaching up when it walks and down to the water when it drinks
        mx, my = self.muzzle(size)
        shoulder = (x + f * size * 0.75, body_y - size * 0.15 * squash)
        pygame.draw.line(surface, coat, shoulder, (mx - f * size * 0.35, my), max(2, int(size * 0.4)))
        head = pygame.Rect(0, 0, size * 0.75, size * 0.42 * squash + 2)
        head.center = (mx - f * size * 0.15, my)
        pygame.draw.ellipse(surface, coat, head)
        pygame.draw.circle(surface, dark, (mx + f * size * 0.15, my), max(1, size * 0.1))
        for k in (-1, 1):
            ear = pygame.Rect(0, 0, size * 0.22, size * 0.32 * squash + 1)
            ear.center = (mx - f * size * (0.45 + 0.08 * k), my - size * 0.3 * squash)
            pygame.draw.ellipse(surface, coat.lerp(dark, 0.3), ear)
