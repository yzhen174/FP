import random
import copy
from mcts import MCTS
from enemy_ai import legal_actions


class Enemy:
    def __init__(self, level: int = 1, enemy_type=None):
        types = {
            "warrior": {"hp": 120, "attack": 18, "defense": 8},
            "tank": {"hp": 160, "attack": 12, "defense": 14},
            "assassin": {"hp": 90, "attack": 22, "defense": 4},
            "bruiser": {"hp": 130, "attack": 16, "defense": 10},
        }

        self.level = level
        self.type = enemy_type or random.choice(list(types.keys()))
        base = types[self.type]

        # scale a little with level
        self.max_hp = int(base["hp"] * (1 + (level - 1) * 0.15))
        self.hp = self.max_hp
        self.attack = int(base["attack"] * (1 + (level - 1) * 0.10))
        self.defense = int(base["defense"] * (1 + (level - 1) * 0.10))

        self.is_defending = False
        self.bleed_stacks = []

    def __repr__(self):
        return f"<Enemy {self.type} L{self.level} HP:{self.hp}/{self.max_hp} ATK:{self.attack} DEF:{self.defense}>"

    def attack_player(self, player, turn=1, max_turn=10):
        """
        Decide an action using MCTS and apply it against the real `player`.

        Behavior trees filter which actions MCTS may search.
        Returns the integer damage dealt (0 for defend).
        """
        allowed = legal_actions(player, self, turn, max_turn)
        if not allowed:
            allowed = ["attack", "defend"]

        state = BattleState(player, self, enemy_legal=allowed)
        mcts = MCTS(iter_limit=200, rollout_limit=12)
        best_action = mcts.search(state)

        if best_action is None or best_action not in allowed:
            best_action = random.choice(allowed)

        if best_action == "defend":
            self.is_defending = True
            return 0

        # perform an actual attack on the live player
        damage = self._compute_damage_vs_player(player)
        player.hp -= damage
        if player.hp < 0:
            player.hp = 0

        return damage

    def _compute_damage_vs_player(self, player):
        # Enemy attack minus player's defense
        player_def = player.get_defense()
        raw = self.attack - player_def
        dmg = max(0, int(raw))
        return dmg


class BattleState:
    """
    Minimal battle state adapter for running MCTS rollouts.

    This avoids mutating the real `Player`/`Enemy` objects by copying only the
    stats we need for simulation. Rollouts are deterministic and use expected
    crit values instead of sampling random crits.
    """

    def __init__(self, player, enemy, enemy_legal=None):
        # Player fields (snapshot)
        self.player_hp = int(player.hp)
        self.player_max_hp = int(player.max_hp)
        self.player_base_damage = float(player.base_damage)
        self.player_strength = float(player.strength)
        self.player_weapon_damage = float(player.get_weapon_damage())
        self.player_weapon_defense = float(player.get_weapon_defense())
        self.player_crit_chance = float(player.get_crit_chance())
        self.player_crit_damage = float(player.get_crit_damage())
        self.player_is_defending = bool(player.is_defending)

        # Enemy fields (snapshot)
        self.enemy_hp = int(enemy.hp)
        self.enemy_max_hp = int(enemy.max_hp)
        self.enemy_attack = float(enemy.attack)
        self.enemy_defense = float(enemy.defense)
        self.enemy_is_defending = bool(enemy.is_defending)

        # turn control for simulation: enemy moves first (we are deciding for enemy)
        self.current_turn = "enemy"
        self.turns = 0
        self.max_turns = 10
        self.enemy_legal = list(enemy_legal) if enemy_legal else ["attack", "defend"]

    def clone(self):
        return copy.deepcopy(self)

    def get_legal_actions(self):
        if self.is_terminal():
            return []
        if self.current_turn == "enemy":
            return list(self.enemy_legal)
        # for rollout simplicity, assume the player always attacks
        return ["attack"]

    def do_action(self, action):
        if self.is_terminal():
            return

        if self.current_turn == "enemy":
            if action == "defend":
                self.enemy_is_defending = True
            else:
                # compute enemy -> player damage using simple formula
                player_def = int(self.player_weapon_defense + (self.player_is_defending and (self.player_weapon_defense * 0.0) or 0) + (5 + self.player_strength * 1.0))
                # The above mixes a conservative estimate of player's defense.
                raw = self.enemy_attack - player_def
                dmg = max(0, int(raw))
                self.player_hp -= dmg
                if self.player_hp < 0:
                    self.player_hp = 0
            self.current_turn = "player"
        else:
            # player attacks -> enemy takes expected damage (include expected crit)
            base = self.player_base_damage + self.player_strength * 1.75 + self.player_weapon_damage
            damage = max(0, base - self.enemy_defense)
            # expected crit multiplier
            damage = damage * (1 + self.player_crit_chance * self.player_crit_damage)
            damage = int(damage)
            self.enemy_hp -= damage
            if self.enemy_hp < 0:
                self.enemy_hp = 0
            self.current_turn = "enemy"

        self.turns += 1

    def is_terminal(self):
        return self.player_hp <= 0 or self.enemy_hp <= 0 or self.turns >= self.max_turns

    def get_result(self, player=None):
        """
        Return reward from the enemy's perspective: 1.0 enemy win, 0.0 enemy loss.
        """
        if self.enemy_hp <= 0 and self.player_hp <= 0:
            return 0.5
        if self.player_hp <= 0:
            return 1.0
        if self.enemy_hp <= 0:
            return 0.0

        # If timeout, compare remaining HP
        if self.enemy_hp > self.player_hp:
            return 1.0
        if self.enemy_hp < self.player_hp:
            return 0.0
        return 0.5
