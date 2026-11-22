from enum import Enum
from ..input.input_state import InputState


class PlayerState(Enum):
    """Estados lógicos do personagem."""
    IDLE = "idle"
    RUNNING = "running"
    JUMPING = "jumping"
    FALLING = "falling"


class PlayerEntity:
    """
    Entidade lógica pura do jogador.
    Totalmente desacoplada de Pygame, PyOpenGL e hardware de áudio.
    Responsável estritamente pelo estado, física e processamento de InputState.
    """
    def __init__(self,
                 x: float = 384.0,
                 y: float = 648.0,
                 width: float = 60.0,
                 height: float = 100.0,
                 speed: float = 300.0,
                 gravity: float = 1200.0,
                 jump_speed: float = -600.0,
                 floor_y: float = 992.0):
        # Dimensões e Posição (World Space)
        self.x: float = float(x)
        self.y: float = float(y)
        self.width: float = float(width)
        self.height: float = float(height)

        # Vetores de Movimentação e Física
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.speed: float = float(speed)
        self.gravity: float = float(gravity)
        self.jump_speed: float = float(jump_speed)

        # Limites e Referências de Pulo
        self.floor_y: float = float(floor_y)
        self.jump_max: float = self.floor_y
        self.jump_min: float = self.jump_max + (0.08 * self.jump_speed)

        # Estados Lógicos
        self.is_grounded: bool = False
        self.facing: int = 1  # +1: Direita, -1: Esquerda
        self.state: PlayerState = PlayerState.IDLE

        # Sinais para sistemas externos (ex: reproduzir áudio na View)
        self.just_jumped: bool = False

    @property
    def bottom(self) -> float:
        return self.y + self.height

    @bottom.setter
    def bottom(self, value: float):
        self.y = value - self.height

    @property
    def right(self) -> float:
        return self.x + self.width

    @right.setter
    def right(self, value: float):
        self.x = value - self.width

    def get_bounding_box(self) -> tuple[float, float, float, float]:
        """Retorna (x, y, largura, altura) para cálculos de colisão AABB."""
        return self.x, self.y, self.width, self.height

    def apply_input(self, input_state: InputState):
        """
        Aplica os comandos contidos no InputState à velocidade do jogador.
        Suporta movimentação contínua e pulo acionado por edge trigger.
        """
        # 1. Movimentação Horizontal
        self.vx = input_state.move_x * self.speed
        if input_state.move_x != 0:
            self.facing = 1 if input_state.move_x > 0 else -1

        # 2. Pulo (apenas se estiver no chão)
        self.just_jumped = False
        if input_state.jump and self.is_grounded:
            self.vy = self.jump_speed
            self.is_grounded = False
            self.just_jumped = True

    def apply_gravity(self, dt: float):
        """Aplica a aceleração da gravidade à velocidade vertical."""
        self.vy += self.gravity * dt

    def update(self, dt: float, input_state: InputState = None, level=None):
        """
        Avança a simulação física do jogador por um passo de tempo dt.
        Suporta colisão com blocos reais do mapa se level for fornecido.
        """
        if dt <= 0:
            return

        from ..physics.physics_system import PhysicsSystem
        if not hasattr(self, '_physics_system'):
            self._physics_system = PhysicsSystem()

        self._physics_system.update_entity(self, dt, level=level, input_state=input_state)
