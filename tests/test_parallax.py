import unittest
from unittest.mock import MagicMock, patch
import pygame
from source.modules.ui.parallax import ParallaxLayer, ParallaxBackground


class TestParallax(unittest.TestCase):
    """
    Testes unitários para o sistema de Parallax:
    - Fatores de deslocamento por camada;
    - Autoscroll autônomo (drift de nuvens);
    - Wrapping horizontal contínuo;
    - Ciclo de vida e liberação de texturas.
    """

    @patch('source.modules.ui.parallax.utils.surface_to_texture', return_value=101)
    def test_parallax_layer_drift_and_wrapping(self, mock_surface_to_texture):
        """Valida o avanço autônomo e o wrapping de nuvens."""
        surf = pygame.Surface((100, 50))
        layer = ParallaxLayer(surf, factor_x=0.1, scale_factor=2.0, autoscroll_speed=20.0)

        # Largura escalada = 100 * 2.0 = 200
        self.assertEqual(layer.scaled_w, 200)

        # dt = 5 segundos -> drift = 20.0 * 5 = 100
        layer.update(dt=5.0)
        self.assertEqual(layer.drift_x, 100.0)

        # dt = 6 segundos adicionais -> drift = (100 + 120) % 200 = 20
        layer.update(dt=6.0)
        self.assertEqual(layer.drift_x, 20.0)

    @patch('source.modules.ui.parallax.utils.surface_to_texture', return_value=102)
    @patch('source.modules.ui.parallax.utils.delete_texture')
    def test_parallax_layer_destroy(self, mock_delete_texture, mock_surface_to_texture):
        """Valida que destroy() invoca delete_texture e limpa o texture_id."""
        surf = pygame.Surface((50, 50))
        layer = ParallaxLayer(surf, factor_x=0.5)

        self.assertEqual(layer.texture_id, 102)
        layer.destroy()
        mock_delete_texture.assert_called_once_with(102)
        self.assertIsNone(layer.texture_id)


if __name__ == '__main__':
    unittest.main()
