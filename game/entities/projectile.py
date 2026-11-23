"""Projetil disparado pelo jogador ou por inimigos."""

import pygame

from game import config as cfg
from game.entities.entity import Entity


class Projectile(Entity):
    def __init__(self, x: float, y: float, direction, hostile: bool = False) -> None:
        color = cfg.RED if hostile else cfg.YELLOW
        image = pygame.Surface((16, 6), pygame.SRCALPHA)
        pygame.draw.rect(image, color, (0, 0, 16, 6))
        pygame.draw.rect(image, cfg.INK, (4, 1, 8, 2))
        vector = pygame.Vector2(direction, 0) if isinstance(direction, (int, float)) else pygame.Vector2(direction)
        if vector.length_squared() == 0:
            vector.x = 1
        vector = vector.normalize()
        if abs(vector.y) > 0.2:
            angle = vector.angle_to(pygame.Vector2(1, 0))
            image = pygame.transform.rotate(image, angle)
        rect = image.get_rect(center=(round(x), round(y)))
        super().__init__(*rect.topleft, image)
        self.velocity = vector * (390 if hostile else 650)
        self.hostile = hostile
        self.damage_value = 1
        self.lifetime = 2.0

    def update(self, dt: float, platforms: list[pygame.Rect]) -> None:
        self.position += self.velocity * dt
        self.sync_rect()
        self.lifetime -= dt
        if self.lifetime <= 0 or any(self.rect.colliderect(platform) for platform in platforms):
            self.alive_in_world = False
            self.kill()
