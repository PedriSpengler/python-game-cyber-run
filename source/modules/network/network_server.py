import socket
import select
import threading
import time
import queue
from typing import Optional
from .network_config import (
    DEFAULT_HOST, DEFAULT_TCP_PORT, DEFAULT_UDP_PORT,
    MAX_PLAYERS, CONNECTION_TIMEOUT, MAX_PACKET_SIZE,
    SIMULATION_TICK_RATE, NETWORK_SYNC_RATE
)
from .messages import MessageType, NetworkEnvelope
from .protocol import Protocol, ProtocolError
from .connection_manager import ConnectionManager, ClientSession
from ..entities.player_entity import PlayerEntity
from ..physics.physics_system import PhysicsSystem
from ..input.input_state import InputState


class NetworkServer:
    """
    Servidor autoritativo de rede local (LAN) para o TAC3.
    Totalmente headless (0 dependências de Pygame ou PyOpenGL).
    Opera com arquitetura dual:
    - TCP: Controle de sessão, handshake de entrada, sala de espera e status.
    - UDP: Recepção de comandos em tempo real e telemetria de gameplay.
    """
    def __init__(self,
                 host: str = DEFAULT_HOST,
                 tcp_port: int = DEFAULT_TCP_PORT,
                 udp_port: int = DEFAULT_UDP_PORT,
                 max_players: int = MAX_PLAYERS):
        self.host = host
        self.tcp_port = tcp_port
        self.udp_port = udp_port

        self.connection_manager = ConnectionManager(max_players=max_players)
        self._running: bool = False

        # Sockets
        self._tcp_socket: Optional[socket.socket] = None
        self._udp_socket: Optional[socket.socket] = None

        # Threads de atendimento
        self._tcp_thread: Optional[threading.Thread] = None
        self._udp_thread: Optional[threading.Thread] = None

        # Fila thread-safe de eventos e comandos recebidos para a simulação
        self.incoming_events: queue.Queue[tuple[str, NetworkEnvelope]] = queue.Queue()

        # Simulação física autoritativa (Bloco 4)
        self.players: dict[int, PlayerEntity] = {}
        self.player_inputs: dict[int, InputState] = {}
        self.spawn_positions: dict[int, tuple[float, float]] = {
            1: (200.0, 300.0),
            2: (350.0, 300.0)
        }
        self.current_tick: int = 0
        self.physics_system: PhysicsSystem = PhysicsSystem()
        self.level = None
        self._players_lock = threading.Lock()
        self._simulation_running: bool = False
        self._simulation_thread: Optional[threading.Thread] = None

    def is_running(self) -> bool:
        return self._running

    def start(self) -> bool:
        """Inicia os sockets TCP e UDP e dispara as threads de atendimento."""
        if self._running:
            return True

        try:
            # 1. Configuração do Socket TCP (Handshake e Controle)
            self._tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._tcp_socket.bind((self.host, self.tcp_port))
            self._tcp_socket.listen(5)
            self._tcp_socket.settimeout(0.5)

            # 2. Configuração do Socket UDP (Gameplay e Telemetria)
            self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._udp_socket.bind((self.host, self.udp_port))
            self._udp_socket.settimeout(0.5)

            self._running = True

            # 3. Disparo das Threads em Background
            self._tcp_thread = threading.Thread(target=self._tcp_accept_loop, daemon=True, name="Server-TCP-Accept")
            self._tcp_thread.start()

            self._udp_thread = threading.Thread(target=self._udp_receive_loop, daemon=True, name="Server-UDP-Recv")
            self._udp_thread.start()

            # 4. Disparo do Loop de Simulação Autoritativa (60Hz / 25Hz broadcast)
            self._simulation_running = True
            self._simulation_thread = threading.Thread(target=self._simulation_loop, daemon=True, name="Server-Simulation")
            self._simulation_thread.start()

            return True
        except Exception as e:
            self.shutdown()
            raise RuntimeError(f"Falha ao iniciar NetworkServer em {self.host}:{self.tcp_port}/{self.udp_port}: {e}")

    def shutdown(self):
        """Encerra determinística e completamente todos os sockets, conexões e threads."""
        if not self._running and self._tcp_socket is None and self._udp_socket is None:
            return

        self._running = False

        # Encerra a thread de simulação
        self._simulation_running = False
        if self._simulation_thread and self._simulation_thread.is_alive():
            self._simulation_thread.join(timeout=1.0)

        with self._players_lock:
            self.players.clear()
            self.player_inputs.clear()

        # Notifica e fecha sessões ativas
        disconnect_pkg = Protocol.serialize(MessageType.DISCONNECT, {"reason": "SERVER_SHUTDOWN"})
        for session in self.connection_manager.get_all_sessions():
            try:
                session.tcp_conn.sendall(disconnect_pkg)
            except Exception:
                pass
        self.connection_manager.clear()

        # Fecha socket TCP
        if self._tcp_socket:
            try:
                self._tcp_socket.close()
            except Exception:
                pass
            self._tcp_socket = None

        # Fecha socket UDP
        if self._udp_socket:
            try:
                self._udp_socket.close()
            except Exception:
                pass
            self._udp_socket = None

        # Aguarda threads com timeout
        if self._tcp_thread and self._tcp_thread.is_alive():
            self._tcp_thread.join(timeout=1.0)
        if self._udp_thread and self._udp_thread.is_alive():
            self._udp_thread.join(timeout=1.0)

    def _tcp_accept_loop(self):
        """Thread responsável por aceitar novas conexões de clientes via TCP."""
        while self._running:
            try:
                conn, addr = self._tcp_socket.accept()
                client_thread = threading.Thread(
                    target=self._tcp_client_handler,
                    args=(conn, addr),
                    daemon=True,
                    name=f"Client-TCP-{addr}"
                )
                client_thread.start()
            except socket.timeout:
                continue
            except Exception:
                break

    def _tcp_client_handler(self, conn: socket.socket, addr: tuple[str, int]):
        """Trata o ciclo de vida da conexão TCP de um cliente específico com framing contínuo."""
        session: Optional[ClientSession] = None
        conn.settimeout(0.5)
        stream_buffer = ""

        try:
            # 1. Aguarda CONNECT_REQUEST inicial
            while self._running and not session:
                try:
                    chunk = conn.recv(MAX_PACKET_SIZE)
                    if not chunk:
                        conn.close()
                        return
                    stream_buffer += chunk.decode('utf-8')
                    envelopes, stream_buffer = Protocol.extract_envelopes(stream_buffer)

                    for envelope in envelopes:
                        if envelope.msg_type == MessageType.CONNECT_REQUEST:
                            name = envelope.payload.get("name", "Jogador")
                            session = self.connection_manager.register_client(conn, addr, name)

                            if session:
                                self.add_player(session.player_id)
                                resp = Protocol.serialize(
                                    MessageType.CONNECT_ACCEPTED,
                                    {
                                        "player_id": session.player_id,
                                        "level_name": "level1",
                                        "max_players": self.connection_manager.max_players
                                    },
                                    session_id=session.session_id
                                )
                                conn.sendall(resp)
                                self._broadcast_lobby_state()
                            else:
                                reject = Protocol.serialize(
                                    MessageType.CONNECT_REJECTED,
                                    {"reason": "SALA_LOTADA"}
                                )
                                conn.sendall(reject)
                                conn.close()
                                return
                            break
                except socket.timeout:
                    continue
                except (UnicodeDecodeError, ProtocolError):
                    continue

            # 2. Loop de escuta de comandos de controle TCP durante a sessão
            while self._running and session:
                try:
                    data = conn.recv(MAX_PACKET_SIZE)
                    if not data:
                        break
                    stream_buffer += data.decode('utf-8')
                    envelopes, stream_buffer = Protocol.extract_envelopes(stream_buffer)

                    for envelope in envelopes:
                        session.touch()
                        self.incoming_events.put((session.session_id, envelope))
                        if envelope.msg_type == MessageType.START_GAME and session.player_id == 1:
                            self.broadcast_tcp(MessageType.START_GAME, envelope.payload)
                        elif envelope.msg_type == MessageType.DISCONNECT:
                            return
                except socket.timeout:
                    if (time.time() - session.last_activity) > CONNECTION_TIMEOUT:
                        break
                    continue
                except (UnicodeDecodeError, ProtocolError):
                    continue

        except Exception:
            pass
        finally:
            if session:
                self.remove_player(session.player_id)
                self.connection_manager.remove_session(session.session_id)
                self._broadcast_lobby_state()
            try:
                conn.close()
            except Exception:
                pass

    def _udp_receive_loop(self):
        """Thread responsável por receber pacotes contínuos de gameplay via UDP."""
        while self._running:
            try:
                data, addr = self._udp_socket.recvfrom(MAX_PACKET_SIZE)
                if not data:
                    continue

                envelope = Protocol.deserialize(data)
                session_id = envelope.session_id

                # Valida se a sessão é autenticada
                session = self.connection_manager.get_session_by_id(session_id)
                if session:
                    # Associa o endereço UDP de envio à sessão autenticada
                    if session.udp_addr != addr:
                        self.connection_manager.bind_udp_address(session_id, addr)

                    session.touch()

                    if envelope.msg_type == MessageType.PING:
                        # Responde PONG com mesmo timestamp para medição de latência
                        pong = Protocol.serialize(
                            MessageType.PONG,
                            {"server_time": time.time(), "client_time": envelope.timestamp},
                            session_id=session_id
                        )
                        self._udp_socket.sendto(pong, addr)
                    else:
                        # Coloca comandos de gameplay na fila para processamento
                        self.incoming_events.put((session_id, envelope))

            except socket.timeout:
                continue
            except (ProtocolError, Exception):
                continue

    def _broadcast_lobby_state(self):
        """Transmite o estado atualizado dos jogadores conectados via TCP."""
        sessions = self.connection_manager.get_all_sessions()
        players_info = [
            {"id": s.player_id, "name": s.player_name, "is_ready": s.is_ready}
            for s in sessions
        ]
        msg = Protocol.serialize(
            MessageType.LOBBY_STATE,
            {"players": players_info, "count": len(players_info)}
        )
        for s in sessions:
            try:
                s.tcp_conn.sendall(msg)
            except Exception:
                pass

    def broadcast_tcp(self, msg_type: MessageType | str, payload: dict = None):
        """Transmite uma mensagem de controle TCP confiável para todas as sessões ativas."""
        for s in self.connection_manager.get_all_sessions():
            try:
                pkg = Protocol.serialize(msg_type, payload or {}, session_id=s.session_id)
                s.tcp_conn.sendall(pkg)
            except Exception:
                pass

    def broadcast_udp(self, msg_type: MessageType | str, payload: dict):
        """Transmite um pacote UDP para todos os clientes associados."""
        if not self._udp_socket:
            return
        pkg = Protocol.serialize(msg_type, payload)
        for s in self.connection_manager.get_all_sessions():
            if s.udp_addr:
                try:
                    self._udp_socket.sendto(pkg, s.udp_addr)
                except Exception:
                    pass

    # =========================================================================
    # Simulação Autoritativa e Sincronização de Estado (Bloco 4)
    # =========================================================================

    def add_player(self, player_id: int):
        """Instancia e registra uma PlayerEntity autoritativa para a sessão."""
        with self._players_lock:
            spawn_x, spawn_y = self.spawn_positions.get(
                player_id,
                (200.0 + (player_id - 1) * 150.0, 300.0)
            )
            player = PlayerEntity(x=spawn_x, y=spawn_y)
            self.players[player_id] = player
            self.player_inputs[player_id] = InputState()

    def remove_player(self, player_id: int):
        """Remove a entidade e estado de entrada da simulação do servidor."""
        with self._players_lock:
            self.players.pop(player_id, None)
            self.player_inputs.pop(player_id, None)

    def _process_incoming_inputs(self):
        """Drena os comandos de entrada recebidos e mapeia para os jogadores respectivos."""
        while not self.incoming_events.empty():
            try:
                session_id, env = self.incoming_events.get_nowait()
            except queue.Empty:
                break

            if env.msg_type == MessageType.PLAYER_INPUT:
                session = self.connection_manager.get_session_by_id(session_id)
                pid = session.player_id if session else env.payload.get("player_id")
                if pid and pid in self.players:
                    move_x = int(env.payload.get("move_x", 0))
                    jump = bool(env.payload.get("jump", False))
                    jump_held = bool(env.payload.get("jump_held", False))
                    tick = int(env.payload.get("tick", 0))
                    self.player_inputs[pid] = InputState(
                        move_x=move_x,
                        jump=jump,
                        jump_held=jump_held,
                        tick=tick
                    )

    def step_simulation(self, dt: float = 1.0 / SIMULATION_TICK_RATE):
        """
        Executa um passo determinístico na simulação física autoritativa.
        Processa comandos, atualiza jogadores e incrementa o tick da simulação.
        """
        self._process_incoming_inputs()
        self.current_tick += 1

        with self._players_lock:
            for pid, player in list(self.players.items()):
                input_state = self.player_inputs.get(pid, InputState())
                self.physics_system.update_entity(player, dt, level=self.level, input_state=input_state)

                # Consome o edge-trigger do pulo após aplicar à física
                if input_state.jump:
                    self.player_inputs[pid] = InputState(
                        move_x=input_state.move_x,
                        jump=False,
                        jump_held=input_state.jump_held,
                        tick=input_state.tick
                    )

    def broadcast_game_state(self, timestamp: Optional[float] = None):
        """Transmite snapshot do estado de jogo a todos os clientes via broadcast UDP."""
        entities_data = []
        with self._players_lock:
            for pid, player in self.players.items():
                entities_data.append({
                    "id": pid,
                    "x": round(player.x, 2),
                    "y": round(player.y, 2),
                    "vx": round(player.vx, 2),
                    "vy": round(player.vy, 2),
                    "facing": player.facing,
                    "grounded": player.is_grounded,
                    "state": player.state.value if hasattr(player.state, "value") else str(player.state)
                })

        payload = {
            "tick": self.current_tick,
            "timestamp": float(timestamp if timestamp is not None else time.time()),
            "entities": entities_data
        }
        self.broadcast_udp(MessageType.GAME_STATE, payload)

    def _simulation_loop(self):
        """Thread que executa a simulação contínua autoritativa a 60Hz e broadcast a 25Hz."""
        tick_interval = 1.0 / SIMULATION_TICK_RATE
        sync_interval = 1.0 / NETWORK_SYNC_RATE
        last_sync_time = 0.0

        while self._running and self._simulation_running:
            start_time = time.time()

            self.step_simulation(tick_interval)

            now = time.time()
            if (now - last_sync_time) >= sync_interval:
                self.broadcast_game_state(now)
                last_sync_time = now

            elapsed = time.time() - start_time
            sleep_time = tick_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
