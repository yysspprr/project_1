import tkinter as tk
from tkinter import messagebox
import random
import game_logic as logic

range_lowest = 1
range_highest = 100
max_tries = 10


secret = random.randint(range_lowest, range_highest)
try_count = 0
lives = logic.STARTING_LIVES
guessed_list = []
rounds_played = 0
current_difficulty = "normal"


# functions
def show_game():
    menu_frame.pack_forget()
    difficulty_frame.pack_forget()
    game_frame.pack()
    new_game()

def show_difficulty():
    menu_frame.pack_forget()
    game_frame.pack_forget()
    difficulty_frame.pack()

def show_menu():
    game_frame.pack_forget()
    difficulty_frame.pack_forget()
    menu_frame.pack()

def quit_to_menu_warning():

    if logic.has_progress(lives, rounds_played, try_count) == True:
        answer = messagebox.askyesno("Return to menu?", "Your progress will be lost. Continue?")
        if answer == False:
            return
    show_menu()

def restart_game_warning():

    if logic.has_progress(lives, rounds_played, try_count) == True:
        answer = messagebox.askyesno("Restart game?", "Your progress will be lost. Continue?")
        if answer == False:
            return
    new_game()

def close_window_warning():

    if logic.has_progress(lives, rounds_played, try_count) == True and game_frame.winfo_ismapped() == True:
        answer = messagebox.askyesno("Quit game?", "Your progress will be lost. Continue?")
        if answer == False:
            return
    window.destroy()

def wobble_hearts():

    for heart in heart_labels:
        offset_1 = random.randint(0, 4)
        offset_2 = random.randint(0, 4)
        heart.pack_configure(pady=(offset_1, 4 - offset_1), padx=(offset_2, 4 - offset_2))
    window.after(150, wobble_hearts)

def get_try_word(try_count):
    if try_count == 1:
        return "try"
    else:
        return "tries"

def update_lives():

    normal_hearts, golden_hearts = logic.heart_counts(lives)

    for position in range(logic.STARTING_LIVES):
        if position < golden_hearts:
            heart_labels[position].config(fg="#DAA520")
        elif position < normal_hearts:
            heart_labels[position].config(fg="red")
        else:
            heart_labels[position].config(fg="grey")

def start_game(difficulty):
    global range_lowest, range_highest, max_tries, current_difficulty

    current_difficulty = difficulty

    range_lowest, range_highest, max_tries = logic.difficulty_settings(difficulty)

    show_game()

def guess_number(event=None):

    if entry.cget("state") == "disabled":
        return

    global try_count, lives

    guess = entry.get()
    entry.delete(0, tk.END)

    result = logic.check_guess(guess, secret, range_lowest, range_highest, guessed_list)

    if result == "invalid":
        label.config(text="Invalid input!", font=("Noto Sans", 10))
        return
    elif result == "out of range":
        label.config(text="Out of range!", font=("Noto Sans", 10))
        return
    elif result == "repeat":
        label.config(text="Already guessed!", font=("Noto Sans", 10))
        return

    try_count += 1
    
    if result == "too high":
        label.config(text=f"Too high! {try_count} {get_try_word(try_count)}.", font=("Noto Sans", 12))
    elif result == "too low":
        label.config(text=f"Too low! {try_count} {get_try_word(try_count)}.", font=("Noto Sans", 12))
    else:
        label.config(text=f"Correct! {try_count} {get_try_word(try_count)}.", font=("Noto Sans", 14))

        lives = logic.lives_after_round(lives, True, current_difficulty)

        update_lives()
        end_round()

    if result != "correct" and try_count == max_tries:
        label.config(text=f"Out of tries!\nRound lost!\nThe number was {secret}.", font=("Noto Sans", 10))

        lives = logic.lives_after_round(lives, False, current_difficulty)

        update_lives()
        end_round()

def end_round():

    global rounds_played

    guess_button.config(state="disabled")
    entry.config(state="disabled")

    rounds_played += 1

    result = logic.game_result(lives)

    if result == "game_lost":
        label.config(text=(f"Out of tries! The number was {secret}.\nOut of lives! Game over!"))
    elif result == "game_won":
        label.config(text=f"Correct! {try_count} {get_try_word(try_count)}.\nYou won!")
    else:
        next_round_button.config(state="normal")

def next_round():

    global secret, try_count
    label.config(text=f"Guess a number! ({range_lowest}-{range_highest})", font=("Noto Sans", 10))
    guess_button.config(state="normal")
    entry.config(state="normal")
    next_round_button.config(state="disabled")
    secret = random.randint(range_lowest, range_highest)
    try_count = 0
    guessed_list.clear()
    rounds_label.config(text=f"Round {rounds_played + 1}", font=("Noto Sans", 10))

    print(f"number = {secret}")

def new_game():

    global lives, rounds_played
    lives = logic.STARTING_LIVES
    rounds_played = 0
    update_lives()
    next_round()

window = tk.Tk()
window.protocol("WM_DELETE_WINDOW", close_window_warning)
window.title("NumberGuess")
window.geometry("260x400")

game_frame = tk.Frame(window)

entry = tk.Entry(game_frame)
entry.pack(pady=10, padx=10)
entry.bind("<Return>", guess_number)

rounds_label = tk.Label(game_frame, text=f"Round {rounds_played + 1}", font=("Noto Sans", 10))
rounds_label.pack()


hearts_frame = tk.Frame(game_frame)
hearts_frame.pack(pady=(0, 10))

heart_1 = tk.Label(hearts_frame, text="♥", fg="red", font=("Noto Sans", 20))
heart_1.pack(side="left")

heart_2 = tk.Label(hearts_frame, text="♥", fg="red", font=("Noto Sans", 20))
heart_2.pack(side="left")

heart_3 = tk.Label(hearts_frame, text="♥", fg="red", font=("Noto Sans", 20))
heart_3.pack(side="left")

heart_labels = [heart_1, heart_2, heart_3]



label = tk.Label(game_frame, text=f"Guess a number! ({range_lowest}-{range_highest})", font=("Noto Sans", 10))
label.pack()

guess_button = tk.Button(game_frame, text="Guess", command=guess_number)
guess_button.pack(pady=10, padx=10)

next_round_button = tk.Button(game_frame, text="Next round", state="disabled", command=next_round)
next_round_button.pack(pady=10, padx=10)

restart_game_button = tk.Button(game_frame, text="Restart game", command=restart_game_warning)
restart_game_button.pack(pady=10, padx=10)

quit_to_menu_button = tk.Button(game_frame, text="Back to menu", command=quit_to_menu_warning)
quit_to_menu_button.pack(pady=10, padx=10)



difficulty_frame = tk.Frame(window)

difficulty_label = tk.Label(difficulty_frame, text="Choose a difficulty", font=("Noto Sans", 10))
difficulty_label.pack()

difficulty_easy_button = tk.Button(difficulty_frame, text="Easy", command=lambda: start_game("easy"))
difficulty_easy_button.pack()

difficulty_normal_button = tk.Button(difficulty_frame, text="Normal", command=lambda: start_game("normal"))
difficulty_normal_button.pack()

difficulty_hard_button = tk.Button(difficulty_frame, text="Hard", command=lambda: start_game("hard"))
difficulty_hard_button.pack()

difficulty_back_button = tk.Button(difficulty_frame, text="Back", command=show_menu)
difficulty_back_button.pack()


menu_frame = tk.Frame(window)

menu_label = tk.Label(menu_frame, text=f"Menu Frame (placeholder)", font=("Noto Sans", 10))
menu_label.pack()

menu_new_game_button = tk.Button(menu_frame, text="New game", command=show_difficulty)
menu_new_game_button.pack()

menu_quit_button = tk.Button(menu_frame, text="Exit", command=window.destroy)
menu_quit_button.pack()

menu_frame.pack()


wobble_hearts()
window.mainloop()