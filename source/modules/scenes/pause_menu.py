import pygame
from .base import Scene
from .ui_widgets import MenuButton, MenuLabel
from ..constants import WIDTH, HEIGHT
from ..utils import utils


class PauseMenuScene(Scene):
    """
    Menu de Pausa (Overlay Modal).
    Renderiza sobre a cena do jogo congelada e oferece: Continuar, Reiniciar e Voltar ao Menu.
    """
    def __init__(self, manager=None):
        super().__init__(manager)
        self.is_overlay = True  # Permite que a cena abaixo continue sendo desenhada
        self.buttons: list[MenuButton] = []
        self.labels: list[MenuLabel] = []
        self.selected_index: int = 0

    def enter(self, params=None):
        cx = WIDTH / 2
        btn_w = 420
        btn_h = 58
        start_y = HEIGHT * 0.44
        spacing = 72

        self.labels.append(MenuLabel("JOGO PAUSADO", cx, HEIGHT * 0.28, font_size=80, color="#FFD700", center=True))
        self.labels.append(MenuLabel("Pressione ESC para retomar", cx, HEIGHT * 0.36, font_size=28, color="#AAAAAA", center=True))

        btn_x = cx - (btn_w / 2)

        # Detecta se a sessão é de Playtest
        is_playtest = False
        if self.manager and len(self.manager.stack) >= 2:
            underlying = self.manager.stack[-2]
            is_playtest = getattr(underlying, 'is_playtest', False)

        options = [
            ("CONTINUAR", self._on_continue),
            ("REINICIAR", self._on_restart),
            ("CONFIGURACOES", self._on_settings),
            ("RETORNAR AO EDITOR" if is_playtest else "MENU PRINCIPAL", self._on_exit_game)
        ]

        for i, (text, callback) in enumerate(options):
            y = start_y + (i * spacing)
            btn = MenuButton(text, btn_x, y, btn_w, btn_h, on_click=callback, font_size=32)
            self.buttons.append(btn)

        if self.buttons:
            self.buttons[0].set_focused(True, play_sound=False)
            self.selected_index = 0

    def _on_continue(self):
        if self.manager:
            self.manager.pop_scene()

    def _on_restart(self):
        if self.manager:
            self.manager.change_scene("game", {"restart": True})

    def _on_settings(self):
        if self.manager:
            self.manager.push_scene("settings")

    def _on_exit_game(self):
        if self.manager:
            # Se for Playtest, desempilha a pausa e o jogo para voltar à EditorScene
            if len(self.manager.stack) >= 2 and getattr(self.manager.stack[-2], 'is_playtest', False):
                self.manager.pop_scene()  # Fecha PauseMenu
                self.manager.pop_scene()  # Fecha GameScene e volta para EditorScene
            else:
                self.manager.change_scene("main_menu")

    def handle_event(self, event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._on_continue()
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

        return True  # Consome eventos enquanto pausado para não atingir o jogo

    def _move_selection(self, delta: int):
        if not self.buttons:
            return
        self.buttons[self.selected_index].set_focused(False, play_sound=False)
        self.selected_index = (self.selected_index + delta) % len(self.buttons)
        self.buttons[self.selected_index].set_focused(True, play_sound=True)

    def update(self, dt: float):
        pass  # O jogo ao fundo fica suspenso!

    def draw(self):
        # Overlay escurecido translúcido cobrindo toda a tela do jogo
        utils.draw_colored_quad(0, 0, WIDTH, HEIGHT, (0.0, 0.0, 0.0, 0.72))

        # Caixa de diálogo central
        box_w = 540
        box_h = 520
        bx = (WIDTH - box_w) / 2
        by = (HEIGHT - box_h) / 2
        utils.draw_colored_quad(bx, by, box_w, box_h, (0.05, 0.08, 0.15, 0.95))

        # Borda dourada da caixa
        border = 2
        utils.draw_colored_quad(bx, by, box_w, border, (1.0, 0.84, 0.0, 1.0))
        utils.draw_colored_quad(bx, by + box_h - border, box_w, border, (1.0, 0.84, 0.0, 1.0))
        utils.draw_colored_quad(bx, by, border, box_h, (1.0, 0.84, 0.0, 1.0))
        utils.draw_colored_quad(bx + box_w - border, by, border, box_h, (1.0, 0.84, 0.0, 1.0))

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
