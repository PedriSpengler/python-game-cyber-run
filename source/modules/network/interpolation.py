import time
import threading
from dataclasses import dataclass, field
from typing import Optional, Any
from .network_config import (
    INTERPOLATION_DELAY, SNAPSHOT_BUFFER_MAX_SIZE, SNAP_DISTANCE_THRESHOLD
)


@dataclass
class EntityState:
    """Estado pontual de uma entidade replicada via rede."""
    id: int
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    facing: int = 1
    grounded: bool = False
    state: str = "idle"


@dataclass
class Snapshot:
    """Snapshot consolidado do mundo em um instante temporal."""
    tick: int
    timestamp: float
    entities: dict[int, EntityState] = field(default_factory=dict)


class InterpolationBuffer:
    """
    Buffer circular / temporal de snapshots de estado para suavização de movimento no cliente.
    Aplica interpolação linear contínua entre os snapshots que cercam o instante:
    render_time - interpolation_delay.

    Propriedades:
    - 100% livre de Pygame e PyOpenGL (headless);
    - Imunidade a jitter e pacotes fora de ordem através de ordenação temporal estrita;
    - Detecção de teletransporte / respawn (snap direto se distância > snap_threshold);
    - Descarte determinístico de snapshots obsoletos para conter uso de memória.
    """
    def __init__(self,
                 delay: float = INTERPOLATION_DELAY,
                 max_size: int = SNAPSHOT_BUFFER_MAX_SIZE,
                 snap_threshold: float = SNAP_DISTANCE_THRESHOLD):
        self.delay: float = float(delay)
        self.max_size: int = int(max_size)
        self.snap_threshold: float = float(snap_threshold)

        self._snapshots: list[Snapshot] = []
        self._lock = threading.Lock()

    @property
    def count(self) -> int:
        with self._lock:
            return len(self._snapshots)

    def clear(self):
        with self._lock:
            self._snapshots.clear()

    def add_snapshot(self, payload: dict[str, Any], local_receive_time: Optional[float] = None) -> bool:
        """
        Registra um novo snapshot recebido via pacote GAME_STATE.
        Retorna True se adicionado com sucesso ou False se duplicado/inválido.
        """
        if not isinstance(payload, dict):
            return False

        tick = int(payload.get("tick", 0))
        # Usa o horário local de recebimento para neutralizar drift de relógio entre cliente e servidor
        timestamp = float(local_receive_time if local_receive_time is not None else time.time())

        raw_entities = payload.get("entities", [])
        if not isinstance(raw_entities, list):
            return False

        entities_dict: dict[int, EntityState] = {}
        for item in raw_entities:
            if not isinstance(item, dict) or "id" not in item:
                continue
            entity_id = int(item["id"])
            entities_dict[entity_id] = EntityState(
                id=entity_id,
                x=float(item.get("x", 0.0)),
                y=float(item.get("y", 0.0)),
                vx=float(item.get("vx", 0.0)),
                vy=float(item.get("vy", 0.0)),
                facing=int(item.get("facing", 1)),
                grounded=bool(item.get("grounded", False)),
                state=str(item.get("state", "idle"))
            )

        new_snapshot = Snapshot(tick=tick, timestamp=timestamp, entities=entities_dict)

        with self._lock:
            # Rejeita pacotes repetidos com o mesmo tick
            if any(s.tick == tick for s in self._snapshots):
                return False

            self._snapshots.append(new_snapshot)
            # Mantém snapshots ordenados estritamente por timestamp crescente
            self._snapshots.sort(key=lambda s: s.timestamp)

            # Poda o excesso de snapshots se exceder max_size
            if len(self._snapshots) > self.max_size:
                self._snapshots = self._snapshots[-self.max_size:]

        return True

    def get_latest_snapshot(self) -> Optional[Snapshot]:
        with self._lock:
            return self._snapshots[-1] if self._snapshots else None

    def sample(self, render_time: float) -> dict[int, EntityState]:
        """
        Calcula o estado suavemente interpolado de todas as entidades conhecidas
        para o tempo de renderização desejado (render_time - delay).
        """
        with self._lock:
            if not self._snapshots:
                return {}

            if len(self._snapshots) == 1:
                return dict(self._snapshots[0].entities)

            target_time = render_time - self.delay

            # Caso 1: O alvo é mais antigo que o snapshot mais velho conhecido (clamp)
            if target_time <= self._snapshots[0].timestamp:
                return dict(self._snapshots[0].entities)

            # Caso 2: O alvo é mais recente que o snapshot mais novo conhecido
            if target_time >= self._snapshots[-1].timestamp:
                latest = self._snapshots[-1]
                # Extrapolação linear segura por no máximo 50ms (0.05s)
                dt_extra = min(0.05, target_time - latest.timestamp)
                result = {}
                for eid, e in latest.entities.items():
                    result[eid] = EntityState(
                        id=eid,
                        x=e.x + (e.vx * dt_extra),
                        y=e.y + (e.vy * dt_extra),
                        vx=e.vx,
                        vy=e.vy,
                        facing=e.facing,
                        grounded=e.grounded,
                        state=e.state
                    )
                return result

            # Caso 3: Interpolação entre s0 (passado) e s1 (futuro)
            s0: Optional[Snapshot] = None
            s1: Optional[Snapshot] = None

            for i in range(len(self._snapshots) - 1):
                if self._snapshots[i].timestamp <= target_time <= self._snapshots[i + 1].timestamp:
                    s0 = self._snapshots[i]
                    s1 = self._snapshots[i + 1]
                    break

            if not s0 or not s1:
                return dict(self._snapshots[-1].entities)

            time_delta = s1.timestamp - s0.timestamp
            alpha = (target_time - s0.timestamp) / time_delta if time_delta > 0 else 0.0
            alpha = max(0.0, min(1.0, alpha))

            interpolated: dict[int, EntityState] = {}
            all_ids = set(s0.entities.keys()) | set(s1.entities.keys())

            for eid in all_ids:
                if eid in s0.entities and eid in s1.entities:
                    e0 = s0.entities[eid]
                    e1 = s1.entities[eid]

                    # Detecção de teletransporte / respawn: snap direto se o delta for brusco
                    dist_sq = (e1.x - e0.x) ** 2 + (e1.y - e0.y) ** 2
                    if dist_sq > (self.snap_threshold ** 2):
                        interpolated[eid] = e1
                    else:
                        interpolated[eid] = EntityState(
                            id=eid,
                            x=e0.x + alpha * (e1.x - e0.x),
                            y=e0.y + alpha * (e1.y - e0.y),
                            vx=e0.vx + alpha * (e1.vx - e0.vx),
                            vy=e0.vy + alpha * (e1.vy - e0.vy),
                            # Estados discretos adotam s1 se alpha >= 0.5, caso contrário s0
                            facing=e1.facing if alpha >= 0.5 else e0.facing,
                            grounded=e1.grounded if alpha >= 0.5 else e0.grounded,
                            state=e1.state if alpha >= 0.5 else e0.state
                        )
                elif eid in s1.entities:
                    interpolated[eid] = s1.entities[eid]
                else:
                    interpolated[eid] = s0.entities[eid]

            return interpolated
