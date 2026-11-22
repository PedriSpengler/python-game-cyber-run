import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pygame
from source.modules.utils import utils
from source.modules.entities.tiles import Tile, TileMap


class TestGraphicsLifecycle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Tenta inicializar pygame display com dummy driver para testes sem janela
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        try:
            pygame.display.init()
            # Se OpenGL estiver disponível no driver dummy, inicializa
            cls.has_gl = False
            try:
                from OpenGL.GL import glGenTextures, glDeleteTextures
                # Cria superficie pequena para teste
                cls.has_gl = True
            except Exception:
                cls.has_gl = False
        except Exception:
            cls.has_gl = False

    def test_tile_flyweight_texture_assignment(self):
        """Valida que quando um texture_id e fornecido, o Tile nao aloca nova textura e marca owns_texture=False."""
        surf = pygame.Surface((32, 32))
        shared_id = 999
        tile = Tile(1, surf, "floor1", texture_id=shared_id)

        self.assertEqual(tile.texture_id, shared_id, "O Tile deve receber o texture_id compartilhado.")
        self.assertFalse(tile.owns_texture, "O Tile com textura compartilhada não deve ser dono da textura.")

    def test_tilemap_flyweight_dictionary(self):
        """Valida o ciclo de vida do dicionário de texturas compartilhadas do TileMap."""
        tilemap = TileMap()
        tilemap.shared_textures[1] = 101
        tilemap.shared_textures[2] = 102

        # Libera texturas
        tilemap.release_textures()
        self.assertEqual(len(tilemap.shared_textures), 0, "Dicionário de texturas compartilhadas deve ser limpo ao chamar release_textures.")

    def test_delete_texture_safe_with_none(self):
        """Valida que utils.delete_texture lida com None e valores inválidos sem levantar exceções."""
        try:
            utils.delete_texture(None)
            utils.delete_texture(0)
        except Exception as e:
            self.fail(f"delete_texture falhou com entrada segura: {e}")


if __name__ == "__main__":
    unittest.main()
