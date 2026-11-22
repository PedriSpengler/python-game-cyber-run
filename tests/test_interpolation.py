import unittest
import time
import sys
from source.modules.network.interpolation import (
    EntityState, Snapshot, InterpolationBuffer
)


class TestInterpolation(unittest.TestCase):
    """
    Testes específicos para o Bloco 5 da Etapa 5:
    - InterpolationBuffer e suavização contínua de movimento no cliente.
    """

    def test_interpolation_has_no_gui_dependencies(self):
        """Valida que o subsistema de interpolação é 100% livre de Pygame e PyOpenGL."""
        import source.modules.network.interpolation as interp_mod
        self.assertFalse(hasattr(interp_mod, "pygame"))
        self.assertFalse(hasattr(interp_mod, "OpenGL"))

    def test_empty_buffer_returns_empty_dict(self):
        """Um buffer vazio não deve falhar e deve retornar dicionário vazio."""
        buf = InterpolationBuffer(delay=0.1)
        self.assertEqual(buf.count, 0)
        self.assertEqual(buf.sample(time.time()), {})

    def test_single_snapshot_sampling(self):
        """Com apenas um snapshot, sample retorna o estado exato desse snapshot."""
        buf = InterpolationBuffer(delay=0.1)
        payload = {
            "tick": 1,
            "entities": [{"id": 1, "x": 100.0, "y": 200.0, "vx": 10.0, "vy": 0.0, "facing": 1, "state": "idle"}]
        }
        buf.add_snapshot(payload, local_receive_time=1.0)
        self.assertEqual(buf.count, 1)

        sampled = buf.sample(render_time=1.2)
        self.assertIn(1, sampled)
        self.assertEqual(sampled[1].x, 100.0)
        self.assertEqual(sampled[1].y, 200.0)

    def test_linear_interpolation_between_two_snapshots(self):
        """
        Valida que a interpolação linear calcula a posição exata proporcional a alpha.
        s0: t=1.0, x=100.0, y=100.0
        s1: t=2.0, x=200.0, y=100.0
        delay = 0.1
        render_time = 1.6 => target_time = 1.5 => alpha = 0.5
        Esperado: x=150.0, y=100.0
        """
        buf = InterpolationBuffer(delay=0.1)
        s0_payload = {
            "tick": 10,
            "entities": [{"id": 1, "x": 100.0, "y": 100.0, "vx": 100.0, "vy": 0.0, "facing": 1, "state": "running"}]
        }
        s1_payload = {
            "tick": 20,
            "entities": [{"id": 1, "x": 200.0, "y": 100.0, "vx": 100.0, "vy": 0.0, "facing": -1, "state": "jumping"}]
        }

        buf.add_snapshot(s0_payload, local_receive_time=1.0)
        buf.add_snapshot(s1_payload, local_receive_time=2.0)
        self.assertEqual(buf.count, 2)

        # target_time = 1.6 - 0.1 = 1.5 (exatamente 50% entre 1.0 e 2.0)
        sampled = buf.sample(render_time=1.6)
        self.assertIn(1, sampled)
        self.assertAlmostEqual(sampled[1].x, 150.0, places=3)
        self.assertAlmostEqual(sampled[1].y, 100.0, places=3)
        # alpha = 0.5 adota os estados discretos do mais recente s1
        self.assertEqual(sampled[1].facing, -1)
        self.assertEqual(sampled[1].state, "jumping")

        # target_time = 1.35 - 0.1 = 1.25 (25% do caminho)
        sampled_quarter = buf.sample(render_time=1.35)
        self.assertAlmostEqual(sampled_quarter[1].x, 125.0, places=3)
        self.assertAlmostEqual(sampled_quarter[1].y, 100.0, places=3)
        # alpha = 0.25 < 0.5 mantém estados de s0
        self.assertEqual(sampled_quarter[1].facing, 1)
        self.assertEqual(sampled_quarter[1].state, "running")

    def test_out_of_order_packets_are_sorted(self):
        """Valida que pacotes que chegam fora de ordem são devidamente organizados cronologicamente."""
        buf = InterpolationBuffer(delay=0.1)
        s1 = {"tick": 2, "entities": [{"id": 1, "x": 200.0, "y": 200.0}]}
        s0 = {"tick": 1, "entities": [{"id": 1, "x": 100.0, "y": 100.0}]}

        # Inserção inversa (s1 antes de s0)
        buf.add_snapshot(s1, local_receive_time=2.0)
        buf.add_snapshot(s0, local_receive_time=1.0)

        # target_time = 1.6 - 0.1 = 1.5 => midpoint
        sampled = buf.sample(render_time=1.6)
        self.assertAlmostEqual(sampled[1].x, 150.0, places=3)
        self.assertAlmostEqual(sampled[1].y, 150.0, places=3)

    def test_teleport_detection_triggers_snap(self):
        """
        Valida que movimentações bruscas que excedem snap_threshold (>200px)
        não são interpoladas continuamente, executando snap direto para evitar artefatos visuais.
        """
        buf = InterpolationBuffer(delay=0.1, snap_threshold=200.0)
        s0 = {"tick": 1, "entities": [{"id": 1, "x": 100.0, "y": 100.0}]}
        # Teleporte de 800px em X (ex: respawn)
        s1 = {"tick": 2, "entities": [{"id": 1, "x": 900.0, "y": 100.0}]}

        buf.add_snapshot(s0, local_receive_time=1.0)
        buf.add_snapshot(s1, local_receive_time=2.0)

        # target_time = 1.5 => sem lerp! Deve realizar snap direto para s1 (900.0)
        sampled = buf.sample(render_time=1.6)
        self.assertEqual(sampled[1].x, 900.0)

    def test_buffer_pruning_limits_memory(self):
        """Valida que snapshots obsoletos são podados para não estourar memória."""
        buf = InterpolationBuffer(delay=0.1, max_size=5)
        for i in range(10):
            buf.add_snapshot({"tick": i, "entities": []}, local_receive_time=float(i))

        # Não deve ultrapassar max_size
        self.assertLessEqual(buf.count, 5)


if __name__ == '__main__':
    unittest.main()
