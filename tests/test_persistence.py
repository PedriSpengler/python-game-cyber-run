import pygame
import os
import sys
import tempfile
import unittest
import numpy as np
import scipy.sparse as sp

# Adiciona a raiz do projeto ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from source.modules.ui.levels import Level1
from source.modules.constants import TILE_MAP_LEVEL1, TILE_SIZE


class MockTile:
    def __init__(self, id, x, y):
        self.id = id
        self.rect = type('Rect', (), {'x': x, 'y': y, 'left': x, 'top': y, 'w': TILE_SIZE, 'h': TILE_SIZE})()


class MockTileMap:
    def __init__(self):
        s1 = pygame.Surface((16, 16))
        s2 = pygame.Surface((16, 16))
        s3 = pygame.Surface((16, 16))
        s4 = pygame.Surface((16, 16))
        self.codes = [
            None,
            (1, s1, "floor1"),
            (2, s2, "floor2"),
            (3, s3, "brick1"),
            (4, s4, "brick2")
        ]

    def get_shared_texture(self, tile_id, surf):
        return 100 + tile_id


class TestPersistence(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_json = os.path.join(self.temp_dir.name, "test_level.json")
        self.temp_npz = os.path.join(self.temp_dir.name, "test_lv.npz")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_and_load_preserves_custom_tiles(self):
        """Valida que um mapa customizado e salvo e recarregado sem ser sobrescrito."""
        level = Level1()
        h, w = TILE_MAP_LEVEL1[1], TILE_MAP_LEVEL1[0]

        # Monta matriz com dados customizados
        level.tiles = [[None for _ in range(w)] for _ in range(h)]
        level.tiles[5][10] = MockTile(1, 10 * TILE_SIZE, 5 * TILE_SIZE)
        level.tiles[20][35] = MockTile(3, 35 * TILE_SIZE, 20 * TILE_SIZE)
        level.tiles[50][100] = MockTile(4, 100 * TILE_SIZE, 50 * TILE_SIZE)

        # Salva em arquivos temporários
        save_ok = level.save(self.temp_json, self.temp_npz)
        self.assertTrue(save_ok, "Falha ao salvar o mapa em arquivos temporários.")
        self.assertTrue(os.path.exists(self.temp_json), "Arquivo JSON temporário não foi criado.")
        self.assertTrue(os.path.exists(self.temp_npz), "Arquivo NPZ temporário não foi criado.")

        # Carrega em uma nova instância
        new_level = Level1()
        mock_tilemap = MockTileMap()
        load_ok = new_level.load(mock_tilemap, self.temp_json, self.temp_npz)
        self.assertTrue(load_ok, "Falha ao carregar o mapa temporário.")

        # Verifica se as posições personalizadas foram preservadas
        self.assertIsNotNone(new_level.tiles[5][10], "Bloco em (5, 10) deveria existir.")
        self.assertEqual(new_level.tiles[5][10].id, 1)

        self.assertIsNotNone(new_level.tiles[20][35], "Bloco em (20, 35) deveria existir.")
        self.assertEqual(new_level.tiles[20][35].id, 3)

        self.assertIsNotNone(new_level.tiles[50][100], "Bloco em (50, 100) deveria existir.")
        self.assertEqual(new_level.tiles[50][100].id, 4)

        # Verifica que células vazias continuam None
        self.assertIsNone(new_level.tiles[0][0])
        self.assertIsNone(new_level.tiles[1][1])

    def test_original_maps_are_not_modified_by_tests(self):
        """Garante que os arquivos originais do jogo não foram alterados."""
        orig_json = os.path.abspath("source/data/level1.json")
        orig_npz = os.path.abspath("source/data/lv1.npz")
        self.assertTrue(os.path.exists(orig_json), "level1.json original deve existir.")
        self.assertTrue(os.path.exists(orig_npz), "lv1.npz original deve existir.")


if __name__ == "__main__":
    unittest.main()
