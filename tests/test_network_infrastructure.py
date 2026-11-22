import unittest
import socket
import time
import sys
from source.modules.network.network_config import (
    DEFAULT_HOST, MAX_PACKET_SIZE, MAX_PLAYERS
)
from source.modules.network.messages import MessageType, NetworkEnvelope
from source.modules.network.protocol import Protocol, ProtocolError
from source.modules.network.connection_manager import ConnectionManager
from source.modules.network.network_server import NetworkServer


class TestNetworkInfrastructure(unittest.TestCase):
    """
    Testes específicos para os Blocos 1 e 2 da Etapa 5:
    - Protocolo, serialização JSON e validação de limites;
    - ConnectionManager e controle autoritativo de sessões;
    - NetworkServer (inicialização, portas, handshake e desligamento sem GUI).
    """

    def test_server_has_no_gui_dependencies(self):
        """Verifica se todo o subsistema de rede opera 100% livre de Pygame e PyOpenGL."""
        import source.modules.network as net
        # Garante que nenhum módulo do pacote network importa pygame ou OpenGL
        for mod_name in sys.modules:
            if mod_name.startswith("source.modules.network"):
                module = sys.modules[mod_name]
                self.assertFalse(hasattr(module, "pygame"))
                self.assertFalse(hasattr(module, "OpenGL"))

    def test_serialization_and_deserialization(self):
        """Valida que mensagens válidas são codificadas e decodificadas com fidelidade."""
        payload = {"name": "Jogador1", "version": 1}
        raw_bytes = Protocol.serialize(MessageType.CONNECT_REQUEST, payload, seq=1, session_id="abc-123")
        self.assertIsInstance(raw_bytes, bytes)
        self.assertLessEqual(len(raw_bytes), MAX_PACKET_SIZE)

        envelope = Protocol.deserialize(raw_bytes)
        self.assertIsInstance(envelope, NetworkEnvelope)
        self.assertEqual(envelope.msg_type, MessageType.CONNECT_REQUEST)
        self.assertEqual(envelope.seq, 1)
        self.assertEqual(envelope.session_id, "abc-123")
        self.assertEqual(envelope.payload["name"], "Jogador1")

    def test_malformed_packet_rejection(self):
        """Garante rejeição de dados truncados, JSON inválido ou campos ausentes."""
        with self.assertRaises(ProtocolError):
            Protocol.deserialize(b"")

        with self.assertRaises(ProtocolError):
            Protocol.deserialize(b"{not-valid-json}")

        with self.assertRaises(ProtocolError):
            # Falta campo obrigatório 'type'
            Protocol.deserialize(b'{"seq": 1, "session_id": "x", "timestamp": 0, "payload": {}}')

    def test_packet_size_limit(self):
        """Rejeita mensagens com payload que exceda MAX_PACKET_SIZE (1024 bytes)."""
        huge_name = "A" * 2000
        with self.assertRaises(ProtocolError):
            Protocol.serialize(MessageType.CONNECT_REQUEST, {"name": huge_name})

        huge_bytes = b'{"type":"PING","seq":0,"session_id":"","timestamp":0,"payload":{' + (b'"k":"' + b'x'*1200 + b'"') + b'}}'
        with self.assertRaises(ProtocolError):
            Protocol.deserialize(huge_bytes)

    def test_message_validation_payload_rules(self):
        """Valida regras de negócio estritas no payload por tipo de mensagem."""
        # PLAYER_INPUT com move_x inválido (deve ser -1, 0 ou 1)
        with self.assertRaises(ProtocolError):
            Protocol.serialize(MessageType.PLAYER_INPUT, {"tick": 10, "move_x": 5, "jump": False})

        # CONNECT_REQUEST sem campo obrigatório 'name'
        with self.assertRaises(ProtocolError):
            Protocol.serialize(MessageType.CONNECT_REQUEST, {})

    def test_connection_manager_unique_ids_and_slots(self):
        """Valida atribuição sequencial de IDs e bloqueio quando lotado."""
        mgr = ConnectionManager(max_players=2)
        mock_sock1 = socket.socket()
        mock_sock2 = socket.socket()
        mock_sock3 = socket.socket()

        try:
            s1 = mgr.register_client(mock_sock1, ("127.0.0.1", 5001), "Alpha")
            self.assertIsNotNone(s1)
            self.assertEqual(s1.player_id, 1)

            s2 = mgr.register_client(mock_sock2, ("127.0.0.1", 5002), "Beta")
            self.assertIsNotNone(s2)
            self.assertEqual(s2.player_id, 2)
            self.assertTrue(mgr.is_full())

            # Terceiro jogador deve ser recusado
            s3 = mgr.register_client(mock_sock3, ("127.0.0.1", 5003), "Gamma")
            self.assertIsNone(s3)

            # Ao desconectar s1, o ID 1 volta a ficar disponível
            mgr.remove_session(s1.session_id)
            self.assertFalse(mgr.is_full())

            s4 = mgr.register_client(mock_sock3, ("127.0.0.1", 5003), "Delta")
            self.assertIsNotNone(s4)
            self.assertEqual(s4.player_id, 1)  # Reutilizou ID 1
        finally:
            mock_sock1.close()
            mock_sock2.close()
            mock_sock3.close()

    def test_session_udp_binding_and_spoof_protection(self):
        """Valida que o ConnectionManager associa o endereço UDP e protege contra spoofing."""
        mgr = ConnectionManager(max_players=2)
        sock = socket.socket()
        try:
            session = mgr.register_client(sock, ("127.0.0.1", 6001), "Player")
            self.assertIsNone(session.udp_addr)

            mgr.bind_udp_address(session.session_id, ("127.0.0.1", 7001))
            self.assertEqual(session.udp_addr, ("127.0.0.1", 7001))

            # Busca por UDP address
            found = mgr.get_session_by_udp(("127.0.0.1", 7001))
            self.assertEqual(found.session_id, session.session_id)

            # Endereço UDP não registrado não encontra sessão
            self.assertIsNone(mgr.get_session_by_udp(("127.0.0.1", 9999)))
        finally:
            sock.close()

    def test_session_timeout_detection(self):
        """Valida expiração de sessões inativas."""
        mgr = ConnectionManager(max_players=2)
        sock = socket.socket()
        try:
            session = mgr.register_client(sock, ("127.0.0.1", 6002), "Inactive")
            session.last_activity = time.time() - 10.0  # Inativo há 10 segundos

            expired = mgr.check_timeouts(timeout_seconds=5.0)
            self.assertEqual(len(expired), 1)
            self.assertEqual(expired[0].session_id, session.session_id)
            self.assertEqual(mgr.active_count, 0)
        finally:
            sock.close()

    def test_server_startup_handshake_and_shutdown(self):
        """
        Teste integrado de rede:
        - Inicia NetworkServer em porta dinâmica de teste;
        - Conecta um cliente TCP e executa handshake CONNECT_REQUEST;
        - Recebe CONNECT_ACCEPTED com ID atribuído;
        - Desliga o servidor e verifica encerramento limpo dos sockets.
        """
        test_tcp_port = 17777
        test_udp_port = 17778
        server = NetworkServer(host="127.0.0.1", tcp_port=test_tcp_port, udp_port=test_udp_port, max_players=2)
        self.assertTrue(server.start())
        self.assertTrue(server.is_running())

        client_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_tcp.settimeout(2.0)

        try:
            client_tcp.connect(("127.0.0.1", test_tcp_port))

            # Envia solicitação de conexão
            req = Protocol.serialize(MessageType.CONNECT_REQUEST, {"name": "TestClient", "version": 1})
            client_tcp.sendall(req)

            # Recebe resposta do servidor
            resp_bytes = client_tcp.recv(MAX_PACKET_SIZE)
            envelope = Protocol.deserialize(resp_bytes)

            self.assertEqual(envelope.msg_type, MessageType.CONNECT_ACCEPTED)
            self.assertEqual(envelope.payload["player_id"], 1)
            self.assertEqual(envelope.payload["max_players"], 2)

            # Verifica se o servidor registrou a sessão
            self.assertEqual(server.connection_manager.active_count, 1)

        except PermissionError:
            self.skipTest("Ambiente de sandbox restringiu conexão de socket loopback local.")
        finally:
            client_tcp.close()
            server.shutdown()
            self.assertFalse(server.is_running())


if __name__ == '__main__':
    unittest.main()
