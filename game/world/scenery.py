"""Renderizacao do ambiente industrial cyberpunk."""

import pygame

from game import config as cfg


class IndustrialScenery:
    def __init__(self) -> None:
        self.animation_time = 0.0

    def update(self, dt: float) -> None:
        self.animation_time += dt

    def draw(self, surface: pygame.Surface, camera_x: float, platforms: list[pygame.Rect]) -> None:
        surface.fill(cfg.BG)
        # Servidores e chamines em parallax.
        for index in range(14):
            x = int(index * 190 - camera_x * 0.25) % 2660 - 120
            height = 100 + (index * 37) % 190
            pygame.draw.rect(surface, (22, 30, 58), (x, 492 - height, 130, height))
            for y in range(492 - height + 18, 470, 28):
                blink = (index + y // 28 + int(self.animation_time * 2)) % 3
                color = cfg.CYAN if blink == 0 else (52, 77, 105)
                pygame.draw.rect(surface, color, (x + 18, y, 12, 8))

        # Cabos e nucleo ao fundo.
        pygame.draw.circle(surface, (35, 49, 82), (760, 115), 72)
        pygame.draw.circle(surface, cfg.BG, (782, 98), 69)
        pygame.draw.line(surface, cfg.PURPLE, (0, 205), (cfg.WIDTH, 125), 3)
        pygame.draw.line(surface, (31, 50, 76), (0, 215), (cfg.WIDTH, 135), 8)

        for platform in platforms:
            rect = platform.move(-round(camera_x), 0)
            pygame.draw.rect(surface, cfg.STEEL, rect)
            pygame.draw.rect(surface, cfg.CYAN, (rect.x, rect.y, rect.w, 4))
            for x in range(rect.x + 12, rect.right, 32):
                pygame.draw.rect(surface, cfg.PURPLE, (x, rect.y + 12, 12, 5))

