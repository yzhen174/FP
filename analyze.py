from typing import Dict
import copy
import math

from enemy import BattleState


class PlayerSnapshot:
	def __init__(self, player, added: Dict[str, int]):
		# copy base properties
		self.base_damage = getattr(player, "base_damage", 10)
		self.base_defense = getattr(player, "base_defense", 5)
		self.base_hp = getattr(player, "base_hp", 100)
		self.base_crit_chance = getattr(player, "base_crit_chance", 0.10)
		self.base_crit_damage = getattr(player, "base_crit_damage", 1.00)

		# current stats
		self.strength = getattr(player, "strength", 0) + added.get("strength", 0)
		self.defense = getattr(player, "defense", 0) + added.get("defense", 0)
		self.crit = getattr(player, "crit", 0) + added.get("crit", 0)
		self.crit_damage = getattr(player, "crit_damage", 0) + added.get("crit_damage", 0)
		self.health = getattr(player, "health", 0) + added.get("health", 0)

		# HP and weapon
		# Recompute max_hp similar to Player.calculate_max_hp
		self.max_hp = int(self.base_hp + self.health * 1.5)
		# Start snapshot HP as the current fraction of max on the real player
		real_hp = getattr(player, "hp", self.max_hp)
		real_max = getattr(player, "max_hp", self.max_hp)
		frac = real_hp / real_max if real_max > 0 else 1.0
		self.hp = max(0, int(self.max_hp * frac))

		# Weapon-derived values
		self._weapon = getattr(player, "weapon", None) or {}

	def get_crit_chance(self):
		crit_chance = (self.base_crit_chance + self.crit * 0.025)
		crit_chance += self._weapon.get("crit_chance", 0)
		return min(crit_chance, 1.0)

	def get_crit_damage(self):
		crit_damage = (self.base_crit_damage + self.crit_damage * 0.075)
		crit_damage += self._weapon.get("crit_damage", 0)
		return crit_damage

	def get_weapon_damage(self):
		return self._weapon.get("damage", 0)

	def get_weapon_defense(self):
		return self._weapon.get("defense", 0)

	def get_defense(self):
		equipment_defense = self.get_weapon_defense()
		# we assume not defending during rollout snapshots for simplicity
		total_defense = self.base_defense + self.defense + equipment_defense
		return int(total_defense)


def evaluate_allocation(player, enemy, added: Dict[str, int]) -> float:
	"""
	Return a score in player's perspective: 1.0 = certain win, 0.0 = certain loss.
	Uses the deterministic `BattleState` rollout (enemy perspective get_result).
	"""
	snap = PlayerSnapshot(player, added)
	# Provide a small snapshot object that BattleState expects (duck-typing)
	# BattleState reads attributes and methods like `get_weapon_damage()`.
	state = BattleState(snap, enemy)
	result = state.get_result()
	# `result` is from enemy perspective (1.0 enemy win). Convert to player perspective
	return 1.0 - float(result)


def analyze_match(player, enemy, max_suggestion_points: int = 7):
	"""
	Analyze a lost match and return (analysis_text, suggestion_dict).

	suggestion_dict maps stat name -> extra points to add.
	"""
	# quick metrics
	# estimate per-attack damages
	player_attack_est = player.base_damage + player.strength * 1.75 + player.get_weapon_damage()
	player_expected_multiplier = 1 + player.get_crit_chance() * player.get_crit_damage()
	player_damage_per_round = max(0, player_attack_est - enemy.defense) * player_expected_multiplier

	enemy_damage_per_round = max(0, enemy.attack - player.get_defense())

	analysis_lines = []
	analysis_lines.append(f"Enemy type: {getattr(enemy, 'type', 'unknown')}")
	analysis_lines.append(f"Player est. damage/round: {player_damage_per_round:.1f}")
	analysis_lines.append(f"Enemy est. damage/round: {enemy_damage_per_round:.1f}")

	# Heuristics about weaknesses
	if player_damage_per_round <= enemy_damage_per_round:
		analysis_lines.append("You are doing less or equal damage per round than the enemy.")
		primary_recommendation = "strength"
	else:
		analysis_lines.append("You deal more damage per round than the enemy, but you still lost—consider survivability or crits.")
		primary_recommendation = "health"

	# Greedy allocation search
	allocation = {"strength": 0, "defense": 0, "crit": 0, "crit_damage": 0, "health": 0}
	best_score = evaluate_allocation(player, enemy, allocation)

	for _ in range(max_suggestion_points):
		best_delta = 0.0
		best_stat = None
		for stat in allocation.keys():
			cand = allocation.copy()
			cand[stat] += 1
			score = evaluate_allocation(player, enemy, cand)
			delta = score - best_score
			if delta > best_delta:
				best_delta = delta
				best_stat = stat

		if best_stat is None:
			break
		allocation[best_stat] += 1
		best_score += best_delta
		# stop early if allocation yields a winning deterministic rollout
		if math.isclose(best_score, 1.0) or best_score > 0.999:
			break

	# Provide textual explanation and the allocation
	analysis = "\n".join(analysis_lines)
	suggestion = {k: v for k, v in allocation.items() if v > 0}

	if not suggestion:
		analysis += "\nNo single-point greedy allocation improved outcome significantly. Try larger re-specs or different weapon choices."
	else:
		analysis += f"\nSuggested point allocation (greedy up to {max_suggestion_points}): {suggestion}"

	return analysis, suggestion


if __name__ == "__main__":
	print("analyze.py: module for post-match analysis. Import analyze_match() in your code.")

