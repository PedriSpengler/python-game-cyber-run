import pygame
from ..display import display
from ..constants import TILE_SIZE, COLOR_BG
from ..utils import utils
from ..ui.levels import Level1
from .notify import Interested, Anchor, Fill
from ..entities.tiles import Tile
from .viewport import EditorViewport


class Grid(Interested):
    def __init__(self, level: Level1, viewport: EditorViewport = None):
        super().__init__()
        largura = display.size[0] * 0.7
        altura = display.size[1] * 0.8

        self.x_tiles = int(largura // TILE_SIZE)
        self.y_tiles = int(altura // TILE_SIZE)

        self.size = (
            int(self.x_tiles * TILE_SIZE),
            int(self.y_tiles * TILE_SIZE)
        )

        self.image = pygame.Surface(self.size).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect_orig = self.image.get_rect()

        self.anchor = [0, 0]
        self.level = level
        self.viewport = viewport or EditorViewport()
        self.show_grid: bool = True
        self.tiles: list[Tile] = []

        # Converte e guarda o ID da GPU
        self.texture_id = utils.surface_to_texture(self.image)
        self.rect.topleft = (display.size[0] * 0.1, display.size[1] * 0.1)

        # Matriz de tiles visíveis para compatibilidade com código existente
        self._init_cell_tiles()
        self.clear()
        self.update_tiles()

    def _init_cell_tiles(self):
        self.tiles.clear()
        for lin in range(self.y_tiles):
            for col in range(self.x_tiles):
                s = pygame.surface.Surface((TILE_SIZE, TILE_SIZE))
                pos = f"{col},{lin}"
                tile = Tile(0, s, pos)
                l = col * TILE_SIZE + self.rect.left
                t = lin * TILE_SIZE + self.rect.top
                tile.rect.topleft = (l, t)
                self.tiles.append(tile)

    def clear(self):
        self.image.fill(COLOR_BG)
        tile_size = int(self.viewport.current_tile_size)

        if self.show_grid and tile_size > 4:
            grid_color = (255, 255, 255, 40)
            # Linhas horizontais
            num_h = int(self.size[1] // tile_size) + 1
            for linha in range(num_h):
                y = int(linha * tile_size - (self.viewport.pan_y % tile_size))
                if 0 <= y < self.size[1]:
                    pygame.draw.line(self.image, grid_color, (0, y), (self.size[0], y))

            # Linhas verticais
            num_v = int(self.size[0] // tile_size) + 1
            for col in range(num_v):
                x = int(col * tile_size - (self.viewport.pan_x % tile_size))
                if 0 <= x < self.size[0]:
                    pygame.draw.line(self.image, grid_color, (x, 0), (x, self.size[1]))

        pygame.draw.rect(self.image, "green", self.rect_orig, 3)

    def update(self, dt):
        for event in self.events_get():
            if event == Anchor:
                # Sincroniza pan com anchor para compatibilidade
                self.viewport.pan_x = self.anchor[0] * self.viewport.current_tile_size
                self.viewport.pan_y = self.anchor[1] * self.viewport.current_tile_size
                self.clear()
                self.update_tiles()
            elif event == Fill:
                self.clear()
                self.update_tiles()

    def update_tiles(self, preview_tiles=None, selection_bounds=None, hover_cell=None):
        """Renderiza os blocos da fase na superfície do grid aplicando zoom e pan."""
        self.clear()
        tile_size = int(self.viewport.current_tile_size)
        if tile_size <= 0:
            return

        col_start = max(0, int(self.viewport.pan_x // tile_size))
        col_end = int((self.viewport.pan_x + self.size[0]) // tile_size) + 1
        lin_start = max(0, int(self.viewport.pan_y // tile_size))
        lin_end = int((self.viewport.pan_y + self.size[1]) // tile_size) + 1

        total_lines = len(self.level.tiles)
        total_cols = len(self.level.tiles[0]) if total_lines > 0 else 0

        # Cache para superfícies escaladas por zoom
        scaled_cache = {}

        for lin in range(lin_start, min(total_lines, lin_end)):
            row = self.level.tiles[lin]
            for col in range(col_start, min(total_cols, col_end)):
                tile = row[col]
                if tile and hasattr(tile, 'image'):
                    screen_x = int(col * tile_size - self.viewport.pan_x)
                    screen_y = int(lin * tile_size - self.viewport.pan_y)

                    if self.viewport.zoom == 1.0:
                        surf = tile.image
                    else:
                        tid = getattr(tile, 'id', id(tile.image))
                        if tid not in scaled_cache:
                            scaled_cache[tid] = pygame.transform.scale(tile.image, (tile_size, tile_size))
                        surf = scaled_cache[tid]

                    self.image.blit(surf, (screen_x, screen_y))

        # Renderiza pré-visualização (ghost tiles)
        if preview_tiles:
            for p_col, p_lin, p_id in preview_tiles:
                if 0 <= p_lin < total_lines and 0 <= p_col < total_cols:
                    screen_x = int(p_col * tile_size - self.viewport.pan_x)
                    screen_y = int(p_lin * tile_size - self.viewport.pan_y)
                    ghost_rect = pygame.Rect(screen_x, screen_y, tile_size, tile_size)
                    pygame.draw.rect(self.image, (255, 215, 0, 180), ghost_rect, 2)

        # Renderiza caixa de seleção
        if selection_bounds:
            c1, l1, c2, l2 = selection_bounds
            sx1 = int(c1 * tile_size - self.viewport.pan_x)
            sy1 = int(l1 * tile_size - self.viewport.pan_y)
            sx2 = int((c2 + 1) * tile_size - self.viewport.pan_x)
            sy2 = int((l2 + 1) * tile_size - self.viewport.pan_y)
            sel_rect = pygame.Rect(sx1, sy1, sx2 - sx1, sy2 - sy1)
            pygame.draw.rect(self.image, (0, 180, 255), sel_rect, 2)

        # Destaca célula sob o cursor
        if hover_cell and hover_cell[0] >= 0 and hover_cell[1] >= 0:
            hc, hl = hover_cell
            hx = int(hc * tile_size - self.viewport.pan_x)
            hy = int(hl * tile_size - self.viewport.pan_y)
            pygame.draw.rect(self.image, (255, 255, 255), (hx, hy, tile_size, tile_size), 1)

        self.texture_id = utils.update_texture(self.texture_id, self.image, self.size)

    def draw(self):
        x, y, w, h = self.rect.x, self.rect.y, self.rect.w, self.rect.h
        utils.draw_textured_quad(self.texture_id, x, y, w, h)

    def destroy(self):
        if self.texture_id is not None:
            utils.delete_texture(self.texture_id)
            self.texture_id = None
