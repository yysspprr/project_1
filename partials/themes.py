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

    "snow": {
        "dark": {
            "bg": "#1c2436",
            "text": "#dbe5f2",
            "accent": "#f2d58a",
            "field": "#28334a",
            "muted": "#8391a8",
            "overlay": (0, 0, 0, 160),
            "history_box": (0, 0, 0, 60),
            "range_fill": "#f2d58a",
            "bar": (0, 0, 0, 50),
            "sky_top": "#090e1b",       # a clear, cold night
            "sky_low": "#1a2337",
            "sky_body": "moon",
            "body": "#eef0e4",
            "body_glow": "#36435e",
            "cloud": "#202a3e",
            "star": "#d2dcee",
            "mountain": "#1d2638",      # far away: kept close to the sky
            "mountain_snow": "#3b4762",
            "fir": "#0e151d",
            "fir_snow": "#2e3a50",
            "snow_top": "#28324a",      # moonlit snow, bluer far away
            "snow_bottom": "#1a2131",
            "snow_shadow": "#111726",
            "snow_lit": "#3a4662",      # moonlight catching the drift crests
            "ice_far": "#182236",       # the frozen pond: darker and glassier than the snow
            "ice_near": "#101826",
            "ice_rim": "#36425c",
            "ice_crack": "#4a5874",
            "flake": "#d6e0ef",
            "aurora_low": "#44d8a4",    # the northern lights: green at the bottom...
            "aurora_high": "#7a62d0",   # ... fading to violet at the top
            "sparkle": "#c3d2ea",       # moonlight glinting on the snow
            "wall": "#2b2a33",          # the village
            "roof": "#2a2026",
            "roof_snow": "#3e4a66",
            "window": "#171c27",
            "window_lit": "#ffcf73",    # warm lights coming on at night
            "smoke": "#46526a",
            "branch": "#1d1a1a",        # the framing: a fir bough and frozen grass
            "needle": "#16231f",
            "bough_snow": "#3e4a66",
            "icicle": "#8fa3c2",
            "bird": "owl",              # an owl keeps watch at night...
            "owl_body": "#3a3029",
            "owl_eye": "#f0c860",
            "fox": "#7a4a2c",           # a fox, hunting mice under the snow
            "fox_light": "#b9b4ab",
            "fox_dark": "#1a120e",
            "sleigh": "#04060b",        # a very rare December visitor, dark against the moon
            "halo": "#121a29",
            "shadow": 0.2,
        },
        "light": {
            "bg": "#d5e0ea",
            "text": "#253244",
            "accent": "#74470a",
            "field": "#eef3f7",
            "muted": "#4b5b70",
            "overlay": (0, 0, 0, 100),
            "history_box": (0, 0, 0, 25),
            "range_fill": "#74470a",
            "bar": (0, 0, 0, 25),
            "sky_top": "#9fb4c8",       # a crisp winter day
            "sky_low": "#dae4ec",
            "sky_body": "sun",
            "body": "#fffbee",
            "body_glow": "#f6f2e2",
            "cloud": "#f1f5f8",
            "mountain": "#a5b6c7",
            "mountain_snow": "#e9eff4",
            "fir": "#4a6157",
            "fir_snow": "#e4ecf1",
            "snow_top": "#e3eaf1",      # bright snow, slightly blue so it isn't glaring
            "snow_bottom": "#cbd8e4",
            "snow_shadow": "#a9bccf",
            "snow_lit": "#f6f9fb",
            "ice_far": "#b6c9d8",       # the frozen pond: a cool grey-blue against the white
            "ice_near": "#9cb3c6",
            "ice_rim": "#f2f6f9",
            "ice_crack": "#dbe6ee",
            "flake": "#ffffff",
            "flake_edge": "#9fb1c4",    # so flakes show against the pale sky
            "sparkle": "#ffffff",
            "sparkle_edge": "#9fb4c8",  # a blue-grey edge so white glints show on pale snow
            "dust": "#ffffff",          # diamond dust: tiny ice crystals glinting in the sunny air
            "dust_edge": "#a9bccf",
            "wall": "#8b6b55",
            "roof": "#6e4537",
            "roof_snow": "#f4f7fa",
            "window": "#4d5d70",
            "smoke": "#b4bfca",         # grey, or it would vanish against the white snow
            "branch": "#4a3d32",
            "needle": "#3d5a4a",
            "bough_snow": "#f4f7fa",
            "icicle": "#a9c4d8",
            "melt": True,               # the sun is warm enough for the icicles to drip
            "bird": "robin",            # ... and a robin by day
            "robin_body": "#6b5a4c",
            "robin_breast": "#d4663a",
            "fox": "#c8642c",
            "fox_light": "#f4efe6",
            "fox_dark": "#2a1d17",
            "halo": "#e3eaf1",
            "shadow": 0.45,
        },
    },

    "stream": {
        "dark": {
            "bg": "#1d1f1d",
            "text": "#dbe5f2",
            "accent": "#f2d58a",
            "field": "#1f2d27",
            "muted": "#8391a8",
            "overlay": (0, 0, 0, 160),
            "history_box": (0, 0, 0, 60),
            "range_fill": "#f2d58a",
            "bar": (0, 0, 0, 50),
            "bed": "#1d1f1d",           # the brook at night: stony bed and gravel
            "damp": "#181a19",
            "gravel": ["#262826", "#1a1c1a", "#222421"],
            "water": "#18303a",         # the water
            "water_deep": "#11232b",
            "shallows": "#1f3a44",
            "foam": "#4d6670",
            "rock": "#2b2f2e",          # stones
            "rock_light": "#3a403f",
            "rock_dark": "#1a1e1d",
            "moss": "#22331f",
            "bank": "#1a2a1c",          # mossy banks and what grows on them
            "bank_dark": "#121e14",
            "bank_speckle": ["#15241a", "#203222", "#121e15"],
            "bank_light": "#223524",
            "clover": "#1f3423",
            "litter": ["#3a3020", "#33281b", "#3d3524"],
            "halo": "#0f1512",
            "shadow": 0.15,
        },
        "light": {
            "bg": "#9a8b70",
            "text": "#253244",
            "accent": "#74470a",
            "field": "#eef3ea",
            "muted": "#4b5b70",
            "overlay": (0, 0, 0, 100),
            "history_box": (0, 0, 0, 25),
            "range_fill": "#74470a",
            "bar": (0, 0, 0, 25),
            "bed": "#a99a7e",           # the brook by day: stony bed and gravel
            "damp": "#968770",
            "gravel": ["#bcb095", "#8f826b", "#a69a85"],
            "water": "#9cc5cd",         # the water
            "water_deep": "#7fb0bd",
            "shallows": "#b9d8da",
            "foam": "#f2f7f6",
            "rock": "#8d918a",          # stones
            "rock_light": "#b7bab2",
            "rock_dark": "#696d66",
            "moss": "#7fa35e",
            "bank": "#86a564",          # mossy banks and what grows on them
            "bank_dark": "#6c8c50",
            "bank_speckle": ["#76975a", "#98b674", "#6c8c4c"],
            "bank_light": "#a3c27d",
            "clover": "#5b8a45",
            "litter": ["#c79a52", "#b0743e", "#d2b064"],
            "halo": "#e4eedc",
            "shadow": 0.35,
        },
    },
}