# Scenery close to us that frames the picture from the edges: reeds growing up from a
# bottom corner, a branch reaching in from a top corner, and lily pads near a side.
# All of it stays in the corners and margins, out of the game's way

import math

import random

import pygame

from partials.config import WIDTH, HEIGHT, s
from partials.backgrounds.base import Layer
from partials.backgrounds.helpers import Swell, make_jitter


class Reeds(Layer):
    # A clump of reeds and grass in a bottom corner. They sway in the wind (the scene's
    # weather["wind"]), bend further when it blows harder, and flinch now and then in
    # heavy rain as drops hit them. Some have a cattail at the top. Each grows out of the
    # water a little above the bottom of the window, with a faint ring where it meets the
    # water, and casts a shadow that lies flat on the water. Its direction comes from where
    # the sun or moon is (the scene's weather["light_x"] and ["light_y"]): in perspective,
    # shadows on the water all point away from the spot on the horizon right below the light,
    # and the lower the light, the longer they are. Stronger when the light is bright
    # (the scene's weather["light"])
    #
    # Palette colors and values it uses:
    #   "reed"          stems and blades (falls back to "muted")
    #   "reed_head"     the cattails (falls back to "reed")
    #   "shadow"        how dark shadows are in this light, 0-1 (falls back to SHADOW)
    #   "ripple"        the ring around each stem's base

    STEMS = 9
    BLADES = 12                     # thinner grass in front of the stems
    STEM_HEIGHT = (80, 170)         # pixels at the medium size
    BLADE_HEIGHT = (30, 85)
    SPREAD = 75                     # how far in from the corner they grow
    CATTAILS = 0.45                 # share of the stems with a cattail
    STEM_WIDTH = 3
    BLADE_WIDTH = 2
    POINTS = 7                      # points along each stem
    LEAN = (-14, 10)                # how far a top leans: negative is in toward the middle

    SWAY = 4                        # how far the tops sway at a normal breeze, in pixels
    SWAY_TIME = (1800, 3200)        # milliseconds for one sway back and forth
    BEND = 6                        # how much further they lean for each step up in wind
    FLINCH = 6                      # how far a top jumps when a drop hits it
    FLINCH_RATE = 1.2               # flinches per second for each stem, in a full storm
    FLINCH_FADE = 250               # milliseconds for a flinch to halve
    JITTER = 0.5                    # outline wobble, in pixels
    ROOT = (34, 72)                 # how far above the bottom of the window the stems come out of the water,
                                    # high enough that their shadows have room to show
    SHADOW = 0.25                   # how dark the shadow is in full light (0 = none, 1 = black)
    CAST_LENGTH = 0.45              # shadow length, in stem heights, with the light 60% of the way up the sky
    CAST = (-0.6, 0.22)             # without a sun or moon: the shadow of a point h pixels up the stem
                                    # lands this many h's sideways and down from the base
    RING = (5, 1.6)                 # half the width and height of the ring at each stem's base

    def __init__(self, scene, side="right", size=1, count=1):
        # size: how tall and wide the clump is, compared to normal
        # count: how many stems and blades, compared to normal
        super().__init__(scene)
        self.side = 1 if side == "left" else -1     # which way is "in from the corner"
        self.corner_x = 0 if side == "left" else WIDTH
        self.size = size
        self.time = 0
        self.stems = []
        for i in range(round(self.STEMS * count)):
            self.stems.append(self.make_stem(self.STEM_HEIGHT, self.STEM_WIDTH, random.random() < self.CATTAILS))
        for i in range(round(self.BLADES * count)):
            self.stems.append(self.make_stem(self.BLADE_HEIGHT, self.BLADE_WIDTH, False))
        self.stems.sort(key=lambda stem: stem["base"])      # further back first, so nearer ones overlap them

    def make_stem(self, heights, width, cattail):
        return {
            "x": self.corner_x + self.side * s(random.uniform(-5, self.SPREAD * self.size)),
            "base": HEIGHT - s(random.uniform(*self.ROOT) * self.size),
            "height": s(random.randint(*heights) * self.size),
            "lean": s(random.uniform(*self.LEAN)),
            "width": s(width),
            "cattail": cattail,
            "period": random.randint(*self.SWAY_TIME),
            "phase": random.uniform(0, 2 * math.pi),
            "kick": 0,
            "jitter": make_jitter(self.POINTS, self.JITTER),
        }

    def update(self, dt):
        self.time += dt
        fade = 0.5 ** (dt / self.FLINCH_FADE)
        chance = self.FLINCH_RATE * self.scene.weather["storm"] * dt / 1000
        for stem in self.stems:
            stem["kick"] *= fade
            if random.random() < chance:
                stem["kick"] += s(self.FLINCH) * random.choice((-1, 1))

    def wobble(self):
        for stem in self.stems:
            stem["jitter"] = make_jitter(self.POINTS, self.JITTER)

    def stem_points(self, stem):
        # From where it comes out of the water up, curving more toward the top
        wind = self.scene.weather["wind"]
        sway = math.sin(self.time / stem["period"] * 2 * math.pi + stem["phase"]) * s(self.SWAY) * wind
        # The wind blows the same way as the rain slants: toward the right
        top_shift = self.side * stem["lean"] + s(self.BEND) * (wind - 1) + sway + stem["kick"]
        points = []
        for i in range(self.POINTS):
            t = i / (self.POINTS - 1)
            points.append((stem["x"] + top_shift * t * t + stem["jitter"][i],
                           stem["base"] - stem["height"] * t))
        return points

    def cast_direction(self, base_x, base_y):
        # How far sideways and down the shadow of one pixel of stem falls
        weather = self.scene.weather
        light_x = weather.get("light_x")
        light_y = weather.get("light_y")
        horizon = self.scene.view.horizon
        if light_x is None or light_y is None or horizon <= 0:
            return self.CAST

        # Away from the point on the horizon right below the light
        away_x = base_x - light_x
        away_y = base_y - horizon
        distance = math.hypot(away_x, away_y) or 1

        # Higher in the sky: shorter shadows
        height = max(0.15, (horizon - light_y) / horizon)
        length = self.CAST_LENGTH * 0.6 / height
        return (away_x / distance * length, away_y / distance * length)

    def cast(self, stem, points):
        # The stem's shadow, lying flat on the water: each point lands further from the base
        # the higher up the stem it is, in the direction away from the light
        base_x, base_y = points[0]
        along_x, along_y = self.cast_direction(base_x, base_y)
        shadow = []
        for x, y in points:
            up = base_y - y
            shadow.append((x + up * along_x, base_y + up * along_y))
        return shadow

    def draw_stem(self, surface, stem, points, reed, head):
        pygame.draw.lines(surface, reed, False, points, stem["width"])
        if stem["cattail"]:
            # A fat rounded head just below the tip
            (x1, y1), (x2, y2) = points[-3], points[-2]
            width = s(6)
            pygame.draw.line(surface, head, (x1, y1), (x2, y2), width)
            pygame.draw.circle(surface, head, (x1, y1), width / 2)
            pygame.draw.circle(surface, head, (x2, y2), width / 2)

    def draw(self, surface, palette):
        reed = pygame.Color(palette.get("reed", palette["muted"]))
        head = pygame.Color(palette.get("reed_head", palette.get("reed", palette["muted"])))
        all_points = [self.stem_points(stem) for stem in self.stems]

        # Shadows first, all of them, so no shadow falls on top of another reed
        darkness = palette.get("shadow", self.SHADOW) * max(0, min(1, self.scene.weather["light"]))
        if darkness > 0.01:
            black = pygame.Color(0, 0, 0)
            for stem, points in zip(self.stems, all_points):
                water = self.scene.color_at(palette, stem["base"])
                shade = water.lerp(black, darkness)
                self.draw_stem(surface, stem, self.cast(stem, points), shade, shade)

        ripple = pygame.Color(palette.get("ripple", palette["muted"]))
        for stem, points in zip(self.stems, all_points):
            # A faint ring where the stem meets the water, then the stem itself
            water = self.scene.color_at(palette, stem["base"])
            x, y = points[0]
            half_w, half_h = s(self.RING[0]), s(self.RING[1])
            pygame.draw.ellipse(surface, water.lerp(ripple, 0.6), (x - half_w, y - half_h, half_w * 2, half_h * 2), 1)
            self.draw_stem(surface, stem, points, reed, head)


class Branch(Layer):
    # A leafy branch reaching in from a top corner. It sways a little in the wind, and
    # drops of water gather on its leaf tips, fall, and make ripples where they land
    # (through on_ripple). It drips more in a storm
    #
    # Palette colors it uses:
    #   "branch"        the wood (falls back to "muted")
    #   "leaf"          the leaves (falls back to "branch")
    #   "rain"          the drips (falls back to "text")

    REACH = 105                     # how far in from the corner it reaches, in pixels at the medium size
    DROOP = 60                      # how far down its tip hangs
    LIMB_WIDTH = (7, 2)             # thick at the corner, thin at the tip
    LEAVES = 20
    LEAF_LENGTH = (12, 19)
    SWAY = 1.5                      # degrees it rocks back and forth at a normal breeze
    SWAY_TIME = 3500                # milliseconds for one rock
    JITTER = 0.06                   # leaf outline wobble, as a share of its size

    DRIP_WAIT = (2500, 6000)        # milliseconds between drips when it's calm
    STORM_DRIPS = 3                 # in a full storm, it drips this many times as often
    DRIP_GROW = 700                 # milliseconds a drop takes to gather on a leaf tip
    DRIP_FALL = 420                 # milliseconds to fall
    DRIP_DROP = (130, 230)          # how far it falls before it hits the water, in pixels
    DRIP_SIZE = 1.8                 # radius of a full drop

    def __init__(self, scene, side="left", on_ripple=None):
        super().__init__(scene)
        self.on_ripple = on_ripple
        self.side = 1 if side == "left" else -1
        self.pivot = (0 if side == "left" else WIDTH, 0)
        self.time = 0

        # The limb and a side twig, as (x, y) points measured from the corner
        reach, droop = s(self.REACH), s(self.DROOP)
        self.limb = [(-s(10), -s(6)), (reach * 0.35, droop * 0.35), (reach * 0.7, droop * 0.75), (reach, droop)]
        fork = self.limb[1]
        self.twig = [fork, (fork[0] + s(18), fork[1] + s(26)), (fork[0] + s(26), fork[1] + s(48))]

        # Leaves hang off both: which piece, which segment, how far along, angle, length
        self.leaves = []
        for i in range(self.LEAVES):
            piece = self.limb if random.random() < 0.65 else self.twig
            segment = random.randrange(len(piece) - 1)
            self.leaves.append({
                "piece": piece,
                "segment": segment,
                "along": random.random(),
                "angle": random.uniform(35, 145),           # mostly hanging down
                "length": s(random.uniform(*self.LEAF_LENGTH)),
                "shade": random.uniform(0, 0.25),
                "jitter": make_jitter(4, self.JITTER),
            })

        self.drip = None
        self.wait = random.randint(*self.DRIP_WAIT)

    def place(self, x, y, angle):
        # A point measured from the corner, turned by the sway and put on the screen
        turn = math.radians(angle)
        cos, sin = math.cos(turn), math.sin(turn)
        return (self.pivot[0] + self.side * (x * cos - y * sin), self.pivot[1] + x * sin + y * cos)

    def sway(self):
        wind = self.scene.weather["wind"]
        return math.sin(self.time / self.SWAY_TIME * 2 * math.pi) * self.SWAY * wind + 0.8 * (wind - 1)

    def leaf_shape(self, leaf, angle):
        piece = leaf["piece"]
        (x1, y1), (x2, y2) = piece[leaf["segment"]], piece[leaf["segment"] + 1]
        x = x1 + (x2 - x1) * leaf["along"]
        y = y1 + (y2 - y1) * leaf["along"]
        turn = math.radians(leaf["angle"])
        length = leaf["length"]
        tip = (x + math.cos(turn) * length * 0.6, y + math.sin(turn) * length)
        middle = ((x + tip[0]) / 2, (y + tip[1]) / 2)
        across = (-(tip[1] - y) * 0.28, (tip[0] - x) * 0.28)
        shape = [(x, y), (middle[0] + across[0], middle[1] + across[1]), tip,
                 (middle[0] - across[0], middle[1] - across[1])]
        placed = []
        for i, (px, py) in enumerate(shape):
            push = 1 + leaf["jitter"][i]
            placed.append(self.place(x + (px - x) * push, y + (py - y) * push, angle))
        return placed

    def update(self, dt):
        self.time += dt
        if self.drip is None:
            self.wait -= dt * (1 + (self.STORM_DRIPS - 1) * self.scene.weather["storm"])
            if self.wait <= 0:
                leaf = random.choice(self.leaves)
                tip = self.leaf_shape(leaf, self.sway())[2]
                self.drip = {"leaf": leaf, "age": 0,
                             "landing": (tip[0], tip[1] + s(random.randint(*self.DRIP_DROP)))}
            return

        self.drip["age"] += dt
        if self.drip["age"] >= self.DRIP_GROW + self.DRIP_FALL:
            x, y = self.drip["landing"]
            if self.on_ripple is not None:
                self.on_ripple(x, y, size=0.7, echoes=1)
            self.drip = None
            self.wait = random.randint(*self.DRIP_WAIT)

    def wobble(self):
        for leaf in self.leaves:
            leaf["jitter"] = make_jitter(4, self.JITTER)

    def draw(self, surface, palette):
        angle = self.sway()
        wood = pygame.Color(palette.get("branch", palette["muted"]))
        leaf_color = pygame.Color(palette.get("leaf", palette.get("branch", palette["muted"])))
        black = pygame.Color(0, 0, 0)

        # The limb gets thinner toward the tip, one segment at a time
        thick, thin = s(self.LIMB_WIDTH[0]), s(self.LIMB_WIDTH[1])
        for piece, start, end in ((self.limb, thick, thin), (self.twig, thick * 0.5, thin)):
            for i in range(len(piece) - 1):
                share = i / (len(piece) - 1)
                width = max(1, round(start + (end - start) * share))
                a = self.place(*piece[i], angle)
                b = self.place(*piece[i + 1], angle)
                pygame.draw.line(surface, wood, a, b, width)
                pygame.draw.circle(surface, wood, b, width / 2)

        for leaf in self.leaves:
            pygame.draw.polygon(surface, leaf_color.lerp(black, leaf["shade"]), self.leaf_shape(leaf, angle))

        # The drip: gathers on a leaf tip, then falls, speeding up
        if self.drip is not None:
            tip = self.leaf_shape(self.drip["leaf"], angle)[2]
            drip_color = pygame.Color(palette.get("rain", palette["text"]))
            age = self.drip["age"]
            if age < self.DRIP_GROW:
                radius = s(self.DRIP_SIZE) * age / self.DRIP_GROW
                position = (tip[0], tip[1] + radius)
            else:
                fall = (age - self.DRIP_GROW) / self.DRIP_FALL
                radius = s(self.DRIP_SIZE)
                x, landing_y = self.drip["landing"]
                position = (x, tip[1] + radius + (landing_y - tip[1]) * fall * fall)
            pygame.draw.circle(surface, drip_color, position, max(1, radius))


class LilyPads(Layer):
    # A cluster of lily pads near one side. They're rooted, so they don't drift away:
    # they turn a little back and forth, bob when a drop lands close by, and a drop
    # landing right on one makes it dip and ripple (nudge() says when that happened).
    # One of them has a flower. They cast a soft shadow, like the floating debris
    #
    # Palette colors it uses:
    #   "pad", "pad_edge"           the pads and their outline (fall back to "muted")
    #   "flower", "flower_middle"   the flower (no flower without "flower")

    COUNT = 4
    PLACE = (0.09, 0.55)            # the cluster's middle: share of the width, share of the way down the water
    SPREAD = (35, 18)               # how far the pads spread around it, in pixels at the medium size
    SIZE = (17, 25)                 # pad radius up close
    NOTCH = 0.35                    # half the notch's width, in radians
    POINTS = 22                     # points around each pad's edge
    TURN = 6                        # most degrees a pad turns back and forth
    LINE_WIDTH = 1
    SHADOW = 0.18                   # how dark the shadow is (0 = none, 1 = black)
    SHADOW_OFFSET = 2.5             # how far down the shadow falls, up close
    REACH = 30                      # a drop this close makes it bob, up close
    BOB_TIME = 700
    BOB_DEPTH = 2
    HIT_BOB = 2.2                   # a drop right on it makes it bob this much harder
    JITTER = 0.04
    FLOWER = 4                      # petal size up close

    def __init__(self, scene, side="left", on_ripple=None):
        super().__init__(scene)
        self.on_ripple = on_ripple
        view = scene.view
        across = self.PLACE[0] if side == "left" else 1 - self.PLACE[0]
        middle_x = WIDTH * across
        middle_y = view.horizon + (HEIGHT - view.horizon) * self.PLACE[1]

        self.pads = []
        for i in range(self.COUNT):
            self.pads.append({
                "x": middle_x + s(random.uniform(-1, 1) * self.SPREAD[0]),
                "y": middle_y + s(random.uniform(-1, 1) * self.SPREAD[1]),
                "size": s(random.uniform(*self.SIZE)),
                "notch": random.uniform(0, 360),
                "turn": Swell(-self.TURN, self.TURN, (4000, 9000)),
                "bob": self.BOB_TIME,
                "bob_size": 1,
                "flower": i == 0,
                "jitter": make_jitter(self.POINTS, self.JITTER),
            })
        self.pads.sort(key=lambda pad: pad["y"])        # far ones first, so near ones overlap them

    def shape(self, pad):
        # A disc with a notch cut in, in its own units around (0, 0)
        points = [(0, 0)]
        for i in range(self.POINTS):
            angle = self.NOTCH + (2 * math.pi - 2 * self.NOTCH) * i / (self.POINTS - 1)
            push = 1 + pad["jitter"][i]
            points.append((math.cos(angle) * push, math.sin(angle) * push))
        return points

    def nudge(self, x, y):
        # Something landed at (x, y): bob the pads close by. True if it landed right on one
        view = self.scene.view
        hit_any = False
        for pad in self.pads:
            dx = pad["x"] - x
            dy = (pad["y"] - y) / view.flatten(pad["y"])
            distance = math.hypot(dx, dy)
            reach = s(self.REACH) * view.scale(pad["y"])
            if distance < pad["size"] * view.scale(pad["y"]):
                hit_any = True
                pad["bob"] = 0
                pad["bob_size"] = self.HIT_BOB
                if self.on_ripple is not None:
                    self.on_ripple(pad["x"], pad["y"], size=0.9, echoes=1, splash=False)
            elif distance < reach + pad["size"]:
                pad["bob"] = 0
                pad["bob_size"] = 1 - distance / (reach + pad["size"])
        return hit_any

    def update(self, dt):
        for pad in self.pads:
            pad["turn"].update(dt)
            pad["bob"] += dt

    def wobble(self):
        for pad in self.pads:
            pad["jitter"] = make_jitter(self.POINTS, self.JITTER)

    def draw(self, surface, palette):
        view = self.scene.view
        fill = pygame.Color(palette.get("pad", palette["muted"]))
        edge = pygame.Color(palette.get("pad_edge", palette["muted"]))
        black = pygame.Color(0, 0, 0)

        for pad in self.pads:
            scale = view.scale(pad["y"])
            bob = 0
            if pad["bob"] < self.BOB_TIME:
                progress = pad["bob"] / self.BOB_TIME
                bob = math.sin(progress * math.pi * 2) * (1 - progress) * s(self.BOB_DEPTH) * pad["bob_size"] * scale
            y = pad["y"] + bob
            angle = pad["notch"] + pad["turn"].value
            points = view.lay_flat(self.shape(pad), pad["x"], y, angle, pad["size"])

            water = self.scene.color_at(palette, pad["y"])
            drop = s(self.SHADOW_OFFSET) * scale
            shadow = [(px, py + drop) for px, py in points]
            pygame.draw.polygon(surface, water.lerp(black, self.SHADOW), shadow)
            pygame.draw.polygon(surface, fill, points)
            pygame.draw.lines(surface, edge, True, points, max(1, round(s(self.LINE_WIDTH) * scale)))

            if pad["flower"] and palette.get("flower"):
                self.draw_flower(surface, palette, pad["x"], y, scale)

    def draw_flower(self, surface, palette, x, y, scale):
        # A few petals standing up around a yellow middle, on top of the pad
        petal = pygame.Color(palette["flower"])
        middle = pygame.Color(palette.get("flower_middle", palette["flower"]))
        size = s(self.FLOWER) * scale
        for i in range(6):
            angle = 2 * math.pi * i / 6
            px = x + math.cos(angle) * size
            py = y - size * 0.6 + math.sin(angle) * size * 0.45
            pygame.draw.ellipse(surface, petal, (px - size * 0.7, py - size * 0.5, size * 1.4, size))
        pygame.draw.circle(surface, middle, (x, y - size * 0.7), max(1, size * 0.45))
