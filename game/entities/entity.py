"""Entidade base com posicao continua e colisao retangular."""

import pygame


class Entity(pygame.sprite.Sprite):
    def __init__(self, x: float, y: float, image: pygame.Surface) -> None:
        super().__init__()
        self.image = image
        self.rect = image.get_rect(topleft=(round(x), round(y)))
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2()
        self.alive_in_world = True

    def sync_rect(self) -> None:
        self.rect.topleft = round(self.position.x), round(self.position.y)

    def damage(self, amount: int) -> None:
        del amount

