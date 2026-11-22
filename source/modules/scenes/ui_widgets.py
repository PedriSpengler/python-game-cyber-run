import pygame
from ..utils import utils
from ..config.sounds import sounds
from ..constants import COLOR_TEXT

# Garante a inicialização do módulo de fontes do Pygame
if not pygame.font.get_init():
    pygame.font.init()


class MenuButton:
    """
    Botao de menu com estetica retro arcade.
    Suporta foco por teclado (setas) e interacao com mouse (hover/click).
    """
    def __init__(self, text: str, x: float, y: float, w: float, h: float, on_click=None, font_size: int = 50):
        self.text = text
        self.rect = pygame.Rect(int(x), int(y), int(w), int(h))
        self.on_click = on_click
        self.is_hovered: bool = False
        self.is_focused: bool = False
        self.font_size = font_size

        try:
            self.font = pygame.font.Font("assets/fonts/Call of Ops Duty II.otf", self.font_size)
        except Exception:
            self.font = pygame.font.Font(None, self.font_size)

        self.normal_tex = None
        self.focused_tex = None
        self.normal_size = (0, 0)
        self.focused_size = (0, 0)

        self._render_text_surfaces()

    def _render_text_surfaces(self):
        # Texto normal
        surf_normal = self.font.render(self.text, True, pygame.Color("#E0E0E0"))
        self.normal_size = surf_normal.get_size()
        self.normal_tex = utils.surface_to_texture(surf_normal)

        # Texto destacado (focado / hovered) em dourado arcade
        surf_focused = self.font.render(self.text, True, pygame.Color("#FFD700"))
        self.focused_size = surf_focused.get_size()
        self.focused_tex = utils.surface_to_texture(surf_focused)

    def set_text(self, new_text: str):
        if new_text != self.text:
            self.text = new_text
            self.destroy()
            self._render_text_surfaces()

    def set_focused(self, focused: bool, play_sound: bool = True):
        was_focused = self.is_focused
        self.is_focused = focused
        if not was_focused and focused and play_sound:
            sounds.play_click()

    def handle_event(self, event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            prev_hover = self.is_hovered
            self.is_hovered = self.rect.collidepoint(event.pos)
            if not prev_hover and self.is_hovered:
                self.is_focused = True
                sounds.play_click()
            elif not self.is_hovered and self.is_focused:
                pass

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                sounds.play_click()
                if self.on_click:
                    self.on_click()
                return True

        elif event.type == pygame.KEYDOWN and self.is_focused:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                sounds.play_click()
                if self.on_click:
                    self.on_click()
                return True
        return False

    def draw(self):
        active = self.is_focused or self.is_hovered
        x, y, w, h = self.rect.x, self.rect.y, self.rect.w, self.rect.h

        # Fundo do botão
        if active:
            # Fundo verde arcade com borda destacada
            utils.draw_colored_quad(x, y, w, h, (0.05, 0.45, 0.05, 0.85))
            # Borda dourada (4 quads finos)
            border = 3
            utils.draw_colored_quad(x, y, w, border, (1.0, 0.84, 0.0, 1.0))
            utils.draw_colored_quad(x, y + h - border, w, border, (1.0, 0.84, 0.0, 1.0))
            utils.draw_colored_quad(x, y, border, h, (1.0, 0.84, 0.0, 1.0))
            utils.draw_colored_quad(x + w - border, y, border, h, (1.0, 0.84, 0.0, 1.0))
            tex = self.focused_tex
            tw, th = self.focused_size
        else:
            # Fundo escuro sutil
            utils.draw_colored_quad(x, y, w, h, (0.08, 0.08, 0.12, 0.7))
            tex = self.normal_tex
            tw, th = self.normal_size

        # Centraliza o texto no botão
        tx = x + (w - tw) / 2
        ty = y + (h - th) / 2
        utils.draw_textured_quad(tex, tx, ty, tw, th)

    def destroy(self):
        """Libera com seguranca as texturas do botao."""
        if self.normal_tex is not None:
            utils.delete_texture(self.normal_tex)
            self.normal_tex = None
        if self.focused_tex is not None:
            utils.delete_texture(self.focused_tex)
            self.focused_tex = None


class MenuLabel:
    """Rotulo de texto renderizado via OpenGL."""
    def __init__(self, text: str, x: float, y: float, font_size: int = 40, color="#FFFFFF", center=False):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.center = center
        self.font_size = font_size

        try:
            self.font = pygame.font.Font("assets/fonts/Call of Ops Duty II.otf", self.font_size)
        except Exception:
            self.font = pygame.font.Font(None, self.font_size)

        self.texture_id = None
        self.size = (0, 0)
        self.render_text()

    def render_text(self):
        if self.texture_id is not None:
            utils.delete_texture(self.texture_id)
        surf = self.font.render(self.text, True, pygame.Color(self.color))
        self.size = surf.get_size()
        self.texture_id = utils.surface_to_texture(surf)

    def set_text(self, new_text: str):
        if new_text != self.text:
            self.text = new_text
            self.render_text()

    def draw(self):
        if self.texture_id is not None:
            w, h = self.size
            x = self.x - (w / 2) if self.center else self.x
            y = self.y - (h / 2) if self.center else self.y
            utils.draw_textured_quad(self.texture_id, x, y, w, h)

    def destroy(self):
        if self.texture_id is not None:
            utils.delete_texture(self.texture_id)
            self.texture_id = None
