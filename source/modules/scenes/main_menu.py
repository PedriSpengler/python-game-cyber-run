import pygame
from .base import Scene
from .ui_widgets import MenuButton, MenuLabel
from ..constants import WIDTH, HEIGHT
from ..utils import utils
from ..config.sounds import sounds


class MainMenuScene(Scene):
    """
    Menu Principal do jogo TAC3.
    Oferece acesso visual e funcional a: Novo Jogo, Editor, Multiplayer, Configuracoes e Sair.
    """
    def __init__(self, manager=None):
        super().__init__(manager)
        self.buttons: list[MenuButton] = []
        self.labels: list[MenuLabel] = []
        self.selected_index: int = 0

    def enter(self, params=None):
        sounds.play_music()

        cx = WIDTH / 2
        btn_w = 460
        btn_h = 60
        start_y = HEIGHT * 0.42
        spacing = 75

        # Título e Subtítulo
        self.labels.append(MenuLabel("GAME TAC3", cx, HEIGHT * 0.18, font_size=110, color="#FFD700", center=True))
        self.labels.append(MenuLabel("2D PLATFORMER & LEVEL MAKER", cx, HEIGHT * 0.28, font_size=38, color="#5C94FC", center=True))
        self.labels.append(MenuLabel("Use as setas/mouse para navegar e ENTER para selecionar", cx, HEIGHT * 0.92, font_size=24, color="#AAAAAA", center=True))

        # Botões do Menu
        btn_x = cx - (btn_w / 2)
        options = [
            ("NOVO JOGO", self._on_new_game),
            ("EDITOR DE FASES", self._on_editor),
            ("MULTIPLAYER (LAN)", self._on_multiplayer),
            ("CONFIGURACOES", self._on_settings),
            ("SAIR", self._on_quit)
        ]

        for i, (text, callback) in enumerate(options):
            y = start_y + (i * spacing)
            btn = MenuButton(text, btn_x, y, btn_w, btn_h, on_click=callback, font_size=36)
            self.buttons.append(btn)

        if self.buttons:
            self.buttons[0].set_focused(True, play_sound=False)
            self.selected_index = 0

    def _on_new_game(self):
        if self.manager:
            self.manager.change_scene("game")

    def _on_editor(self):
        if self.manager:
            self.manager.change_scene("editor")

    def _on_multiplayer(self):
        if self.manager:
            self.manager.change_scene("multiplayer_menu")

    def _on_settings(self):
        if self.manager:
            self.manager.push_scene("settings")

    def _on_quit(self):
        if self.manager:
            self.manager.quit()

    def handle_event(self, event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self._move_selection(-1)
                return True
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._move_selection(1)
                return True
            elif event.key == pygame.K_ESCAPE:
                self._on_quit()
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
        # Fundo retrô gradiente simples com quads
        utils.draw_colored_quad(0, 0, WIDTH, HEIGHT, (0.04, 0.06, 0.12, 1.0))
        # Faixa de destaque no topo
        utils.draw_colored_quad(0, 0, WIDTH, HEIGHT * 0.35, (0.02, 0.03, 0.08, 0.95))

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
