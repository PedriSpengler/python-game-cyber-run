import pygame
from .input_state import InputState


class InputManager:
    """
    Capturador de comandos de hardware local via Pygame.
    Traduz entradas de teclado para instâncias puras de InputState,
    com suporte a buffer de pulo (edge trigger) para evitar perda de comandos.
    """
    def __init__(self):
        self._prev_jump_held: bool = False
        self._jump_buffered: bool = False
        self._tick_counter: int = 0

    def handle_event(self, event):
        """Registra eventos de tecla pontuais diretamente da fila de eventos."""
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                self._jump_buffered = True

    def get_input_state(self) -> InputState:
        """
        Gera o InputState consolidado do tick atual.
        Combina o estado contínuo das teclas com o buffer de ações pontuais.
        """
        self._tick_counter += 1
        keys = pygame.key.get_pressed()

        # 1. Movimentação Horizontal Contínua
        move_x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_x -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_x += 1

        # 2. Pulo (Edge Trigger + Buffer)
        jump_held = bool(keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP])
        jump_pressed = self._jump_buffered or (jump_held and not self._prev_jump_held)

        # Consome o buffer de pulo pontual
        self._jump_buffered = False
        self._prev_jump_held = jump_held

        return InputState(
            move_x=move_x,
            jump=jump_pressed,
            jump_held=jump_held,
            action=False,
            tick=self._tick_counter
        )

    def reset(self):
        self._prev_jump_held = False
        self._jump_buffered = False
        self._tick_counter = 0
