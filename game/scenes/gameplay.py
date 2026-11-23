"""Cena jogavel: coordena fase, entidades, sistemas e camera."""

import pygame

from game import config as cfg
from game.entities.enemy import Enemy
from game.entities.item import Item
from game.entities.player import Player
from game.scenes.base import Scene
from game.systems.combat import resolve_combat
from game.systems.lan import PORT
from game.ui.hud import Hud
from game.world.level import Level
from game.world.stage_data import LEGACY_CODE_DUNGEON


class GameplayScene(Scene):
    def __init__(self, game, stage=LEGACY_CODE_DUNGEON, editor=None, lan=None) -> None:
        super().__init__(game)
        self.level = Level(stage)
        self.editor = editor
        self.lan = lan
        self.lan_font = pygame.font.Font(None, 23) if lan else None
        self.hud = Hud()
        self.reset_run()

    def reset_run(self):
        data = self.level.definition
        self.player = Player(*data.start)
        self.enemies = pygame.sprite.Group(*(
            Enemy(spawn.x, spawn.y, spawn.patrol_left, spawn.patrol_right)
            for spawn in data.enemies
        ))
        self.items = pygame.sprite.Group(*(
            Item(spawn.x, spawn.y, spawn.kind) for spawn in data.items
        ))
        self.projectiles = pygame.sprite.Group()
        self.camera_x = 0.0

    def close(self):
        if self.lan is not None:
            self.lan.close()

    def leave(self):
        if self.editor is not None:
            self.game.change_scene("editor")
        else:
            self.game.change_scene("menu")

    def finish(self, won):
        if self.lan is not None:
            self.reset_run()
        else:
            self.game.change_scene("result", won=won, score=self.player.score,
                                   stage=self.level.definition, editor=self.editor)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self.leave()
        elif self.lan is not None and not self.lan.connected:
            return
        elif event.key in (pygame.K_w, pygame.K_SPACE):
            self.player.request_jump()
        elif event.key == pygame.K_k:
            self.player.try_dash(self.game.audio)
        elif event.key == pygame.K_l:
            self.player.try_overclock(self.game.audio)
        elif event.key == pygame.K_i:
            self.player.try_shield(self.game.audio)

    def update(self, dt: float) -> None:
        if self.lan is not None:
            position = [self.player.rect.x, self.player.rect.y, self.player.facing]
            if not self.lan.tick(position):
                self.game.change_scene("client", message="Conexão LAN encerrada ou sem resposta.",
                                       address=self.lan.server[0])
                return
            if not self.lan.connected:
                return
        keys = pygame.key.get_pressed()
        movement = int(keys[pygame.K_d]) - int(keys[pygame.K_a])
        aim = pygame.Vector2(
            int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT]),
            int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP]),
        )
        if keys[pygame.K_j]:
            self.player.try_shoot(self.projectiles, self.game.audio, aim)

        self.player.update(dt, movement, self.level.platforms, self.game.audio)
        right_bound = self.level.width - self.player.rect.width
        bounded_x = max(0, min(self.player.position.x, right_bound))
        if bounded_x != self.player.position.x:
            self.player.position.x = bounded_x
            self.player.velocity.x = 0
            self.player.sync_rect()
        self.level.update(dt)
        for enemy in list(self.enemies):
            enemy.update(dt, self.player, self.projectiles)
        for projectile in list(self.projectiles):
            projectile.update(dt, self.level.platforms)
        resolve_combat(self.player, self.enemies, self.items, self.projectiles, self.game.audio)

        max_camera = self.level.width - cfg.WIDTH
        target = max(0, min(self.player.rect.centerx - cfg.WIDTH * 0.42, max_camera))
        self.camera_x += (target - self.camera_x) * min(1, dt * 7)

        if self.player.life.empty or self.player.position.y > cfg.HEIGHT + 150:
            self.finish(won=False)
        elif self.player.rect.right >= self.level.definition.exit_x:
            self.finish(won=True)

    def draw(self, surface: pygame.Surface) -> None:
        self.level.draw(surface, self.camera_x)
        sprites = [*self.items, *self.enemies, *self.projectiles, self.player]
        for sprite in sprites:
            position = (sprite.rect.x - round(self.camera_x), sprite.rect.y)
            if sprite is self.player and self.player.invulnerable > 0 and int(self.player.invulnerable * 12) % 2:
                continue
            image = sprite.image
            if hasattr(sprite, "facing") and sprite.facing < 0:
                image = pygame.transform.flip(image, True, False)
            surface.blit(image, position)
        if self.lan is not None:
            for x, y, facing in self.lan.players:
                image = self.player.image
                if facing < 0:
                    image = pygame.transform.flip(image, True, False)
                pos = (x - round(self.camera_x), y)
                surface.blit(image, pos)
                pygame.draw.line(surface, cfg.MAGENTA, (pos[0], y - 5), (pos[0] + image.get_width(), y - 5), 2)
            status = f"LAN  •  {len(self.lan.players) + 1} jogador(es)"
            if self.lan.host:
                status = f"Servidor LAN (UDP {PORT})  •  {len(self.lan.players) + 1} jogador(es)"
            elif not self.lan.connected:
                status = f"Conectando a {self.lan.server[0]}…  Esc para cancelar"
            text = self.lan_font.render(status, True, cfg.CYAN)
            surface.blit(text, (cfg.WIDTH - text.get_width() - 12, cfg.HEIGHT - 23))
        self._draw_shield(surface)
        self.hud.draw(surface, self.player, self.level.definition)

    def _draw_shield(self, surface: pygame.Surface) -> None:
        if self.player.shield_timer <= 0:
            return
        center = (self.player.rect.centerx - round(self.camera_x), self.player.rect.centery)
        pygame.draw.circle(surface, cfg.CYAN, center, 31, 2)

