"""Regressões do disparo diagonal, do editor e das sessões LAN."""

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from game.core.game import Game
from game.entities.projectile import Projectile
from game.scenes.editor import FILENAME, load_stage
from game.systems.lan import LanSession
from game.systems.preferences import write_data
from game.world.stage_data import LEGACY_CODE_DUNGEON


class GameRegressionTests(unittest.TestCase):
    def tearDown(self):
        pygame.quit()

    def test_diagonal_projectile_is_centered_and_aligned(self):
        projectile = Projectile(100, 100, (1, -1))
        self.assertEqual(projectile.rect.center, (100, 100))
        mask = pygame.mask.from_surface(projectile.image)
        pixels = [(x, y) for y in range(mask.get_size()[1])
                  for x in range(mask.get_size()[0]) if mask.get_at((x, y))]
        left = min(pixels)[0]
        right = max(pixels)[0]
        self.assertGreater(
            min(y for x, y in pixels if x == left),
            max(y for x, y in pixels if x == right),
        )

    def test_editor_retains_unsaved_edits_and_undo_after_playtest(self):
        with TemporaryDirectory() as directory, patch("game.systems.preferences.DATA_DIR", Path(directory)):
            game = Game()
            game.change_scene("editor")
            editor = game.scene
            original = editor.stage
            editor.change_stage(exit_x=1400)
            editor.play()
            game.scene.leave()
            self.assertIs(game.scene, editor)
            self.assertEqual(editor.stage.exit_x, 1400)
            game.change_scene("menu")
            game.change_scene("editor")
            editor.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_z, mod=pygame.KMOD_CTRL))
            self.assertEqual(game.scene.stage, original)

    def test_invalid_saved_stage_falls_back_to_default(self):
        with TemporaryDirectory() as directory, patch("game.systems.preferences.DATA_DIR", Path(directory)):
            write_data(FILENAME, {
                "start": [80, 400], "exit_x": 2420, "platforms": [[1, 2, 3]],
                "enemies": [], "items": [],
            })
            self.assertEqual(load_stage().platforms, LEGACY_CODE_DUNGEON.platforms)

    def test_player_cannot_move_past_left_edge(self):
        game = Game()
        game.change_scene("gameplay")
        player = game.scene.player
        player.position.x = -10
        player.sync_rect()
        game.scene.update(1 / 60)
        self.assertEqual(player.rect.left, 0)

    def test_lan_leave_and_server_close(self):
        host = LanSession(port=0)
        self.addCleanup(host.close)
        port = host.socket.getsockname()[1]
        client = LanSession("127.0.0.1", port)
        self.addCleanup(client.close)
        other = LanSession("127.0.0.1", port)
        self.addCleanup(other.close)
        client.tick([20, 30, 1])
        other.tick([40, 50, -1])
        host.tick([10, 20, 1])
        self.assertTrue(client.tick([20, 30, 1]))
        self.assertTrue(client.connected)
        self.assertIn([40, 50, -1], client.players)
        other.close()
        host.tick([10, 20, 1])
        self.assertEqual(host.players, [[20, 30, 1]])
        host.close()
        self.assertFalse(client.tick([20, 30, 1]))
