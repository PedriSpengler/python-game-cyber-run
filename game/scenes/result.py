"""Cena exibida apos vitoria ou derrota."""

import pygame

from game import config as cfg
from game.scenes.base import Scene
from game.world.stage_data import LEGACY_CODE_DUNGEON


class ResultScene(Scene):
    def __init__(self, game, won: bool, score: int, stage=LEGACY_CODE_DUNGEON, editor=None) -> None:
        super().__init__(game)
        self.won = won
        self.score = score
        self.stage = stage
        self.editor = editor
        self.title_font = pygame.font.Font(None, 68)
        self.text_font = pygame.font.Font(None, 30)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.game.change_scene("gameplay", stage=self.stage, editor=self.editor)
            elif event.key == pygame.K_m:
                self.game.change_scene("menu")
            elif event.key == pygame.K_ESCAPE:
                if self.editor is None:
                    self.game.running = False
                else:
                    self.game.change_scene("editor", stage=self.stage, camera=self.editor.camera)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(cfg.BG)
        title_text = "ACESSO ROOT CONCEDIDO" if self.won else "CONEXAO ENCERRADA"
        color = cfg.YELLOW if self.won else cfg.RED
        title = self.title_font.render(title_text, True, color)
        score = self.text_font.render(f"PONTUACAO: {self.score:05d}", True, cfg.INK)
        back = "editor" if self.editor is not None else "sair"
        options = self.text_font.render(f"Enter: repetir fase    M: menu    Esc: {back}", True, cfg.CYAN)
        surface.blit(title, title.get_rect(center=(cfg.WIDTH / 2, 210)))
        surface.blit(score, score.get_rect(center=(cfg.WIDTH / 2, 285)))
        surface.blit(options, options.get_rect(center=(cfg.WIDTH / 2, 355)))
