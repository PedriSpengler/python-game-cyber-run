"""Cena exibida apos vitoria ou derrota."""

import pygame

from game import config as cfg
from game.scenes.base import Scene


class ResultScene(Scene):
    def __init__(self, game, won: bool, score: int) -> None:
        super().__init__(game)
        self.won = won
        self.score = score
        self.title_font = pygame.font.Font(None, 68)
        self.text_font = pygame.font.Font(None, 30)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.game.change_scene("gameplay")
            elif event.key == pygame.K_m:
                self.game.change_scene("menu")
            elif event.key == pygame.K_ESCAPE:
                self.game.running = False

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(cfg.BG)
        title_text = "ACESSO ROOT CONCEDIDO" if self.won else "CONEXAO ENCERRADA"
        color = cfg.YELLOW if self.won else cfg.RED
        title = self.title_font.render(title_text, True, color)
        score = self.text_font.render(f"PONTUACAO: {self.score:05d}", True, cfg.INK)
        options = self.text_font.render("Enter: repetir fase    M: menu    Esc: sair", True, cfg.CYAN)
        surface.blit(title, title.get_rect(center=(cfg.WIDTH / 2, 210)))
        surface.blit(score, score.get_rect(center=(cfg.WIDTH / 2, 285)))
        surface.blit(options, options.get_rect(center=(cfg.WIDTH / 2, 355)))
