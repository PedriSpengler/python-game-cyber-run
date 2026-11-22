import pygame
from ..constants import WIDTH, HEIGHT, SIZE_PLAYER, GRAVITY, MAP_H, TILE_SIZE
from .player_entity import PlayerEntity
from ..rendering.player_view import PlayerView
from ..input.input_manager import InputManager


class Player:
    """
    Camada de Compatibilidade Temporária (Padrão Facade).
    Integra PlayerEntity (lógica pura), PlayerView (renderização OpenGL)
    e InputManager (captura de teclado), preservando a interface legada
    utilizada por GameScene, Camera2D e pelo Level Editor.
    """
    def __init__(self, x: float = WIDTH * 0.2, y: float = HEIGHT * 0.6):
        # Entidade de Lógica e Física Pura
        floor_y = (int(MAP_H * 0.9) * TILE_SIZE) + TILE_SIZE
        self.entity = PlayerEntity(
            x=x,
            y=y,
            width=SIZE_PLAYER[0],
            height=SIZE_PLAYER[1],
            speed=300.0,
            gravity=GRAVITY,
            jump_speed=-600.0,
            floor_y=floor_y
        )

        # Camada Visual (Texturas e Animações)
        self.view = PlayerView(size=SIZE_PLAYER)

        # Capturador de Comandos Locais
        self.input_manager = InputManager()

        # Retângulo compatível para câmera e detecção existente
        self.rect = pygame.Rect(int(self.entity.x), int(self.entity.y), int(self.entity.width), int(self.entity.height))

        # Vetor compatível com código legado
        self.direction = pygame.math.Vector2(0, 0)

    @property
    def x(self) -> float:
        return self.entity.x

    @x.setter
    def x(self, val: float):
        self.entity.x = float(val)
        self.rect.x = int(val)

    @property
    def y(self) -> float:
        return self.entity.y

    @y.setter
    def y(self, val: float):
        self.entity.y = float(val)
        self.rect.y = int(val)

    @property
    def is_grounded(self) -> bool:
        return self.entity.is_grounded

    @is_grounded.setter
    def is_grounded(self, val: bool):
        self.entity.is_grounded = bool(val)

    @property
    def speed(self) -> float:
        return self.entity.speed

    def update(self, dt: float, level=None):
        """Atualiza a lógica física via InputState e sincroniza a View."""
        input_state = self.input_manager.get_input_state()
        self.entity.update(dt, input_state=input_state, level=level)

        # Sincroniza o rect legado com a entidade lógica
        self.rect.x = int(self.entity.x)
        self.rect.y = int(self.entity.y)
        self.direction.x = self.entity.vx
        self.direction.y = self.entity.vy

        # Atualiza animações e áudio na View
        self.view.update(dt, self.entity)

    def draw(self, camera_offset: tuple[float, float] = (0.0, 0.0)):
        """Delega a renderização gráfica para a PlayerView."""
        self.view.draw(self.entity, camera_offset)

    def destroy(self):
        """Libera os recursos na GPU alocados pela View."""
        self.view.destroy()
