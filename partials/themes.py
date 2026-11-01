# Color palettes: each theme has a dark and a light version,
# and every palette uses the same names

THEMES = {
    "plain": {
        "dark": {
            "bg": "#1e1e2e",
            "text": "#cdd6f4",
            "accent": "#f9e2af",
            "field": "#313244",
            "muted": "#7f849c",
            "overlay": (0, 0, 0, 160),        # behind the warning modal
            "history_box": (0, 0, 0, 60),
            "range_fill": "#f9e2af",
            "bar": (0, 0, 0, 50),
        },
        "light": {
            "bg": "#eff1f5",
            "text": "#4c4f69",
            "accent": "#df8e1d",
            "field": "#ccd0da",
            "muted": "#8c8fa1",
            "overlay": (0, 0, 0, 100),
            "history_box": (0, 0, 0, 25),
            "range_fill": "#df8e1d",
            "bar": (0, 0, 0, 25),
        },
    },

    "rain": {
        "dark": {
            "bg": "#1a2230",
            "text": "#d6e2f0",
            "accent": "#f2d58a",
            "field": "#26324a",
            "muted": "#7d8ba0",
            "overlay": (0, 0, 0, 160),
            "history_box": (0, 0, 0, 60),
            "range_fill": "#f2d58a",
            "bar": (0, 0, 0, 50),
            "ripple": "#4a5d7a",        # the brightest a fresh ripple gets
            "ripple_light": "#647896",  # the far side of a ripple, catching the moonlight
            "water_top": "#222d3f",     # far away: catches a little light from the sky
            "water_bottom": "#121925",  # up close: deeper and darker
            "glint": "#7d93b3",         # the brightest a glint of light gets
            "rain": "#a9bbd4",          # falling streaks
            "leaves": ["#6a7a46", "#8a6a3e", "#7a5f3a", "#5c6e4c"],     # floating leaves: one picked per leaf
            "twig": "#6c5a45",
            "bug": "#05080d",           # water striders: mostly you see their dimples
            "fish": "#0a0f17",          # a fish's back breaking the surface
            "sky_top": "#0b101c",       # the night sky, top of the window
            "sky_low": "#1d2738",       # ... and just above the horizon
            "sky_body": "moon",         # dark mode is night
            "body": "#ece6c8",
            "body_glow": "#3a4560",
            "cloud": "#232c3e",
            "star": "#c8d2e6",
            "trees": "#0f1621",         # the far shore: kept soft so it stays in the haze
            "far_hill": "#151d2b",
            "reed": "#202a2a",          # the framing: a touch of moonlight so it isn't lost in the dark
            "reed_head": "#312d2b",
            "branch": "#1a1c20",
            "leaf": "#222f2d",
            "pad": "#31423b",
            "pad_edge": "#25312e",
            "flower": "#b9a8bc",
            "flower_middle": "#c9b465",
            "halo": "#0c121c",
            "shadow": 0.12,             # moonlight casts only faint shadows          # the soft glow behind text, so it stands out from the scenery
        },
        "light": {
            "bg": "#b0c4d4",
            "text": "#253244",
            "accent": "#74470a",
            "field": "#d3dee8",
            "muted": "#4b5b70",
            "overlay": (0, 0, 0, 100),
            "history_box": (0, 0, 0, 25),
            "range_fill": "#74470a",
            "bar": (0, 0, 0, 25),
            "ripple": "#5f7890",
            "ripple_light": "#4d657c",  # darker, not lighter: on an overcast day it reflects the pale sky, which vanishes on pale water
            "water_top": "#c5d5e2",
            "water_bottom": "#9db4c7",
            "glint": "#f4f8fb",
            "rain": "#4f677e",
            "leaves": ["#7a8a4e", "#a27a42", "#8c6a3a", "#68805a"],
            "twig": "#6a563f",
            "bug": "#26303c",
            "fish": "#3e4c5a",
            "sky_top": "#b9c7d3",
            "sky_low": "#dde5ec",
            "sky_body": "sun",          # light mode is day
            "body": "#fbf7ea",
            "body_glow": "#f3f1e6",
            "cloud": "#eef2f5",
            "trees": "#94a39d",
            "far_hill": "#adbbc5",
            "reed": "#5d6e43",
            "reed_head": "#6e4c2f",
            "branch": "#4a3d32",
            "leaf": "#6a7f4b",
            "pad": "#6e8e55",
            "pad_edge": "#4f6a3c",
            "flower": "#f3dbe6",
            "flower_middle": "#e8c860",
            "halo": "#d3dee8",
            "shadow": 0.25,
        },
    },
}