AGGRESSIVE = "Aggressive"
DEFENSIVE = "Defensive"
DESPERATE = "Desperate"


def read_world(player, enemy, turn, max_turn):
    enemy_max = enemy.max_hp if enemy.max_hp else 1
    player_max = player.max_hp if player.max_hp else 1
    bleed_stacks = getattr(enemy, "bleed_stacks", [])

    return {
        "enemy_hp_ratio": enemy.hp / enemy_max,
        "player_hp_ratio": player.hp / player_max,
        "player_guarding": player.is_defending,
        "bleed_count": len(bleed_stacks),
        "enemy_type": enemy.type,
        "turns_left": max_turn - turn,
    }


def update_mood(enemy, world):
    current = getattr(enemy, "mood", None)
    enemy_type = world["enemy_type"]

    if enemy_type == "tank":
        mood = _tank_mood(world["enemy_hp_ratio"], current)
    elif enemy_type in ("warrior", "bruiser"):
        mood = _warrior_mood(world["enemy_hp_ratio"], current)
    elif enemy_type == "assassin":
        mood = _assassin_mood(
            world["enemy_hp_ratio"],
            world["player_guarding"],
            world["turns_left"],
            current,
        )
    else:
        mood = AGGRESSIVE

    enemy.mood = mood
    return mood


def _tank_mood(hp_ratio, current):
    if current == DESPERATE:
        if hp_ratio > 0.35:
            return DEFENSIVE
        return DESPERATE
    if hp_ratio > 0.30:
        return DEFENSIVE
    return DESPERATE


def _warrior_mood(hp_ratio, current):
    if current == DEFENSIVE:
        if hp_ratio > 0.45:
            return AGGRESSIVE
        return DEFENSIVE
    if hp_ratio > 0.40:
        return AGGRESSIVE
    return DEFENSIVE


def _assassin_mood(hp_ratio, player_guarding, turns_left, current):
    low_hp = hp_ratio < 0.25
    almost_out_of_time = turns_left <= 2

    if current == DESPERATE:
        if hp_ratio < 0.30 or turns_left <= 2:
            return DESPERATE

    if low_hp or almost_out_of_time:
        return DESPERATE
    if player_guarding:
        return DEFENSIVE
    return AGGRESSIVE


class Condition:
    def __init__(self, check):
        self.check = check

    def run(self, world):
        if self.check(world):
            return "success"
        return "failure"


class Action:
    def __init__(self, name):
        self.name = name

    def run(self, world):
        return self.name


class Sequence:
    def __init__(self, *children):
        self.children = children

    def run(self, world):
        result = "success"
        for child in self.children:
            result = child.run(world)
            if result == "failure":
                return "failure"
        return result


class Selector:
    def __init__(self, *children):
        self.children = children

    def run(self, world):
        for child in self.children:
            result = child.run(world)
            if result != "failure":
                return result
        return "failure"


LOW_HP_TREE = Selector(
    Sequence(
        Condition(lambda world: world["enemy_hp_ratio"] < 0.30),
        Action("defend"),
    ),
    Action("attack"),
)

TANK_TREE = Selector(
    Sequence(
        Condition(lambda world: world["mood"] == DESPERATE),
        Action("attack"),
    ),
    Sequence(
        Condition(lambda world: world["mood"] == DEFENSIVE),
        Action("defend"),
    ),
    Sequence(
        Condition(lambda world: world["player_guarding"]),
        Action("defend"),
    ),
    Action("attack"),
)

WARRIOR_TREE = Selector(
    Sequence(
        Condition(lambda world: world["mood"] == AGGRESSIVE),
        Action("attack"),
    ),
    Sequence(
        Condition(lambda world: world["mood"] == DEFENSIVE),
        Condition(lambda world: world["enemy_hp_ratio"] < 0.40),
        Action("defend"),
    ),
    Action("attack"),
)

ASSASSIN_TREE = Selector(
    Sequence(
        Condition(
            lambda world: (
                world["mood"] == DESPERATE or world["turns_left"] <= 2
            )
        ),
        Action("attack"),
    ),
    Sequence(
        Condition(lambda world: world["player_guarding"]),
        Action("defend"),
    ),
    Action("attack"),
)

TREES = {
    "tank": TANK_TREE,
    "warrior": WARRIOR_TREE,
    "assassin": ASSASSIN_TREE,
    # Bruiser is like a warrior but more likely to guard against a defending player
    # and will choose to defend earlier when its HP is moderately low.
    "bruiser": Selector(
        Sequence(
            Condition(lambda world: world["mood"] == AGGRESSIVE),
            Action("attack"),
        ),
        Sequence(
            Condition(lambda world: world["player_guarding"]),
            Action("defend"),
        ),
        Sequence(
            Condition(lambda world: world["mood"] == DEFENSIVE),
            Condition(lambda world: world["enemy_hp_ratio"] < 0.55),
            Action("defend"),
        ),
        Action("attack"),
    ),
}


def tick(player, enemy, turn, max_turn):
    world = read_world(player, enemy, turn, max_turn)
    update_mood(enemy, world)
    world["mood"] = enemy.mood
    tree = TREES.get(enemy.type, LOW_HP_TREE)
    result = tree.run(world)
    if result in ("attack", "defend"):
        return result
    return "attack"


def legal_actions(player, enemy, turn, max_turn):
    tick(player, enemy, turn, max_turn)

    if enemy.type == "tank" and enemy.mood == DEFENSIVE:
        return ["defend"]
    if enemy.mood == DESPERATE:
        return ["attack"]
    if (
        enemy.type == "assassin"
        and player.is_defending
        and enemy.mood != DESPERATE
    ):
        return ["defend"]
    return ["attack", "defend"]


class FakePlayer:
    def __init__(self, hp=100, max_hp=100, is_defending=False):
        self.hp = hp
        self.max_hp = max_hp
        self.is_defending = is_defending

    def get_defense(self):
        return 5


def run_case(title, enemy_type, player, hp_ratio=1.0, max_turn=10):
    from enemy import Enemy

    enemy = Enemy(1, enemy_type)
    enemy.hp = int(enemy.max_hp * hp_ratio)
    print("\n====", title, "====")
    print("type:", enemy.type, "hp:", enemy.hp, "/", enemy.max_hp)
    print("player guarding:", player.is_defending)

    for turn in range(1, max_turn + 1):
        action = tick(player, enemy, turn, max_turn)
        print("turn", turn, "| mood:", enemy.mood, "| action:", action)


if __name__ == "__main__":
    attacker = FakePlayer(is_defending=False)
    guarder = FakePlayer(is_defending=True)

    run_case("tank vs attacker", "tank", attacker)
    run_case("warrior vs attacker", "warrior", attacker)
    run_case("assassin vs attacker", "assassin", attacker)

    run_case("tank vs guard", "tank", guarder)
    run_case("assassin vs guard", "assassin", guarder)

    run_case("tank at 20% HP", "tank", attacker, hp_ratio=0.20)
    run_case("assassin at 20% HP", "assassin", attacker, hp_ratio=0.20)

