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
        },
        "light": {
            "bg": "#e4ecf3",
            "text": "#34445a",
            "accent": "#c98a1c",
            "field": "#cdd8e4",
            "muted": "#8796aa",
            "overlay": (0, 0, 0, 100),
            "history_box": (0, 0, 0, 25),
            "range_fill": "#c98a1c",
            "bar": (0, 0, 0, 25),
            "ripple": "#a3b7cc",
        },
    },
}