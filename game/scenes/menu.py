"""Cena de abertura e instrucoes."""

import pygame

from game import config as cfg
from game.scenes.base import Scene


class MenuScene(Scene):
    def __init__(self, game) -> None:
        super().__init__(game)
        self.time = 0.0
        self.title_font = pygame.font.Font(None, 76)
        self.subtitle_font = pygame.font.Font(None, 32)
        self.text_font = pygame.font.Font(None, 24)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.game.change_scene("gameplay")
            elif event.key == pygame.K_ESCAPE:
                self.game.running = False

    def update(self, dt: float) -> None:
        self.time += dt

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(cfg.BG)
        for x in range(0, cfg.WIDTH, 32):
            height = 30 + ((x // 32 * 19 + int(self.time * 30)) % 170)
            pygame.draw.rect(surface, (20, 34, 57), (x, cfg.HEIGHT - height, 19, height))
        title = self.title_font.render("CTRL//REVOLT", True, cfg.CYAN)
        subtitle = self.subtitle_font.render("INDUSTRIAL CYBER-RUN", True, cfg.MAGENTA)
        mission = self.text_font.render("Invada o servidor central. Derrube a CENTINELA.", True, cfg.INK)
        start = self.subtitle_font.render("[ ENTER ] INICIAR", True, cfg.YELLOW)
        surface.blit(title, title.get_rect(center=(cfg.WIDTH / 2, 175)))
        surface.blit(subtitle, subtitle.get_rect(center=(cfg.WIDTH / 2, 232)))
        surface.blit(mission, mission.get_rect(center=(cfg.WIDTH / 2, 315)))
        if int(self.time * 2) % 2 == 0:
            surface.blit(start, start.get_rect(center=(cfg.WIDTH / 2, 390)))

