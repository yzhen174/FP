import math
import random
from typing import Any, Optional


class Node:
    def __init__(self, state: Any, parent: Optional['Node'] = None, parent_action: Any = None):
        self.state = state
        self.parent = parent
        self.parent_action = parent_action
        self.children = []
        self._untried_actions = None
        self.visits = 0
        self.wins = 0.0

    def untried_actions(self):
        if self._untried_actions is None:
            try:
                self._untried_actions = list(self.state.get_legal_actions())
            except Exception:
                self._untried_actions = []
        return self._untried_actions

    def uct_select_child(self, exploration: float = math.sqrt(2.0)) -> 'Node':
        # UCT selection: maximize win_rate + exploration * sqrt(ln(N)/n)
        assert self.children, "No children to select from"
        best = max(
            self.children,
            key=lambda c: (c.wins / c.visits) + exploration * math.sqrt(2 * math.log(self.visits) / c.visits),
        )
        return best

    def add_child(self, action: Any, state: Any) -> 'Node':
        child = Node(state, parent=self, parent_action=action)
        # lazily initialize untried actions list
        if self._untried_actions is None:
            try:
                self._untried_actions = list(self.state.get_legal_actions())
            except Exception:
                self._untried_actions = []
        try:
            self._untried_actions.remove(action)
        except ValueError:
            pass
        self.children.append(child)
        return child

    def update(self, result: float) -> None:
        self.visits += 1
        self.wins += result


class MCTS:
    def __init__(self, iter_limit: int = 1000, exploration: float = math.sqrt(2.0), rollout_limit: int = 100):
        self.iter_limit = iter_limit
        self.exploration = exploration
        self.rollout_limit = rollout_limit

    def search(self, root_state: Any, return_node: bool = False) -> Any:
        """
        Run MCTS starting from `root_state`.

        Returns the best action found (the action leading to the child with
        the highest visit count). If `return_node` is True, returns the Node
        for that child instead of the action.
        """
        root_node = Node(root_state)

        for _ in range(self.iter_limit):
            node = root_node
            state = root_state.clone()

            # Selection
            while node.untried_actions() == [] and node.children:
                node = node.uct_select_child(self.exploration)
                state.do_action(node.parent_action)

            # Expansion
            untried = node.untried_actions()
            if untried:
                action = random.choice(untried)
                state.do_action(action)
                node = node.add_child(action, state.clone())

            # Simulation / Rollout
            rollout_state = state.clone()
            rollout_steps = 0
            while (not rollout_state.is_terminal()) and rollout_steps < self.rollout_limit:
                actions = rollout_state.get_legal_actions()
                if not actions:
                    break
                rollout_state.do_action(random.choice(actions))
                rollout_steps += 1

            # Backpropagation
            result = self._get_result(root_state, rollout_state)
            while node is not None:
                node.update(result)
                node = node.parent

        # choose the most visited child
        if not root_node.children:
            return None if not return_node else root_node

        best_child = max(root_node.children, key=lambda c: c.visits)
        return best_child if return_node else best_child.parent_action

    def _get_result(self, root_state: Any, terminal_state: Any) -> float:
        # Try get_result with a player if possible
        try:
            player = getattr(root_state, "player", None)
            if player is not None:
                return float(terminal_state.get_result(player))
        except Exception:
            pass

        try:
            return float(terminal_state.get_result())
        except Exception:
            pass

        # Fallback to common attributes
        for attr in ("reward", "score", "value"):
            if hasattr(terminal_state, attr):
                try:
                    return float(getattr(terminal_state, attr))
                except Exception:
                    continue

        # If nothing else available, return 0/1 based on terminal_state.is_terminal()
        try:
            return 1.0 if terminal_state.is_terminal() else 0.0
        except Exception:
            return 0.0


if __name__ == "__main__":
    print("mcts.py: MCTS core module. Import and use MCTS in your game integration.")
