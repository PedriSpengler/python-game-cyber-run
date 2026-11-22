import pygame
from .base import Scene
from .ui_widgets import MenuButton, MenuLabel
from ..constants import WIDTH, HEIGHT
from ..utils import utils
from ..network.network_server import NetworkServer
from ..network.network_client import NetworkClient
from ..network.network_config import DEFAULT_HOST, DEFAULT_TCP_PORT, DEFAULT_UDP_PORT


class MultiplayerMenuScene(Scene):
    """
    Menu Inicial de Multiplayer em Rede Local (LAN).
    Apresenta a estrutura visual e navegacao para Criar Partida (Host) e Conectar-se (Cliente).
    A camada de rede funcional sera implementada na Etapa 5.
    """
    def __init__(self, manager=None):
        super().__init__(manager)
        self.buttons: list[MenuButton] = []
        self.labels: list[MenuLabel] = []
        self.selected_index: int = 0

    def enter(self, params=None):
        cx = WIDTH / 2
        btn_w = 480
        btn_h = 60
        start_y = HEIGHT * 0.44
        spacing = 75

        self.labels.append(MenuLabel("MULTIPLAYER EM LAN", cx, HEIGHT * 0.18, font_size=90, color="#FFD700", center=True))
        self.labels.append(MenuLabel("Rede Local Cliente-Servidor (Em preparacao para a Etapa 5)", cx, HEIGHT * 0.28, font_size=28, color="#5C94FC", center=True))

        btn_x = cx - (btn_w / 2)
        options = [
            ("CRIAR PARTIDA (HOST)", self._on_host),
            ("CONECTAR-SE (CLIENTE)", self._on_join),
            ("VOLTAR AO MENU", self._on_back)
        ]

        for i, (text, callback) in enumerate(options):
            y = start_y + (i * spacing)
            btn = MenuButton(text, btn_x, y, btn_w, btn_h, on_click=callback, font_size=32)
            self.buttons.append(btn)

        if self.buttons:
            self.buttons[0].set_focused(True, play_sound=False)
            self.selected_index = 0

    def _set_status(self, text: str, color: str = "#FF4444"):
        if len(self.labels) >= 3:
            self.labels.pop()
        self.labels.append(MenuLabel(text, WIDTH / 2, HEIGHT * 0.82, font_size=24, color=color, center=True))

    def _on_host(self):
        try:
            server = NetworkServer(host=DEFAULT_HOST, tcp_port=DEFAULT_TCP_PORT, udp_port=DEFAULT_UDP_PORT)
            if not server.start():
                self._set_status("Falha ao iniciar servidor local. Verifique as portas de rede.")
                return

            client = NetworkClient()
            if not client.connect(host=DEFAULT_HOST, tcp_port=DEFAULT_TCP_PORT, udp_port=DEFAULT_UDP_PORT, player_name="Host"):
                server.shutdown()
                self._set_status(f"Erro ao conectar ao proprio host: {client.rejection_reason}")
                return

            if self.manager:
                self.manager.change_scene("lobby", {"is_host": True, "server": server, "client": client})
        except Exception as e:
            self._set_status(f"Exceção ao criar sala: {e}")

    def _on_join(self):
        try:
            client = NetworkClient()
            if not client.connect(host=DEFAULT_HOST, tcp_port=DEFAULT_TCP_PORT, udp_port=DEFAULT_UDP_PORT, player_name="Cliente"):
                self._set_status(f"Falha ao conectar: {client.rejection_reason or 'Servidor nao encontrado'}")
                return

            if self.manager:
                self.manager.change_scene("lobby", {"is_host": False, "client": client})
        except Exception as e:
            self._set_status(f"Exceção ao conectar: {e}")

    def _on_back(self):
        if self.manager:
            self.manager.change_scene("main_menu")

    def handle_event(self, event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._on_back()
                return True
            elif event.key in (pygame.K_UP, pygame.K_w):
                self._move_selection(-1)
                return True
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._move_selection(1)
                return True

        for btn in self.buttons:
            if btn.handle_event(event):
                return True

        return False

    def _move_selection(self, delta: int):
        if not self.buttons:
            return
        self.buttons[self.selected_index].set_focused(False, play_sound=False)
        self.selected_index = (self.selected_index + delta) % len(self.buttons)
        self.buttons[self.selected_index].set_focused(True, play_sound=True)

    def update(self, dt: float):
        pass

    def draw(self):
        utils.draw_colored_quad(0, 0, WIDTH, HEIGHT, (0.04, 0.06, 0.12, 1.0))
        utils.draw_colored_quad(0, 0, WIDTH, HEIGHT * 0.32, (0.02, 0.03, 0.08, 0.95))

        for label in self.labels:
            label.draw()

        for btn in self.buttons:
            btn.draw()

    def exit(self):
        for btn in self.buttons:
            btn.destroy()
        self.buttons.clear()

        for label in self.labels:
            label.destroy()
        self.labels.clear()
