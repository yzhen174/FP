from player import Player
from enemy import Enemy
from battle import battle
import analyze

SAVE_FILE = "save.txt"


def main_menu():
    while True:
        print("\n==================================================================================")
        print("GAME GOAL:")
        print("Create a strong character and make strategic moves to defeat the AI enemy")
        print("\n==================================================================================")
        print("GAME PURPOSE:")
        print("AI analyzes player strategy and provides recommendations for game play improvement")
        print("\n==================================================================================")
        print("HOW TO PLAY:")
        print("1. Start a game by choosing \"New Game\"")
        print("2. Build your character by distributing available stat points among attributes")
        print("3. Begin level and defeat enemy in 10 turns or less")
        print("4. Defeat enemy by reducing enemy HP to 0 while maintaining your HP above 0")
        print("5. During each turn, choose an action, example: attack or defend")
        print("6. If you lose, review AI feedback to improve game play strategy in next game")
        print("7. In between levels and losses, update stat distribution to improve game play")
        print("\n==================================================================================")
        print("OPTIONS:")
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
    player.stats()
    game_loop(player, level)


def continue_game():
    try:
        with open(SAVE_FILE, "r") as file:
            level = int(file.readline().strip())
        print("\nSave loaded.")
        print("Current Level:", level)
        player = Player()
        player.stats()
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
        

        if player_won:
            result = win_menu(player)
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

            result = lose_menu(player)
            if result == "retry":
                player.hp = player_hp
                continue
            elif result == "restart":
                level = 1
                player = Player()
                player.stats()
                continue

def win_menu(player):
    while True:
        print("\n====================")
        print("      YOU WIN!")
        print("====================")
        print("1. Next Level")
        print("2. Stats")
        print("3. Exit and Save")

        choice = input("Choose an option: ")
        if choice == "1":
            return "next"
        elif choice == "2":
            player.stats()
        elif choice == "3":
            return "exit"
        else:
            print("Invalid choice.")

def lose_menu(player):
    while True:
        print("\n====================")
        print(" YOU LOST")
        print("====================")

        print("1. Retry")
        print("2. Stats")
        print("3. Restart")

        choice = input("Choose an option: ")
        if choice == "1":
            return "retry"
        elif choice == "2":
            player.stats()
        elif choice == "3":
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
