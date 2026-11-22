import json
import time
from typing import Any
from .network_config import (
    MAX_PACKET_SIZE, MAX_PAYLOAD_SIZE, MAX_NAME_LENGTH, PROTOCOL_VERSION
)
from .messages import MessageType, NetworkEnvelope


class ProtocolError(Exception):
    """Exceção levantada quando um pacote de rede viola o protocolo."""
    pass


class Protocol:
    """
    Serializador e validador estrito do protocolo de rede do TAC3.
    Rejeita pacotes malformados, campos desconhecidos ou valores fora dos limites.
    Utiliza estritamente JSON UTF-8 (proibido o uso de pickle).
    """

    @staticmethod
    def serialize(msg_type: MessageType | str,
                  payload: dict[str, Any] = None,
                  seq: int = 0,
                  session_id: str = "",
                  timestamp: float = None) -> bytes:
        """Serializa uma mensagem para bytes UTF-8 com validação de limites."""
        type_str = msg_type.value if isinstance(msg_type, MessageType) else str(msg_type)
        if type_str not in MessageType._value2member_map_:
            raise ProtocolError(f"Tipo de mensagem desconhecido: '{type_str}'")

        payload_dict = payload or {}
        Protocol._validate_payload(type_str, payload_dict)

        envelope = {
            "type": type_str,
            "seq": int(seq),
            "session_id": str(session_id),
            "timestamp": float(timestamp if timestamp is not None else time.time()),
            "payload": payload_dict
        }

        raw_json = json.dumps(envelope, separators=(',', ':'))
        encoded = raw_json.encode('utf-8')

        if len(encoded) > MAX_PACKET_SIZE:
            raise ProtocolError(
                f"Mensagem '{type_str}' excede o tamanho máximo permitido: {len(encoded)} > {MAX_PACKET_SIZE} bytes"
            )

        return encoded

    @staticmethod
    def deserialize(raw_bytes: bytes) -> NetworkEnvelope:
        """Desserializa e valida rigorosamente um pacote de bytes recebido."""
        if not raw_bytes:
            raise ProtocolError("Pacote vazio recebido.")

        if len(raw_bytes) > MAX_PACKET_SIZE:
            raise ProtocolError(f"Pacote excede {MAX_PACKET_SIZE} bytes: {len(raw_bytes)} bytes")

        try:
            text = raw_bytes.decode('utf-8')
            decoder = json.JSONDecoder()
            data, _ = decoder.raw_decode(text.lstrip())
        except UnicodeDecodeError as e:
            raise ProtocolError(f"Erro de decodificação UTF-8: {e}")
        except json.JSONDecodeError as e:
            raise ProtocolError(f"JSON malformado recebido: {e}")

        return Protocol._parse_envelope_dict(data)

    @staticmethod
    def _parse_envelope_dict(data: Any) -> NetworkEnvelope:
        """Valida e converte um dicionário decodificado em NetworkEnvelope."""
        if not isinstance(data, dict):
            raise ProtocolError("Envelope raiz deve ser um objeto JSON.")

        # Validação de campos obrigatórios do envelope
        for required_key in ("type", "seq", "session_id", "timestamp", "payload"):
            if required_key not in data:
                raise ProtocolError(f"Campo obrigatório ausente no envelope: '{required_key}'")

        msg_type_str = data["type"]
        if msg_type_str not in MessageType._value2member_map_:
            raise ProtocolError(f"Tipo de mensagem inválido ou desconhecido: '{msg_type_str}'")

        payload = data["payload"]
        if not isinstance(payload, dict):
            raise ProtocolError("O payload deve ser um objeto dicionário.")

        Protocol._validate_payload(msg_type_str, payload)

        return NetworkEnvelope(
            msg_type=msg_type_str,
            seq=int(data["seq"]),
            session_id=str(data["session_id"]),
            timestamp=float(data["timestamp"]),
            payload=payload
        )

    @staticmethod
    def extract_envelopes(stream_buffer: str) -> tuple[list[NetworkEnvelope], str]:
        """
        Extrai envelopes JSON completos de um buffer de stream TCP contínuo.
        Resolve problemas de fragmentação e concatenação via json.JSONDecoder.raw_decode.
        Retorna (lista_de_envelopes_válidos, buffer_remanescente_incompleto).
        """
        decoder = json.JSONDecoder()
        envelopes = []
        text = stream_buffer.lstrip()

        while text:
            try:
                data, end_idx = decoder.raw_decode(text)
            except json.JSONDecodeError:
                # O buffer atual contém apenas um fragmento incompleto; aguarda o próximo recv()
                break

            envelope = Protocol._parse_envelope_dict(data)
            envelopes.append(envelope)
            text = text[end_idx:].lstrip()

        return envelopes, text

    @staticmethod
    def _validate_payload(msg_type: str, payload: dict[str, Any]):
        """Validação estrita de tipos e limites por tipo de mensagem."""
        if msg_type == MessageType.CONNECT_REQUEST:
            if "name" not in payload:
                raise ProtocolError("CONNECT_REQUEST requer o campo 'name'.")
            name = str(payload["name"]).strip()
            if not name or len(name) > MAX_NAME_LENGTH:
                raise ProtocolError(f"Nome de jogador inválido ou superior a {MAX_NAME_LENGTH} caracteres.")
            version = payload.get("version", PROTOCOL_VERSION)
            if version != PROTOCOL_VERSION:
                raise ProtocolError(f"Versão de protocolo incompatível: {version} != {PROTOCOL_VERSION}")

        elif msg_type == MessageType.CONNECT_ACCEPTED:
            for field in ("player_id", "level_name", "max_players"):
                if field not in payload:
                    raise ProtocolError(f"CONNECT_ACCEPTED requer '{field}'.")
            if not (1 <= int(payload["player_id"]) <= 32):
                raise ProtocolError("player_id fora do intervalo permitido [1..32].")

        elif msg_type == MessageType.PLAYER_INPUT:
            for field in ("tick", "move_x", "jump"):
                if field not in payload:
                    raise ProtocolError(f"PLAYER_INPUT requer '{field}'.")
            move_x = int(payload["move_x"])
            if move_x not in (-1, 0, 1):
                raise ProtocolError(f"move_x inválido: {move_x}. Esperado -1, 0 ou 1.")

        elif msg_type == MessageType.GAME_STATE:
            if "tick" not in payload or "entities" not in payload:
                raise ProtocolError("GAME_STATE requer 'tick' e lista 'entities'.")
            if not isinstance(payload["entities"], list):
                raise ProtocolError("Campo 'entities' deve ser uma lista.")

        elif msg_type == MessageType.DISCONNECT:
            if "reason" not in payload:
                payload["reason"] = "normal"
