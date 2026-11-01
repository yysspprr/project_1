# A snowy fir bough reaching in from the edge of the window, hung with icicles,
# sometimes with a bird sitting on it

import math

import random

import pygame

from partials.config import WIDTH, s
from partials.backgrounds.framing import Branch


class FirBough(Branch):
    # A fir branch loaded with snow, reaching in from the left or right edge of the window
    # at any height, as if from a tree standing just out of sight. It sways in the wind.
    # Short needles bristle along the limb and its twig,
    # lumps of snow sit on top, and icicles hang underneath. In sunshine (when the palette
    # has "melt") the icicles drip now and then. A bird perches on it: a robin by day that
    # turns and hops, or an owl at night that blinks (from the palette's "bird")
    #
    # Palette colors and values it uses:
    #   "branch"                the wood
    #   "needle"                the needles (falls back to "fir")
    #   "bough_snow"            the snow on top (falls back to "roof_snow", then "snow_top")
    #   "icicle"                the icicles (falls back to "flake")
    #   "melt"                  present (any value) when it's warm enough for icicles to drip
    #   "bird"                  "robin", "owl", or leave it out for no bird
    #   "robin_body", "robin_breast", "owl_body", "owl_eye"

    REACH = 125
    DROOP = 80
    LIMB_WIDTH = (8, 3)
    NEEDLE_STEP = 3                 # pixels between needle pairs along the wood
    NEEDLE_LENGTH = (9, 14)
    NEEDLE_ANGLE = (45, 70)         # degrees between a needle and the wood
    SNOW_LUMPS = 7
    ICICLES = 6
    ICICLE_LENGTH = (5, 14)

    DRIP_WAIT = (2000, 5000)
    DRIP_GROW = 900
    DRIP_FALL = 450
    DRIP_DROP = (120, 220)
    DRIP_SIZE = 1.5

    PERCH = (1, 0.45)               # where the bird sits: limb segment, how far along it
    BIRD_SIZE = 13                  # pixels at the medium size
    TURN_TIME = (2500, 7000)        # milliseconds between a robin turning around
    HOP_TIME = 260
    BLINK_TIME = (2000, 6000)       # milliseconds between an owl's blinks
    BLINK_LENGTH = 160
    ANGLE_STEP = 0.25               # the bough is painted once for every this many degrees of sway, then reused

    def __init__(self, scene, side="left", height=0, reach=None, droop=None, bird=True):
        # height: where along the edge it grows from, in pixels from the top
        # reach, droop: how far in it reaches and how far its tip hangs (pixels at the medium size)
        # bird: whether a bird perches on this one
        if reach is not None:
            self.REACH = reach
        if droop is not None:
            self.DROOP = droop
        super().__init__(scene, side)
        self.pivot = (self.pivot[0], height)
        self.has_bird = bird
        self.leaves = []            # a fir has needles instead
        self.needles = self.make_needles()
        self.lumps = self.make_lumps()
        self.icicles = self.make_icicles()
        self.melting = False
        self.facing = random.choice((-1, 1))
        self.turn_timer = random.randint(*self.TURN_TIME)
        self.hop = self.HOP_TIME
        self.blink_timer = random.randint(*self.BLINK_TIME)
        self.paintings = {}         # the bough painted at each angle it has swayed to
        self.painted_palette = None

    # ---- Building it ----

    def along(self, piece, segment, share):
        (x1, y1), (x2, y2) = piece[segment], piece[segment + 1]
        return (x1 + (x2 - x1) * share, y1 + (y2 - y1) * share)

    def direction(self, piece, segment):
        (x1, y1), (x2, y2) = piece[segment], piece[segment + 1]
        length = math.hypot(x2 - x1, y2 - y1) or 1
        return ((x2 - x1) / length, (y2 - y1) / length)

    def make_needles(self):
        # Pairs of short needles all along the wood, angled forward, one on each side
        needles = []
        for piece in (self.limb, self.twig):
            for segment in range(len(piece) - 1):
                (x1, y1), (x2, y2) = piece[segment], piece[segment + 1]
                steps = max(2, int(math.hypot(x2 - x1, y2 - y1) / s(self.NEEDLE_STEP)))
                dx, dy = self.direction(piece, segment)
                for k in range(steps):
                    bx, by = self.along(piece, segment, k / steps)
                    for side in (-1, 1):
                        turn = math.radians(random.uniform(*self.NEEDLE_ANGLE) * side)
                        nx = dx * math.cos(turn) - dy * math.sin(turn)
                        ny = dx * math.sin(turn) + dy * math.cos(turn)
                        length = s(random.uniform(*self.NEEDLE_LENGTH))
                        needles.append(((bx, by), (bx + nx * length, by + ny * length + s(1.5)),
                                        random.uniform(0, 0.25)))
        return needles

    def make_lumps(self):
        # Heaps of snow sitting on top of the limb: a few overlapping circles each
        lumps = []
        for i in range(self.SNOW_LUMPS):
            segment = random.randrange(len(self.limb) - 1)
            x, y = self.along(self.limb, segment, random.random())
            size = s(random.uniform(4, 7)) * (1 - 0.35 * segment / (len(self.limb) - 1))
            for k in range(3):
                lumps.append((x + (k - 1) * size * 0.9, y - size * 0.55 - (size * 0.3 if k == 1 else 0), size))
        return lumps

    def make_icicles(self):
        icicles = []
        for i in range(self.ICICLES):
            segment = random.randrange(len(self.limb) - 1)
            x, y = self.along(self.limb, segment, random.uniform(0.15, 0.9))
            icicles.append({"top": (x, y + s(2)), "length": s(random.uniform(*self.ICICLE_LENGTH)),
                            "width": s(random.uniform(1.5, 2.5))})
        return icicles

    # ---- Moving ----

    def update(self, dt):
        self.time += dt

        # Robin: turns around now and then, with a little hop
        self.turn_timer -= dt
        if self.turn_timer <= 0:
            self.facing = -self.facing
            self.hop = 0
            self.turn_timer = random.randint(*self.TURN_TIME)
        self.hop += dt

        # Owl: blinks now and then
        self.blink_timer -= dt
        if self.blink_timer < -self.BLINK_LENGTH:
            self.blink_timer = random.randint(*self.BLINK_TIME)

        # Icicles drip in the sun
        if self.drip is None:
            if self.melting:
                self.wait -= dt * max(0, self.scene.weather["light"])
            if self.wait <= 0:
                icicle = random.choice(self.icicles)
                tip = self.icicle_tip(icicle, self.sway())
                self.drip = {"icicle": icicle, "age": 0,
                             "landing": (tip[0], tip[1] + s(random.randint(*self.DRIP_DROP)))}
            return
        self.drip["age"] += dt
        if self.drip["age"] >= self.DRIP_GROW + self.DRIP_FALL:
            self.drip = None
            self.wait = random.randint(*self.DRIP_WAIT)

    def wobble(self):
        pass                        # the needles bristle enough as they are

    # ---- Drawing ----

    def icicle_tip(self, icicle, angle):
        x, y = icicle["top"]
        return self.place(x, y + icicle["length"], angle)

    def draw(self, surface, palette):
        # The bough itself, from a painting at (about) this angle; the bird and drips live on top
        angle = round(self.sway() / self.ANGLE_STEP) * self.ANGLE_STEP
        self.melting = "melt" in palette
        if self.painted_palette is not palette:
            self.paintings = {}
            self.painted_palette = palette
        if angle not in self.paintings:
            self.paintings[angle] = self.paint(palette, angle)
        surface.blit(self.paintings[angle], self.painted_at)

        self.draw_bird(surface, palette, angle)

        # A melting drip: gathers at an icicle's tip, then falls
        if self.drip is not None:
            ice = pygame.Color(palette.get("icicle", palette.get("flake", palette["text"])))
            tip = self.icicle_tip(self.drip["icicle"], angle)
            age = self.drip["age"]
            if age < self.DRIP_GROW:
                radius = s(self.DRIP_SIZE) * age / self.DRIP_GROW
                position = (tip[0], tip[1] + radius)
            else:
                fall = (age - self.DRIP_GROW) / self.DRIP_FALL
                radius = s(self.DRIP_SIZE)
                x, landing_y = self.drip["landing"]
                position = (x, tip[1] + (landing_y - tip[1]) * fall * fall)
            pygame.draw.circle(surface, ice, position, max(1, radius))

    def paint(self, palette, angle):
        # Needles, wood, icicles and snow, on a see-through image just big enough for the bough.
        # place() works in window positions, so the bough's root is moved for the painting
        width = s(self.REACH) + s(50)
        left = 0 if self.side > 0 else WIDTH - width
        top = int(self.pivot[1]) - s(30)
        image = pygame.Surface((width, s(self.DROOP) + s(100)), pygame.SRCALPHA)
        real_pivot = self.pivot
        self.pivot = (real_pivot[0] - left, real_pivot[1] - top)
        self.painted_at = (left, top)
        surface = image
        wood = pygame.Color(palette.get("branch", palette["muted"]))
        needle = pygame.Color(palette.get("needle", palette.get("fir", palette["muted"])))
        snow = pygame.Color(palette.get("bough_snow", palette.get("roof_snow", palette.get("snow_top", palette["bg"]))))
        ice = pygame.Color(palette.get("icicle", palette.get("flake", palette["text"])))
        black = pygame.Color(0, 0, 0)

        # Needles behind the wood
        line = max(1, s(2))
        for start, end, shade in self.needles:
            pygame.draw.line(surface, needle.lerp(black, shade), self.place(*start, angle), self.place(*end, angle), line)

        # The wood, thinner toward the tip
        thick, thin = s(self.LIMB_WIDTH[0]), s(self.LIMB_WIDTH[1])
        for piece, first, last in ((self.limb, thick, thin), (self.twig, thick * 0.5, thin)):
            for i in range(len(piece) - 1):
                share = i / (len(piece) - 1)
                width = max(1, round(first + (last - first) * share))
                a, b = self.place(*piece[i], angle), self.place(*piece[i + 1], angle)
                pygame.draw.line(surface, wood, a, b, width)
                pygame.draw.circle(surface, wood, b, width / 2)

        # Icicles: thin pointed triangles hanging straight down, with a bright edge
        for icicle in self.icicles:
            x, y = icicle["top"]
            half = icicle["width"] / 2
            top_left = self.place(x - half, y, angle)
            top_right = self.place(x + half, y, angle)
            tip = self.icicle_tip(icicle, angle)
            pygame.draw.polygon(surface, ice.lerp(wood, 0.15), [top_left, top_right, tip])
            pygame.draw.line(surface, ice, top_left, tip, 1)

        # Snow on top
        for x, y, size in self.lumps:
            pygame.draw.circle(surface, snow, self.place(x, y, angle), size)
        self.pivot = real_pivot
        return image

    def draw_bird(self, surface, palette, angle):
        kind = palette.get("bird")
        if not self.has_bird:
            return
        if kind not in ("robin", "owl"):
            return
        segment, share = self.PERCH
        px, py = self.along(self.limb, segment, share)
        x, y = self.place(px, py - s(1), angle)            # where its feet grip the branch
        size = s(self.BIRD_SIZE)
        if kind == "robin":
            self.draw_robin(surface, palette, x, y, size)
        else:
            self.draw_owl(surface, palette, x, y, size)

    def draw_robin(self, surface, palette, x, y, size):
        body = pygame.Color(palette.get("robin_body", "#6b5a4c"))
        breast = pygame.Color(palette.get("robin_breast", "#d4663a"))
        face = self.facing
        hop = 0
        if self.hop < self.HOP_TIME:
            hop = math.sin(math.pi * self.hop / self.HOP_TIME) * size * 0.4
        y -= hop
        # Tail sticking out behind, then a round body, a red breast, the head and a beak
        tail = [(x - face * size * 0.4, y - size * 0.5), (x - face * size * 1.1, y - size * 0.2),
                (x - face * size * 1.0, y - size * 0.05)]
        pygame.draw.polygon(surface, body, tail)
        pygame.draw.ellipse(surface, body, (x - size * 0.6, y - size * 0.95, size * 1.2, size * 0.9))
        pygame.draw.ellipse(surface, breast, (x - size * 0.15 + face * size * 0.15, y - size * 0.8,
                                              size * 0.55, size * 0.6))
        head = (x + face * size * 0.35, y - size * 1.0)
        pygame.draw.circle(surface, body, head, size * 0.35)
        pygame.draw.circle(surface, breast, (head[0] + face * size * 0.12, head[1] + size * 0.12), size * 0.18)
        beak = [(head[0] + face * size * 0.3, head[1] - size * 0.05), (head[0] + face * size * 0.55, head[1]),
                (head[0] + face * size * 0.3, head[1] + size * 0.08)]
        pygame.draw.polygon(surface, pygame.Color("#3a2e26"), beak)
        pygame.draw.circle(surface, pygame.Color("#1a1512"), (head[0] + face * size * 0.12, head[1] - size * 0.05),
                           max(1, size * 0.07))

    def draw_owl(self, surface, palette, x, y, size):
        body = pygame.Color(palette.get("owl_body", "#4a3e36"))
        eye = pygame.Color(palette.get("owl_eye", "#f0c860"))
        size *= 1.15
        # A round, upright body with ear tufts, and two big eyes that blink
        pygame.draw.ellipse(surface, body, (x - size * 0.55, y - size * 1.5, size * 1.1, size * 1.5))
        for side in (-1, 1):
            tuft = [(x + side * size * 0.15, y - size * 1.4), (x + side * size * 0.5, y - size * 1.7),
                    (x + side * size * 0.45, y - size * 1.3)]
            pygame.draw.polygon(surface, body, tuft)
        blinking = self.blink_timer <= 0
        for side in (-1, 1):
            center = (x + side * size * 0.22, y - size * 1.05)
            if blinking:
                pygame.draw.line(surface, eye.lerp(body, 0.5), (center[0] - size * 0.14, center[1]),
                                 (center[0] + size * 0.14, center[1]), max(1, s(1)))
            else:
                pygame.draw.circle(surface, eye, center, size * 0.17)
                pygame.draw.circle(surface, pygame.Color("#120e0c"), center, max(1, size * 0.07))
