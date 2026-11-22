from enum import Enum
from dataclasses import dataclass, field
from typing import Any


class MessageType(str, Enum):
    """Tipos de mensagens suportados pelo protocolo de rede do TAC3."""
    # Controle e Conexão (TCP)
    CONNECT_REQUEST = "CONNECT_REQUEST"
    CONNECT_ACCEPTED = "CONNECT_ACCEPTED"
    CONNECT_REJECTED = "CONNECT_REJECTED"
    LOBBY_STATE = "LOBBY_STATE"
    START_GAME = "START_GAME"
    DISCONNECT = "DISCONNECT"
    ACK = "ACK"

    # Gameplay Contínuo e Medição (UDP)
    PLAYER_INPUT = "PLAYER_INPUT"
    GAME_STATE = "GAME_STATE"
    PING = "PING"
    PONG = "PONG"


@dataclass
class NetworkEnvelope:
    """Envelope padrão de todos os pacotes trafegados na rede."""
    msg_type: str
    seq: int = 0
    session_id: str = ""
    timestamp: float = 0.0
    payload: dict[str, Any] = field(default_factory=dict)
