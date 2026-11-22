import time
import uuid
import socket
from dataclasses import dataclass, field
from typing import Optional
from .network_config import MAX_PLAYERS, CONNECTION_TIMEOUT


@dataclass
class ClientSession:
    """Representa a sessão autenticada de um jogador conectado ao servidor."""
    session_id: str
    player_id: int
    player_name: str
    tcp_conn: socket.socket
    tcp_addr: tuple[str, int]
    udp_addr: Optional[tuple[str, int]] = None
    is_ready: bool = False
    connected_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    ping_ms: float = 0.0

    def touch(self):
        """Atualiza o registro de atividade recente da sessão."""
        self.last_activity = time.time()


class ConnectionManager:
    """
    Gerenciador autoritativo de sessões, slots e controle de participantes.
    Garante que clientes não escolham seus IDs e impede envio de comandos forjados.
    """
    def __init__(self, max_players: int = MAX_PLAYERS):
        self.max_players = max_players
        self.sessions: dict[str, ClientSession] = {}  # session_id -> ClientSession
        self._available_ids: list[int] = list(range(1, max_players + 1))

    @property
    def active_count(self) -> int:
        return len(self.sessions)

    def is_full(self) -> bool:
        return len(self.sessions) >= self.max_players

    def register_client(self, tcp_conn: socket.socket, addr: tuple[str, int], name: str) -> Optional[ClientSession]:
        """
        Cadastra um novo cliente autenticado via conexão TCP.
        Retorna a sessão criada ou None se a sala estiver cheia.
        """
        if self.is_full() or not self._available_ids:
            return None

        player_id = self._available_ids.pop(0)
        session_id = str(uuid.uuid4())

        session = ClientSession(
            session_id=session_id,
            player_id=player_id,
            player_name=str(name)[:16],
            tcp_conn=tcp_conn,
            tcp_addr=addr,
            last_activity=time.time()
        )
        self.sessions[session_id] = session
        return session

    def bind_udp_address(self, session_id: str, udp_addr: tuple[str, int]) -> bool:
        """Associa o endereço UDP de envio à sessão TCP autenticada."""
        if session_id in self.sessions:
            self.sessions[session_id].udp_addr = udp_addr
            self.sessions[session_id].touch()
            return True
        return False

    def get_session_by_id(self, session_id: str) -> Optional[ClientSession]:
        return self.sessions.get(session_id)

    def get_session_by_udp(self, udp_addr: tuple[str, int]) -> Optional[ClientSession]:
        """Localiza a sessão autenticada associada a determinado endereço UDP."""
        for session in self.sessions.values():
            if session.udp_addr == udp_addr:
                return session
        return None

    def get_session_by_player_id(self, player_id: int) -> Optional[ClientSession]:
        for session in self.sessions.values():
            if session.player_id == player_id:
                return session
        return None

    def get_all_sessions(self) -> list[ClientSession]:
        return list(self.sessions.values())

    def remove_session(self, session_id: str) -> Optional[ClientSession]:
        """Remove a sessão e libera o player_id de volta para a lista de vagas."""
        if session_id in self.sessions:
            session = self.sessions.pop(session_id)
            if session.player_id not in self._available_ids:
                self._available_ids.append(session.player_id)
                self._available_ids.sort()
            try:
                session.tcp_conn.close()
            except Exception:
                pass
            return session
        return None

    def check_timeouts(self, timeout_seconds: float = CONNECTION_TIMEOUT) -> list[ClientSession]:
        """Varre e desconecta sessões inativas há mais de timeout_seconds."""
        now = time.time()
        expired = []
        for s in list(self.sessions.values()):
            if (now - s.last_activity) > timeout_seconds:
                expired.append(s)

        for s in expired:
            self.remove_session(s.session_id)
        return expired

    def clear(self):
        """Desconecta todas as sessões e limpa o registro."""
        for s in list(self.sessions.values()):
            self.remove_session(s.session_id)
        self._available_ids = list(range(1, self.max_players + 1))
