"""Player model for The Spooky Temple game.

This module defines a simple `Player` class that tracks the player's
health, food, and money.

The class is intentionally small and easy to expand with additional
game-related behavior.
"""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass


def _get_single_key(prompt: str) -> str:
    """Read a single keypress from the user (no Enter needed) when possible."""
    try:
        # Unix-like getch
        import termios
        import tty

        sys.stdout.write(prompt)
        sys.stdout.flush()

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        sys.stdout.write("\n")
        return ch
    except Exception:
        # Fallback to standard input in environments that don't support raw mode
        return input(prompt).strip()


@dataclass
class Player:
    """Represents a player in The Spooky Temple.

    Attributes:
        health: The player's current health (0 means dead).
        food: How much food the player has (used for survival mechanics).
        money: How much money the player has (used for purchases).
    """

    health: int = 100
    food: int = 10
    money: int = 0

    def is_alive(self) -> bool:
        """Return True if the player is still alive (health > 0)."""
        return self.health > 0

    def change_health(self, amount: int) -> None:
        """Modify health by the given amount (can be positive or negative).

        The player's health is clamped to a minimum of 0.
        """
        self.health = max(0, self.health + amount)

    def change_food(self, amount: int) -> None:
        """Modify food by the given amount (can be positive or negative)."""
        self.food = max(0, self.food + amount)

    def change_money(self, amount: int) -> None:
        """Modify money by the given amount (can be positive or negative)."""
        self.money = max(0, self.money + amount)

    def spend_money(self, cost: int) -> bool:
        """Attempt to spend money; return True if successful."""
        if cost < 0:
            raise ValueError("Cost must be non-negative")
        if self.money < cost:
            return False
        self.money -= cost
        return True

    def eat(self, amount: int = 1) -> None:
        """Consume food to restore health.

        This is a simple placeholder for a consumption mechanic. It will
        decrement food and restore a small amount of health.
        """
        if amount <= 0 or self.food <= 0:
            return

        eaten = min(self.food, amount)
        self.food -= eaten
        self.change_health(eaten * 2)


class SpookyTempleGame:
    """A tiny text-based version of The Spooky Temple."""

    def __init__(self) -> None:
        self.player = Player()
        self.day = 1

    def _print_status(self) -> None:
        print(f"\n--- Day {self.day} ---")
        print(f"Health: {self.player.health}")
        print(f"Food:   {self.player.food}")
        print(f"Money:  {self.player.money}")

    def _prompt_action(self) -> str:
        print("\nWhat will you do?")
        print("  [e] Explore the temple (risky, may earn money/food)")
        print("  [r] Rest (recover a little health)")
        print("  [f] Eat some food (restore health)")
        print("  [s] Spend money in the market")
        print("  [q] Quit")
        choice = _get_single_key("Choose an action: ")
        return choice.strip().lower()

    def _explore(self) -> None:
        outcome = random.choice(["treasure", "trap", "meal", "nothing"])
        if outcome == "treasure":
            gained = random.randint(5, 20)
            self.player.change_money(gained)
            print(f"You found {gained} coins in a dusty chest!")
        elif outcome == "trap":
            damage = random.randint(5, 25)
            self.player.change_health(-damage)
            print(f"A hidden trap springs! You take {damage} damage.")
        elif outcome == "meal":
            food = random.randint(1, 3)
            self.player.change_food(food)
            print(f"You scavenge a meal and gain {food} food.")
        else:
            print("You wander through empty corridors and find nothing of note.")

    def _rest(self) -> None:
        recovered = random.randint(3, 8)
        self.player.change_health(recovered)
        self.player.change_food(-1)
        print(f"You rest and recover {recovered} health, but it costs 1 food.")

    def _eat(self) -> None:
        if self.player.food <= 0:
            print("You have no food to eat.")
            return
        self.player.eat()
        print("You eat some food and feel a little better.")

    def _shop(self) -> None:
        print("\nThe market sells:")
        print("  1) Health potion (+15 health) - 10 coins")
        print("  2) Food ration (+3 food) - 8 coins")
        print("  3) Leave")
        choice = _get_single_key("Select an item (1-3): ").strip()
        if choice == "1":
            if self.player.spend_money(10):
                self.player.change_health(15)
                print("You drink the potion and feel renewed.")
            else:
                print("You don't have enough coins.")
        elif choice == "2":
            if self.player.spend_money(8):
                self.player.change_food(3)
                print("You buy a food ration.")
            else:
                print("You don't have enough coins.")
        else:
            print("You decide not to buy anything.")

    def run(self) -> None:
        print("Welcome to The Spooky Temple! Survive as long as you can.")
        while self.player.is_alive():
            self._print_status()
            action = self._prompt_action()

            if action == "e":
                self._explore()
            elif action == "r":
                self._rest()
            elif action == "f":
                self._eat()
            elif action == "s":
                self._shop()
            elif action == "q":
                print("You leave the temple for now. Come back soon!")
                break
            else:
                print("Sorry, I don't understand that action.")

            if not self.player.is_alive():
                print("\nYour health dropped to 0. The temple claims another soul.")
                break

            self.day += 1

        print("Game over.")


if __name__ == "__main__":
    game = SpookyTempleGame()
    game.run()
