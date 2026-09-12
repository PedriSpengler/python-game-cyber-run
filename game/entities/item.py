"""Itens coletaveis: pacotes de dados e patches de integridade."""

from game.entities.entity import Entity
from game.systems.assets import item_sprite


class Item(Entity):
    def __init__(self, x: float, y: float, kind: str = "data") -> None:
        asset_kind = "health" if kind == "patch" else "data"
        super().__init__(x, y, item_sprite(asset_kind))
        self.kind = kind

    def collect(self, player) -> None:
        if self.kind == "patch":
            player.life.heal(1)
        else:
            player.score += 100
        self.kill()
