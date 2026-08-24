from typing import Dict
import copy
import math

from enemy import BattleState


class PlayerSnapshot:
	def __init__(self, player, added: Dict[str, int]):
		# copy base properties
		self.base_damage = getattr(player, "base_damage", 25)
		self.base_defense = getattr(player, "base_defense", 10)
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
		"""frac = real_hp / real_max if real_max > 0 else 1.0"""
		self.hp = self.max_hp

		# Weapon-derived values
		self._weapon = getattr(player, "weapon", None) or {}
		self.is_defending = getattr(player, "is_defending", False)

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
	Return a granular score in player's perspective between 0 and 1.

	We run a deterministic BattleState rollout and compute a continuous
	metric based on remaining HP ratio: player_share = player_hp / (player_hp + enemy_hp).
	This gives smoother feedback than the coarse win/loss result and makes
	greedy search sensitive to small improvements.
	"""
	snap = PlayerSnapshot(player, added)
	state = BattleState(snap, enemy)

	# play out deterministically as in simulate_match: enemy uses MCTS-light, player attacks
	# To keep this function cheap, use a small MCTS instance for enemy choices
	from mcts import MCTS as _MCTS
	mcts = _MCTS(iter_limit=60, rollout_limit=8)

	while not state.is_terminal():
		if state.current_turn == "enemy":
			action = mcts.search(state)
			if action is None:
				action = "attack"
			state.do_action(action)
		else:
			state.do_action("attack")

	p = float(state.player_hp)
	e = float(state.enemy_hp)
	if p + e <= 0:
		# both dead: neutral
		return 0.5
	# player's share of remaining HP (0..1)
	return p / (p + e)


def analyze_match(player, enemy, max_suggestion_points: int = 7):
	"""
	Analyze a lost match and return (analysis_text, suggestion_dict).

	suggestion_dict maps stat name -> extra points to add.
	"""
	# quick metrics
	# estimate per-attack damages
	player_attack_est = player.base_damage + player.strength * 1.85 + player.get_weapon_damage()
	player_expected_multiplier = 1 + player.get_crit_chance() * player.get_crit_damage()
	player_damage_per_round = max(0, player_attack_est - enemy.defense) * player_expected_multiplier

	enemy_damage_per_round = max(0, enemy.attack - player.get_defense())

	analysis_lines = []
	analysis_lines.append(f"Enemy type: {getattr(enemy, 'type', 'unknown')}")
	analysis_lines.append(f"Player est. damage/round: {player_damage_per_round:.1f}")
	analysis_lines.append(f"Enemy est. damage/round: {enemy_damage_per_round:.1f}")

	# Heuristics about weaknesses
	if player_damage_per_round <= enemy_damage_per_round:
		analysis_lines.append("Your attacks are doing less or equal the amount of damage as the enemy's attacks per round.")
		primary_recommendation = "strength: Try increasing your strength"
	else:
		analysis_lines.append("You deal more damage than the enemy per round, but you still lost. Think about survivability and critical hits.")
		primary_recommendation = "health or defense: Try increasing health or defense for higher chances of survival"

	# Greedy allocation search
	allocation = {"strength": 0, "defense": 0, "crit": 0, "crit_damage": 0, "health": 0}
	best_score = evaluate_allocation(player, enemy, allocation)

	remaining = max_suggestion_points
	# Greedy: in each iteration, consider adding 1..remaining points to each stat,
	# pick the action (stat, points) with the best score improvement.
	while remaining > 0:
		best_delta = 0.0
		best_choice = None
		for stat in allocation.keys():
			for k in range(1, remaining + 1):
				cand = allocation.copy()
				cand[stat] += k
				score = evaluate_allocation(player, enemy, cand)
				delta = score - best_score
				if delta > best_delta:
					best_delta = delta
					best_choice = (stat, k)

		if best_choice is None:
			break
		stat, k = best_choice
		allocation[stat] += k
		remaining -= k
		best_score += best_delta
		if best_score >= 0.999:
			break

	# Provide textual explanation and the allocation
	analysis = "\n".join(analysis_lines)
	suggestion = {k: v for k, v in allocation.items() if v > 0}

	if not suggestion:
		# No single-point greedy allocation improved outcome significantly. Try larger re-specs or different weapon choices.
		analysis += "\nNo small stat change made a big different. Try changing serveral stat points at once or choosing a different weapon."
	else:
		analysis += f"\nSuggested point allocation (greedy up to {max_suggestion_points}): {suggestion}"

		# Add short descriptions for each suggested stat so the player understands why
		rationale_map = {
			"strength": "Increases your damage output so you defeat enemies faster.",
			"defense": "Reduces incoming damage each hit, improving survivability.",
			"health": "Increases max HP so you survive more rounds.",
			"crit": "Raises crit chance, increasing the chance of high-damage hits.",
			"crit_damage": "Boosts crit multiplier, making critical hits much stronger.",
		}

		analysis += "\nWhy these help:"
		for stat, pts in suggestion.items():
			reason = rationale_map.get(stat, "Provides a general improvement.")
			analysis += f"\n- {stat}: +{pts} — {reason}"

	return analysis, suggestion


if __name__ == "__main__":
	print("analyze.py: module for post-match analysis. Import analyze_match() in your code.")

