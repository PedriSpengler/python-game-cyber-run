"""Inimigo sentinela com patrulha e ataque a distancia."""

import pygame

from game.components.health import Health
from game.entities.entity import Entity
from game.entities.projectile import Projectile
from game.systems.assets import enemy_sprite


class Enemy(Entity):
    def __init__(self, x: float, y: float, left_limit: float, right_limit: float) -> None:
        super().__init__(x, y, enemy_sprite())
        self.life = Health(3)
        self.left_limit = left_limit
        self.right_limit = right_limit
        self.direction = 1
        self.shot_timer = 1.0

    def update(self, dt: float, player: Entity, projectiles: pygame.sprite.Group) -> None:
        self.position.x += self.direction * 75 * dt
        if self.position.x <= self.left_limit:
            self.position.x, self.direction = self.left_limit, 1
        elif self.position.x >= self.right_limit:
            self.position.x, self.direction = self.right_limit, -1
        self.sync_rect()

        self.shot_timer -= dt
        near = abs(player.rect.centerx - self.rect.centerx) < 480
        if near and self.shot_timer <= 0:
            direction = pygame.Vector2(player.rect.center) - pygame.Vector2(self.rect.center)
            projectiles.add(Projectile(self.rect.centerx, self.rect.centery, direction, hostile=True))
            self.shot_timer = 1.35

    def damage(self, amount: int) -> None:
        self.life.damage(amount)
        if self.life.empty:
            self.alive_in_world = False
            self.kill()
