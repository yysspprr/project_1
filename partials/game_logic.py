STARTING_LIVES = 3
FREE_LOWEST = -9999             # the widest range free mode allows
FREE_HIGHEST = 9999
FREE_HISTORY_SIZE = 10          # free mode shows the last this-many guesses

def free_range_problem(low, high):
    # What's wrong with a free mode range, or None if it's fine
    if low < FREE_LOWEST or high > FREE_HIGHEST:
        return f"stay between {FREE_LOWEST} and {FREE_HIGHEST}!"
    if low >= high:
        return "'from' must be lower than 'to'!"
    return None

def check_guess(guess, secret, range_lowest, range_highest, guesses):
    try:
        number = int(guess)
    except ValueError:
        return "invalid"

    if number < range_lowest or number > range_highest:
        return "out of range"

    if number in guesses:
        return "repeat"

    if number > secret:
        return "too high"
    elif number < secret:
        return "too low"
    else:
        return "correct"

def game_result(lives, tokens, tokens_needed):
    if lives == 0:
        return "game lost"
    elif tokens == tokens_needed:
        return "game won"
    else:
        return "playing"

def has_progress(lives, tokens, tokens_needed, rounds_played, try_count):
    if game_result(lives, tokens, tokens_needed) != "playing":
        return False
    return rounds_played > 0 or try_count > 0

def difficulty_settings(difficulty):
    # lowest, highest, max tries, tokens needed to win
    if difficulty == "easy":
        return 0, 50, 10, 3
    elif difficulty == "hard":
        return 0, 100, 7, 7
    else:
        return 0, 100, 10, 5

def max_digits(range_lowest, range_highest):
    return max(len(str(range_lowest)), len(str(range_highest)))

def after_round(lives, tokens, won_round, difficulty):
    if won_round:
        if lives < STARTING_LIVES:
            lives += 1          # recovering: win back a life
        else:
            tokens += 1         # full health: earn a token
    else:
        if tokens > 0:
            if difficulty == "hard":
                tokens = 0      # hard mode: lose them all
            else:
                tokens -= 1
        else:
            lives -= 1
    return lives, tokens

def narrowed_range(guesses, secret, range_lowest, range_highest):
    low = range_lowest
    high = range_highest
    for guess in guesses:
        if guess < secret:
            low = max(low, guess + 1)       # too low: the answer is above it
        elif guess > secret:
            high = min(high, guess - 1)     # too high: the answer is below it
    return low, high

def closest_guesses(guesses, secret):
    # The highest guess below the secret and the lowest guess above it
    # (None if there's no guess on that side yet)
    below = None
    above = None
    for guess in guesses:
        if guess < secret:
            if below is None or guess > below:
                below = guess
        elif guess > secret:
            if above is None or guess < above:
                above = guess
    return below, above