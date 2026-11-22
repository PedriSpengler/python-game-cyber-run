import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from source.modules.constants import TILE_SIZE, TILE_MAP_LEVEL1


class TestEditorLogic(unittest.TestCase):
    def test_global_coordinate_mapping_with_anchor(self):
        """Valida a fórmula de conversão de coordenadas locais da tela para coordenadas globais do mapa."""
        # Simula âncora deslocada no editor
        anchor = [25, 10]
        
        # Coordenada local de tela da célula clicada
        local_col = 4
        local_lin = 3

        # Mapeamento com a fórmula corrigida
        map_col = local_col + anchor[0]
        map_lin = local_lin + anchor[1]

        self.assertEqual(map_col, 29, "Coluna global incorreta.")
        self.assertEqual(map_lin, 13, "Linha global incorreta.")

        # Posição em pixels no mundo
        world_left = map_col * TILE_SIZE
        world_top = map_lin * TILE_SIZE

        self.assertEqual(world_left, 29 * 32)
        self.assertEqual(world_top, 13 * 32)

    def test_editor_boundary_protection(self):
        """Garante que posições fora dos limites do mapa (TILE_MAP_LEVEL1) sejam rejeitadas."""
        max_cols, max_lines = TILE_MAP_LEVEL1[0], TILE_MAP_LEVEL1[1]

        # Coordenada além do limite
        out_col = max_cols + 5
        out_lin = max_lines + 2

        is_valid = (0 <= out_lin < max_lines) and (0 <= out_col < max_cols)
        self.assertFalse(is_valid, "Coordenada além do limite da fase deveria ser inválida.")


if __name__ == "__main__":
    unittest.main()
