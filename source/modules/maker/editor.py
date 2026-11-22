import pygame
from ..display import display
from .info import Info
from .grid import Grid
from ..entities.tiles import TileMap, Tile
from OpenGL.GL import *
from ..ui.background import Background
from ..ui.levels import Level1
from ..constants import TILE_MAP_LEVEL1, TILE_SIZE
from .notify import Notify, Anchor, Select, Fill
from .pallet import Pallet
from .viewport import EditorViewport
from .tools import ToolManager
from .commands import CommandHistory, ResizeMapCommand


class Editor:
    """
    Controlador central do Level Editor do TAC3.
    Coordena viewport, histórico (Undo/Redo), ferramentas de edição,
    grade de tiles e paleta de recursos.
    """
    def __init__(self):
        self.running: bool = False
        self.has_unsaved_changes: bool = False
        self.viewport = EditorViewport()
        self.tool_manager = ToolManager()
        self.history = CommandHistory(max_history=100)
        self.active_tile_id: int = 1
        self.cursor_map_pos: tuple[int, int] = (0, 0)

        # Referências a componentes
        self.bg = None
        self.tile_map = None
        self.level1 = None
        self.grid = None
        self.info = None
        self.pallet = None

        self.notify_anchor = None
        self.notify_select = None
        self.notify_fill = None

    @property
    def level(self):
        """Alias para facilitar acesso por ferramentas."""
        return self.level1

    def init_editor(self, custom_level=None):
        """Inicializa os recursos e estado do editor."""
        display.create_display()
        self.bg = Background("Black")

        # Carrega mapa de tiles
        self.tile_map = TileMap()
        self.tile_map.load_sprite_maps()

        if custom_level is not None:
            self.level1 = custom_level
            self.level1.tile_map = self.tile_map
        else:
            self.level1 = Level1()
            self.level1.load(self.tile_map)

        self.grid = Grid(self.level1, self.viewport)
        self.info = Info(self.grid)
        self.pallet = Pallet(self.tile_map)

        self.notify_anchor = Notify([self.grid, self.info], Anchor)
        self.notify_select = Notify([self.pallet], Select)
        self.notify_fill = Notify([self.grid], Fill)

        # Seleciona o primeiro tile disponível por padrão
        if self.pallet.tiles:
            self.pallet.select = self.pallet.tiles[0]
            self.active_tile_id = self.pallet.select.id

        self.history.clear()
        self.has_unsaved_changes = False

    def set_active_tile_id(self, tile_id: int):
        """Define o ID do tile ativo e atualiza a seleção na paleta."""
        self.active_tile_id = tile_id
        for tile in self.pallet.tiles:
            if tile.id == tile_id:
                self.pallet.select = tile
                self.notify_select.event()
                break

    def notify_change(self):
        """Notifica o grid para re-renderizar sua textura."""
        if self.grid:
            tool = self.tool_manager.active_tool
            preview = tool.get_preview_tiles(self, self.cursor_map_pos[0], self.cursor_map_pos[1])
            sel_bounds = tool.get_selected_bounds() if hasattr(tool, 'get_selected_bounds') else None
            self.grid.update_tiles(
                preview_tiles=preview,
                selection_bounds=sel_bounds,
                hover_cell=self.cursor_map_pos
            )

    def undo(self) -> bool:
        """Desfaz a última operação."""
        ok = self.history.undo()
        if ok:
            self.has_unsaved_changes = self.history.has_unsaved_changes()
            self.notify_change()
        return ok

    def redo(self) -> bool:
        """Refaz a operação desfeita."""
        ok = self.history.redo()
        if ok:
            self.has_unsaved_changes = self.history.has_unsaved_changes()
            self.notify_change()
        return ok

    def create_new_map(self, width: int = 200, height: int = 50):
        """Cria um novo mapa limpo."""
        self.level1.create_new_map(width, height)
        self.history.clear()
        self.has_unsaved_changes = True
        self.viewport.pan_x = 0
        self.viewport.pan_y = 0
        self.notify_change()

    def resize_map(self, new_width: int, new_height: int):
        """Redimensiona o mapa registrando comando de histórico."""
        cmd = ResizeMapCommand(self.level1, new_width, new_height)
        if self.history.execute(cmd):
            self.has_unsaved_changes = True
            self.notify_change()

    def handle_event(self, event) -> bool:
        """
        Ponto central e exclusivo de tratamento de eventos do Editor.
        Elimina duplicações de lógica entre cena e componentes.
        """
        # 1. Teclas e Atalhos Globais do Editor
        if event.type == pygame.KEYDOWN:
            mods = pygame.key.get_mods()
            ctrl = bool(mods & pygame.KMOD_CTRL or mods & pygame.KMOD_META)
            shift = bool(mods & pygame.KMOD_SHIFT)

            if ctrl and not shift and event.key == pygame.K_z:
                self.undo()
                return True
            elif (ctrl and event.key == pygame.K_y) or (ctrl and shift and event.key == pygame.K_z):
                self.redo()
                return True
            elif ctrl and event.key == pygame.K_c:
                tool = self.tool_manager.active_tool
                if hasattr(tool, 'copy'):
                    tool.copy(self)
                return True
            elif ctrl and event.key == pygame.K_x:
                tool = self.tool_manager.active_tool
                if hasattr(tool, 'cut'):
                    tool.cut(self)
                return True
            elif ctrl and event.key == pygame.K_v:
                tool = self.tool_manager.active_tool
                if hasattr(tool, 'paste'):
                    tool.paste(self, self.cursor_map_pos[0], self.cursor_map_pos[1])
                return True
            elif event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE:
                tool = self.tool_manager.active_tool
                if hasattr(tool, 'delete_selection'):
                    tool.delete_selection(self)
                return True
            elif event.key == pygame.K_b:
                self.tool_manager.set_tool("paint")
                return True
            elif event.key == pygame.K_e:
                self.tool_manager.set_tool("erase")
                return True
            elif event.key == pygame.K_g:
                self.tool_manager.set_tool("fill")
                return True
            elif event.key == pygame.K_u:
                self.tool_manager.set_tool("rectangle")
                return True
            elif event.key == pygame.K_m:
                self.tool_manager.set_tool("selection")
                return True
            elif event.key == pygame.K_i:
                self.tool_manager.set_tool("eyedropper")
                return True
            elif event.key == pygame.K_h:
                if self.grid:
                    self.grid.show_grid = not self.grid.show_grid
                    self.notify_change()
                return True
            elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                self.viewport.zoom_in()
                self.notify_change()
                return True
            elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                self.viewport.zoom_out()
                self.notify_change()
                return True

        # 2. Navegação por Teclado (Setas e WASD)
        if event.type == pygame.KEYDOWN:
            pan_step = int(self.viewport.current_tile_size * 2)
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.viewport.pan_x = max(0.0, self.viewport.pan_x - pan_step)
                self.notify_change()
                return True
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                max_pan_x = max(0.0, len(self.level1.tiles[0]) * self.viewport.current_tile_size - self.grid.size[0])
                self.viewport.pan_x = min(max_pan_x, self.viewport.pan_x + pan_step)
                self.notify_change()
                return True
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.viewport.pan_y = max(0.0, self.viewport.pan_y - pan_step)
                self.notify_change()
                return True
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                max_pan_y = max(0.0, len(self.level1.tiles) * self.viewport.current_tile_size - self.grid.size[1])
                self.viewport.pan_y = min(max_pan_y, self.viewport.pan_y + pan_step)
                self.notify_change()
                return True

        # 3. Zoom via Roda do Mouse
        if event.type == pygame.MOUSEWHEEL:
            if event.y > 0:
                self.viewport.zoom_in()
            elif event.y < 0:
                self.viewport.zoom_out()
            self.notify_change()
            return True

        # 4. Eventos de Mouse na Paleta
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            x, y = event.pos
            if self.pallet and self.pallet.rect.collidepoint(x, y):
                for tile in self.pallet.tiles:
                    l = self.pallet.rect.left + tile.rect.left
                    t = self.pallet.rect.top + tile.rect.top
                    r = pygame.Rect(l, t, tile.rect.w, tile.rect.h)
                    if r.collidepoint(x, y):
                        self.pallet.select = tile
                        self.active_tile_id = tile.id
                        self.notify_select.event()
                        # Ao escolher um bloco, ativa a ferramenta de pintura se estava em borracha/seleção
                        if self.tool_manager.active_tool_name in ("erase", "eyedropper"):
                            self.tool_manager.set_tool("paint")
                        return True

        # 5. Eventos de Mouse na Grade (Grid)
        if self.grid and hasattr(event, 'pos'):
            x, y = event.pos
            col, lin = self.viewport.screen_to_map(x, y, self.grid.rect)
            if col >= 0 and lin >= 0:
                self.cursor_map_pos = (col, lin)

            # Início de Arraste de Pan (Botão do meio ou Botão esquerdo + Espaço)
            keys = pygame.key.get_pressed()
            space_pressed = keys[pygame.K_SPACE]

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 2 or (event.button == 1 and space_pressed):
                    self.viewport.start_pan((x, y))
                    return True
                elif event.button == 1 and self.grid.rect.collidepoint(x, y):
                    self.tool_manager.active_tool.on_press(self, col, lin)
                    self.has_unsaved_changes = self.history.has_unsaved_changes() or getattr(self, 'has_unsaved_changes', False)
                    self.notify_change()
                    return True

            elif event.type == pygame.MOUSEMOTION:
                if self.viewport.is_panning:
                    self.viewport.update_pan((x, y))
                    self.notify_change()
                    return True
                elif event.buttons[0] and self.grid.rect.collidepoint(x, y) and not space_pressed:
                    self.tool_manager.active_tool.on_drag(self, col, lin)
                    self.notify_change()
                    return True
                elif self.grid.rect.collidepoint(x, y):
                    self.notify_change()

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button in (1, 2) and self.viewport.is_panning:
                    self.viewport.end_pan()
                    self.notify_change()
                    return True
                elif event.button == 1 and self.grid.rect.collidepoint(x, y):
                    self.tool_manager.active_tool.on_release(self, col, lin)
                    self.has_unsaved_changes = self.history.has_unsaved_changes()
                    self.notify_change()
                    return True

        return False

    def update(self, dt: float):
        if self.info and self.grid:
            self.info.update(dt, self.grid)
        if self.grid:
            self.grid.update(dt)
        if self.pallet:
            self.pallet.update(dt)

    def render(self):
        if self.bg:
            self.bg.draw()
        if self.info:
            self.info.draw()
        if self.grid:
            self.grid.draw()
        if self.pallet:
            self.pallet.draw()

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.render()
        pygame.display.flip()

    def run(self):
        self.running = True
        self.init_editor()
        while self.running:
            dt = display.game_tick()
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    self.running = False
                self.handle_event(event)
            self.update(dt)
            self.draw()


editor = Editor()
