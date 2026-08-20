import random


class Player:
    def __init__(self):
        self.base_damage = 25
        self.base_defense = 10
        self.base_hp = 100
        self.base_crit_chance = 0.10
        self.base_crit_damage = 1.00
       
        self.strength = 0
        self.defense = 0
        self.crit = 0
        self.crit_damage = 0
        self.health = 0
        self.stat_points = 5

        self.max_hp = self.calculate_max_hp()
        self.hp = self.max_hp
        
        self.weapon = None
        self.inventory = {}
        self.is_defending = False

    def calculate_max_hp(self):
        return int(self.base_hp + self.health * 1.5)

    def update_hp(self):

        old_max_hp = self.max_hp
        self.max_hp = self.calculate_max_hp()
        hp_difference = self.max_hp - old_max_hp

        if hp_difference > 0:
            self.hp += hp_difference

        if self.hp > self.max_hp:
            self.hp = self.max_hp

    def get_crit_chance(self):
        crit_chance = (self.base_crit_chance+ self.crit * 0.025)
        if self.weapon is not None:
            crit_chance += self.weapon.get("crit_chance",0)
        return min(crit_chance, 1.0)

    def get_crit_damage(self):
        crit_damage = (self.base_crit_damage + self.crit_damage * 0.075)
        if self.weapon is not None:
            crit_damage += self.weapon.get("crit_damage",0)
        return crit_damage

    def get_weapon_damage(self):
        if self.weapon is None:
            return 0
        return self.weapon.get("damage",0)

    def get_weapon_defense(self):
        if self.weapon is None:
            return 0
        return self.weapon.get("defense",0)

    def attack(self, enemy):
        weapon_damage = self.get_weapon_damage()
        damage = (
            self.base_damage
            + self.strength * 1.85
            + weapon_damage
            - enemy.defense
        )

        damage = max(0,damage)
        critical = False
        if random.random() < self.get_crit_chance():
            critical = True
            crit_bonus = (damage * self.get_crit_damage())
            damage += crit_bonus

        damage = int(damage)
        enemy.hp -= damage
        if enemy.hp < 0:
            enemy.hp = 0

        if self.weapon is not None and self.weapon["type"] == "dagger":
            self.add_bleed(enemy,damage)

        if critical:
            print("CRITICAL HIT!")
        return damage

    def get_defense(self):
        equipment_defense = (self.get_weapon_defense())
        if self.is_defending:
            total_defense = (
                self.base_defense
                + self.defense * 1.25
                + equipment_defense
            )
        else:
            total_defense = (
                self.base_defense
                + self.defense
                + equipment_defense
            )
        return int(total_defense)

    def add_bleed(self, enemy, attack_damage):
        if not hasattr(enemy, "bleed_stacks"):
            enemy.bleed_stacks = []

        bleed_damage = int(attack_damage * 0.30)
        bleed = {
            "damage": bleed_damage,
            "turns": 2
        }
        enemy.bleed_stacks.append(bleed)

        print(
            "Bleed applied:",
            bleed_damage,
            "damage for 2 turns."
        )

    def bleed(self, enemy):
        if not hasattr(enemy, "bleed_stacks"):
            return 0

        total_bleed_damage = 0
        remaining_bleeds = []

        for bleed in enemy.bleed_stacks:
            enemy.hp -= bleed["damage"]
            total_bleed_damage += (bleed["damage"])
            bleed["turns"] -= 1

            if bleed["turns"] > 0:
                remaining_bleeds.append(bleed)

        enemy.bleed_stacks = (remaining_bleeds)
        if enemy.hp < 0:
            enemy.hp = 0
        if total_bleed_damage > 0:
            print("Bleed dealt",total_bleed_damage,"damage.")
        return total_bleed_damage

    def weapon_recived(self, weapon_type):
        if weapon_type == "sword":
            return {
            "type": "sword",
            "name": "Sword",
            "damage": 15,
            "defense": 0,
            "crit_chance": 0.05,
            "crit_damage": 0.25
        }
        elif weapon_type == "shield":
            return {
            "type": "shield",
            "name": "Shield",
            "damage": 0,
            "defense": 15,
            "crit_chance": 0,
            "crit_damage": 0
        }
        elif weapon_type == "sword_buckler":
            return {
            "type": "sword_buckler",
            "name": "Sword and Buckler",
            "damage": 8,
            "defense": 8,
            "crit_chance": 0,
            "crit_damage": 0
        }
        elif weapon_type == "dagger":
            return {
            "type": "dagger",
            "name": "Dagger",
            "damage": 5,
            "defense": 0,
            "crit_chance": 0.05,
            "crit_damage": 0
        }
        return None
    
    def stats(self):
        while True:
            print("\n====================")
            print("       STATS")
            print("====================")

            print("Strength:", self.strength)
            print("Defense:", self.defense)
            print("Crit:", self.crit)
            print("Crit Damage:", self.crit_damage)
            print("Health:", self.health)

            print("Crit Chance:",
              round(self.get_crit_chance() * 100, 1), "%")

            print("Crit Damage:",
              round(self.get_crit_damage() * 100, 1), "%")

            print("Stat Points:", self.stat_points)

            if self.weapon is None:
                print("Weapon: None")
            else:
                print("Weapon:", self.weapon["name"])

            print("\n1. Add Strength")
            print("2. Add Defense")
            print("3. Add Crit")
            print("4. Add Crit Damage")
            print("5. Add Health")
            print("6. Finish")
            print("7. Reset Stats")
            print("8. Open Inventory")

            choice = input("Choose an option: ")

            if choice == "6":
                return

            if choice == "7":
                stat_point = (
                self.strength
                + self.defense
                + self.health
                + self.crit
                + self.crit_damage
            )

                self.stat_points += stat_point
                self.strength = 0
                self.defense = 0
                self.crit = 0
                self.crit_damage = 0
                self.health = 0

                self.max_hp = self.calculate_max_hp()
                self.hp = self.max_hp

                print("Stats have been reset.")
                continue

            if choice == "8":
                self.inventory_menu()
                continue
            elif choice not in ["1", "2", "3", "4", "5"]:
                print("Invalid choice.")
                continue
            elif self.stat_points <= 0:
                print("You have no stat points.")
                continue

            try:
                stat_number = int(input("Enter # of stat point you want to add: "))
            except ValueError:
                print("Invalid number.")
                continue

            if stat_number <= 0 or stat_number > self.stat_points:
                print("Invalid number.")
                continue

            if choice == "1":
                self.strength += stat_number
            elif choice == "2":
                self.defense += stat_number
            elif choice == "3":
                self.crit += stat_number
            elif choice == "4":
                self.crit_damage += stat_number
            elif choice == "5":
                self.health += stat_number
                self.update_hp()
            self.stat_points -= stat_number


    def add_item(self, item):
        weapon_type = item["type"]

        if weapon_type in self.inventory:
            self.inventory[weapon_type]["count"] += 1
        else:
            self.inventory[weapon_type] = {
            "item": item,
            "count": 1
        }
            
        print(item["name"], "was added to your inventory.")

    def show_inventory(self):
        print("\n====================")
        print("     INVENTORY")
        print("====================")
        if len(self.inventory) == 0:
            print("Inventory is empty.")
        else:
            number = 1
            for weapon_type in self.inventory:
                inventory_item = self.inventory[weapon_type]
                item = inventory_item["item"]
                count = inventory_item["count"]
                print(number,".",item["name"],"x",count)
                number += 1

        if self.weapon is None:
            print("\nEquipped: None")
        else:
            print("\nEquipped:",self.weapon["name"])

    def inventory_menu(self):
        while True:
            self.show_inventory()
            print("\n1. Equip")
            print("2. Unequip")
            print("3. Back")

            choice = input("Choose an option: ")
            if choice == "1":
                self.choose_equipment()
            elif choice == "2":
                self.unequip()
            elif choice == "3":
                return
            else:
                print("Invalid choice.")

    def unequip(self):
        if self.weapon is None:
            print("No equipment is currently equipped.")
            return

        old_weapon = self.weapon
        self.add_item(old_weapon)
        print("Unequipped:", old_weapon["name"])
        self.weapon = None

    def choose_equipment(self):
        if len(self.inventory) == 0:
            print("Inventory is empty.")
            return
        
        weapon_types = list(self.inventory.keys())
        print("\nChoose equipment:")

        for i in range(len(weapon_types)):
            weapon_type = weapon_types[i]
            item = self.inventory[weapon_type]["item"]
            count = self.inventory[weapon_type]["count"]
            print(i + 1,".",item["name"],"x",count)

        try:
            choice = int(input("Choose equipment number: "))
        except ValueError:
            print("Invalid choice.")
            return

        if choice < 1 or choice > len(weapon_types):
            print("Invalid choice.")
            return
        
        weapon_type = weapon_types[choice - 1]
        inventory_item = self.inventory[weapon_type]
        new_weapon = inventory_item["item"]

        if self.weapon is not None:
            self.add_item(self.weapon)
  
        self.weapon = new_weapon.copy()
        inventory_item["count"] -= 1

        if inventory_item["count"] <= 0:
            del self.inventory[weapon_type]
        print("Equipped:",self.weapon["name"])
