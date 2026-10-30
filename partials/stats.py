# Player stats: loading, saving and recording finished games

import json

from partials.config import BASE_DIR

STATS_PATH = BASE_DIR / "data" / "stats.json"
REGULAR_MODES = ("easy", "normal", "hard")
RECENT_FREE_GAMES = 5           # how many free games the recent list keeps

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

def empty_free_stats():
    return {
        "games": 0,
        "guesses": 0,
        "no_help_wins": 0,          # won with both the range bar and the history off
        "biggest_range": None,      # [from, to] of the widest range won; None until the first game
        "recent": [],               # the newest games first
    }

def load_stats():
    stats = {}
    for mode in REGULAR_MODES:
        stats[mode] = empty_mode_stats()
    stats["free"] = empty_free_stats()

    try:
        with open(STATS_PATH) as file:
            saved = json.load(file)
        for mode in REGULAR_MODES:
            if mode in saved:
                stats[mode].update(saved[mode])
        if "free" in saved:
            stats["free"].update(saved["free"])
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    return stats

def save_stats(stats):
    STATS_PATH.parent.mkdir(exist_ok=True)          # make the data folder if it isn't there yet
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

def record_free_game(stats, low, high, tries, range_bar, history):
    entry = stats["free"]
    entry["games"] += 1
    entry["guesses"] += tries

    if not range_bar and not history:
        entry["no_help_wins"] += 1

    # The widest range so far (both ends count, so 1 to 10 is 10 numbers)
    size = high - low + 1
    biggest = entry["biggest_range"]
    if biggest is None or size > biggest[1] - biggest[0] + 1:
        entry["biggest_range"] = [low, high]

    # Newest game at the front, and keep only the last few
    entry["recent"].insert(0, {"from": low, "to": high, "tries": tries,
                               "range bar": range_bar, "history": history})
    entry["recent"] = entry["recent"][:RECENT_FREE_GAMES]

    save_stats(stats)