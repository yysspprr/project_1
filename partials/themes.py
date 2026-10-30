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
            "water_top": "#222d3f",     # far away: catches a little light from the sky
            "water_bottom": "#121925",  # up close: deeper and darker
            "glint": "#7d93b3",         # the brightest a glint of light gets
            "rain": "#a9bbd4",          # falling streaks
            "leaves": ["#6a7a46", "#8a6a3e", "#7a5f3a", "#5c6e4c"],     # floating leaves: one picked per leaf
            "twig": "#6c5a45",
        },
        "light": {
            "bg": "#b0c4d4",
            "text": "#253244",
            "accent": "#8a560c",
            "field": "#d3dee8",
            "muted": "#4b5b70",
            "overlay": (0, 0, 0, 100),
            "history_box": (0, 0, 0, 25),
            "range_fill": "#8a560c",
            "bar": (0, 0, 0, 25),
            "ripple": "#5f7890",
            "water_top": "#c5d5e2",
            "water_bottom": "#9db4c7",
            "glint": "#f4f8fb",
            "rain": "#4f677e",
            "leaves": ["#7a8a4e", "#a27a42", "#8c6a3a", "#68805a"],
            "twig": "#6a563f",
        },
    },
}