import unittest
import time
import socket
import sys
from source.modules.network.messages import MessageType, NetworkEnvelope
from source.modules.network.protocol import Protocol
from source.modules.network.network_server import NetworkServer
from source.modules.network.network_client import NetworkClient
from source.modules.input.input_state import InputState


class TestSimulationSync(unittest.TestCase):
    """
    Testes específicos para o Bloco 4 da Etapa 5:
    - Simulação autoritativa no servidor a 60Hz;
    - Processamento de inputs dos jogadores e física com PhysicsSystem;
    - Transmissão periódica de snapshots (GAME_STATE) a 25Hz.
    """

    def test_simulation_has_no_gui_dependencies(self):
        """Verifica que o loop de simulação e entidades são 100% livres de Pygame e PyOpenGL."""
        import source.modules.network.network_server as srv_mod
        self.assertFalse(hasattr(srv_mod, "pygame"))
        self.assertFalse(hasattr(srv_mod, "OpenGL"))

        server = NetworkServer()
        self.assertFalse(server.is_running())
        self.assertEqual(server.current_tick, 0)
        self.assertEqual(len(server.players), 0)

    def test_player_registration_and_simulation_step(self):
        """Valida adição de jogadores, incremento de ticks e integração da gravidade."""
        server = NetworkServer()
        server.add_player(1)
        self.assertIn(1, server.players)
        p1 = server.players[1]
        self.assertEqual(p1.x, 200.0)
        self.assertEqual(p1.y, 300.0)

        # Executa um passo de simulação física (dt = 1/60s)
        server.step_simulation(dt=1.0 / 60.0)
        self.assertEqual(server.current_tick, 1)
        # Gravidade deve acelerar verticalmente o jogador (vy > 0)
        self.assertGreater(p1.vy, 0.0)

        # Remoção do jogador
        server.remove_player(1)
        self.assertNotIn(1, server.players)

    def test_input_processing_and_jump_edge_trigger(self):
        """Valida aplicação de move_x, disparo do pulo e consumo do edge-trigger."""
        server = NetworkServer()
        server.add_player(1)
        p1 = server.players[1]
        p1.is_grounded = True
        p1.vy = 0.0

        # Enfileira comando de entrada simulado
        env = NetworkEnvelope(
            msg_type=MessageType.PLAYER_INPUT,
            seq=1,
            session_id="test_sess",
            timestamp=time.time(),
            payload={"player_id": 1, "tick": 5, "move_x": 1, "jump": True, "jump_held": True}
        )
        server.incoming_events.put(("test_sess", env))

        # Executa passo da simulação
        server.step_simulation(dt=1.0 / 60.0)

        # Movimentação horizontal deve ter sido aplicada (velocidade positiva)
        self.assertEqual(p1.vx, p1.speed)
        self.assertEqual(p1.facing, 1)

        # Pulo deve ter sido disparado (vy negativo)
        self.assertLess(p1.vy, 0.0)

        # O edge-trigger jump deve ter sido resetado para False no servidor
        self.assertFalse(server.player_inputs[1].jump)

    def _check_sandbox_permission(self, client: NetworkClient):
        if client.rejection_reason and ("Operation not permitted" in client.rejection_reason or "[Errno 1]" in client.rejection_reason):
            self.skipTest("Ambiente de sandbox restringiu conexão de socket loopback local.")

    def test_live_simulation_and_game_state_broadcast(self):
        """
        Teste integrado com servidor e cliente reais:
        - Servidor roda loop autoritativo;
        - Cliente conecta e vincula porta UDP;
        - Servidor difunde GAME_STATE a 25Hz via broadcast UDP;
        - Cliente ingere snapshots diretamente em seu InterpolationBuffer.
        """
        test_tcp_port = 19777
        test_udp_port = 19778
        server = NetworkServer(host="127.0.0.1", tcp_port=test_tcp_port, udp_port=test_udp_port, max_players=2)
        self.assertTrue(server.start())

        client = NetworkClient()
        try:
            connected = client.connect(
                host="127.0.0.1",
                tcp_port=test_tcp_port,
                udp_port=test_udp_port,
                player_name="SimTester"
            )
            self._check_sandbox_permission(client)
            self.assertTrue(connected, f"Falha na conexão: {client.rejection_reason}")

            # Aguarda tempo suficiente para recepção de múltiplos snapshots (>= 200ms -> ~5 snapshots a 25Hz)
            time.sleep(0.3)

            # Verifica se o cliente recebeu snapshots no seu buffer de interpolação
            self.assertGreater(client.interpolation_buffer.count, 0)

            # Valida amostragem de entidades interpoladas
            entities = client.get_interpolated_entities()
            self.assertIn(1, entities)
            e1 = entities[1]
            self.assertIsInstance(e1.x, float)
            self.assertIsInstance(e1.y, float)

        except PermissionError:
            self.skipTest("Ambiente de sandbox restringiu conexão de socket loopback local.")
        finally:
            client.shutdown()
            server.shutdown()


if __name__ == '__main__':
    unittest.main()
