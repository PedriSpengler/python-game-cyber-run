"""Regras de dano, coleta e pontuacao da partida."""

import pygame


def resolve_combat(player, enemies: pygame.sprite.Group, items: pygame.sprite.Group,
                   projectiles: pygame.sprite.Group, audio) -> None:
    for item in pygame.sprite.spritecollide(player, items, False):
        item.collect(player)
        audio.play("pickup")

    for projectile in list(projectiles):
        if projectile.hostile:
            if projectile.rect.colliderect(player.rect):
                player.damage(projectile.damage_value)
                projectile.kill()
                audio.play("hit")
        else:
            hits = pygame.sprite.spritecollide(projectile, enemies, False)
            if hits:
                target = hits[0]
                target.damage(projectile.damage_value)
                if not target.alive_in_world:
                    player.score += 250
                projectile.kill()
                audio.play("hit")

    if pygame.sprite.spritecollide(player, enemies, False):
        player.damage(1)

