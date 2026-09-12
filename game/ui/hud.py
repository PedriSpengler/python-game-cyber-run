"""Painel de vida, pontos e ajuda de controles."""

import pygame

from game import config as cfg


class Hud:
    def __init__(self) -> None:
        self.font = pygame.font.Font(None, 28)
        self.small = pygame.font.Font(None, 21)

    def draw(self, surface: pygame.Surface, player, stage) -> None:
        for index in range(player.life.maximum):
            color = cfg.MAGENTA if index < player.life.current else cfg.STEEL
            pygame.draw.rect(surface, color, (24 + index * 30, 22, 22, 15))
        score = self.font.render(f"DADOS  {player.score:05d}", True, cfg.INK)
        surface.blit(score, (24, 49))
        level_text = self.small.render(f"FASE {stage.number}: {stage.name}", True, cfg.CYAN)
        surface.blit(level_text, (24, 78))
        help_text = self.small.render("A/D move | W pula | Setas miram | J tiro | K dash | L overclock | I escudo", True, cfg.INK)
        surface.blit(help_text, (cfg.WIDTH - help_text.get_width() - 18, 20))

        overclock = "ATIVO" if player.overclock_timer > 0 else f"{player.overclock_cooldown:.1f}s"
        shield = "ATIVO" if player.shield_timer > 0 else f"{player.shield_cooldown:.1f}s"
        status = self.small.render(f"OVERCLOCK {overclock}   ESCUDO {shield}", True, cfg.YELLOW)
        surface.blit(status, (cfg.WIDTH - status.get_width() - 18, 49))
