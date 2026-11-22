from abc import ABC, abstractmethod
from collections import deque
from .commands import TileChangeCommand


class IEditorTool(ABC):
    """Interface abstrata para o padrão Strategy de ferramentas do Editor."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def on_press(self, controller, col: int, lin: int):
        pass

    @abstractmethod
    def on_drag(self, controller, col: int, lin: int):
        pass

    @abstractmethod
    def on_release(self, controller, col: int, lin: int):
        pass

    def get_preview_tiles(self, controller, current_col: int, current_lin: int) -> list[tuple[int, int, int]]:
        """Retorna lista de (col, lin, tile_id) para desenhar pré-visualização na tela."""
        return []


class PaintTool(IEditorTool):
    """
    Ferramenta de Pintura (Lápis).
    Permite cliques pontuais e pinceladas contínuas com o botão pressionado.
    Agrupa toda a pincelada contínua em uma única operação de histórico.
    """
    def __init__(self):
        super().__init__("paint")
        self.stroke_changes: dict[tuple[int, int], tuple[int, int]] = {}
        self.is_painting: bool = False

    def on_press(self, controller, col: int, lin: int):
        if col < 0 or lin < 0:
            return
        self.is_painting = True
        self.stroke_changes.clear()
        self._record_cell(controller, col, lin)

    def on_drag(self, controller, col: int, lin: int):
        if self.is_painting and col >= 0 and lin >= 0:
            self._record_cell(controller, col, lin)

    def on_release(self, controller, col: int, lin: int):
        if not self.is_painting:
            return
        self.is_painting = False

        if self.stroke_changes:
            # Lista de (col, lin, old_id, new_id)
            changes = [
                (c, l, old_id, new_id)
                for (c, l), (old_id, new_id) in self.stroke_changes.items()
            ]
            cmd = TileChangeCommand(controller.level, changes, description="Pintar Tiles")
            # As alterações visuais já foram aplicadas durante a pincelada;
            # adicionamos diretamente à pilha de undo do histórico
            controller.history.undo_stack.append(cmd)
            controller.history.redo_stack.clear()
            controller.has_unsaved_changes = True
            self.stroke_changes.clear()

    def _record_cell(self, controller, col: int, lin: int):
        key = (col, lin)
        target_tile_id = controller.active_tile_id
        if target_tile_id is None:
            return

        old_id = controller.level.get_tile_id(col, lin)
        if old_id != target_tile_id and key not in self.stroke_changes:
            self.stroke_changes[key] = (old_id, target_tile_id)
            controller.level.set_tile_id(col, lin, target_tile_id)
            controller.notify_change()


class EraseTool(IEditorTool):
    """
    Ferramenta de Borracha.
    Remove blocos (ID 0) com suporte a cliques pontuais e arrasto contínuo,
    agrupando em uma única operação de histórico reversível.
    """
    def __init__(self):
        super().__init__("erase")
        self.stroke_changes: dict[tuple[int, int], tuple[int, int]] = {}
        self.is_erasing: bool = False

    def on_press(self, controller, col: int, lin: int):
        if col < 0 or lin < 0:
            return
        self.is_erasing = True
        self.stroke_changes.clear()
        self._record_cell(controller, col, lin)

    def on_drag(self, controller, col: int, lin: int):
        if self.is_erasing and col >= 0 and lin >= 0:
            self._record_cell(controller, col, lin)

    def on_release(self, controller, col: int, lin: int):
        if not self.is_erasing:
            return
        self.is_erasing = False

        if self.stroke_changes:
            changes = [
                (c, l, old_id, new_id)
                for (c, l), (old_id, new_id) in self.stroke_changes.items()
            ]
            cmd = TileChangeCommand(controller.level, changes, description="Apagar Tiles")
            controller.history.undo_stack.append(cmd)
            controller.history.redo_stack.clear()
            controller.has_unsaved_changes = True
            self.stroke_changes.clear()

    def _record_cell(self, controller, col: int, lin: int):
        key = (col, lin)
        old_id = controller.level.get_tile_id(col, lin)
        if old_id != 0 and key not in self.stroke_changes:
            self.stroke_changes[key] = (old_id, 0)
            controller.level.set_tile_id(col, lin, 0)
            controller.notify_change()


class FillTool(IEditorTool):
    """
    Ferramenta Balde de Tinta (Flood Fill).
    Preenche a região contígua com mesmo ID usando busca em largura (BFS) iterativa,
    evitando estouro de pilha de recursão em mapas grandes.
    """
    def __init__(self):
        super().__init__("fill")

    def on_press(self, controller, col: int, lin: int):
        if col < 0 or lin < 0:
            return

        target_new_id = controller.active_tile_id
        if target_new_id is None:
            return

        target_old_id = controller.level.get_tile_id(col, lin)
        if target_old_id == target_new_id:
            return

        max_h = len(controller.level.tiles)
        max_w = len(controller.level.tiles[0]) if max_h > 0 else 0
        if not (0 <= lin < max_h and 0 <= col < max_w):
            return

        # BFS iterativo
        visited = set()
        queue = deque([(col, lin)])
        visited.add((col, lin))
        changes = []

        while queue:
            c, l = queue.popleft()
            changes.append((c, l, target_old_id, target_new_id))

            for dc, dl in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nc, nl = c + dc, l + dl
                if 0 <= nc < max_w and 0 <= nl < max_h:
                    if (nc, nl) not in visited:
                        if controller.level.get_tile_id(nc, nl) == target_old_id:
                            visited.add((nc, nl))
                            queue.append((nc, nl))

        if changes:
            cmd = TileChangeCommand(controller.level, changes, description="Preenchimento")
            controller.history.execute(cmd)
            controller.has_unsaved_changes = True
            controller.notify_change()

    def on_drag(self, controller, col: int, lin: int):
        pass

    def on_release(self, controller, col: int, lin: int):
        pass


class RectangleTool(IEditorTool):
    """
    Ferramenta de Desenho de Retângulos.
    Permite criar blocos retangulares preenchidos ou vazados (contornados).
    """
    def __init__(self, filled: bool = True):
        super().__init__("rectangle")
        self.filled = filled
        self.start_pos: tuple[int, int] = None
        self.current_pos: tuple[int, int] = None
        self.is_drawing: bool = False

    def on_press(self, controller, col: int, lin: int):
        if col >= 0 and lin >= 0:
            self.is_drawing = True
            self.start_pos = (col, lin)
            self.current_pos = (col, lin)

    def on_drag(self, controller, col: int, lin: int):
        if self.is_drawing and col >= 0 and lin >= 0:
            self.current_pos = (col, lin)

    def on_release(self, controller, col: int, lin: int):
        if not self.is_drawing or not self.start_pos or not self.current_pos:
            self.is_drawing = False
            return

        target_new_id = controller.active_tile_id
        if target_new_id is None:
            self.is_drawing = False
            return

        sc, sl = self.start_pos
        ec, el = self.current_pos
        c1, c2 = min(sc, ec), max(sc, ec)
        l1, l2 = min(sl, el), max(sl, el)

        max_h = len(controller.level.tiles)
        max_w = len(controller.level.tiles[0]) if max_h > 0 else 0

        changes = []
        for l in range(max(0, l1), min(max_h, l2 + 1)):
            for c in range(max(0, c1), min(max_w, c2 + 1)):
                if not self.filled:
                    # Apenas contorno
                    if c not in (c1, c2) and l not in (l1, l2):
                        continue
                old_id = controller.level.get_tile_id(c, l)
                if old_id != target_new_id:
                    changes.append((c, l, old_id, target_new_id))

        if changes:
            cmd = TileChangeCommand(controller.level, changes, description="Desenhar Retângulo")
            controller.history.execute(cmd)
            controller.has_unsaved_changes = True
            controller.notify_change()

        self.is_drawing = False
        self.start_pos = None
        self.current_pos = None

    def get_preview_tiles(self, controller, current_col: int, current_lin: int) -> list[tuple[int, int, int]]:
        if not self.is_drawing or not self.start_pos:
            return []
        sc, sl = self.start_pos
        ec, el = current_col, current_lin
        c1, c2 = min(sc, ec), max(sc, ec)
        l1, l2 = min(sl, el), max(sl, el)
        target_id = controller.active_tile_id or 1

        previews = []
        for l in range(l1, l2 + 1):
            for c in range(c1, c2 + 1):
                if not self.filled and c not in (c1, c2) and l not in (l1, l2):
                    continue
                previews.append((c, l, target_id))
        return previews


class EyedropperTool(IEditorTool):
    """
    Ferramenta Conta-gotas.
    Captura o ID do tile sob o cursor, atualiza a paleta e reativa a ferramenta de pintura.
    """
    def __init__(self):
        super().__init__("eyedropper")

    def on_press(self, controller, col: int, lin: int):
        if col < 0 or lin < 0:
            return
        tile_id = controller.level.get_tile_id(col, lin)
        if tile_id > 0:
            controller.set_active_tile_id(tile_id)
            controller.tool_manager.set_tool("paint")

    def on_drag(self, controller, col: int, lin: int):
        pass

    def on_release(self, controller, col: int, lin: int):
        pass


class SelectionTool(IEditorTool):
    """
    Ferramenta de Seleção e Manipulação.
    Permite selecionar regiões retangulares, copiar, recortar, colar e excluir.
    """
    def __init__(self):
        super().__init__("selection")
        self.start_pos: tuple[int, int] = None
        self.end_pos: tuple[int, int] = None
        self.is_selecting: bool = False
        self.clipboard: list[list[int]] = []  # Submatriz de IDs copiada

    def on_press(self, controller, col: int, lin: int):
        if col >= 0 and lin >= 0:
            self.is_selecting = True
            self.start_pos = (col, lin)
            self.end_pos = (col, lin)

    def on_drag(self, controller, col: int, lin: int):
        if self.is_selecting and col >= 0 and lin >= 0:
            self.end_pos = (col, lin)

    def on_release(self, controller, col: int, lin: int):
        if self.is_selecting and col >= 0 and lin >= 0:
            self.end_pos = (col, lin)
            self.is_selecting = False

    def get_selected_bounds(self) -> tuple[int, int, int, int]:
        """Retorna (min_col, min_lin, max_col, max_lin) ou None."""
        if not self.start_pos or not self.end_pos:
            return None
        c1, c2 = min(self.start_pos[0], self.end_pos[0]), max(self.start_pos[0], self.end_pos[0])
        l1, l2 = min(self.start_pos[1], self.end_pos[1]), max(self.start_pos[1], self.end_pos[1])
        return c1, l1, c2, l2

    def copy(self, controller) -> bool:
        """Copia a submatriz selecionada para a área de transferência."""
        bounds = self.get_selected_bounds()
        if not bounds:
            return False
        c1, l1, c2, l2 = bounds
        self.clipboard = []
        for l in range(l1, l2 + 1):
            row = []
            for c in range(c1, c2 + 1):
                row.append(controller.level.get_tile_id(c, l))
            self.clipboard.append(row)
        return True

    def cut(self, controller) -> bool:
        """Recorta a submatriz selecionada, copiando e apagando da fase via Undo/Redo."""
        if self.copy(controller):
            return self.delete_selection(controller)
        return False

    def delete_selection(self, controller) -> bool:
        """Apaga os tiles dentro da seleção atual."""
        bounds = self.get_selected_bounds()
        if not bounds:
            return False
        c1, l1, c2, l2 = bounds
        changes = []
        for l in range(l1, l2 + 1):
            for c in range(c1, c2 + 1):
                old_id = controller.level.get_tile_id(c, l)
                if old_id != 0:
                    changes.append((c, l, old_id, 0))
        if changes:
            cmd = TileChangeCommand(controller.level, changes, description="Excluir Seleção")
            controller.history.execute(cmd)
            controller.has_unsaved_changes = True
            controller.notify_change()
            return True
        return False

    def paste(self, controller, target_col: int, target_lin: int) -> bool:
        """Cola os tiles do clipboard a partir de (target_col, target_lin) via Undo/Redo."""
        if not self.clipboard or target_col < 0 or target_lin < 0:
            return False

        max_h = len(controller.level.tiles)
        max_w = len(controller.level.tiles[0]) if max_h > 0 else 0

        changes = []
        for dl, row in enumerate(self.clipboard):
            for dc, new_id in enumerate(row):
                c = target_col + dc
                l = target_lin + dl
                if 0 <= c < max_w and 0 <= l < max_h:
                    old_id = controller.level.get_tile_id(c, l)
                    if old_id != new_id:
                        changes.append((c, l, old_id, new_id))

        if changes:
            cmd = TileChangeCommand(controller.level, changes, description="Colar Tiles")
            controller.history.execute(cmd)
            controller.has_unsaved_changes = True
            controller.notify_change()
            return True
        return False


class ToolManager:
    """Gerenciador de ferramentas e atalhos de teclado."""
    def __init__(self):
        self.tools: dict[str, IEditorTool] = {
            "paint": PaintTool(),
            "erase": EraseTool(),
            "fill": FillTool(),
            "rectangle": RectangleTool(filled=True),
            "selection": SelectionTool(),
            "eyedropper": EyedropperTool(),
        }
        self.active_tool_name: str = "paint"

    @property
    def active_tool(self) -> IEditorTool:
        return self.tools[self.active_tool_name]

    def set_tool(self, name: str):
        if name in self.tools:
            self.active_tool_name = name
