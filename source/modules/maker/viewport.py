import pygame
from ..constants import TILE_SIZE


class EditorViewport:
    """
    Gerencia a navegação espacial do editor (Pan e Zoom) e a conversão matemática
    entre coordenadas da tela (Screen Space) e índices da matriz da fase (Map Space).
    Garante que transformações visuais não modifiquem os dados reais do mapa.
    """
    def __init__(self, cell_size: int = TILE_SIZE):
        self.base_cell_size: int = cell_size
        self.zoom_levels: list[float] = [0.5, 0.75, 1.0, 1.5, 2.0]
        self.zoom_index: int = 2  # Padrão: 1.0x
        self.zoom: float = self.zoom_levels[self.zoom_index]

        # Deslocamento do mundo em pixels (Pan)
        self.pan_x: float = 0.0
        self.pan_y: float = 0.0

        # Estado de arraste com mouse (Pan)
        self.is_panning: bool = False
        self.pan_start_mouse: tuple[int, int] = (0, 0)
        self.pan_start_offset: tuple[float, float] = (0.0, 0.0)

    @property
    def current_tile_size(self) -> float:
        """Tamanho de cada célula na tela após aplicação do zoom."""
        return self.base_cell_size * self.zoom

    def set_zoom(self, new_zoom: float):
        """Define o zoom com clamping entre 0.5x e 2.0x."""
        self.zoom = max(0.5, min(2.0, float(new_zoom)))

    def zoom_in(self, pivot_screen_pos: tuple[int, int] = None, grid_rect: pygame.Rect = None):
        """Aumenta o nível de zoom mantendo o cursor ou centro como ponto focal."""
        if self.zoom_index < len(self.zoom_levels) - 1:
            self.zoom_index += 1
            self.zoom = self.zoom_levels[self.zoom_index]

    def zoom_out(self, pivot_screen_pos: tuple[int, int] = None, grid_rect: pygame.Rect = None):
        """Reduz o nível de zoom mantendo o cursor ou centro como ponto focal."""
        if self.zoom_index > 0:
            self.zoom_index -= 1
            self.zoom = self.zoom_levels[self.zoom_index]

    def start_pan(self, mouse_pos: tuple[int, int]):
        """Inicia o arraste de navegação (Pan)."""
        self.is_panning = True
        self.pan_start_mouse = mouse_pos
        self.pan_start_offset = (self.pan_x, self.pan_y)

    def update_pan(self, current_mouse_pos: tuple[int, int]):
        """Atualiza o deslocamento durante o arraste."""
        if self.is_panning:
            dx = current_mouse_pos[0] - self.pan_start_mouse[0]
            dy = current_mouse_pos[1] - self.pan_start_mouse[1]
            self.pan_x = self.pan_start_offset[0] - dx
            self.pan_y = self.pan_start_offset[1] - dy

    def end_pan(self):
        """Finaliza o arraste de navegação."""
        self.is_panning = False

    def screen_to_map(self, screen_x: float, screen_y: float, grid_rect: pygame.Rect) -> tuple[int, int]:
        """
        Converte coordenadas de clique na janela para coordenadas de célula (col, lin) da matriz do mapa.
        Retorna (-1, -1) se fora da área do grid.
        """
        if not grid_rect.collidepoint(screen_x, screen_y):
            return -1, -1

        # Coordenadas relativas à área interna do grid
        rel_x = screen_x - grid_rect.left + self.pan_x
        rel_y = screen_y - grid_rect.top + self.pan_y

        tile_size = self.current_tile_size
        col = int(rel_x // tile_size)
        lin = int(rel_y // tile_size)
        return col, lin

    def map_to_screen(self, col: int, lin: int, grid_rect: pygame.Rect) -> tuple[float, float]:
        """
        Converte coordenadas da matriz do mapa para coordenadas da tela na janela.
        """
        tile_size = self.current_tile_size
        screen_x = grid_rect.left + (col * tile_size) - self.pan_x
        screen_y = grid_rect.top + (lin * tile_size) - self.pan_y
        return screen_x, screen_y
