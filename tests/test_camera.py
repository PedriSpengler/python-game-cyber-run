import unittest
import math
from source.modules.camera import Camera2D


class TestCamera2D(unittest.TestCase):
    """
    Testes unitários para a classe Camera2D:
    - Conversão entre World Space e Screen Space;
    - Interpolação independente de framerate (decaimento exponencial);
    - Limites de clamping do mundo (evitar áreas vazias à esquerda e direita).
    """

    def setUp(self):
        self.camera = Camera2D(viewport_width=1920, viewport_height=1080)
        # Mundo com largura de 500 tiles de 32px = 16000px
        self.camera.set_world_bounds(world_w=16000, world_h=3200)

    def test_coordinate_conversions(self):
        """Valida que world_to_screen e screen_to_world são operações inversas exatas."""
        self.camera.x = 500.0
        self.camera.y = 0.0

        world_x, world_y = 1200.0, 300.0
        screen_x, screen_y = self.camera.world_to_screen(world_x, world_y)
        self.assertEqual(screen_x, 700.0)
        self.assertEqual(screen_y, 300.0)

        restored_world_x, restored_world_y = self.camera.screen_to_world(screen_x, screen_y)
        self.assertEqual(restored_world_x, world_x)
        self.assertEqual(restored_world_y, world_y)

    def test_left_boundary_clamping(self):
        """Garante que a câmera não ultrapasse a margem esquerda (x < 0)."""
        target_mock = (50, 500)  # Jogador muito próximo ao início
        self.camera.follow(target_mock, dt=1.0)
        self.assertGreaterEqual(self.camera.x, 0.0)

    def test_right_boundary_clamping(self):
        """Garante que a câmera respeite o limite máximo do mundo (world_w - viewport_width)."""
        max_allowed_x = 16000 - 1920
        target_mock = (15900, 500)  # Jogador no fim da fase

        # Múltiplos updates simulando tempo suficiente para convergir
        for _ in range(50):
            self.camera.follow(target_mock, dt=0.1)

        self.assertLessEqual(self.camera.x, max_allowed_x)
        self.assertAlmostEqual(self.camera.x, max_allowed_x, delta=1.0)

    def test_framerate_independent_lerp(self):
        """
        Valida que a aproximação suave utiliza decaimento exponencial:
        alpha = 1 - exp(-smooth_speed * dt).
        """
        self.camera.x = 0.0
        target_mock = (3000, 500)

        # Atualiza com dt=0.016 (~60 FPS)
        dt = 0.016
        expected_target_x = 3000 - (1920 * 0.35)  # 3000 - 672 = 2328
        alpha = 1.0 - math.exp(-self.camera.smooth_speed * dt)

        self.camera.follow(target_mock, dt=dt)
        expected_x = expected_target_x * alpha

        self.assertAlmostEqual(self.camera.x, expected_x, places=2)
        self.assertGreater(self.camera.x, 0.0)
        self.assertLess(self.camera.x, expected_target_x)


if __name__ == '__main__':
    unittest.main()
