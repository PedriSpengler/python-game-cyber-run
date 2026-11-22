import unittest
import time
import socket
import threading
from source.modules.network.network_server import NetworkServer
from source.modules.network.network_client import NetworkClient
from source.modules.network.messages import MessageType
from source.modules.network.interpolation import InterpolationBuffer
from source.modules.scenes.manager import SceneManager
from source.modules.scenes.lobby_scene import LobbyScene
from source.modules.scenes.game_scene import GameScene


class TestMultiplayerEndToEnd(unittest.TestCase):
    """
    Suíte de Testes de Integração de Ponta a Ponta para a Etapa 5 (Bloco 8).
    Valida as 5 fases do ciclo de vida multiplayer LAN:
    - Fase A: Inicialização do Host e Servidor Autoritativo;
    - Fase B: Conexão e Handshake do Cliente 2;
    - Fase C: Início de Partida (START_GAME) e transição;
    - Fase D: Simulação autoritativa a 60Hz, inputs e broadcast a 25Hz com interpolação;
    - Fase E: Desconexão graciosa, ausência de sockets/threads órfãos.
    """

    def _check_sandbox_permission(self, client: NetworkClient):
        if client.rejection_reason and ("Operation not permitted" in client.rejection_reason or "[Errno 1]" in client.rejection_reason):
            self.skipTest("Ambiente de sandbox restringiu conexão de socket loopback local.")

    def test_complete_multiplayer_lifecycle_phases_a_to_e(self):
        """Executa a sequência completa de ponta a ponta (Fases A até E)."""
        test_tcp = 21777
        test_udp = 21778

        # -------------------------------------------------------------
        # FASE A: INICIALIZAÇÃO
        # -------------------------------------------------------------
        server = NetworkServer(host="127.0.0.1", tcp_port=test_tcp, udp_port=test_udp, max_players=2)
        self.assertTrue(server.start())
        self.assertTrue(server.is_running())

        host_client = NetworkClient()
        try:
            h_ok = host_client.connect(host="127.0.0.1", tcp_port=test_tcp, udp_port=test_udp, player_name="HostPlayer")
            self._check_sandbox_permission(host_client)
            self.assertTrue(h_ok)
            self.assertEqual(host_client.player_id, 1)
            self.assertEqual(server.connection_manager.active_count, 1)
            self.assertIn(1, server.players)

            # -------------------------------------------------------------
            # FASE B: CONEXÃO DO CLIENTE 2
            # -------------------------------------------------------------
            guest_client = NetworkClient()
            g_ok = guest_client.connect(host="127.0.0.1", tcp_port=test_tcp, udp_port=test_udp, player_name="GuestPlayer")
            self._check_sandbox_permission(guest_client)
            self.assertTrue(g_ok)
            self.assertEqual(guest_client.player_id, 2)
            self.assertEqual(server.connection_manager.active_count, 2)
            self.assertIn(2, server.players)

            # Ambos devem receber estado atualizado do lobby
            time.sleep(0.15)
            h_events = host_client.get_events()
            g_events = guest_client.get_events()
            self.assertTrue(any(ev.msg_type == MessageType.LOBBY_STATE for ev in h_events) or len(host_client.lobby_players) >= 2)
            self.assertTrue(any(ev.msg_type == MessageType.LOBBY_STATE for ev in g_events) or len(guest_client.lobby_players) >= 2)

            # -------------------------------------------------------------
            # FASE C: INÍCIO DA PARTIDA (START_GAME)
            # -------------------------------------------------------------
            # Host dispara início da partida via TCP
            host_client.send_tcp_message(MessageType.START_GAME, {"level_name": "level1", "max_players": 2})

            time.sleep(0.15)
            # Servidor processa e difunde START_GAME para ambos
            h_events = host_client.get_events()
            g_events = guest_client.get_events()
            self.assertTrue(host_client.is_game_started or any(ev.msg_type == MessageType.START_GAME for ev in h_events))
            self.assertTrue(guest_client.is_game_started or any(ev.msg_type == MessageType.START_GAME for ev in g_events))

            # -------------------------------------------------------------
            # FASE D: SIMULAÇÃO AUTORITATIVA E SINCRONIZAÇÃO
            # -------------------------------------------------------------
            # Cliente 2 transmite comando de movimentação para a direita
            p2_initial_x = server.players[2].x
            guest_client.send_input(move_x=1, jump=False, jump_held=False, tick=10)

            # Host transmite comando parado
            host_client.send_input(move_x=0, jump=False, jump_held=False, tick=10)

            # Aguarda tempo suficiente para múltiplos ticks (60Hz) e snapshots (25Hz)
            time.sleep(0.35)

            # O servidor deve ter simulado autoritativamente o avanço do Player 2
            self.assertGreater(server.players[2].x, p2_initial_x)
            self.assertGreater(server.current_tick, 10)

            # Cliente 2 deve ter recebido snapshots no buffer de interpolação
            self.assertGreater(guest_client.interpolation_buffer.count, 0)
            entities_g = guest_client.get_interpolated_entities()
            self.assertIn(1, entities_g)
            self.assertIn(2, entities_g)
            self.assertGreater(entities_g[2].x, p2_initial_x)

            # Host também deve ter recebido snapshots atualizados do Player 2
            self.assertGreater(host_client.interpolation_buffer.count, 0)
            entities_h = host_client.get_interpolated_entities()
            self.assertIn(2, entities_h)
            self.assertGreater(entities_h[2].x, p2_initial_x)

            # -------------------------------------------------------------
            # FASE E: DESCONEXÃO E ENCERRAMENTO LIMPO
            # -------------------------------------------------------------
            guest_client.disconnect(reason="TESTE_CONCLUIDO")
            self.assertFalse(guest_client.is_connected())

            time.sleep(0.2)
            # Servidor deve ter removido Player 2 e mantido Player 1 funcional
            self.assertEqual(server.connection_manager.active_count, 1)
            self.assertNotIn(2, server.players)
            self.assertIn(1, server.players)
            self.assertTrue(host_client.is_connected())

            # Host desconecta e servidor encerra
            host_client.disconnect(reason="HOST_FECHOU")
            server.shutdown()
            self.assertFalse(server.is_running())
            self.assertEqual(server.connection_manager.active_count, 0)

        except PermissionError:
            self.skipTest("Ambiente de sandbox restringiu conexão de socket loopback local.")
        finally:
            if 'guest_client' in locals():
                guest_client.shutdown()
            host_client.shutdown()
            server.shutdown()

    def test_packet_resilience_in_interpolation_buffer(self):
        """Valida que o buffer rejeita ticks duplicados e reordena pacotes com jitter."""
        buf = InterpolationBuffer(delay=0.1)

        # Inserção desordenada: Tick 3 (t=3.0), Tick 1 (t=1.0), Tick 2 (t=2.0)
        s3 = {"tick": 3, "entities": [{"id": 1, "x": 300.0, "y": 100.0}]}
        s1 = {"tick": 1, "entities": [{"id": 1, "x": 100.0, "y": 100.0}]}
        s2 = {"tick": 2, "entities": [{"id": 1, "x": 200.0, "y": 100.0}]}

        self.assertTrue(buf.add_snapshot(s3, local_receive_time=3.0))
        self.assertTrue(buf.add_snapshot(s1, local_receive_time=1.0))
        self.assertTrue(buf.add_snapshot(s2, local_receive_time=2.0))

        # Rejeição de tick duplicado
        duplicate_s2 = {"tick": 2, "entities": [{"id": 1, "x": 999.0, "y": 999.0}]}
        self.assertFalse(buf.add_snapshot(duplicate_s2, local_receive_time=2.1))

        # Verifica ordenação temporal na amostragem (t_target = 2.0 -> midpoint entre s1 e s3)
        sample = buf.sample(render_time=2.1)
        self.assertEqual(sample[1].x, 200.0)

    def test_unexpected_client_crash_and_server_recovery(self):
        """Valida que queda inesperada de conexão do cliente (socket fechado) não congela o servidor."""
        test_tcp = 21779
        test_udp = 21780
        server = NetworkServer(host="127.0.0.1", tcp_port=test_tcp, udp_port=test_udp, max_players=2)
        self.assertTrue(server.start())

        client_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_tcp.connect(("127.0.0.1", test_tcp))
            from source.modules.network.protocol import Protocol
            req = Protocol.serialize(MessageType.CONNECT_REQUEST, {"name": "CrashDummy", "version": 1})
            client_tcp.sendall(req)

            resp = client_tcp.recv(1024)
            env = Protocol.deserialize(resp)
            self.assertEqual(env.msg_type, MessageType.CONNECT_ACCEPTED)
            self.assertEqual(server.connection_manager.active_count, 1)

            # Simula crash brusco do processo do cliente (fechamento repentino do socket sem DISCONNECT)
            client_tcp.close()

            # Aguarda a thread do servidor detectar o EOF/fechamento do socket
            time.sleep(0.3)
            self.assertEqual(server.connection_manager.active_count, 0)
            self.assertEqual(len(server.players), 0)

            # Servidor continua responsivo para aceitar novo cliente
            client2 = NetworkClient()
            c2_ok = client2.connect(host="127.0.0.1", tcp_port=test_tcp, udp_port=test_udp, player_name="NextPlayer")
            self.assertTrue(c2_ok)
            self.assertEqual(server.connection_manager.active_count, 1)
            client2.shutdown()

        except PermissionError:
            self.skipTest("Ambiente de sandbox restringiu conexão de socket loopback local.")
        finally:
            client_tcp.close()
            server.shutdown()

    def test_thread_lifecycle_no_orphan_threads(self):
        """Valida inicializações e encerramentos repetidos sem acúmulo de threads órfãs."""
        test_tcp = 21781
        test_udp = 21782

        initial_thread_count = threading.active_count()

        for _ in range(3):
            srv = NetworkServer(host="127.0.0.1", tcp_port=test_tcp, udp_port=test_udp)
            srv.start()
            self.assertTrue(srv.is_running())
            srv.shutdown()
            self.assertFalse(srv.is_running())

        # Dá tempo para as threads finalizarem
        time.sleep(0.2)
        final_thread_count = threading.active_count()
        self.assertEqual(initial_thread_count, final_thread_count)


if __name__ == '__main__':
    unittest.main()
