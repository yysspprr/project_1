# Player stats: loading, saving and recording finished games

import json

from partials.config import BASE_DIR

STATS_PATH = BASE_DIR / "data" / "stats.json"
REGULAR_MODES = ("easy", "normal", "hard")

def empty_mode_stats():
    # A fresh set of stats for one difficulty
    return {
        "wins": 0,
        "losses": 0,
        "streak": 0,                # wins in a row right now
        "best_streak": 0,
        "best_win": None,           # fewest guesses in a won game; None until the first win
        "rounds": 0,
        "guesses": 0,
        "first_tries": 0,           # rounds guessed on the very first try
    }

def load_stats():
    stats = {}
    for mode in REGULAR_MODES:
        stats[mode] = empty_mode_stats()

    try:
        with open(STATS_PATH) as file:
            saved = json.load(file)
        for mode in REGULAR_MODES:
            if mode in saved:
                stats[mode].update(saved[mode])
    except (FileNotFoundError, json.JSONDecodeError):
        pass                        # no file yet, or a broken one: start fresh

    return stats

def save_stats(stats):
    with open(STATS_PATH, "w") as file:
        json.dump(stats, file, indent=4)

def record_game(stats, mode, won, guesses, rounds, first_tries):
    # Add one finished game to a mode's stats, and save
    entry = stats[mode]
    entry["rounds"] += rounds
    entry["guesses"] += guesses
    entry["first_tries"] += first_tries

    if won:
        entry["wins"] += 1
        entry["streak"] += 1
        entry["best_streak"] = max(entry["best_streak"], entry["streak"])
        if entry["best_win"] is None or guesses < entry["best_win"]:
            entry["best_win"] = guesses
    else:
        entry["losses"] += 1
        entry["streak"] = 0

    save_stats(stats)