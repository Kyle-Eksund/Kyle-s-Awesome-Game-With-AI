"""Temple Time - Player model and simple temple adventure demo.

This module defines a Player class to track health, food, money, and carried items.
It also includes a small CLI story and a simple temple run where your item choices
can help you survive enemies and traps.

Run this file directly to start a simple interactive demo.
"""

import random
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class Item:
    """A simple item that can affect the player's journey."""

    name: str
    description: str
    # Effect is a callable that takes (player, context) and returns a string describing what happened.
    effect: Callable[["Player", Dict], str]


@dataclass
class Enemy:
    """An enemy encountered in the temple."""

    name: str
    health: int
    damage: int
    special: Optional[str] = None  # e.g., "poison", "shield"
    armor: int = 0

    @property
    def is_alive(self) -> bool:
        return self.health > 0


@dataclass
class Player:
    """A player in the "Temple Time" adventure."""

    name: str
    health: int = 100
    food: int = 50
    money: int = 20
    items: List[Item] = field(default_factory=list)
    poisoned_turns: int = 0

    def status(self) -> str:
        """Return a short status summary."""
        status = (
            f"{self.name}: Health={self.health}, Food={self.food}, Money={self.money}, "
            f"Items={[item.name for item in self.items]}"
        )
        if self.poisoned_turns > 0:
            status += f", Poisoned({self.poisoned_turns})"
        return status

    def apply_status_effects(self) -> Optional[str]:
        """Apply status effects like poison at the start of a turn."""
        if self.poisoned_turns > 0:
            self.poisoned_turns -= 1
            self.health = max(self.health - 5, 0)
            return "You suffer 5 poison damage." if self.health > 0 else "Poison kills you."
        return None

    def status(self) -> str:
        """Return a short status summary."""
        return (
            f"{self.name}: Health={self.health}, Food={self.food}, Money={self.money}, "
            f"Items={[item.name for item in self.items]}"
        )

    def take_damage(self, amount: int, reason: str = "") -> str:
        """Apply damage to the player."""
        self.health = max(self.health - amount, 0)
        return f"{reason} (-{amount} HP)" if reason else f"Took {amount} damage."

    def heal(self, amount: int) -> str:
        """Heal the player."""
        old = self.health
        self.health = min(self.health + amount, 100)
        return f"Healed {self.health - old} HP."

    def eat(self, amount: int) -> str:
        """Eat food to restore a little health.

        Eating also reduces food supply.
        """
        if self.food <= 0:
            return "You have no food to eat."

        used = min(self.food, amount)
        self.food -= used
        heal = used // 2
        self.health = min(self.health + heal, 100)
        return f"Ate {used} food and recovered {heal} health."

    def spend(self, amount: int) -> bool:
        """Spend money if available."""
        if amount > self.money:
            return False
        self.money -= amount
        return True

    def add_item(self, item: Item) -> None:
        """Add an item to the player's inventory."""
        self.items.append(item)

    def use_item(self, item_name: str, context: Dict) -> str:
        """Use an item by name if the player has it."""
        for item in self.items:
            if item.name.lower() == item_name.lower():
                return item.effect(self, context)
        return f"You don't have a {item_name}."


# ---------------------------------------------------------------------------
# Item effects
# ---------------------------------------------------------------------------

def effect_torch(player: Player, context: Dict) -> str:
    """A torch helps you avoid traps in the temple."""
    if context.get("event") == "trap":
        # Avoid some damage
        return "Your torch lights the way and you carefully avoid the trap."

    return "You hold the torch high, lighting the dark passage."


def effect_rope(player: Player, context: Dict) -> str:
    """A rope can save you from falls or help you climb."""
    if context.get("event") == "pit":
        return "You toss the rope across the pit, slide down safely, and avoid falling."

    return "You feel secure with the rope in your pack."


def effect_potion(player: Player, context: Dict) -> str:
    """A potion heals the player and is consumed."""
    # Remove the potion from inventory once used.
    player.items = [i for i in player.items if i.name != "Healing Potion"]
    return player.heal(30)


def effect_dagger(player: Player, context: Dict) -> str:
    """A dagger helps against enemies."""
    if context.get("event") == "combat" and isinstance(context.get("enemy"), Enemy):
        enemy: Enemy = context["enemy"]
        damage = random.randint(10, 18)
        enemy.health = max(enemy.health - damage, 0)
        if not enemy.is_alive:
            return f"You strike true with your dagger and defeat the {enemy.name}!"
        return f"You slash the {enemy.name} for {damage} damage. It has {enemy.health} HP left."

    return "You keep the dagger ready, just in case."


def effect_food_rations(player: Player, context: Dict) -> str:
    """Food rations can restore energy mid-run."""
    # Remove rations when used.
    player.items = [i for i in player.items if i.name != "Food Rations"]
    player.food += 20
    return "You eat the rations and feel energized (+20 food)."


def build_default_items() -> List[Item]:
    return [
        Item(
            name="Torch",
            description="Lights dark corridors and helps detect traps.",
            effect=effect_torch,
        ),
        Item(
            name="Rope",
            description="Useful for climbing and crossing pits safely.",
            effect=effect_rope,
        ),
        Item(
            name="Healing Potion",
            description="Restores health when used.",
            effect=effect_potion,
        ),
        Item(
            name="Dagger",
            description="A basic weapon to help fend off enemies.",
            effect=effect_dagger,
        ),
        Item(
            name="Food Rations",
            description="Extra food to keep you fed in the temple.",
            effect=effect_food_rations,
        ),
    ]


def generate_enemy(depth: int) -> Enemy:
    """Create a randomized enemy scaled to the depth of the temple."""
    choices = [
        ("Cave Snake", 20 + depth * 4, 6 + depth * 2, "poison", 0),
        ("Ancient Warrior", 28 + depth * 5, 8 + depth * 2, "shield", 3),
        ("Temple Guard", 26 + depth * 5, 7 + depth * 2, None, 1),
        ("Temple Bat", 18 + depth * 3, 5 + depth * 2, None, 0),
        ("Crypt Spider", 22 + depth * 4, 6 + depth * 2, "poison", 0),
    ]
    name, hp, dmg, special, armor = random.choice(choices)
    return Enemy(name=name, health=hp, damage=dmg, special=special, armor=armor)


def run_combat(player: Player, enemy: Enemy) -> bool:
    """Run a simple turn-based combat encounter."""

    print(f"\nA {enemy.name} attacks! (HP: {enemy.health})")

    while player.health > 0 and enemy.is_alive:
        # Status effects first
        status_msg = player.apply_status_effects()
        if status_msg:
            print(status_msg)
            if player.health <= 0:
                break

        print(f"\n-- Combat: {player.name} (HP {player.health}) vs {enemy.name} (HP {enemy.health})")
        print("  1) Attack")
        print("  2) Use item")
        print("  3) Run")
        print("  4) Check status")
        choice = input("Choose an action (1-4): ").strip()

        if choice == "1":
            base = random.randint(8, 14)
            crit = random.random() < 0.18
            damage = int(base * 1.5) if crit else base
            if enemy.armor > 0:
                mitigated = min(enemy.armor, damage)
                damage -= mitigated
                print(f"The {enemy.name}'s armor absorbs {mitigated} damage.")
            enemy.health = max(enemy.health - damage, 0)
            hit_word = "critical hit" if crit else "hit"
            print(f"You {hit_word} the {enemy.name} for {damage} damage.")

        elif choice == "2":
            if not player.items:
                print("You have no items to use.")
                continue
            print("Items:", ", ".join(i.name for i in player.items))
            item_name = input("Which item do you want to use? ").strip()
            if not item_name:
                continue
            print(player.use_item(item_name, {"event": "combat", "enemy": enemy}))
            if not enemy.is_alive:
                break
            continue

        elif choice == "3":
            escape_chance = 0.5
            if random.random() < escape_chance:
                print(f"You break away from the {enemy.name} and flee deeper into the temple.")
                return True
            print("You fail to escape!")

        elif choice == "4":
            print(player.status())
            continue

        else:
            print("Not a valid choice. Please enter 1-4.")
            continue

        # Enemy turn
        if enemy.is_alive:
            if enemy.special == "poison" and random.random() < 0.25:
                player.poisoned_turns = max(player.poisoned_turns, 3)
                print(f"The {enemy.name} bites you and injects poison!")

            if random.random() < 0.2:
                print(f"You dodge the {enemy.name}'s attack!")
            else:
                enemy_damage = random.randint(max(enemy.damage - 2, 1), enemy.damage + 2)
                print(player.take_damage(enemy_damage, f"The {enemy.name} attacks!"))

    if player.health <= 0:
        print("You fall to the floor, defeated by your foe.")
        return False

    print(f"You have defeated the {enemy.name}.")
    return True


def attempt_exit(chamber: int) -> bool:
    """Attempt to exit the temple; the deeper you go, the harder it becomes."""
    base_chance = 0.9
    penalty = 0.12 * (chamber - 1)
    chance = max(base_chance - penalty, 0.1)
    roll = random.random()
    print(f"You try to find your way out (success chance {chance:.0%})...")
    if roll < chance:
        print("You remember the way and escape the temple!")
        return True
    print("You wander the corridors and lose your way...")
    return False


def maybe_random_encounter(player: Player, chamber: int) -> bool:
    """Random chance to encounter a roaming threat in the temple."""
    if random.random() > 0.35:
        return True

    enemy = generate_enemy(chamber)
    print(f"\nAs you move forward, a {enemy.name} lunges from the shadows!")
    return run_combat(player, enemy)


# ---------------------------------------------------------------------------
# Adventure flow
# ---------------------------------------------------------------------------

def print_header() -> None:
    print("\n=== TEMPLE TIME ===\n")


def show_backstory() -> None:
    story = (
        "You are an explorer drawn to the fabled Temple of Time. "
        "Legends say the temple tests those who enter with clever traps, ancient guardians, "
        "and strange time-warping rooms."
    )
    print(story)


def choose_items(available_items: List[Item], count: int = 2) -> List[Item]:
    """Prompt the player to choose starting items."""

    print("\nBefore you enter, choose two items to bring with you:")
    for idx, item in enumerate(available_items, start=1):
        print(f"  {idx}. {item.name}: {item.description}")

    chosen: List[Item] = []
    while len(chosen) < count:
        choice = input(f"Choose item {len(chosen) + 1} (1-{len(available_items)}): ").strip()
        if not choice.isdigit():
            print("Please enter a number.")
            continue

        idx = int(choice)
        if idx < 1 or idx > len(available_items):
            print("Not a valid choice.")
            continue

        item = available_items[idx - 1]
        if item in chosen:
            print("You already selected that item.")
            continue

        chosen.append(item)
        print(f"Picked: {item.name}.\n")

    return chosen


def choose_room(chamber: int) -> Dict:
    """Pick a room type and description based on how deep you are in the temple."""

    room_types = ["empty", "treasure", "enemy", "trap", "heal", "pit"]
    weights = [0.35, 0.18, 0.2, 0.15, 0.06, 0.06]
    room_type = random.choices(room_types, weights, k=1)[0]

    if room_type == "enemy":
        name = random.choice([
            "echoing hall", "shaded alcove", "ancient corridor", "tomb-lined passage"
        ])
        return {
            "type": "enemy",
            "name": name,
            "description": f"The air feels heavy; you sense something watching you in the {name}.",
        }

    if room_type == "trap":
        name = random.choice([
            "shadowy corridor", "spike trap chute", "sudden collapse", "frozen chamber"
        ])
        damage = random.randint(10, 18) + chamber
        return {
            "type": "trap",
            "name": name,
            "description": f"You feel a shiver as you step into the {name}. Something feels off.",
            "damage": damage,
        }

    if room_type == "pit":
        name = random.choice(["bottomless pit", "gaping chasm", "deep crevasse"])
        damage = random.randint(18, 30)
        return {
            "type": "pit",
            "name": name,
            "description": f"You arrive at a {name}. It's too wide to jump across.",
            "damage": damage,
        }

    if room_type == "heal":
        name = random.choice(["mysterious heal fountain", "glowing pool", "soothing spring"])
        heal = random.randint(12, 22)
        return {
            "type": "heal",
            "name": name,
            "description": f"You see a {name}, its waters shimmer with a calming light.",
            "heal": heal,
        }

    if room_type == "treasure":
        name = random.choice(["hidden alcove", "ancient chest", "forgotten treasure room"])
        return {
            "type": "treasure",
            "name": name,
            "description": f"You discover a {name}. It may hold something valuable.",
        }

    # Empty
    name = random.choice(["empty chamber", "torch-lit cavern", "quiet room"])
    return {
        "type": "empty",
        "name": name,
        "description": f"You step into a {name}. It's eerily quiet.",
    }


def run_temple_run(player: Player) -> None:
    """Run through a short series of temple chambers."""

    chambers = random.randint(4, 6)
    print(f"\nThe temple stretches ahead. You must survive {chambers} chambers to escape.")

    chamber = 0
    while chamber < chambers and player.health > 0:
        chamber += 1
        room = choose_room(chamber)

        print(f"\n--- Chamber {chamber} ---")
        print(room["description"])

        # Allow the player to decide how to proceed
        while True:
            print("\nWhat would you like to do?")
            print("  1) Proceed")
            print("  2) Use an item")
            print("  3) Eat food")
            print("  4) Check status")
            print("  5) Exit temple")
            choice = input("Choose an option (1-5): ").strip().lower()

            if choice in ("1", "p", "proceed"):
                break
            if choice in ("2", "i", "item", "use"):
                if not player.items:
                    print("You have no items to use.")
                    continue
                print("Items:", ", ".join(i.name for i in player.items))
                item_name = input("Which item do you want to use? ").strip()
                if not item_name:
                    continue
                print(player.use_item(item_name, {"event": room["type"]}))
                continue
            if choice in ("3", "e", "eat"):
                print(player.eat(10))
                continue
            if choice in ("4", "s", "status"):
                print(player.status())
                continue
            if choice in ("5", "x", "exit"):
                if attempt_exit(chamber):
                    return
                player.food = max(player.food - 10, 0)
                player.take_damage(5, "Wandering in the dark")
                print("You lose time and food as you stumble around.")
                break

            print("Not a valid choice. Please enter 1-5.")

        if player.health <= 0:
            break

        # Random roaming threat
        if not maybe_random_encounter(player, chamber):
            break
        if player.health <= 0:
            break

        # Resolve room outcome
        if room["type"] == "trap":
            if any(i.name == "Torch" for i in player.items):
                print("Your torch helped you spot the trap and you avoid it.")
            else:
                print(player.take_damage(room["damage"], "A trap triggers!"))

        elif room["type"] == "enemy":
            enemy = generate_enemy(chamber)
            enemy.name = room["name"]
            if not run_combat(player, enemy):
                break

        elif room["type"] == "pit":
            if any(i.name == "Rope" for i in player.items):
                print("You lower the rope and cross safely.")
            else:
                print(player.take_damage(room["damage"], "You fall into the pit!"))

        elif room["type"] == "heal":
            print(player.heal(room["heal"]))

        elif room["type"] == "treasure":
            treasure_roll = random.random()
            if treasure_roll < 0.4:
                amount = random.randint(8, 18)
                player.money += amount
                print(f"You find {amount} gold coins! (+{amount} money)")
            elif treasure_roll < 0.7:
                amount = random.randint(8, 18)
                player.food += amount
                print(f"You find some preserved food and eat it. (+{amount} food)")
            else:
                # Find a useful item
                new_item = random.choice(["Healing Potion", "Food Rations"])
                if new_item not in [i.name for i in player.items]:
                    items = build_default_items()
                    item_obj = next(i for i in items if i.name == new_item)
                    player.add_item(item_obj)
                    print(f"You discover a {new_item} and add it to your pack.")
                else:
                    extra = random.randint(5, 12)
                    player.money += extra
                    print(f"You find {extra} gold coins tucked away. (+{extra} money)")

        elif room["type"] == "empty":
            find_roll = random.random()
            if find_roll < 0.25:
                print("A hidden drawer slides open, revealing a few coins.")
                player.money += random.randint(3, 8)
            elif find_roll < 0.55:
                print("You find a small sack of rations hidden in the corner.")
                player.food += 10
            elif find_roll < 0.7:
                print("A loose tile snaps under your foot!")
                print(player.take_damage(8, "A hidden spike hits you."))
            else:
                print("The room is quiet. Nothing happens.")

        # Food drains a bit after each chamber
        player.food = max(player.food - 5, 0)
        if player.food == 0:
            print("You are starving and feel weak...")
            player.take_damage(10, "Starvation")

        print(player.status())

    if player.health > 0 and chamber >= chambers:
        print("\nYou exit the temple, battered but alive. The legend lives on!")
    elif player.health > 0:
        print("\nYou left the temple and live to come back another day.")
    else:
        print("\nYou succumbed to the temple's trials. The story ends here.")


def main() -> None:
    print_header()
    show_backstory()
    name = input("What is your name, explorer? ").strip() or "Traveler"

    while True:
        player = Player(name=name)
        items = build_default_items()
        chosen = choose_items(items, count=2)
        for item in chosen:
            player.add_item(item)

        print("\nYour journey begins...")
        print(player.status())

        run_temple_run(player)

        again = input("\nPlay again? (y/n): ").strip().lower()
        if again not in ("y", "yes"):
            print("\nThanks for playing Temple Time. Safe travels!")
            break
        print("\n--- A new run begins ---\n")


if __name__ == "__main__":
    main()
