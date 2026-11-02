# Life in the snow: tracks pressed into it, a fox that comes by now and then to hunt
# mice under the snow, and, rarely, a night visitor in the sky

import math

import random

import pygame

from partials.config import WIDTH, s
from partials.backgrounds.base import Layer


class Tracks(Layer):
    # Prints pressed into the snow, which slowly fill in again: quicker while it's
    # snowing (the scene's weather["storm"]). Anything can press one with press()
    #
    # Palette colors it uses:
    #   "track"         the prints (falls back to "snow_shadow")

    FILL = 45000                    # milliseconds for a print to fill in when it isn't snowing
    STORM_FILL = 4                  # in a full storm, prints fill in this many times as fast
    STRENGTH = 0.55

    def __init__(self, scene):
        super().__init__(scene)
        self.prints = []

    def press(self, x, y, size, age=0):
        # A print at (x, y), size wide (in pixels, already sized for its distance)
        self.prints.append({"x": x, "y": y, "size": size, "age": age})

    def update(self, dt):
        rate = 1 + (self.STORM_FILL - 1) * self.scene.weather["storm"]
        for track in self.prints:
            track["age"] += dt * rate
        self.prints = [track for track in self.prints if track["age"] < self.FILL]

    def draw(self, surface, palette):
        view = self.scene.view
        mark = pygame.Color(palette.get("track", palette.get("snow_shadow", palette["muted"])))
        for track in self.prints:
            fresh = 1 - track["age"] / self.FILL
            behind = self.scene.color_at(palette, track["y"])
            color = behind.lerp(mark, self.STRENGTH * fresh)
            width = track["size"]
            height = max(1, width * view.flatten(track["y"]) * 1.6)
            pygame.draw.ellipse(surface, color, (track["x"] - width / 2, track["y"] - height / 2, width, height))


class Fox(Layer):
    # Every so often a fox trots in from one side and stops in the margin to listen for
    # mice under the snow. It crouches, leaps in an arc and dives head first into the snow,
    # wiggles there with its tail in the air, pops back out and trots off the way it came.
    # It leaves paw prints and a hole where it dove (through a Tracks layer), and comes by
    # less often while it's snowing
    #
    # Palette colors it uses:
    #   "fox"           its coat (no fox without it)
    #   "fox_light"     the white of its chest and tail tip
    #   "fox_dark"      legs, ear tips and nose
    #   "fox_shadow"    the shadow under it (falls back to "snow_shadow")
    #   "snow_lit"      the snow it throws up when it dives (falls back to "snow_top")

    WAIT = (25000, 60000)           # milliseconds between visits when it's calm
    STORM_WAIT = 3                  # in a full storm, the wait is this many times longer
    DEPTH = (0.03, 0.09)            # how far away it hunts: 0 = right in front of us, 1 = the horizon
                                    # (in front of the pond, so it hunts on snow, not ice)
    LENGTH = 40                     # nose to tail, in pixels as if up close
    SPEED = 55                      # trotting speed, pixels per second as if up close
    STRIDE = 0.28                   # paw print spacing, in fox lengths
    INSIDE = (30, 60)               # how far in from the edge it stops to hunt

    LISTEN = (1200, 2400)           # how long it stands listening
    CROUCH = 400
    LEAP = 650
    LEAP_HEIGHT = 0.55              # in fox lengths
    LEAP_DISTANCE = 0.9
    DIVE = (900, 1600)              # how long it stays head-down in the snow
    EMERGE = 450
    QUIET = 0.4                     # how much it fades behind the game's text (it's solid: only a little)

    def __init__(self, scene, tracks=None):
        super().__init__(scene)
        self.tracks = tracks
        self.state = "away"
        self.timer = random.randint(*self.WAIT) // 3        # the first visit comes sooner
        self.puffs = []

    # ---- A visit ----

    def start_visit(self):
        view = self.scene.view
        self.facing = random.choice((-1, 1))                # 1: coming in from the left, facing right
        self.y = view.height_at(random.uniform(*self.DEPTH))
        self.scale = view.scale(self.y)
        self.length = s(self.LENGTH) * self.scale
        edge = -self.length if self.facing > 0 else WIDTH + self.length
        self.x = edge
        self.home = edge
        inside = s(random.uniform(*self.INSIDE))
        self.goal = inside if self.facing > 0 else WIDTH - inside
        self.walked = 0
        self.step = 0                                       # where it is in its trot cycle
        self.pitch = 0                                      # nose up (-) or down (+), in degrees
        self.lift = 0                                       # how high off the ground, in pixels
        self.state = "trot_in"

    def trot(self, dt, target):
        # Move toward target at a trot, pressing paw prints as it goes; True once it's there
        speed = s(self.SPEED) * self.scale * dt / 1000
        distance = target - self.x
        move = max(-speed, min(speed, distance))
        self.x += move
        self.walked += abs(move)
        self.step += abs(move) / (self.length * self.STRIDE) * math.pi
        if self.tracks is not None and self.walked >= self.length * self.STRIDE:
            self.walked = 0
            side = 1 if int(self.step / math.pi) % 2 else -1
            self.tracks.press(self.x, self.y + side * self.length * 0.06 * self.scene.view.flatten(self.y),
                              self.length * 0.07)
        return abs(distance) <= speed

    def update(self, dt):
        if self.state == "away":
            storm = self.scene.weather["storm"]
            self.timer -= dt / (1 + (self.STORM_WAIT - 1) * storm)
            if self.timer <= 0:
                self.start_visit()
            return

        self.timer -= dt
        for puff in self.puffs:
            puff["age"] += dt
        self.puffs = [puff for puff in self.puffs if puff["age"] < puff["life"]]

        if self.state == "trot_in":
            if self.trot(dt, self.goal):
                self.state, self.timer = "listen", random.randint(*self.LISTEN)
        elif self.state == "listen":
            if self.timer <= 0:
                self.state, self.timer = "crouch", self.CROUCH
        elif self.state == "crouch":
            if self.timer <= 0:
                self.state, self.timer = "leap", self.LEAP
                self.leap_from = self.x
        elif self.state == "leap":
            t = 1 - max(0, self.timer) / self.LEAP
            self.x = self.leap_from + self.facing * self.length * self.LEAP_DISTANCE * t
            self.lift = math.sin(math.pi * t) * self.length * self.LEAP_HEIGHT
            self.pitch = -25 + 90 * t                       # nose up as it springs, nose down as it falls
            if self.timer <= 0:
                self.lift, self.pitch = 0, 65
                self.state, self.timer = "dive", random.randint(*self.DIVE)
                self.splash()
        elif self.state == "dive":
            if self.timer <= 0:
                self.state, self.timer = "emerge", self.EMERGE
        elif self.state == "emerge":
            t = 1 - max(0, self.timer) / self.EMERGE
            self.pitch = 65 * (1 - t)
            if self.timer <= 0:
                self.pitch = 0
                if self.tracks is not None:
                    self.tracks.press(self.head_x(), self.y, self.length * 0.3)    # the hole it made
                self.facing = -self.facing
                self.state = "trot_out"
        elif self.state == "trot_out":
            if self.trot(dt, self.home):
                self.state = "away"
                self.timer = random.randint(*self.WAIT)

    def head_x(self):
        return self.x + self.facing * self.length * 0.4

    def splash(self):
        # Snow thrown up where it dives in
        for i in range(8):
            self.puffs.append({"x": self.head_x(), "y": self.y, "age": 0, "life": random.randint(350, 700),
                               "dx": random.uniform(-1, 1) * self.length * 0.5,
                               "rise": random.uniform(0.3, 0.7) * self.length})

    # ---- Drawing ----

    def place(self, u, v):
        # A point on the fox (u forward, v up, in fox lengths) on the screen, after its
        # pitch (turning around the middle of its body), facing and lift
        turn = math.radians(self.pitch)
        cu, cv = u, v - 0.45
        ru = cu * math.cos(turn) - cv * math.sin(turn)
        rv = cu * math.sin(turn) * -1 + cv * math.cos(turn)
        return (self.x + self.facing * ru * self.length,
                self.y - self.lift - (rv + 0.45) * self.length)

    def shape(self, points):
        return [self.place(u, v) for u, v in points]

    def draw(self, surface, palette):
        if self.state == "away" or "fox" not in palette:
            return
        coat = pygame.Color(palette["fox"])
        light = pygame.Color(palette.get("fox_light", "#f2efe8"))
        dark = pygame.Color(palette.get("fox_dark", "#2a1d17"))
        keep = self.scene.keep(self.x, self.QUIET)
        behind = self.scene.color_at(palette, self.y)
        coat, light, dark = behind.lerp(coat, keep), behind.lerp(light, keep), behind.lerp(dark, keep)

        # Its shadow on the snow, smaller the higher it leaps
        shadow = pygame.Color(palette.get("fox_shadow", palette.get("snow_shadow", palette["muted"])))
        width = self.length * 0.8 * (1 - 0.4 * self.lift / max(self.length, 1))
        height = max(1, width * self.scene.view.flatten(self.y) * 0.5)
        pygame.draw.ellipse(surface, behind.lerp(shadow, 0.5), (self.x - width / 2, self.y - height / 2, width, height))

        # Legs: swinging while it trots, tucked in while it leaps
        line = max(1, round(self.length * 0.05))
        trotting = self.state in ("trot_in", "trot_out")
        crouch = 0.08 if self.state == "crouch" else 0
        for hip, offset in ((0.2, 0), (0.24, math.pi), (-0.18, math.pi), (-0.22, 0)):
            swing = math.sin(self.step + offset) * 0.09 if trotting else 0
            foot_v = 0.2 if self.state in ("leap", "dive") else 0
            pygame.draw.line(surface, dark, self.place(hip, 0.38 - crouch), self.place(hip + swing, foot_v), line)

        # Bushy tail with a white tip
        tail = [(-0.26, 0.52), (-0.55, 0.58), (-0.8, 0.46), (-0.86, 0.36), (-0.62, 0.38), (-0.3, 0.42)]
        if self.state == "dive":
            wag = math.sin(self.timer / 90) * 0.06          # it wiggles while it digs
            tail = [(u, v + wag * (-u)) for u, v in tail]
        pygame.draw.polygon(surface, coat, self.shape(tail))
        pygame.draw.circle(surface, light, self.place(tail[3][0] + 0.03, tail[3][1] + 0.03), self.length * 0.055)

        # Body, chest, head, ears, snout
        body = []
        for k in range(12):
            angle = 2 * math.pi * k / 12
            body.append((math.cos(angle) * 0.32, 0.45 - crouch + math.sin(angle) * 0.13))
        pygame.draw.polygon(surface, coat, self.shape(body))
        pygame.draw.circle(surface, light, self.place(0.27, 0.4 - crouch), self.length * 0.06)

        tilt = math.sin(self.timer / 260) * 0.03 if self.state == "listen" else 0
        head = (0.38, 0.6 - crouch + tilt)
        pygame.draw.circle(surface, coat, self.place(*head), self.length * 0.1)
        snout = [(head[0] + 0.05, head[1] + 0.03), (head[0] + 0.21, head[1] - 0.03), (head[0] + 0.05, head[1] - 0.06)]
        pygame.draw.polygon(surface, coat, self.shape(snout))
        pygame.draw.circle(surface, dark, self.place(head[0] + 0.2, head[1] - 0.03), max(1, self.length * 0.025))
        for ear in (-0.04, 0.03):
            points = [(head[0] + ear - 0.03, head[1] + 0.07), (head[0] + ear, head[1] + 0.2),
                      (head[0] + ear + 0.04, head[1] + 0.07)]
            pygame.draw.polygon(surface, dark, self.shape(points))

        # Head first in the snow: a heap of snow covers its front half
        snow = pygame.Color(palette.get("snow_lit", palette.get("snow_top", palette["bg"])))
        if self.state in ("dive", "emerge"):
            buried = 1 if self.state == "dive" else max(0, self.timer / self.EMERGE)
            heap_w = self.length * 0.75 * buried
            heap_h = self.length * 0.42 * buried
            hx = self.head_x()
            if heap_w > 1:
                pygame.draw.ellipse(surface, snow, (hx - heap_w / 2, self.y - heap_h * 0.8, heap_w, heap_h))
        for puff in self.puffs:
            t = puff["age"] / puff["life"]
            px = puff["x"] + puff["dx"] * t
            py = puff["y"] - math.sin(math.pi * t) * puff["rise"]
            pygame.draw.circle(surface, snow, (px, py), max(1, self.length * 0.05 * (1 - t)))


class SleighRide(Layer):
    # Rare: now and then on a night, a sleigh pulled by reindeer flies across the sky in
    # front of the moon, as a dark silhouette with a little trail of glitter.
    # Only at night (when the palette has "sleigh")
    #
    # Palette colors it uses:
    #   "sleigh"        the silhouette (no visits without it)
    #   "star"          the glitter trail (falls back to "text")

    WAIT = (300000, 600000)         # milliseconds between visits: 5 to 10 minutes
    FLIGHT = 7000                   # milliseconds to cross the sky
    SIZE = 12                       # one reindeer's length, in pixels at the medium size
    REINDEER = 4                    # in pairs
    TRAIL = 14                      # glitter specks left behind

    def __init__(self, scene, sky=None):
        super().__init__(scene)
        self.sky = sky
        self.timer = random.randint(*self.WAIT)
        self.flying = None
        self.allowed = False        # set from the palette each frame: only at night
        self.trail = []

    def path(self, t):
        # Right to left across the sky, dipping to pass in front of the moon
        start, end = WIDTH + s(40), -s(140)
        x = start + (end - start) * t
        if self.sky is not None:
            moon_x, moon_y = self.sky.body_x, self.sky.body_y
        else:
            moon_x, moon_y = WIDTH * 0.8, self.scene.view.horizon * 0.4
        dip = ((x - moon_x) / WIDTH) ** 2
        return x, moon_y + s(4) + dip * s(60)

    def update(self, dt):
        for speck in self.trail:
            speck["age"] += dt
        self.trail = [speck for speck in self.trail if speck["age"] < speck["life"]]

        if self.flying is None:
            if self.allowed:
                self.timer -= dt
                if self.timer <= 0:
                    self.flying = 0
            return
        self.flying += dt
        if random.random() < 0.5:
            x, y = self.path(self.flying / self.FLIGHT)
            self.trail.append({"x": x + s(self.SIZE) * 1.8, "y": y + random.uniform(-2, 2),
                               "age": 0, "life": random.randint(500, 1200)})
            self.trail = self.trail[-self.TRAIL:]
        if self.flying >= self.FLIGHT:
            self.flying = None
            self.timer = random.randint(*self.WAIT)

    def draw(self, surface, palette):
        self.allowed = "sleigh" in palette
        if not self.allowed:
            return
        glitter = pygame.Color(palette.get("star", palette["text"]))
        for speck in self.trail:
            fade = 1 - speck["age"] / speck["life"]
            behind = self.scene.color_at(palette, speck["y"])
            surface.set_at((int(speck["x"]), int(speck["y"])), behind.lerp(glitter, fade * 0.8))
        if self.flying is None:
            return

        color = pygame.Color(palette["sleigh"])
        t = self.flying / self.FLIGHT
        x, y = self.path(t)
        size = s(self.SIZE)
        gallop = self.flying / 110

        # The sleigh: a curved body with a runner underneath, Santa sitting in it
        sleigh_x = x + size * 2.4
        pygame.draw.polygon(surface, color, [(sleigh_x - size * 0.7, y - size * 0.15), (sleigh_x + size * 0.7, y - size * 0.15),
                                             (sleigh_x + size * 0.9, y - size * 0.6), (sleigh_x + size * 0.55, y + size * 0.25),
                                             (sleigh_x - size * 0.6, y + size * 0.25)])
        pygame.draw.line(surface, color, (sleigh_x - size * 0.9, y + size * 0.4), (sleigh_x + size * 0.6, y + size * 0.4), max(1, s(1)))
        pygame.draw.line(surface, color, (sleigh_x - size * 0.9, y + size * 0.4), (sleigh_x - size * 1.0, y + size * 0.2), max(1, s(1)))
        pygame.draw.circle(surface, color, (sleigh_x - size * 0.1, y - size * 0.45), size * 0.3)
        pygame.draw.circle(surface, color, (sleigh_x - size * 0.15, y - size * 0.85), size * 0.17)
        pygame.draw.polygon(surface, color, [(sleigh_x - size * 0.3, y - size * 0.9), (sleigh_x + size * 0.15, y - size * 1.25),
                                             (sleigh_x, y - size * 0.85)])

        # The reindeer, in pairs ahead of it, with the reins running back
        for pair in range(self.REINDEER // 2):
            for side in (0, 1):
                rx = x - pair * size * 1.3 + side * size * 0.25
                ry = y - side * size * 0.25 + math.sin(gallop + pair) * size * 0.08
                self.draw_reindeer(surface, color, rx, ry, size, gallop + pair + side)
        pygame.draw.line(surface, color, (x - (self.REINDEER // 2 - 1) * size * 1.3, y - size * 0.35),
                         (sleigh_x - size * 0.5, y - size * 0.3), 1)

    def draw_reindeer(self, surface, color, x, y, size, gallop):
        # Facing left: body, neck and head, antlers, galloping legs
        pygame.draw.ellipse(surface, color, (x - size * 0.4, y - size * 0.45, size * 0.8, size * 0.35))
        pygame.draw.line(surface, color, (x - size * 0.3, y - size * 0.35), (x - size * 0.5, y - size * 0.7), max(1, s(2)))
        pygame.draw.circle(surface, color, (x - size * 0.55, y - size * 0.72), size * 0.11)
        for prong in (-0.2, 0.05):
            pygame.draw.line(surface, color, (x - size * 0.5, y - size * 0.8), (x - size * (0.45 + prong), y - size * 1.05), 1)
        stretch = math.sin(gallop * 2) * 0.25
        for hip, offset in ((-0.3, 1), (0.3, -1)):
            pygame.draw.line(surface, color, (x + size * hip, y - size * 0.2),
                             (x + size * (hip - 0.15 + stretch * offset), y + size * 0.1), 1)
