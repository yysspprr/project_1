# Life in the garden pond: koi gliding under the surface (now and then one rises and
# breaks it with a ring), lily pads with a few flowers, and at night the stone lantern's
# light flickering on the water near it

import math

import random

import pygame

from partials.config import WIDTH, HEIGHT, s
from partials.backgrounds.base import Layer
from partials.backgrounds.helpers import Timer


class Koi(Layer):
    # Koi swimming slowly around the pond, seen from above through the water: long bodies
    # that bend as they turn, a tail that sways, small fins, and patches of orange, red,
    # gold, white and black. Deeper down they fade into the water's color; sometimes one
    # rises to the surface, shows its colors fully, nudges the water into a ring, and sinks
    # again. They swim in the pond's own flat circle (the pond is an oval because it's seen
    # at a slant), so turns look right in perspective
    #
    # Palette colors it uses:
    #   "koi"                   a list of body colors
    #   "koi_spot"              the black markings

    COUNT = 5
    LENGTH = (24, 32)               # pixels at the medium size, up close
    SPEED = 13                      # pixels per second
    TURN = 1.4                      # how hard they wander, radians per second at most
    SEGMENTS = 8
    WIDTH = (0.13, 0.19, 0.2, 0.18, 0.14, 0.1, 0.07, 0.05)      # body width along it, as shares of its length
    DEPTH = 0.5                     # how strongly they show when swimming deep
    SURFACE = 0.95                  # ... and at the surface
    RISE = (6000, 16000)            # milliseconds between one koi or another rising
    RISE_TIME = 3200                # milliseconds a rise lasts, up and back down
    QUIET = 0.45

    def __init__(self, scene, pond, on_ring):
        super().__init__(scene)
        self.pond = pond
        self.on_ring = on_ring
        self.squash = s(pond.HALF[1]) / s(pond.HALF[0])     # the pond's oval, as a circle squashed this much
        self.time = 0
        self.rise = Timer(self.RISE)
        self.rise.left = random.uniform(2000, self.RISE[1])
        self.fish = [self.new_fish(i) for i in range(self.COUNT)]

    def to_screen(self, u, v):
        return (self.pond.cx + u, self.pond.cy + v * self.squash)

    def new_fish(self, i):
        for attempt in range(40):
            angle, share = random.uniform(0, 2 * math.pi), random.uniform(0, 0.6)
            u = math.cos(angle) * s(self.pond.HALF[0]) * share
            v = math.sin(angle) * s(self.pond.HALF[0]) * share
            if self.pond.inside(*self.to_screen(u, v), 0.7):
                break
        heading = random.uniform(0, 2 * math.pi)
        length = s(random.uniform(*self.LENGTH))
        step = length / (self.SEGMENTS - 1)
        spine = [(u - math.cos(heading) * step * k, v - math.sin(heading) * step * k) for k in range(self.SEGMENTS)]
        colors = random.sample(range(4), 2)
        markings = [(random.randint(1, 5), random.choice((-0.5, 0, 0.5)), random.uniform(0.6, 1.1)) for k in range(random.randint(2, 4))]
        return {"spine": spine, "heading": heading, "length": length, "step": step, "turn": 0.0,
                "base": colors[0], "patch": colors[1], "patches": [random.randint(0, 6) for k in range(3)],
                "spots": markings if random.random() < 0.6 else [], "phase": random.uniform(0, 2 * math.pi),
                "speed": random.uniform(0.7, 1.2), "rising": None}

    def update(self, dt):
        self.time += dt
        seconds = dt / 1000
        if self.rise.tick(dt):
            fish = random.choice(self.fish)
            if fish["rising"] is None:
                fish["rising"] = 0.0
        for fish in self.fish:
            u, v = fish["spine"][0]
            # Wander, but turn back toward the middle before reaching the edge
            fish["turn"] += random.uniform(-1, 1) * self.TURN * seconds * 3
            fish["turn"] = max(-self.TURN, min(self.TURN, fish["turn"]))
            ahead = (u + math.cos(fish["heading"]) * fish["length"] * 1.3, v + math.sin(fish["heading"]) * fish["length"] * 1.3)
            if not self.pond.inside(*self.to_screen(*ahead), 0.8):
                home = math.atan2(-v, -u)
                fish["turn"] = math.copysign(self.TURN, math.sin(home - fish["heading"]))
            fish["heading"] += fish["turn"] * seconds
            speed = s(self.SPEED) * fish["speed"]
            u += math.cos(fish["heading"]) * speed * seconds
            v += math.sin(fish["heading"]) * speed * seconds
            # The rest of the body follows the head, each joint keeping its distance
            spine = [(u, v)]
            for k in range(1, self.SEGMENTS):
                px, py = spine[-1]
                qx, qy = fish["spine"][k]
                dx, dy = qx - px, qy - py
                distance = math.hypot(dx, dy) or 1
                spine.append((px + dx / distance * fish["step"], py + dy / distance * fish["step"]))
            fish["spine"] = spine
            fish["phase"] += seconds * (4 + 3 * fish["speed"])
            if fish["rising"] is not None:
                before = fish["rising"]
                fish["rising"] += dt
                if before < self.RISE_TIME / 2 <= fish["rising"]:
                    x, y = self.to_screen(*spine[0])
                    self.on_ring(x, y)
                if fish["rising"] > self.RISE_TIME:
                    fish["rising"] = None

    def outline(self, fish):
        # Both sides of the body, the tail swaying more than the head
        spine = fish["spine"]
        left, right = [], []
        for k, (u, v) in enumerate(spine):
            nxt = spine[min(k + 1, len(spine) - 1)]
            prv = spine[max(k - 1, 0)]
            du, dv = prv[0] - nxt[0], prv[1] - nxt[1]
            length = math.hypot(du, dv) or 1
            nu, nv = -dv / length, du / length
            sway = math.sin(fish["phase"] - k * 0.8) * fish["length"] * 0.05 * (k / len(spine))
            half = self.WIDTH[k] * fish["length"]
            cu, cv = u + nu * sway, v + nv * sway
            left.append(self.to_screen(cu + nu * half, cv + nv * half))
            right.append(self.to_screen(cu - nu * half, cv - nv * half))
        return left, right

    def draw(self, surface, palette):
        if "koi" not in palette:
            return
        colors = [pygame.Color(c) for c in palette["koi"]]
        spot = pygame.Color(palette.get("koi_spot", palette["text"]))
        for fish in self.fish:
            head = self.to_screen(*fish["spine"][0])
            rise = 0
            if fish["rising"] is not None:
                rise = math.sin(math.pi * fish["rising"] / self.RISE_TIME)
            strength = (self.DEPTH + (self.SURFACE - self.DEPTH) * rise) * self.scene.keep(head[0], self.QUIET * (1 - rise))
            water = self.pond.water_color(palette, head[1])

            def tint(color):
                return water.lerp(color, max(0, min(1, strength)))

            left, right = self.outline(fish)
            # Fins: two at the front, and the tail fanning out behind
            for side, points in ((1, left), (-1, right)):
                root = points[2]
                tip = (root[0] + (root[0] - (left[2][0] + right[2][0]) / 2) * 1.6,
                       root[1] + (root[1] - (left[2][1] + right[2][1]) / 2) * 1.6 + 1)
                pygame.draw.polygon(surface, tint(colors[fish["base"]]), [root, tip, points[3]])
            tail = self.to_screen(*fish["spine"][-1])
            back = fish["spine"][-1]
            before = fish["spine"][-2]
            du, dv = back[0] - before[0], back[1] - before[1]
            length = math.hypot(du, dv) or 1
            swing = math.sin(fish["phase"] - 6) * 0.5
            fins = []
            for spread in (-0.6, 0.6):
                angle = math.atan2(dv, du) + spread + swing
                fins.append(self.to_screen(back[0] + math.cos(angle) * fish["length"] * 0.22,
                                           back[1] + math.sin(angle) * fish["length"] * 0.22))
            pygame.draw.polygon(surface, tint(colors[fish["base"]]), [tail, fins[0], self.to_screen(back[0] + du / length * fish["length"] * 0.12,
                                                                                                    back[1] + dv / length * fish["length"] * 0.12), fins[1]])
            # Body, then its patches of a second color, then black spots
            pygame.draw.polygon(surface, tint(colors[fish["base"]]), left + right[::-1])
            for k in fish["patches"]:
                if k + 1 < len(left):
                    pygame.draw.polygon(surface, tint(colors[fish["patch"]]), [left[k], left[k + 1], right[k + 1], right[k]])
            for k, across, size in fish["spots"]:
                x = (left[k][0] + right[k][0]) / 2 + (left[k][0] - right[k][0]) * across * 0.4
                y = (left[k][1] + right[k][1]) / 2 + (left[k][1] - right[k][1]) * across * 0.4
                pygame.draw.circle(surface, tint(spot), (x, y), max(1, fish["length"] * 0.045 * size))


class LilyPads(Layer):
    # Two little clusters of lily pads near the pond's edges: round leaves with a notch,
    # lying flat (squashed like the pond), a darker rim and a vein or two, and a few pink
    # and white flowers. They rock very slightly. Painted once
    #
    # Palette colors it uses:
    #   "lily_pad", "lily_pad_dark"         the leaves and their rims and veins
    #   "lily_flower" (a list), "lily_middle"

    CLUSTERS = ((1.15, 0.72, 5), (-2.35, 0.7, 4))      # (direction from the pond's middle, share to its edge, pads)
    SIZE = (10, 16)                 # pad radius, pixels at the medium size
    FLOWERS = 0.35                  # share of pads with a flower

    def __init__(self, scene, pond):
        super().__init__(scene)
        self.pond = pond
        self.squash = s(pond.HALF[1]) / s(pond.HALF[0]) * 1.1
        self.pads = []
        for angle, share, count in self.CLUSTERS:
            cx, cy = pond.point(angle, share)
            for k in range(count):
                x, y = cx + random.uniform(-s(24), s(24)), cy + random.uniform(-s(8), s(8))
                if not pond.inside(x, y, 0.85):
                    continue
                r = s(random.uniform(*self.SIZE)) * scene.view.scale(y)
                self.pads.append({"x": x, "y": y, "r": r, "notch": random.uniform(0, 2 * math.pi),
                                  "flower": random.random() < self.FLOWERS, "pick": random.random()})
        self.pads.sort(key=lambda pad: pad["y"])
        self.image = None
        self.painted_palette = None

    def paint(self, palette):
        image = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pad = pygame.Color(palette.get("lily_pad", palette["muted"]))
        dark = pygame.Color(palette.get("lily_pad_dark", palette["muted"]))
        flowers = [pygame.Color(c) for c in palette.get("lily_flower", [palette["text"]])]
        middle = pygame.Color(palette.get("lily_middle", palette["accent"]))
        for leaf in self.pads:
            x, y, r, notch = leaf["x"], leaf["y"], leaf["r"], leaf["notch"]
            points = [(x, y)]
            for k in range(25):
                a = notch + 0.35 + (2 * math.pi - 0.7) * k / 24
                points.append((x + math.cos(a) * r, y + math.sin(a) * r * self.squash))
            pygame.draw.polygon(image, dark, [(px, py + 1) for px, py in points])
            pygame.draw.polygon(image, pad, points)
            pygame.draw.lines(image, dark, True, points, 1)
            for k in (1.6, 3.1, 4.6):
                a = notch + k
                pygame.draw.line(image, dark, (x, y), (x + math.cos(a) * r * 0.75, y + math.sin(a) * r * 0.75 * self.squash), 1)
            if leaf["flower"]:
                color = flowers[int(leaf["pick"] * len(flowers)) % len(flowers)]
                fx, fy = x + r * 0.15, y - r * 0.25
                for k in range(8):
                    a = k * math.pi / 4
                    tip = (fx + math.cos(a) * r * 0.55, fy + math.sin(a) * r * 0.55 * 0.6 - r * 0.12)
                    pygame.draw.polygon(image, color.lerp(dark, 0.12) if k % 2 else color,
                                        [(fx, fy - r * 0.1), tip, (fx + math.cos(a + 0.4) * r * 0.2, fy + math.sin(a + 0.4) * r * 0.12)])
                pygame.draw.circle(image, middle, (fx, fy - r * 0.12), max(1, r * 0.14))
        self.image = image
        self.painted_palette = palette

    def draw(self, surface, palette):
        if self.painted_palette is not palette:
            self.paint(palette)
        surface.blit(self.image, (0, 0))


class LanternShimmer(Layer):
    # At night: the stone lantern's flame flickering on the water at the near edge of the
    # pond, a cluster of little warm glints that come and go. Night only: needs
    # "lantern_glow" in the palette
    #
    # Palette colors it uses:
    #   "lantern_glow"

    COUNT = 16
    REACH = 34                      # how far the glints spread, pixels at the medium size

    def __init__(self, scene, pond, lantern):
        super().__init__(scene)
        self.pond = pond
        self.time = 0
        # Where the lantern is nearest the pond, a little way in from the edge
        angle = math.atan2((lantern.y - pond.cy) / s(pond.HALF[1]), (lantern.x - pond.cx) / s(pond.HALF[0]))
        self.center = pond.point(angle, 0.86)
        self.glints = []
        for i in range(self.COUNT):
            for attempt in range(20):
                x = self.center[0] + random.uniform(-1, 1) * s(self.REACH)
                y = self.center[1] + random.uniform(-0.6, 0.6) * s(self.REACH) * 0.5
                if pond.inside(x, y, 0.95):
                    break
            near = 1 - min(1, math.hypot(x - self.center[0], (y - self.center[1]) * 2) / s(self.REACH))
            self.glints.append((x, y, near, random.uniform(300, 900), random.uniform(0, 2 * math.pi), s(random.uniform(2, 5))))

    def update(self, dt):
        self.time += dt

    def draw(self, surface, palette):
        if "lantern_glow" not in palette:
            return
        glow = pygame.Color(palette["lantern_glow"])
        for x, y, near, period, phase, length in self.glints:
            flicker = 0.5 + 0.5 * math.sin(self.time / period * 2 * math.pi + phase)
            strength = near * flicker * 0.85
            if strength < 0.1:
                continue
            color = self.pond.water_color(palette, y).lerp(glow, strength)
            pygame.draw.line(surface, color, (x - length / 2, y), (x + length / 2, y), max(1, s(1)))
