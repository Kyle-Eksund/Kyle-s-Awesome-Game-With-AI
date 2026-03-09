"""Temple Explorer player model.

This module defines a simple Player class for tracking health, food,
and stamina in the Temple Explorer game.

Example:
    player = Player(name="Ari")
    player.take_damage(10)
    player.eat(5)
    player.rest(3)
"""

from __future__ import annotations


class Player:
    """A player in Temple Explorer.

    Attributes:
        name: The player's display name.
        health: Current health (0 = dead).
        food: Current food level (affects stamina).
        stamina: Current stamina (used for actions).
        max_health: Maximum health value.
        max_food: Maximum food value.
        max_stamina: Maximum stamina value.
    """

    def __init__(
        self,
        name: str,
        max_health: int = 100,
        max_food: int = 100,
        max_stamina: int = 100,
    ):
        self.name = name
        self.max_health = max_health
        self.max_food = max_food
        self.max_stamina = max_stamina

        self.health = max_health
        self.food = max_food
        self.stamina = max_stamina

    def _clamp(self, value: int, minimum: int, maximum: int) -> int:
        return max(minimum, min(value, maximum))

    @property
    def is_alive(self) -> bool:
        """Returns True if the player is alive (health > 0)."""
        return self.health > 0

    def take_damage(self, amount: int) -> None:
        """Reduce health by a given amount."""
        if amount <= 0:
            return
        self.health = self._clamp(self.health - amount, 0, self.max_health)

    def heal(self, amount: int) -> None:
        """Restore health by a given amount."""
        if amount <= 0 or not self.is_alive:
            return
        self.health = self._clamp(self.health + amount, 0, self.max_health)

    def eat(self, amount: int) -> None:
        """Increase food (and optionally restore a bit of stamina)."""
        if amount <= 0:
            return
        self.food = self._clamp(self.food + amount, 0, self.max_food)
        # Optionally restore some stamina when eating
        self.stamina = self._clamp(self.stamina + amount // 2, 0, self.max_stamina)

    def expend_stamina(self, amount: int) -> None:
        """Consume stamina for actions."""
        if amount <= 0:
            return
        self.stamina = self._clamp(self.stamina - amount, 0, self.max_stamina)

    def rest(self, time: int) -> None:
        """Restore stamina based on time rested.

        Stamina restoration is limited by the available food.
        """
        if time <= 0:
            return
        restored = time * 5
        # Stamina recovery is more effective when food is high
        bonus = self.food // 10
        self.stamina = self._clamp(self.stamina + restored + bonus, 0, self.max_stamina)

    def consume_food(self, amount: int) -> None:
        """Consume food without restoring stamina.

        Useful when food is needed for other game systems.
        """
        if amount <= 0:
            return
        self.food = self._clamp(self.food - amount, 0, self.max_food)

    def __repr__(self) -> str:
        return (
            f"<Player name={self.name!r} health={self.health}/{self.max_health} "
            f"food={self.food}/{self.max_food} stamina={self.stamina}/{self.max_stamina}>"
        )
