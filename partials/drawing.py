# Drawing tools: wobbly text, sprites, boiling boxes and image helpers.
# Nothing in here knows about the game itself; main.py decides what to draw where.

import math
import random

import pygame

from partials.config import WOBBLE_STYLES, BOX_WOBBLE, BOX_SCALE, FRAME_COUNT, s

# =======================================================
# Wobbly text and images                                #
# =======================================================

def make_letters(text, font, color, digit_font=None):
    letter_images = []
    for letter in text:
        if digit_font is not None and letter.isdigit():
            letter_images.append(render_digit(letter, font, digit_font, color))
        else:
            letter_images.append(font.render(letter, True, color))
    return letter_images

def render_digit(digit, font, digit_font, color):
    # A digit in the digit font, lined up with the main font's baseline
    image = digit_font.render(digit, True, color)
    lined_up = pygame.Surface((image.get_width(), font.get_height()), pygame.SRCALPHA)
    lined_up.blit(image, (0, font.get_ascent() - digit_font.get_ascent()))
    return lined_up

def make_poses(images, style="strong"):
    amount, tilt = WOBBLE_STYLES[style]
    poses = []
    for image in images:
        dx = random.randint(-amount, amount)
        dy = random.randint(-amount, amount)
        angle = random.randint(-tilt, tilt)
        poses.append((dx, dy, angle))
    return poses

# Cache for tilted images, so each one is only rotated once
tilted_cache = {}

def get_tilted(image, angle):
    key = (image, angle)
    if key not in tilted_cache:
        if len(tilted_cache) > 1000:
            tilted_cache.clear()
        tilted_cache[key] = pygame.transform.rotozoom(image, angle, 1)
    return tilted_cache[key]

def draw_wobbly(images, poses, anchor_x, y, align="center", gap=0):
    screen = pygame.display.get_surface()
    total_width = 0
    for image in images:
        total_width += image.get_width()
    total_width += gap * (len(images) - 1)

    if align == "left":
        left = anchor_x
    else:
        left = anchor_x - total_width // 2
    x = left

    for position in range(len(images)):
        dx, dy, angle = poses[position]
        tilted = get_tilted(images[position], angle)
        center = (x + images[position].get_width() // 2 + dx,
                  y + images[position].get_height() // 2 + dy)
        screen.blit(tilted, tilted.get_rect(center=center))
        x += images[position].get_width() + gap

    return pygame.Rect(left, y, total_width, images[0].get_height())

def draw_stacked(images, poses, center_x, y, gap, row_gap):
    split = len(images) // 2
    row_height = images[0].get_height()

    if split > 0:
        draw_wobbly(images[:split], poses[:split], center_x, y, gap=gap)
    draw_wobbly(images[split:], poses[split:], center_x, y + row_height + row_gap, gap=gap)

# =======================================================
# Labels and sprites                                    #
# =======================================================

def make_label(text, font, color, style="subtle", digit_font=None, x=0, y=0):
    # A wobbly piece of text: its letter images, their poses and how strongly it wobbles
    letters = make_letters(text, font, color, digit_font)
    return {"letters": letters, "poses": make_poses(letters, style), "style": style, "x": x, "y": y}

def draw_label(label, x, y, align="center"):
    if len(label["letters"]) > 0:               # an empty label (like no message) draws nothing
        draw_wobbly(label["letters"], label["poses"], x, y, align=align)

def rewobble(label):
    # New poses in the label's own style; works for buttons too
    label["poses"] = make_poses(label["letters"], label["style"])

def make_sprite(slots, style="subtle"):
    # Wobbly images: each slot has a few frames to pick from, and a random one shows each tick
    sprite = {"slots": slots, "style": style}
    reanimate(sprite)
    return sprite

def reanimate(sprite):
    # Pick a new frame for every slot, and new poses
    images = []
    for frames in sprite["slots"]:
        images.append(random.choice(frames))
    sprite["letters"] = images
    sprite["poses"] = make_poses(images, sprite["style"])

# =======================================================
# Boiling boxes                                         #
# =======================================================

def rounded_box_points(rect, radius=s(14), corner_steps=6, edge_steps=8):
    # Points along a rounded rectangle: a curved arc at each corner,
    # with evenly spaced points along the straight edges in between
    corners = [
        (rect.right - radius, rect.top + radius, -90),
        (rect.right - radius, rect.bottom - radius, 0),
        (rect.left + radius, rect.bottom - radius, 90),
        (rect.left + radius, rect.top + radius, 180),
    ]
    arcs = []
    for cx, cy, start in corners:
        arc = []
        for i in range(corner_steps + 1):
            angle = math.radians(start + 90 * i / corner_steps)
            arc.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
        arcs.append(arc)

    points = []
    for i in range(4):
        points.extend(arcs[i])
        end = arcs[i][-1]
        next_start = arcs[(i + 1) % 4][0]
        for step in range(1, edge_steps):
            t = step / edge_steps
            points.append((end[0] + (next_start[0] - end[0]) * t,
                           end[1] + (next_start[1] - end[1]) * t))
    return points

def jitter_points(points, amount=BOX_WOBBLE):
    jittered = []
    for x, y in points:
        jittered.append((x + random.uniform(-amount, amount),
                         y + random.uniform(-amount, amount)))
    return jittered

def make_box_image(points, rect, fill_color, line_color):
    pad = s(6)
    width = rect.width + pad * 2
    height = rect.height + pad * 2
    big = pygame.Surface((width * BOX_SCALE, height * BOX_SCALE), pygame.SRCALPHA)

    big_points = []
    for x, y in points:
        big_points.append(((x - rect.left + pad) * BOX_SCALE,
                           (y - rect.top + pad) * BOX_SCALE))

    pygame.draw.polygon(big, fill_color, big_points)
    if line_color is not None:
        pygame.draw.lines(big, line_color, True, big_points, s(3) * BOX_SCALE)
        for point in big_points:
            pygame.draw.circle(big, line_color, point, s(3) / 2 * BOX_SCALE)

    return pygame.transform.smoothscale(big, (width, height))

def make_box(rect, fill_color, line_color, radius=s(14), edge_steps=8, wobble=BOX_WOBBLE):
    # A boiling box: its shape, colors and how much it wobbles, plus its current image
    box = {
        "rect": rect,
        "points": rounded_box_points(rect, radius=radius, edge_steps=edge_steps),
        "fill": fill_color,
        "line": line_color,
        "wobble": wobble,
    }
    rejitter(box)
    return box

def rejitter(box):
    # A new wobbly image of the box, in its own colors and wobble amount
    jittered = jitter_points(box["points"], box["wobble"])
    box["image"] = make_box_image(jittered, box["rect"], box["fill"], box["line"])

def draw_box(box):
    screen = pygame.display.get_surface()
    screen.blit(box["image"], box["image"].get_rect(center=box["rect"].center))

# =======================================================
# Images                                                #
# =======================================================

def tint_image(image, color):
    tinted = image.copy()
    tinted.fill(color, special_flags=pygame.BLEND_RGBA_MULT)
    return tinted

def tint_frames(frames, color):
    tinted = []
    for frame in frames:
        tinted.append(tint_image(frame, color))
    return tinted

def load_frames(folder, name, size):
    frames = []
    for number in range(1, FRAME_COUNT + 1):
        path = str(folder / f"{name}_{number}.png")
        image = pygame.image.load(path).convert_alpha()
        frames.append(pygame.transform.smoothscale(image, size))
    return frames