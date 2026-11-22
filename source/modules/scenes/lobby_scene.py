import pygame
from typing import Optional
from .base import Scene
from .ui_widgets import MenuButton, MenuLabel
from ..constants import WIDTH, HEIGHT
from ..utils import utils
from ..network.messages import MessageType
from ..network.network_server import NetworkServer
from ..network.network_client import NetworkClient


class LobbyScene(Scene):
    """
    Cena de Sala de Espera (Lobby LAN) do modo Multiplayer.
    Apresenta os jogadores conectados, status de prontidão e controles de início de partida.
    Integra a comunicação em tempo real via NetworkClient / NetworkServer.
    """
    def __init__(self, manager=None):
        super().__init__(manager)
        self.is_host: bool = False
        self.server: Optional[NetworkServer] = None
        self.client: Optional[NetworkClient] = None

        self.buttons: list[MenuButton] = []
        self.labels: list[MenuLabel] = []
        self.selected_index: int = 0
        self.is_ready: bool = True
        self.status_msg: str = "Aguardando participantes..."

    def enter(self, params=None):
        self.buttons.clear()
        self.labels.clear()

        if params:
            self.is_host = bool(params.get("is_host", False))
            self.server = params.get("server")
            self.client = params.get("client")

        cx = WIDTH / 2
        btn_w = 460
        btn_h = 55
        btn_x = cx - (btn_w / 2)

        self.labels.append(MenuLabel("SALA DE ESPERA (LOBBY LAN)", cx, HEIGHT * 0.15, font_size=80, color="#FFD700", center=True))

        role_text = "Você é o HOST da sala" if self.is_host else "Você está CONECTADO como Cliente"
        self.labels.append(MenuLabel(role_text, cx, HEIGHT * 0.24, font_size=28, color="#5C94FC", center=True))

        if self.is_host:
            self.buttons.append(MenuButton("INICIAR PARTIDA", btn_x, HEIGHT * 0.65, btn_w, btn_h, on_click=self._on_start_game, font_size=30))
            self.buttons.append(MenuButton("FECHAR SALA E VOLTAR", btn_x, HEIGHT * 0.75, btn_w, btn_h, on_click=self._on_leave, font_size=30))
        else:
            self.buttons.append(MenuButton("ESTOU PRONTO", btn_x, HEIGHT * 0.65, btn_w, btn_h, on_click=self._toggle_ready, font_size=30))
            self.buttons.append(MenuButton("DESCONECTAR E VOLTAR", btn_x, HEIGHT * 0.75, btn_w, btn_h, on_click=self._on_leave, font_size=30))

        if self.buttons:
            self.buttons[0].set_focused(True, play_sound=False)
            self.selected_index = 0

    def _toggle_ready(self):
        self.is_ready = not self.is_ready
        btn_text = "ESTOU PRONTO" if self.is_ready else "AGUARDANDO..."
        self.buttons[0].text = btn_text
        if self.client:
            self.client.send_tcp_message(MessageType.ACK, {"ready": self.is_ready})

    def _on_start_game(self):
        if not self.is_host:
            return

        # Host inicia a partida: notifica os clientes via broadcast TCP
        if self.server:
            start_envelope = {
                "level_name": "level1",
                "max_players": 2
            }
            self.server.broadcast_tcp(MessageType.START_GAME, start_envelope)
        elif self.client:
            self.client.send_tcp_message(MessageType.START_GAME, {"level_name": "level1", "max_players": 2})

        # Transita para a GameScene no modo multiplayer
        if self.manager:
            self.manager.change_scene("game", {
                "is_multiplayer": True,
                "network_client": self.client,
                "network_server": self.server
            })

    def _on_leave(self):
        if self.client:
            self.client.disconnect(reason="SAIDA_VOLUNTARIA")
            self.client.shutdown()
            self.client = None

        if self.server:
            self.server.shutdown()
            self.server = None

        if self.manager:
            self.manager.change_scene("multiplayer_menu")

    def handle_event(self, event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._on_leave()
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
        # Processa eventos assíncronos recebidos do cliente de rede
        if self.client:
            for env in self.client.get_events():
                if env.msg_type == MessageType.START_GAME:
                    if self.manager:
                        self.manager.change_scene("game", {
                            "is_multiplayer": True,
                            "network_client": self.client,
                            "network_server": self.server
                        })
                    return
                elif env.msg_type == MessageType.DISCONNECT:
                    self._on_leave()
                    return

    def draw(self):
        # 1. Fundo estilizado do lobby
        utils.draw_colored_quad(0, 0, WIDTH, HEIGHT, (0.03, 0.05, 0.10, 1.0))
        utils.draw_colored_quad(0, 0, WIDTH, HEIGHT * 0.30, (0.02, 0.03, 0.07, 0.95))

        for label in self.labels:
            label.draw()

        # 2. Painéis dos Jogadores Conectados (Slots 1 e 2)
        cx = WIDTH / 2
        card_w = 420
        card_h = 100
        card_y = HEIGHT * 0.36

        # Slot 1: Jogador 1 (Host)
        slot1_x = cx - card_w - 20
        p1_color = (0.08, 0.16, 0.28, 0.85)
        utils.draw_colored_quad(slot1_x, card_y, card_w, card_h, p1_color)
        utils.draw_colored_quad(slot1_x, card_y, 8, card_h, (0.2, 0.6, 1.0, 1.0))  # Borda azul

        # Slot 2: Jogador 2 (Cliente)
        slot2_x = cx + 20
        has_player2 = False
        if self.server:
            has_player2 = self.server.connection_manager.active_count >= 2
        elif self.client and hasattr(self.client, 'lobby_players'):
            has_player2 = len(self.client.lobby_players) >= 2

        p2_color = (0.08, 0.24, 0.16, 0.85) if has_player2 else (0.06, 0.08, 0.12, 0.60)
        p2_border = (0.2, 0.8, 0.4, 1.0) if has_player2 else (0.4, 0.4, 0.4, 0.5)
        utils.draw_colored_quad(slot2_x, card_y, card_w, card_h, p2_color)
        utils.draw_colored_quad(slot2_x, card_y, 8, card_h, p2_border)

        # Informações textuais dos slots
        p1_text = "JOGADOR 1 (HOST)" + (" [VOCE]" if self.is_host else "")
        MenuLabel(p1_text, slot1_x + 20, card_y + 25, font_size=24, color="#FFFFFF").draw()
        MenuLabel("Status: PRONTO", slot1_x + 20, card_y + 55, font_size=20, color="#5C94FC").draw()

        if has_player2:
            p2_text = "JOGADOR 2" + (" [VOCE]" if not self.is_host else "")
            MenuLabel(p2_text, slot2_x + 20, card_y + 25, font_size=24, color="#FFFFFF").draw()
            MenuLabel("Status: CONECTADO", slot2_x + 20, card_y + 55, font_size=20, color="#00FF66").draw()
        else:
            MenuLabel("JOGADOR 2", slot2_x + 20, card_y + 25, font_size=24, color="#888888").draw()
            MenuLabel("Aguardando conexao LAN...", slot2_x + 20, card_y + 55, font_size=20, color="#AAAAAA").draw()

        # 3. Botões de ação
        for btn in self.buttons:
            btn.draw()

    def exit(self):
        for btn in self.buttons:
            btn.destroy()
        self.buttons.clear()
        self.labels.clear()
