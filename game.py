from player import Player
from enemy import Enemy
from battle import battle
import analyze

SAVE_FILE = "save.txt"


def main_menu():
    while True:
        print("\n====================")
        print("GAME")
        print("====================")
        print("1. Continue Game")
        print("2. New Game")
        print("3. Exit")

        choice = input("Choose an option: ")
        if choice == "1":
            continue_game()
        elif choice == "2":
            new_game()
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")


def new_game():
    level = 1
    player = Player()
    stat_screen(player)
    game_loop(player, level)


def continue_game():
    try:
        with open(SAVE_FILE, "r") as file:
            level = int(file.readline().strip())
        print("\nSave loaded.")
        print("Current Level:", level)
        player = Player()
        stat_screen(player)
        game_loop(player, level)

    except FileNotFoundError:
        print("\nNo save file found.")
        print("Please start a new game first.")


def game_loop(player, level):
    while True:
        print("\n====================")
        print("LEVEL", level)
        print("====================")

        enemy = Enemy(level)
        player_hp = player.hp
        player_won = battle(player, enemy, level)
        stat_screen(player)

        if player_won:
            result = win_menu()
            if result == "next":
                level += 1
                continue
            elif result == "exit":
                save_game(level)
                return
        else:
            # Run post-match analysis and suggestions before showing lose menu
            try:
                analysis_text, suggestion = analyze.analyze_match(player, enemy)
                print("\n====================")
                print("    MATCH ANALYSIS")
                print("====================")
                print(analysis_text)
                if suggestion:
                    print("\nSuggested allocation:")
                    for stat, points in suggestion.items():
                        print("-", stat + ":", "+" + str(points))
            except Exception:
                # Fail silently so we don't interfere with existing flow
                pass

            result = lose_menu()
            if result == "retry":
                player.hp = player_hp
                continue
            elif result == "restart":
                level = 1
                player = Player()
                stat_screen(player)
                continue

def stat_screen(player):
    player.stats()

def win_menu():
    while True:
        print("\n====================")
        print("      YOU WIN!")
        print("====================")
        print("1. Next Level")
        print("2. Exit and Save")

        choice = input("Choose an option: ")
        if choice == "1":
            return "next"
        elif choice == "2":
            return "exit"
        else:
            print("Invalid choice.")

def lose_menu():
    while True:
        print("\n====================")
        print(" YOU LOST")
        print("====================")

        print("1. Retry")
        print("2. Restart")

        choice = input("Choose an option: ")
        if choice == "1":
            return "retry"
        elif choice == "2":
            return "restart"
        else:
            print("Invalid choice.")


def save_game(level):
    with open(SAVE_FILE, "w") as file:
        file.write(str(level))
    print("\nGame saved.")
    print("Progress saved at Level", level)

if __name__ == "__main__":
    main_menu()