import random


def battle(player, enemy, level):
    scale_enemy(enemy, level)
    turn = 1
    max_turn = 10

    while player.hp > 0 and enemy.hp > 0:
        print("\n====================")
        print("Turn", turn)
        print("====================")

        print("Player HP:", player.hp, "/", player.max_hp)
        print("Enemy HP:", enemy.hp, "/", enemy.max_hp)

        player_turn(player, enemy)
        player.bleed(enemy)
        if enemy.hp <= 0:
            enemy.hp = 0
            win_reward(player)
            check_weapon_break(player)
            return True
  
        enemy_turn(player, enemy)
        if player.hp <= 0 or turn >= max_turn:
            player.hp = max(0, player.hp)
            check_weapon_break(player)
            return False

        turn += 1


def player_turn(player, enemy):
    while True:
        print("\n1. Attack")
        print("2. Defend")
        choice = input("> ")

        if choice == "1":
            damage = player.attack(enemy)
            print("You dealt",damage,"damage.")
            break
        elif choice == "2":
            player.is_defending = True
            print("Guard")
            break
        else:
            print("Invalid choice.")


def enemy_turn(player, enemy):
    damage = enemy.attack_player(player)
    print("Enemy dealt",damage,"damage.")

    player.is_defending = False

def scale_enemy(enemy, level):
    if level == 1:
        return
    multiplier = random.uniform(1.25, 1.75)

    enemy.max_hp = int(enemy.max_hp * multiplier)
    enemy.hp = enemy.max_hp
    enemy.attack = int(enemy.attack * multiplier)
    enemy.defense = int(enemy.defense * multiplier)

    print("Enemy stat multiplier:",round(multiplier, 2))


def win_reward(player):
    points = 3
    player.stat_points += points
    if random.random() <= 0.15:
        print("\nYou found equipment!")
        weapon_type = random.choice([
            "sword",
            "shield",
            "sword_buckler",
            "dagger"
        ])
        item = player.weapon_recived(weapon_type)
        player.add_item(item)
        print("You got", item["name"])

def check_weapon_break(player):
    if player.weapon is None:
        return
    
    if random.random() <= 0.10:
        print("\nYour",player.weapon["name"],"broke!")
        player.weapon = None