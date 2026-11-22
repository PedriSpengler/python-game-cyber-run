import socket
import threading
import time
import queue
from typing import Optional, Any
from .network_config import (
    DEFAULT_HOST, DEFAULT_TCP_PORT, DEFAULT_UDP_PORT,
    MAX_PACKET_SIZE, CONNECTION_TIMEOUT, PING_INTERVAL, PROTOCOL_VERSION
)
from .messages import MessageType, NetworkEnvelope
from .protocol import Protocol, ProtocolError
from .interpolation import InterpolationBuffer, EntityState


class NetworkClient:
    """
    Cliente de rede em LAN para o TAC3.
    Totalmente headless (0 dependências de Pygame ou PyOpenGL).
    Opera com arquitetura dual:
    - TCP: Handshake, controle de sala e eventos de sessão.
    - UDP: Transmissão de comandos em tempo real e telemetria.
    """
    def __init__(self):
        # Estado de Conexão
        self._connected: bool = False
        self._running: bool = False
        self._rejection_reason: Optional[str] = None

        # Atributos Atribuídos pelo Servidor
        self.session_id: str = ""
        self.player_id: Optional[int] = None
        self.assigned_level_name: str = "level1"
        self.max_players: int = 2

        # Endereços do Servidor
        self.host: str = DEFAULT_HOST
        self.tcp_port: int = DEFAULT_TCP_PORT
        self.udp_port: int = DEFAULT_UDP_PORT
        self.server_udp_addr: tuple[str, int] = (DEFAULT_HOST, DEFAULT_UDP_PORT)

        # Sockets
        self._tcp_socket: Optional[socket.socket] = None
        self._udp_socket: Optional[socket.socket] = None

        # Threads de Background
        self._tcp_thread: Optional[threading.Thread] = None
        self._udp_thread: Optional[threading.Thread] = None
        self._heartbeat_thread: Optional[threading.Thread] = None

        # Controle de Sequência e Telemetria
        self._seq_counter: int = 0
        self.ping_ms: float = 0.0
        self.last_seen_server: float = 0.0

        # Filas Thread-Safe de Mensagens Recebidas para a Aplicação
        self.events_queue: queue.Queue[NetworkEnvelope] = queue.Queue()

        # Buffer de Interpolação para Suavização de Movimento (Bloco 5)
        self.interpolation_buffer: InterpolationBuffer = InterpolationBuffer()

        # Estado da Sala e Partida
        self.is_in_lobby: bool = False
        self.is_game_started: bool = False
        self.lobby_players: list[dict] = []

    def is_connected(self) -> bool:
        return self._connected and self._running

    @property
    def rejection_reason(self) -> Optional[str]:
        return self._rejection_reason

    def _next_seq(self) -> int:
        self._seq_counter += 1
        return self._seq_counter

    def connect(self,
                host: str = DEFAULT_HOST,
                tcp_port: int = DEFAULT_TCP_PORT,
                udp_port: int = DEFAULT_UDP_PORT,
                player_name: str = "Jogador",
                timeout: float = CONNECTION_TIMEOUT) -> bool:
        """
        Inicia a conexão TCP com o servidor e executa o handshake autoritativo.
        Retorna True se aceito com ID atribuído, ou False em caso de recusa/erro.
        """
        if self.is_connected():
            return True

        self.host = host
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        self.server_udp_addr = (host, udp_port)
        self._rejection_reason = None

        try:
            # 1. Conexão TCP
            self._tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._tcp_socket.settimeout(timeout)
            self._tcp_socket.connect((self.host, self.tcp_port))

            # 2. Envio de CONNECT_REQUEST
            handshake_req = Protocol.serialize(
                MessageType.CONNECT_REQUEST,
                {"name": player_name[:16], "version": PROTOCOL_VERSION},
                seq=self._next_seq()
            )
            self._tcp_socket.sendall(handshake_req)

            # 3. Recepção da resposta inicial do servidor com extração contínua (stream framing)
            resp_bytes = self._tcp_socket.recv(MAX_PACKET_SIZE)
            if not resp_bytes:
                self.shutdown()
                return False

            envelopes, remaining_stream = Protocol.extract_envelopes(resp_bytes.decode('utf-8'))
            if not envelopes:
                self.shutdown()
                return False

            envelope = envelopes[0]

            if envelope.msg_type == MessageType.CONNECT_REJECTED:
                self._rejection_reason = envelope.payload.get("reason", "RECUSADO")
                self.shutdown()
                return False

            if envelope.msg_type != MessageType.CONNECT_ACCEPTED:
                self.shutdown()
                return False

            # Armazena dados autoritativos atribuídos pelo servidor
            self.session_id = envelope.session_id
            self.player_id = int(envelope.payload["player_id"])
            self.assigned_level_name = envelope.payload.get("level_name", "level1")
            self.max_players = envelope.payload.get("max_players", 2)
            self._connected = True
            self._running = True
            self.is_in_lobby = True
            self.last_seen_server = time.time()

            # Enfileira os envelopes adicionais concatenados no stream TCP (ex: LOBBY_STATE)
            for extra_env in envelopes[1:]:
                self.events_queue.put(extra_env)
                if extra_env.msg_type == MessageType.LOBBY_STATE:
                    self.lobby_players = extra_env.payload.get("players", [])

            # 4. Inicialização do Socket UDP (Ephemeral Port)
            self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._udp_socket.bind(("", 0))
            self._udp_socket.settimeout(0.5)

            # 5. Vinculação imediata do endereço UDP junto ao servidor
            self.send_ping()

            # 6. Disparo de Threads de Escuta em Background
            self._tcp_socket.settimeout(0.5)
            self._tcp_thread = threading.Thread(target=self._tcp_receive_loop, daemon=True, name="Client-TCP-Recv")
            self._tcp_thread.start()

            self._udp_thread = threading.Thread(target=self._udp_receive_loop, daemon=True, name="Client-UDP-Recv")
            self._udp_thread.start()

            self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True, name="Client-Heartbeat")
            self._heartbeat_thread.start()

            return True

        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            self._rejection_reason = f"FALHA_CONEXAO: {e}"
            self.shutdown()
            return False
        except ProtocolError as e:
            self._rejection_reason = f"ERRO_PROTOCOLO: {e}"
            self.shutdown()
            return False

    def send_message(self, msg_type: MessageType | str, payload: dict[str, Any] = None, reliable: bool = True) -> bool:
        """
        Envia uma mensagem para o servidor.
        Se reliable=True (padrão), utiliza TCP garantido.
        Se reliable=False, utiliza UDP não confiável de baixa latência.
        """
        if reliable:
            return self.send_tcp_message(msg_type, payload)
        else:
            return self.send_udp_message(msg_type, payload)

    def send_tcp_message(self, msg_type: MessageType | str, payload: dict[str, Any] = None) -> bool:
        """Envia uma mensagem confiável de controle via TCP."""
        if not self.is_connected() or not self._tcp_socket:
            return False
        try:
            raw = Protocol.serialize(
                msg_type,
                payload or {},
                seq=self._next_seq(),
                session_id=self.session_id
            )
            self._tcp_socket.sendall(raw)
            return True
        except Exception:
            self.disconnect(reason="TCP_SEND_ERROR")
            return False

    def send_udp_message(self, msg_type: MessageType | str, payload: dict[str, Any] = None) -> bool:
        """Envia um datagrama de gameplay via UDP com session_id."""
        if not self._running or not self._udp_socket:
            return False
        try:
            raw = Protocol.serialize(
                msg_type,
                payload or {},
                seq=self._next_seq(),
                session_id=self.session_id
            )
            self._udp_socket.sendto(raw, self.server_udp_addr)
            return True
        except Exception:
            return False

    def send_input(self, move_x: int, jump: bool, jump_held: bool = False, tick: int = 0) -> bool:
        """Transmite comandos de entrada do jogador via UDP."""
        payload = {
            "player_id": self.player_id,
            "tick": int(tick),
            "move_x": int(move_x),
            "jump": bool(jump),
            "jump_held": bool(jump_held)
        }
        return self.send_udp_message(MessageType.PLAYER_INPUT, payload)

    def send_ping(self) -> bool:
        """Envia PING via UDP para aferição de latência e heartbeat."""
        now = time.time()
        payload = {"client_time": now}
        return self.send_udp_message(MessageType.PING, payload)

    def get_events(self) -> list[NetworkEnvelope]:
        """Consome de forma não-bloqueante todos os eventos recebidos da rede."""
        events = []
        while not self.events_queue.empty():
            try:
                events.append(self.events_queue.get_nowait())
            except queue.Empty:
                break
        return events

    def get_interpolated_entities(self, render_time: Optional[float] = None) -> dict[int, EntityState]:
        """Retorna as entidades suavizadas pelo buffer de interpolação no tempo de renderização."""
        now = render_time if render_time is not None else time.time()
        return self.interpolation_buffer.sample(now)

    def _tcp_receive_loop(self):
        """Thread que escuta mensagens TCP do servidor com suporte a enquadramento JSON."""
        stream_buffer = ""
        while self._running and self._tcp_socket:
            try:
                data = self._tcp_socket.recv(MAX_PACKET_SIZE)
                if not data:
                    self.disconnect(reason="SERVIDOR_FECHOU")
                    break

                self.last_seen_server = time.time()
                stream_buffer += data.decode('utf-8')
                envelopes, stream_buffer = Protocol.extract_envelopes(stream_buffer)

                for env in envelopes:
                    self.events_queue.put(env)

                    if env.msg_type == MessageType.LOBBY_STATE:
                        self.lobby_players = env.payload.get("players", [])
                    elif env.msg_type == MessageType.START_GAME:
                        self.is_game_started = True
                        self.is_in_lobby = False
                    elif env.msg_type == MessageType.DISCONNECT:
                        self.disconnect(reason=env.payload.get("reason", "DESCONECTADO"))
                        return

            except socket.timeout:
                if (time.time() - self.last_seen_server) > (CONNECTION_TIMEOUT * 2):
                    self.disconnect(reason="TIMEOUT_SERVIDOR")
                    break
                continue
            except (UnicodeDecodeError, ProtocolError):
                continue
            except Exception:
                self.disconnect(reason="ERRO_LEITURA_TCP")
                break

    def _udp_receive_loop(self):
        """Thread que escuta datagramas UDP do servidor (PONG e GAME_STATE)."""
        while self._running and self._udp_socket:
            try:
                data, addr = self._udp_socket.recvfrom(MAX_PACKET_SIZE)
                if not data:
                    continue

                envelope = Protocol.deserialize(data)
                self.last_seen_server = time.time()

                if envelope.msg_type == MessageType.PONG:
                    client_time = envelope.payload.get("client_time", 0.0)
                    if client_time > 0:
                        self.ping_ms = max(0.0, (time.time() - client_time) * 1000.0)
                elif envelope.msg_type == MessageType.GAME_STATE:
                    self.interpolation_buffer.add_snapshot(envelope.payload)

                self.events_queue.put(envelope)

            except socket.timeout:
                continue
            except (ProtocolError, Exception):
                continue

    def _heartbeat_loop(self):
        """Envia pings periódicos para aferição de latência e manutenção de rotas NAT."""
        while self._running:
            time.sleep(PING_INTERVAL)
            if self.is_connected():
                self.send_ping()

    def disconnect(self, reason: str = "normal"):
        """Desconecta do servidor e notifica via TCP."""
        if self._connected:
            try:
                self.send_tcp_message(MessageType.DISCONNECT, {"reason": reason})
            except Exception:
                pass
        self.shutdown()

    def shutdown(self):
        """Finalização determinística de sockets e threads."""
        self._connected = False
        self._running = False
        self.is_in_lobby = False
        self.is_game_started = False
        self.interpolation_buffer.clear()

        if self._tcp_socket:
            try:
                self._tcp_socket.close()
            except Exception:
                pass
            self._tcp_socket = None

        if self._udp_socket:
            try:
                self._udp_socket.close()
            except Exception:
                pass
            self._udp_socket = None

        if self._tcp_thread and self._tcp_thread.is_alive():
            self._tcp_thread.join(timeout=1.0)
        if self._udp_thread and self._udp_thread.is_alive():
            self._udp_thread.join(timeout=1.0)
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=1.0)
