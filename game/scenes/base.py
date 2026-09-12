"""Contrato comum para todas as cenas."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from game.core.game import Game


class Scene:
    def __init__(self, game: "Game") -> None:
        self.game = game

    def handle_event(self, event: pygame.event.Event) -> None:
        del event

    def update(self, dt: float) -> None:
        del dt

    def draw(self, surface: pygame.Surface) -> None:
        raise NotImplementedError

