import pygame
from .base import Scene
from .ui_widgets import MenuButton, MenuLabel
from ..constants import WIDTH, HEIGHT
from ..utils import utils
from ..config.settings import settings
from ..config.sounds import sounds


class SettingsScene(Scene):
    """
    Cena de Configuracoes.
    Permite ajustar volume da musica, volume de efeitos sonoros e alternar exibicao de FPS.
    As configuracoes produzem efeitos reais e sao persistidas em JSON.
    """
    def __init__(self, manager=None):
        super().__init__(manager)
        self.buttons: list[MenuButton] = []
        self.labels: list[MenuLabel] = []
        self.selected_index: int = 0

    def enter(self, params=None):
        cx = WIDTH / 2
        btn_w = 520
        btn_h = 60
        start_y = HEIGHT * 0.38
        spacing = 75

        self.labels.append(MenuLabel("CONFIGURACOES", cx, HEIGHT * 0.18, font_size=90, color="#FFD700", center=True))
        self.labels.append(MenuLabel("Ajuste as preferencias com as setas ESQUERDA/DIREITA ou clique", cx, HEIGHT * 0.28, font_size=28, color="#5C94FC", center=True))

        btn_x = cx - (btn_w / 2)

        self.btn_music = MenuButton(self._get_music_text(), btn_x, start_y, btn_w, btn_h, on_click=self._toggle_music, font_size=32)
        self.btn_sfx = MenuButton(self._get_sfx_text(), btn_x, start_y + spacing, btn_w, btn_h, on_click=self._toggle_sfx, font_size=32)
        self.btn_fps = MenuButton(self._get_fps_text(), btn_x, start_y + (spacing * 2), btn_w, btn_h, on_click=self._toggle_fps, font_size=32)
        self.btn_back = MenuButton("SALVAR E VOLTAR", btn_x, start_y + (spacing * 3.5), btn_w, btn_h, on_click=self._on_back, font_size=34)

        self.buttons = [self.btn_music, self.btn_sfx, self.btn_fps, self.btn_back]
        self.buttons[0].set_focused(True, play_sound=False)
        self.selected_index = 0

    def _get_music_text(self) -> str:
        pct = int(settings.music_volume * 100)
        status = f"{pct}%" if settings.music_enabled else "MUTADO"
        return f"MUSICA: < {status} >"

    def _get_sfx_text(self) -> str:
        pct = int(settings.sfx_volume * 100)
        status = f"{pct}%" if settings.sfx_enabled else "MUTADO"
        return f"EFEITOS: < {status} >"

    def _get_fps_text(self) -> str:
        status = "LIGADO" if settings.show_fps else "DESLIGADO"
        return f"EXIBIR FPS: < {status} >"

    def _change_music_volume(self, delta: float):
        new_vol = max(0.0, min(1.0, round(settings.music_volume + delta, 2)))
        settings.music_volume = new_vol
        settings.music_enabled = (new_vol > 0.0)
        settings.apply()
        self.btn_music.set_text(self._get_music_text())
        sounds.play_click()

    def _change_sfx_volume(self, delta: float):
        new_vol = max(0.0, min(1.0, round(settings.sfx_volume + delta, 2)))
        settings.sfx_volume = new_vol
        settings.sfx_enabled = (new_vol > 0.0)
        settings.apply()
        self.btn_sfx.set_text(self._get_sfx_text())
        sounds.play_click()

    def _toggle_music(self):
        self._change_music_volume(0.1 if settings.music_volume < 1.0 else -1.0)

    def _toggle_sfx(self):
        self._change_sfx_volume(0.1 if settings.sfx_volume < 1.0 else -1.0)

    def _toggle_fps(self):
        settings.show_fps = not settings.show_fps
        self.btn_fps.set_text(self._get_fps_text())
        sounds.play_click()

    def _on_back(self):
        settings.save()
        if self.manager:
            self.manager.pop_scene()

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
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                if self.selected_index == 0:
                    self._change_music_volume(-0.1)
                elif self.selected_index == 1:
                    self._change_sfx_volume(-0.1)
                elif self.selected_index == 2:
                    self._toggle_fps()
                return True
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                if self.selected_index == 0:
                    self._change_music_volume(0.1)
                elif self.selected_index == 1:
                    self._change_sfx_volume(0.1)
                elif self.selected_index == 2:
                    self._toggle_fps()
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
