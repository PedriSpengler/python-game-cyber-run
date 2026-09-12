"""Personagem controlavel: correr, pular, atirar e avancar rapidamente."""

import pygame

from game import config as cfg
from game.components.health import Health
from game.entities.entity import Entity
from game.entities.projectile import Projectile
from game.systems.assets import player_sprite
from game.systems.dynamics import move_and_collide
from game.systems.physics import approach, clamp


class Player(Entity):
    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, player_sprite())
        self.life = Health(5)
        self.score = 0
        self.facing = 1
        self.on_ground = False
        self.coyote_timer = 0.0
        self.jump_buffer = 0.0
        self.shot_timer = 0.0
        self.dash_timer = 0.0
        self.dash_cooldown = 0.0
        self.invulnerable = 0.0
        self.jump_count = 0
        self.overclock_timer = 0.0
        self.overclock_cooldown = 0.0
        self.shield_timer = 0.0
        self.shield_cooldown = 0.0

    def request_jump(self) -> None:
        self.jump_buffer = 0.12

    def try_dash(self, audio) -> None:
        if self.dash_cooldown <= 0:
            self.dash_timer = cfg.DASH_DURATION
            self.dash_cooldown = cfg.DASH_COOLDOWN
            self.velocity.x = self.facing * cfg.DASH_SPEED
            self.velocity.y = 0
            audio.play("dash")

    def try_shoot(self, projectiles: pygame.sprite.Group, audio, aim: pygame.Vector2 | None = None) -> None:
        if self.shot_timer <= 0:
            direction = pygame.Vector2(self.facing, 0) if aim is None or aim.length_squared() == 0 else aim
            direction = direction.normalize()
            x = self.rect.centerx + direction.x * 18
            y = self.rect.centery + direction.y * 12
            projectiles.add(Projectile(x, y, direction))
            self.shot_timer = cfg.SHOT_COOLDOWN * (0.55 if self.overclock_timer > 0 else 1.0)
            audio.play("shoot")

    def try_overclock(self, audio) -> None:
        if self.overclock_cooldown <= 0:
            self.overclock_timer = cfg.OVERCLOCK_DURATION
            self.overclock_cooldown = cfg.OVERCLOCK_COOLDOWN
            audio.play("pickup")

    def try_shield(self, audio) -> None:
        if self.shield_cooldown <= 0:
            self.shield_timer = cfg.SHIELD_DURATION
            self.shield_cooldown = cfg.SHIELD_COOLDOWN
            audio.play("dash")

    def update(self, dt: float, movement: int, platforms: list[pygame.Rect], audio) -> None:
        self.shot_timer = max(0.0, self.shot_timer - dt)
        self.dash_cooldown = max(0.0, self.dash_cooldown - dt)
        self.invulnerable = max(0.0, self.invulnerable - dt)
        self.overclock_timer = max(0.0, self.overclock_timer - dt)
        self.overclock_cooldown = max(0.0, self.overclock_cooldown - dt)
        self.shield_timer = max(0.0, self.shield_timer - dt)
        self.shield_cooldown = max(0.0, self.shield_cooldown - dt)
        self.jump_buffer = max(0.0, self.jump_buffer - dt)
        self.coyote_timer = 0.10 if self.on_ground else max(0.0, self.coyote_timer - dt)

        if movement:
            self.facing = movement

        if self.dash_timer > 0:
            self.dash_timer -= dt
            self.velocity.x = self.facing * cfg.DASH_SPEED
        else:
            speed_multiplier = 1.35 if self.overclock_timer > 0 else 1.0
            target = movement * cfg.PLAYER_SPEED * speed_multiplier
            acceleration = cfg.PLAYER_ACCELERATION if movement else (cfg.GROUND_FRICTION if self.on_ground else cfg.AIR_FRICTION)
            self.velocity.x = approach(self.velocity.x, target, acceleration * dt)
            self.velocity.y = clamp(self.velocity.y + cfg.GRAVITY * dt, -cfg.JUMP_SPEED, cfg.MAX_FALL_SPEED)

        can_jump = self.coyote_timer > 0 or self.jump_count < 2
        if self.jump_buffer > 0 and can_jump and self.dash_timer <= 0:
            self.velocity.y = -cfg.JUMP_SPEED
            self.on_ground = False
            self.coyote_timer = 0
            self.jump_buffer = 0
            self.jump_count += 1
            audio.play("jump")

        collision = move_and_collide(self, dt, platforms)
        self.on_ground = collision.on_ground
        if self.on_ground:
            self.jump_count = 0

    def damage(self, amount: int) -> None:
        if self.invulnerable <= 0 and self.shield_timer <= 0:
            self.life.damage(amount)
            self.invulnerable = 0.8
