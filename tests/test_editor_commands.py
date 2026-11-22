import unittest
import pygame
from source.modules.maker.commands import CommandHistory, TileChangeCommand, ResizeMapCommand
from source.modules.maker.tools import (
    ToolManager, PaintTool, EraseTool, FillTool, RectangleTool, SelectionTool, EyedropperTool
)
from source.modules.maker.viewport import EditorViewport
from source.modules.ui.levels import Level1


class MockTileMap:
    def __init__(self):
        # Cria alguns códigos de teste: ID 1 (Floor), ID 2 (Brick), ID 3 (Block)
        self.codes = [
            None,
            (1, pygame.Surface((32, 32)), "Floor"),
            (2, pygame.Surface((32, 32)), "Brick"),
            (3, pygame.Surface((32, 32)), "Block"),
        ]

    def get_shared_texture(self, tile_id, surf):
        return 100 + tile_id


class MockController:
    """Mock do controller do editor para testar as ferramentas de forma isolada."""
    def __init__(self, level):
        self.level = level
        self.active_tile_id = 2  # Brick
        self.history = CommandHistory(max_history=50)
        self.tool_manager = ToolManager()
        self.has_unsaved_changes = False
        self.notified = False

    def notify_change(self):
        self.notified = True

    def set_active_tile_id(self, tile_id):
        self.active_tile_id = tile_id


class TestEditorCommandsAndTools(unittest.TestCase):
    def setUp(self):
        self.tile_map = MockTileMap()
        self.level = Level1()
        self.level.tile_map = self.tile_map
        # Cria mapa 10x10 vazio
        self.level.create_new_map(width=10, height=10, default_floor=False)
        self.controller = MockController(self.level)

    def test_tile_change_command_undo_redo(self):
        """Valida a execução e reversão do comando atômico de alteração de tiles."""
        cmd = TileChangeCommand(self.level, [(2, 3, 0, 1), (2, 4, 0, 1)])
        self.controller.history.execute(cmd)

        self.assertEqual(self.level.get_tile_id(2, 3), 1)
        self.assertEqual(self.level.get_tile_id(2, 4), 1)

        # Desfazer
        self.controller.history.undo()
        self.assertEqual(self.level.get_tile_id(2, 3), 0)
        self.assertEqual(self.level.get_tile_id(2, 4), 0)

        # Refazer
        self.controller.history.redo()
        self.assertEqual(self.level.get_tile_id(2, 3), 1)
        self.assertEqual(self.level.get_tile_id(2, 4), 1)

    def test_command_history_unsaved_changes_tracking(self):
        """Valida que has_unsaved_changes reflete o estado do histórico."""
        history = self.controller.history
        self.assertFalse(history.has_unsaved_changes())

        cmd = TileChangeCommand(self.level, [(0, 0, 0, 2)])
        history.execute(cmd)
        self.assertTrue(history.has_unsaved_changes())

        # Salva
        history.mark_saved()
        self.assertFalse(history.has_unsaved_changes())

        # Desfaz: agora diverge do estado salvo!
        history.undo()
        self.assertTrue(history.has_unsaved_changes())

        # Refaz: volta ao estado salvo!
        history.redo()
        self.assertFalse(history.has_unsaved_changes())

    def test_paint_tool_continuous_stroke_grouping(self):
        """Garante que uma pincelada contínua de arrasto seja agrupada em um único Undo."""
        tool = PaintTool()
        self.controller.active_tile_id = 2

        # Pressiona e arrasta por 3 células
        tool.on_press(self.controller, 1, 1)
        tool.on_drag(self.controller, 1, 2)
        tool.on_drag(self.controller, 1, 3)
        tool.on_release(self.controller, 1, 3)

        self.assertEqual(self.level.get_tile_id(1, 1), 2)
        self.assertEqual(self.level.get_tile_id(1, 2), 2)
        self.assertEqual(self.level.get_tile_id(1, 3), 2)

        # Apenas 1 comando no histórico
        self.assertEqual(len(self.controller.history.undo_stack), 1)

        # Um único Undo reverte todas as 3 células
        self.controller.history.undo()
        self.assertEqual(self.level.get_tile_id(1, 1), 0)
        self.assertEqual(self.level.get_tile_id(1, 2), 0)
        self.assertEqual(self.level.get_tile_id(1, 3), 0)

    def test_erase_tool(self):
        """Valida a remoção de tiles e sua reversibilidade via Undo."""
        self.level.set_tile_id(5, 5, 3)
        self.assertEqual(self.level.get_tile_id(5, 5), 3)

        tool = EraseTool()
        tool.on_press(self.controller, 5, 5)
        tool.on_release(self.controller, 5, 5)

        self.assertEqual(self.level.get_tile_id(5, 5), 0)
        self.controller.history.undo()
        self.assertEqual(self.level.get_tile_id(5, 5), 3)

    def test_flood_fill_tool(self):
        """Valida o preenchimento de regiões contíguas por Flood Fill."""
        # Cria uma linha delimitadora com ID 1
        for c in range(10):
            self.level.set_tile_id(c, 5, 1)

        # Preenche a metade superior (linhas 0 a 4) com ID 3 a partir de (0, 0)
        self.controller.active_tile_id = 3
        fill_tool = FillTool()
        fill_tool.on_press(self.controller, 0, 0)

        # Toda a área superior deve ter virado 3
        for l in range(5):
            for c in range(10):
                self.assertEqual(self.level.get_tile_id(c, l), 3)

        # A linha delimitadora não deve ter sido alterada
        for c in range(10):
            self.assertEqual(self.level.get_tile_id(c, 5), 1)

        # A área inferior (linhas 6 a 9) continua vazia (0)
        for l in range(6, 10):
            for c in range(10):
                self.assertEqual(self.level.get_tile_id(c, l), 0)

        # Desfazer o fill restaura a área superior
        self.controller.history.undo()
        for l in range(5):
            for c in range(10):
                self.assertEqual(self.level.get_tile_id(c, l), 0)

    def test_rectangle_tool(self):
        """Valida o desenho de retângulo preenchido e contornado."""
        self.controller.active_tile_id = 2
        rect_tool = RectangleTool(filled=True)

        rect_tool.on_press(self.controller, 1, 1)
        rect_tool.on_drag(self.controller, 3, 3)
        rect_tool.on_release(self.controller, 3, 3)

        for l in range(1, 4):
            for c in range(1, 4):
                self.assertEqual(self.level.get_tile_id(c, l), 2)

        self.controller.history.undo()
        for l in range(1, 4):
            for c in range(1, 4):
                self.assertEqual(self.level.get_tile_id(c, l), 0)

    def test_selection_copy_cut_paste(self):
        """Valida as operações de seleção: copiar, colar e recortar."""
        self.level.set_tile_id(2, 2, 1)
        self.level.set_tile_id(3, 2, 2)

        sel_tool = SelectionTool()
        sel_tool.on_press(self.controller, 2, 2)
        sel_tool.on_drag(self.controller, 3, 2)
        sel_tool.on_release(self.controller, 3, 2)

        # Copiar
        self.assertTrue(sel_tool.copy(self.controller))
        self.assertEqual(sel_tool.clipboard, [[1, 2]])

        # Colar em (5, 5)
        self.assertTrue(sel_tool.paste(self.controller, target_col=5, target_lin=5))
        self.assertEqual(self.level.get_tile_id(5, 5), 1)
        self.assertEqual(self.level.get_tile_id(6, 5), 2)

        # Recortar a seleção original
        self.assertTrue(sel_tool.cut(self.controller))
        self.assertEqual(self.level.get_tile_id(2, 2), 0)
        self.assertEqual(self.level.get_tile_id(3, 2), 0)

    def test_eyedropper_tool(self):
        """Valida que o conta-gotas captura o ID correto e atualiza a ferramenta."""
        self.level.set_tile_id(4, 4, 3)
        eyedropper = EyedropperTool()

        eyedropper.on_press(self.controller, 4, 4)
        self.assertEqual(self.controller.active_tile_id, 3)
        self.assertEqual(self.controller.tool_manager.active_tool_name, "paint")

    def test_resize_map_command(self):
        """Valida o redimensionamento do mapa e preservação dos dados via Undo."""
        self.level.set_tile_id(1, 1, 2)

        cmd = ResizeMapCommand(self.level, new_w=15, new_h=12)
        self.controller.history.execute(cmd)

        self.assertEqual(len(self.level.tiles), 12)
        self.assertEqual(len(self.level.tiles[0]), 15)
        self.assertEqual(self.level.get_tile_id(1, 1), 2)

        # Reverte
        self.controller.history.undo()
        self.assertEqual(len(self.level.tiles), 10)
        self.assertEqual(len(self.level.tiles[0]), 10)
        self.assertEqual(self.level.get_tile_id(1, 1), 2)

    def test_editor_viewport_coordinates(self):
        """Valida a conversão de coordenadas com pan e zoom."""
        viewport = EditorViewport(cell_size=32)
        grid_rect = pygame.Rect(100, 50, 800, 600)

        # Zoom 1.0x, Pan (0, 0)
        col, lin = viewport.screen_to_map(132, 82, grid_rect)
        self.assertEqual(col, 1)
        self.assertEqual(lin, 1)

        # Zoom 2.0x (cell_size = 64)
        viewport.set_zoom(2.0)
        col, lin = viewport.screen_to_map(164, 114, grid_rect)
        self.assertEqual(col, 1)
        self.assertEqual(lin, 1)


if __name__ == '__main__':
    unittest.main()
