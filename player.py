"""Temple Time - Player model and simple temple adventure demo.

This module defines a Player class to track health, food, money, and carried items.
It also includes a small CLI story and a simple temple run where your item choices
can help you survive enemies and traps.

Run this file directly to start a simple interactive demo.
"""

import random
import time
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


# ---------------------------------------------------------------------------
# Word list and typing minigame
# ---------------------------------------------------------------------------

COMBAT_WORDS = [
    "strike", "slash", "thrust", "pierce", "smite", "cleave", "swiftly",
    "warrior", "temple", "combat", "fiery", "ancient", "shadow", "lightning",
    "roar", "charge", "defend", "courage", "battle", "victory", "dragon",
    "phoenix", "granite", "thunderstorm", "moonlight", "crystal", "obsidian",
    "avalanche", "earthquake", "phoenix", "horizon", "destiny", "adventure"
]


def print_slowly(text: str, delay: float = 0.03) -> None:
    """Print text slowly, one character at a time, for dramatic effect."""
    for char in text:
        print(char, end="", flush=True)
        time.sleep(delay)
    print()


def run_typing_minigame() -> int:
    """Run a typing minigame where player types a random word to deal damage."""
    word = random.choice(COMBAT_WORDS)
    player_input = input(f"Type '{word}': ").strip()
    
    if player_input.lower() == word.lower():
        damage = 8 + (len(word) * 2)
        print(f"+{damage} damage!")
        return damage
    else:
        damage = random.randint(4, 6)
        print(f"+{damage} damage (wrong word)")
        return damage


@dataclass
class Player:
    """A player in the "Temple Time" adventure."""

    name: str
    health: int = 100
    food: int = 100  # more starting food to survive longer
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
        """Consume food to heal; heals 5 health per use and shows remaining food."""
        if self.food <= 0:
            return "You have no food to eat."

        self.food -= 1
        heal = 5
        self.health = min(self.health + heal, 100)
        return f"Ate food (-1). Health +{heal}. Food left: {self.food}."
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
        """Use an item by name if the player has it. The item is consumed."""
        for idx, item in enumerate(self.items):
            if item.name.lower() == item_name.lower():
                result = item.effect(self, context)
                # remove item from inventory
                self.items.pop(idx)
                return result
        return f"You don't have a {item_name}."


# ---------------------------------------------------------------------------
# Item effects
# ---------------------------------------------------------------------------

def effect_torch(player: Player, context: Dict) -> str:
    """A torch helps you avoid traps and can burn foes in combat."""
    if context.get("event") == "trap":
        # Avoid some damage
        return "Your torch lights the way and you carefully avoid the trap."

    if context.get("event") == "combat" and isinstance(context.get("enemy"), Enemy):
        enemy: Enemy = context["enemy"]
        # sometimes you burn, sometimes you distract
        if random.random() < 0.4:
            enemy.damage = max(enemy.damage - 1, 1)
            return f"You hurl the torch, distracting the {enemy.name} and weakening its next strike."
        damage = random.randint(5, 10)
        enemy.health = max(enemy.health - damage, 0)
        if not enemy.is_alive:
            return f"You blaze the {enemy.name} with your torch and it goes down in flames!"
        return f"You swing the torch, burning the {enemy.name} for {damage} damage."

    return "You hold the torch high, lighting the dark passage."


def effect_rope(player: Player, context: Dict) -> str:
    """A rope can save you from falls or help you climb, and can be used in combat."""
    if context.get("event") == "pit":
        return "You toss the rope across the pit, slide down safely, and avoid falling."

    if context.get("event") == "combat" and isinstance(context.get("enemy"), Enemy):
        enemy: Enemy = context["enemy"]
        # binding the enemy reduces its armor and damage
        reduced = min(enemy.armor, 2)
        enemy.armor = max(enemy.armor - reduced, 0)
        enemy.damage = max(enemy.damage - 2, 1)
        return (
            f"You lasso and wrap the {enemy.name}, weakening its attacks (-{reduced} armor, -2 damage)."
        )

    return "You feel secure with the rope in your pack."
def effect_potion(player: Player, context: Dict) -> str:
    """A potion heals the player and is consumed.  In combat it also soothes wounds quickly or can be thrown."""
    # inventory removal handled by use_item
    if context.get("event") == "combat" and isinstance(context.get("enemy"), Enemy):
        enemy: Enemy = context["enemy"]
        if random.random() < 0.5:
            # drink to heal
            msg = player.heal(30)
            if player.poisoned_turns > 0:
                player.poisoned_turns = 0
                msg += " You feel the poison fade away."
            return msg
        else:
            # throw at enemy
            damage = random.randint(8, 14)
            enemy.health = max(enemy.health - damage, 0)
            if not enemy.is_alive:
                return f"You hurl the potion and shatter it on the {enemy.name}, killing it with the splash!"
            return f"You toss the potion at the {enemy.name}, dealing {damage} damage."
    # non-combat fallback
    msg = player.heal(30)
    return msg


def effect_dagger(player: Player, context: Dict) -> str:
    """A dagger helps against enemies with quick strikes or piercing attacks."""
    if context.get("event") == "combat" and isinstance(context.get("enemy"), Enemy):
        enemy: Enemy = context["enemy"]
        # chance to bypass armor or land a critical strike
        crit = random.random() < 0.2
        piercing = random.random() < 0.25
        damage = random.randint(10, 18)
        if crit:
            damage = int(damage * 1.5)
        if piercing and enemy.armor > 0:
            taken = min(enemy.armor, 3)
            enemy.armor = max(enemy.armor - taken, 0)
            armor_msg = f" (pierced {taken} armor)"
        else:
            armor_msg = ""
        enemy.health = max(enemy.health - damage, 0)
        if not enemy.is_alive:
            return f"You strike true with your dagger and defeat the {enemy.name}!"
        return f"You slash the {enemy.name} for {damage} damage{armor_msg}. It has {enemy.health} HP left."

    return "You keep the dagger ready, just in case."


def effect_food_rations(player: Player, context: Dict) -> str:
    """Food rations can restore energy mid-run or distract an enemy in combat."""
    # inventory removal handled by use_item
    if context.get("event") == "combat" and isinstance(context.get("enemy"), Enemy):
        enemy: Enemy = context["enemy"]
        heal = 10
        player.health = min(player.health + heal, 100)
        return f"You toss rations to the {enemy.name}, confusing it and healing {heal} HP."
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
        Item(
            name="Medkit",
            description="Heals 70 health when used.",
            effect=lambda player, ctx: player.heal(70),
        ),
    ]


def generate_enemy(depth: int) -> Enemy:
    """Create a randomized enemy scaled to the depth of the temple."""
    # expand enemy variety with more original creatures
    choices = [
        ("Cave Snake", 18 + depth * 3, 2 + depth, "poison", 0),
        ("Ancient Warrior", 28 + depth * 5, 4 + depth, "shield", 3),
        ("Temple Guard", 22 + depth * 4, 3 + depth, None, 1),
        ("Temple Bat", 16 + depth * 2, 2 + depth, None, 0),
        ("Crypt Spider", 25 + depth * 4, 3 + depth, "poison", 1),
        ("Ancient Spider Queen", 35 + depth * 6, 5 + depth, "poison", 2),
        ("Sand Wraith", 24 + depth * 5, 4 + depth, "curse", 2),
        ("Bone Golem", 30 + depth * 6, 5 + depth * 2, None, 4),
        ("Mummy Lord", 32 + depth * 7, 6 + depth * 2, "poison", 2),
        ("Venom Serpent", 20 + depth * 3, 2 + depth, "poison", 0),
        ("Shadow Stalker", 26 + depth * 4, 4 + depth, None, 1),
        ("Poison Scorpion", 24 + depth * 4, 3 + depth, "poison", 2),
        ("Cursed Tomb Guardian", 28 + depth * 5, 4 + depth, "curse", 3),
        ("Scarab Swarm", 19 + depth * 3, 3 + depth, None, 0),
    ]
    name, hp, dmg, special, armor = random.choice(choices)
    return Enemy(name=name, health=hp, damage=dmg, special=special, armor=armor)


def run_combat(player: Player, enemy: Enemy) -> bool:
    """Run a simple turn-based combat encounter."""
    print(f"{enemy.name} (HP {enemy.health})")

    while player.health > 0 and enemy.is_alive:
        status_msg = player.apply_status_effects()
        if status_msg:
            print(status_msg)
            if player.health <= 0:
                break
        # combat action costs food each turn
        player.food = max(player.food - 1, 0)

        # starvation warning
        if player.food <= 0:
            print("Starving! Damage reduced, eat soon.")
        print(f"{player.name} (HP {player.health}) vs {enemy.name} (HP {enemy.health})")
        print("1)Attack 2)Item 3)Run 4)Status")
        choice = input("> ").strip()

        if choice == "1":
            damage = run_typing_minigame()
            if player.food <= 0:
                damage = damage // 2
            if enemy.armor > 0:
                mitigated = min(enemy.armor, damage)
                damage -= mitigated
                if mitigated > 0:
                    print(f"Armor: -{mitigated}")
            enemy.health = max(enemy.health - damage, 0)
        elif choice == "2":
            if not player.items:
                print("No items.")
                continue
            print("Items:", ", ".join(i.name for i in player.items))
            item_name = input("Use: ").strip()
            if not item_name:
                continue
            print(player.use_item(item_name, {"event": "combat", "enemy": enemy}))
            if not enemy.is_alive:
                break
            continue
        elif choice == "3":
            if player.food <= 0 and random.random() < 0.3:
                print("You collapse from starvation and die.")
                player.health = 0
                return False
            if random.random() < 0.5:
                print("Escaped!")
                return True
            print("Failed!")
        elif choice == "4":
            print(player.status())
            # if starving and choose status, still risk death
            if player.food <= 0 and random.random() < 0.3:
                print("You starve while lost and die.")
                player.health = 0
                return False
            continue
        else:
            print("Invalid.")
            continue

        if enemy.is_alive:
            if enemy.special == "poison" and random.random() < 0.25:
                player.poisoned_turns = max(player.poisoned_turns, 3)
                print(f"{enemy.name} poisons!")
            elif random.random() < 0.2:
                print("Dodged!")
            else:
                enemy_damage = random.randint(max(enemy.damage - 1, 1), enemy.damage + 1)
                print(player.take_damage(enemy_damage, f"{enemy.name}"))

    if player.health <= 0:
        print("Defeated.")
        return False

    print(f"{enemy.name} defeated!")
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
    story = "You enter the Temple of Time, full of traps and guardians."
    print_slowly(story, delay=0.05)
    print("\nWARNING: When you encounter enemies, you must type random words to")
    print("deal damage. Longer words deal more damage. Type carefully!\n")


def choose_items(available_items: List[Item], count: int = 2) -> List[Item]:
    """Prompt the player to choose starting items."""

    print("\nPick 2 items:")
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

    # include a choice room where the player must pick a direction
    room_types = ["empty", "treasure", "enemy", "trap", "heal", "pit", "choice"]
    weights = [0.33, 0.15, 0.18, 0.14, 0.06, 0.06, 0.08]
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
    if room_type == "choice":
        # a branching corridor where player must decide
        name = random.choice(["forked passage", "split corridor", "three-way junction"])
        return {
            "type": "choice",
            "name": name,
            "description": f"You reach a {name}. You can go left, right or forward.",
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

    chambers = 15  # fixed number of challenges to reach the heart
    print(f"The temple stretches ahead. Survive {chambers} chambers to escape.")

    chamber = 0
    while chamber < chambers and player.health > 0:
        chamber += 1
        room = choose_room(chamber)

        print(f"Chamber {chamber}: {room['description']}")
        # starting each chamber, food drains a bit quicker later per action

        # Allow the player to decide how to proceed
        while True:
            # each decision costs food
            player.food = max(player.food - 1, 0)
            # Choice room: only show direction options
            if room["type"] == "choice":
                print("Choose: 1)Left 2)Right 3)Forward")
                choice = input("> ").strip().lower()
                
                if choice in ("1", "l", "left"):
                    dmg = random.randint(15, 25)
                    player.take_damage(dmg, "Trap")
                    print(f"Trap! (-{dmg} HP)")
                    break
                elif choice in ("2", "r", "right"):
                    dmg = random.randint(8, 15)
                    player.poisoned_turns += 10
                    player.take_damage(dmg, "Curse")
                    print(f"Ancient ghost pharaoh curses you! (-{dmg} HP, poisoned)")
                    break
                elif choice in ("3", "f", "forward"):
                    print("Safe path.")
                    break
                else:
                    print("Invalid.")
                    continue
            
            # Normal menu for other room types
            else:
                print("1)Proceed 2)Item 3)Eat 4)Status 5)Exit")
                choice = input("> ").strip().lower()

                if choice in ("1", "p", "proceed"):
                    break
                if choice in ("2", "i", "item", "use"):
                    if not player.items:
                        print("No items.")
                        continue
                    print("Items:", ", ".join(i.name for i in player.items))
                    item_name = input("Use: ").strip()
                    if not item_name:
                        continue
                    print(player.use_item(item_name, {"event": room["type"]}))
                    continue
                if choice in ("3", "e", "eat"):
                    print(player.eat(1))
                    continue
                if choice in ("4", "s", "status"):
                    print(player.status())
                    continue
                if choice in ("5", "x", "exit"):
                    if attempt_exit(chamber):
                        return
                    player.food = max(player.food - 10, 0)
                    player.take_damage(5, "Lost 5 HP")
                    print("Lost in the dark.")
                    break

                print("Invalid.")

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
        elif room["type"] == "choice":
            # choice already handled in menu
            pass

        elif room["type"] == "enemy":
            enemy = generate_enemy(chamber)
            # describe where the enemy is encountered without renaming it to a room
            print(f"A {enemy.name} emerges from the {room['name']}!")
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

        # Food drains more after each chamber
        player.food = max(player.food - 8, 0)
        if player.food == 0:
            print("You are starving and feel weak...")
            player.take_damage(10, "Starvation")
            # show status only when starving
            print(player.status())

    if player.health > 0 and chamber >= chambers:
        # reached final chamber; reward and automatically find exit when you collect the treasure
        bonus = random.randint(2000, 5000)
        player.money += bonus
        print("\nYou reach the temple's heart and uncover a hoard of coins!")
        print(f"You collect {bonus} gold – you now have {player.money} money. This could change your life.")
        print("As you pocket the treasure, a hidden passage opens and you find your way out.")
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
        # always start with a medkit in addition to chosen items
        medkit = next((i for i in build_default_items() if i.name=="Medkit"), None)
        if medkit:
            player.add_item(medkit)

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
