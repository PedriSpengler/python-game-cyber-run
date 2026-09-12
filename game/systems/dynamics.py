"""Dinamica de corpos e resolucao de colisoes com plataformas."""

from dataclasses import dataclass

import pygame


@dataclass
class CollisionResult:
    on_ground: bool = False
    hit_ceiling: bool = False
    hit_wall: bool = False


def move_and_collide(body, dt: float, platforms: list[pygame.Rect]) -> CollisionResult:
    """Move um corpo nos eixos X/Y e resolve colisoes AABB."""
    result = CollisionResult()
    body.position.x += body.velocity.x * dt
    body.sync_rect()
    for platform in platforms:
        if body.rect.colliderect(platform):
            if body.velocity.x > 0:
                body.rect.right = platform.left
            elif body.velocity.x < 0:
                body.rect.left = platform.right
            body.position.x = body.rect.x
            body.velocity.x = 0
            result.hit_wall = True

    body.position.y += body.velocity.y * dt
    body.sync_rect()
    for platform in platforms:
        if body.rect.colliderect(platform):
            if body.velocity.y > 0:
                body.rect.bottom = platform.top
                result.on_ground = True
            elif body.velocity.y < 0:
                body.rect.top = platform.bottom
                result.hit_ceiling = True
            body.position.y = body.rect.y
            body.velocity.y = 0
    return result

