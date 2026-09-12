"""Dados declarativos das fases, separados da logica e do desenho."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EnemySpawn:
    x: int
    y: int
    patrol_left: int
    patrol_right: int


@dataclass(frozen=True)
class ItemSpawn:
    x: int
    y: int
    kind: str = "data"


@dataclass(frozen=True)
class StageDefinition:
    number: int
    name: str
    width: int
    start: tuple[int, int]
    exit_x: int
    platforms: tuple[tuple[int, int, int, int], ...]
    enemies: tuple[EnemySpawn, ...]
    items: tuple[ItemSpawn, ...]


LEGACY_CODE_DUNGEON = StageDefinition(
    number=1,
    name="LEGACY CODE DUNGEON",
    width=2500,
    start=(80, 400),
    exit_x=2420,
    platforms=(
        (0, 492, 2500, 80),
        (330, 390, 240, 28),
        (720, 330, 220, 28),
        (1090, 420, 260, 28),
        (1480, 340, 230, 28),
        (1870, 400, 300, 28),
        (2290, 300, 180, 28),
    ),
    enemies=(
        EnemySpawn(560, 440, 500, 680),
        EnemySpawn(1160, 368, 1100, 1280),
        EnemySpawn(1600, 288, 1490, 1660),
        EnemySpawn(2050, 348, 1900, 2140),
    ),
    items=(
        ItemSpawn(420, 350),
        ItemSpawn(800, 290),
        ItemSpawn(1210, 380, "patch"),
        ItemSpawn(1555, 300),
        ItemSpawn(1990, 360),
        ItemSpawn(2350, 260),
    ),
)

