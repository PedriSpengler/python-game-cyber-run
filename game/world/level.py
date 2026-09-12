"""Instancia executavel de uma fase definida por dados."""

import pygame

from game.world.scenery import IndustrialScenery
from game.world.stage_data import StageDefinition


class Level:
    def __init__(self, definition: StageDefinition) -> None:
        self.definition = definition
        self.platforms = [pygame.Rect(*values) for values in definition.platforms]
        self.scenery = IndustrialScenery()

    @property
    def width(self) -> int:
        return self.definition.width

    def update(self, dt: float) -> None:
        self.scenery.update(dt)

    def draw(self, surface: pygame.Surface, camera_x: float) -> None:
        self.scenery.draw(surface, camera_x, self.platforms)
