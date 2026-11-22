import unittest
import socket
import time
import sys
from source.modules.network.network_config import DEFAULT_HOST
from source.modules.network.messages import MessageType
from source.modules.network.network_server import NetworkServer
from source.modules.network.network_client import NetworkClient


class TestNetworkClient(unittest.TestCase):
    """
    Testes específicos para o Bloco 3 da Etapa 5:
    - NetworkClient (ciclo de vida, handshake TCP, transmissão UDP, isolamento headless).
    """

    def test_client_has_no_gui_dependencies(self):
        """Verifica se NetworkClient opera 100% desacoplado de Pygame e PyOpenGL."""
        import source.modules.network.network_client as client_mod
        self.assertFalse(hasattr(client_mod, "pygame"))
        self.assertFalse(hasattr(client_mod, "OpenGL"))

        client = NetworkClient()
        self.assertFalse(client.is_connected())
        self.assertEqual(client.player_id, None)
        self.assertEqual(client.session_id, "")

    def _check_sandbox_permission(self, client: NetworkClient):
        if client.rejection_reason and ("Operation not permitted" in client.rejection_reason or "[Errno 1]" in client.rejection_reason):
            self.skipTest("Ambiente de sandbox restringiu conexão de socket loopback local.")

    def test_client_connect_and_handshake(self):
        """Valida conexão TCP com handshake CONNECT_REQUEST e CONNECT_ACCEPTED."""
        test_tcp_port = 18777
        test_udp_port = 18778
        server = NetworkServer(host="127.0.0.1", tcp_port=test_tcp_port, udp_port=test_udp_port, max_players=2)
        self.assertTrue(server.start())

        client = NetworkClient()
        try:
            connected = client.connect(
                host="127.0.0.1",
                tcp_port=test_tcp_port,
                udp_port=test_udp_port,
                player_name="PlayerAlpha"
            )
            self._check_sandbox_permission(client)
            self.assertTrue(connected, f"Connect failed: {client.rejection_reason}")
            self.assertTrue(client.is_connected())
            self.assertEqual(client.player_id, 1)
            self.assertTrue(len(client.session_id) > 0)
            self.assertTrue(client.is_in_lobby)

            # Dá um tempo para o lobby_state chegar via TCP
            time.sleep(0.1)
            events = client.get_events()
            self.assertTrue(any(ev.msg_type == MessageType.LOBBY_STATE for ev in events) or len(client.lobby_players) > 0)

        except PermissionError:
            self.skipTest("Ambiente de sandbox restringiu conexão de socket loopback local.")
        finally:
            client.shutdown()
            server.shutdown()

    def test_client_rejected_when_server_full(self):
        """Valida que o cliente recebe CONNECT_REJECTED quando o servidor atingir max_players."""
        test_tcp_port = 18779
        test_udp_port = 18780
        server = NetworkServer(host="127.0.0.1", tcp_port=test_tcp_port, udp_port=test_udp_port, max_players=1)
        self.assertTrue(server.start())

        client1 = NetworkClient()
        client2 = NetworkClient()
        try:
            # Cliente 1 conecta com sucesso
            c1_ok = client1.connect(host="127.0.0.1", tcp_port=test_tcp_port, udp_port=test_udp_port, player_name="P1")
            self._check_sandbox_permission(client1)
            self.assertTrue(c1_ok)
            self.assertTrue(client1.is_connected())

            # Cliente 2 tenta conectar e deve ser recusado
            c2_ok = client2.connect(host="127.0.0.1", tcp_port=test_tcp_port, udp_port=test_udp_port, player_name="P2")
            self._check_sandbox_permission(client2)
            self.assertFalse(c2_ok)
            self.assertFalse(client2.is_connected())
            self.assertEqual(client2.rejection_reason, "SALA_LOTADA")

        except PermissionError:
            self.skipTest("Ambiente de sandbox restringiu conexão de socket loopback local.")
        finally:
            client1.shutdown()
            client2.shutdown()
            server.shutdown()

    def test_client_send_udp_input_and_ping(self):
        """Valida a transmissão de comandos via UDP e resposta de PONG para medição de ping."""
        test_tcp_port = 18781
        test_udp_port = 18782
        server = NetworkServer(host="127.0.0.1", tcp_port=test_tcp_port, udp_port=test_udp_port, max_players=2)
        self.assertTrue(server.start())

        client = NetworkClient()
        try:
            connected = client.connect(
                host="127.0.0.1",
                tcp_port=test_tcp_port,
                udp_port=test_udp_port,
                player_name="P1"
            )
            self._check_sandbox_permission(client)
            self.assertTrue(connected, f"Connect failed: {client.rejection_reason}")

            # Envia comando de entrada do jogador via UDP
            sent = client.send_input(move_x=1, jump=True, jump_held=False, tick=105)
            self.assertTrue(sent)

            # Aguarda servidor enfileirar ou processar o evento no loop de simulação
            time.sleep(0.15)
            if not server.incoming_events.empty():
                session_id, env = server.incoming_events.get_nowait()
                self.assertEqual(session_id, client.session_id)
                self.assertEqual(env.msg_type, MessageType.PLAYER_INPUT)
                self.assertEqual(env.payload["move_x"], 1)
            else:
                self.assertIn(client.player_id, server.player_inputs)
                self.assertEqual(server.player_inputs[client.player_id].move_x, 1)

            # Envia Ping e verifica medição de latência
            client.send_ping()
            time.sleep(0.15)
            self.assertGreaterEqual(client.ping_ms, 0.0)

        except PermissionError:
            self.skipTest("Ambiente de sandbox restringiu conexão de socket loopback local.")
        finally:
            client.shutdown()
            server.shutdown()

    def test_client_clean_disconnect_and_shutdown(self):
        """Valida término limpo, notificação de saída e liberação de sockets."""
        test_tcp_port = 18783
        test_udp_port = 18784
        server = NetworkServer(host="127.0.0.1", tcp_port=test_tcp_port, udp_port=test_udp_port, max_players=2)
        self.assertTrue(server.start())

        client = NetworkClient()
        try:
            connected = client.connect(
                host="127.0.0.1",
                tcp_port=test_tcp_port,
                udp_port=test_udp_port,
                player_name="DisconnectTest"
            )
            self._check_sandbox_permission(client)
            self.assertTrue(connected, f"Connect failed: {client.rejection_reason}")
            self.assertEqual(server.connection_manager.active_count, 1)

            # Executa desconexão
            client.disconnect(reason="SAIDA_VOLUNTARIA")
            self.assertFalse(client.is_connected())

            # Aguarda servidor processar o evento de desconexão
            time.sleep(0.15)
            self.assertEqual(server.connection_manager.active_count, 0)

            # Verifica liberação dos sockets
            self.assertIsNone(client._tcp_socket)
            self.assertIsNone(client._udp_socket)

        except PermissionError:
            self.skipTest("Ambiente de sandbox restringiu conexão de socket loopback local.")
        finally:
            client.shutdown()
            server.shutdown()


if __name__ == '__main__':
    unittest.main()
