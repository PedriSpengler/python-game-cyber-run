"""Componente de vida independente de jogador ou inimigo."""

from dataclasses import dataclass


@dataclass
class Health:
    maximum: int
    current: int | None = None

    def __post_init__(self) -> None:
        self.current = self.maximum if self.current is None else max(0, min(self.current, self.maximum))

    @property
    def empty(self) -> bool:
        return self.current == 0

    @property
    def ratio(self) -> float:
        return self.current / self.maximum

    def damage(self, amount: int) -> bool:
        """Aplica dano e informa se o valor de vida foi alterado."""
        if amount <= 0 or self.empty:
            return False
        self.current = max(0, self.current - amount)
        return True

    def heal(self, amount: int) -> bool:
        if amount <= 0 or self.current >= self.maximum:
            return False
        self.current = min(self.maximum, self.current + amount)
        return True

