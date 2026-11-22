import pygame
from .base import Scene
from .ui_widgets import MenuButton, MenuLabel
from ..maker.editor import editor
from ..constants import WIDTH, HEIGHT
from ..utils import utils


class EditorScene(Scene):
    """
    Cena do Level Editor do TAC3.
    Integra a interface do usuário retrô (barra superior de ações, barra lateral de ferramentas,
    painel de informações e status) com o controlador central Editor.
    Suporta criação, edição, histórico (Undo/Redo), persistência e Playtest integrado.
    """
    def __init__(self, manager=None):
        super().__init__(manager)
        self.top_buttons: list[MenuButton] = []
        self.tool_buttons: list[MenuButton] = []
        self.labels: list[MenuLabel] = []
        self.editor = editor
        self.status_timer: float = 0.0

    def enter(self, params=None):
        # Inicializa o editor apenas se ainda não estiver pronto (preserva o estado após Playtest)
        if self.editor.grid is None:
            self.editor.init_editor()

        self._build_ui()

    def _build_ui(self):
        self._destroy_ui()

        # 1. Barra Superior de Ações
        btn_w = 130
        btn_h = 38
        top_y = 10
        spacing = 138
        x = WIDTH - 20 - (6 * spacing)

        self.btn_new = MenuButton("NOVO", x, top_y, btn_w, btn_h, on_click=self._on_new, font_size=20)
        self.btn_save = MenuButton("SALVAR", x + spacing, top_y, btn_w, btn_h, on_click=self._on_save, font_size=20)
        self.btn_undo = MenuButton("DESFAZER", x + (2 * spacing), top_y, btn_w, btn_h, on_click=self._on_undo, font_size=20)
        self.btn_redo = MenuButton("REFAZER", x + (3 * spacing), top_y, btn_w, btn_h, on_click=self._on_redo, font_size=20)
        self.btn_playtest = MenuButton("TESTAR (F5)", x + (4 * spacing), top_y, btn_w, btn_h, on_click=self._on_playtest, font_size=20)
        self.btn_back = MenuButton("VOLTAR", x + (5 * spacing), top_y, btn_w, btn_h, on_click=self._on_back, font_size=20)

        self.top_buttons = [
            self.btn_new, self.btn_save, self.btn_undo, self.btn_redo,
            self.btn_playtest, self.btn_back
        ]

        # 2. Barra Lateral Esquerda de Ferramentas
        tool_w = 150
        tool_h = 36
        tool_x = 16
        tool_start_y = 90
        tool_spacing = 44

        tools_def = [
            ("LAPIS (B)", lambda: self._select_tool("paint")),
            ("BORRACHA (E)", lambda: self._select_tool("erase")),
            ("BALDE (G)", lambda: self._select_tool("fill")),
            ("RETANGULO (U)", lambda: self._select_tool("rectangle")),
            ("SELECAO (M)", lambda: self._select_tool("selection")),
            ("CONTA-GOTAS (I)", lambda: self._select_tool("eyedropper")),
            ("ZOOM +", self._zoom_in),
            ("ZOOM -", self._zoom_out),
            ("GRADE (H)", self._toggle_grid),
        ]

        self.tool_buttons = []
        for i, (name, cb) in enumerate(tools_def):
            ty = tool_start_y + (i * tool_spacing)
            btn = MenuButton(name, tool_x, ty, tool_w, tool_h, on_click=cb, font_size=18)
            self.tool_buttons.append(btn)

        # 3. Rótulos Informativos
        self.lbl_title = MenuLabel("TAC3 LEVEL MAKER", 20, 16, font_size=26, color="#FFD700")
        self.lbl_status = MenuLabel("", WIDTH / 2 - 150, 18, font_size=20, color="#00FF00", center=True)
        self.lbl_info = MenuLabel("", 20, HEIGHT - 32, font_size=20, color="#CCCCCC")

        self.labels = [self.lbl_title, self.lbl_status, self.lbl_info]

    def _select_tool(self, name: str):
        self.editor.tool_manager.set_tool(name)
        self.editor.notify_change()

    def _zoom_in(self):
        self.editor.viewport.zoom_in()
        self.editor.notify_change()

    def _zoom_out(self):
        self.editor.viewport.zoom_out()
        self.editor.notify_change()

    def _toggle_grid(self):
        if self.editor.grid:
            self.editor.grid.show_grid = not self.editor.grid.show_grid
            self.editor.notify_change()

    def _on_new(self):
        self.editor.create_new_map()
        self.lbl_status.set_text("NOVO MAPA CRIADO!")
        self.status_timer = 3.0

    def _on_save(self):
        try:
            ok = self.editor.level1.save()
            if ok:
                self.editor.history.mark_saved()
                self.editor.has_unsaved_changes = False
                self.lbl_status.set_text("MAPA SALVO COM SUCESSO!")
            else:
                self.lbl_status.set_text("ERRO AO SALVAR MAPA.")
            self.status_timer = 3.0
        except Exception as e:
            self.lbl_status.set_text(f"ERRO: {e}")
            self.status_timer = 3.0

    def _on_undo(self):
        if self.editor.undo():
            self.lbl_status.set_text("DESFEITO")
            self.status_timer = 1.5

    def _on_redo(self):
        if self.editor.redo():
            self.lbl_status.set_text("REFEITO")
            self.status_timer = 1.5

    def _on_playtest(self):
        """Inicia o Playtest utilizando a fase atual sem tocar nos arquivos originais."""
        if self.manager:
            self.manager.push_scene("game", params={"playtest": True, "level": self.editor.level1})

    def _on_back(self):
        # Se houver alterações não salvas, salva preventivamente para evitar perda de dados
        if self.editor.has_unsaved_changes:
            self.editor.level1.save()
        if self.manager:
            self.manager.change_scene("main_menu")

    def handle_event(self, event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F5:
                self._on_playtest()
                return True
            elif event.key == pygame.K_ESCAPE:
                self._on_back()
                return True

        # Processa botões da barra superior
        for btn in self.top_buttons:
            if btn.handle_event(event):
                return True

        # Processa botões de ferramentas
        for btn in self.tool_buttons:
            if btn.handle_event(event):
                return True

        # Centralização: Todos os demais eventos são delegados ao Editor
        return self.editor.handle_event(event)

    def update(self, dt: float):
        if self.status_timer > 0:
            self.status_timer -= dt
            if self.status_timer <= 0:
                self.lbl_status.set_text("")

        self.editor.update(dt)

        # Atualiza texto da barra de informações
        tool_name = self.editor.tool_manager.active_tool_name.upper()
        cx, cy = self.editor.cursor_map_pos
        zoom_val = self.editor.viewport.zoom
        w = len(self.editor.level1.tiles[0]) if self.editor.level1.tiles and len(self.editor.level1.tiles) > 0 else 0
        h = len(self.editor.level1.tiles) if self.editor.level1.tiles else 0
        unsaved_flag = " *" if self.editor.has_unsaved_changes else ""

        self.lbl_title.set_text(f"TAC3 LEVEL MAKER{unsaved_flag}")
        info_str = f"FERRAMENTA: {tool_name} | CURSOR: ({cx}, {cy}) | ZOOM: {zoom_val:.2f}x | DIMENSOES: {w}x{h}"
        self.lbl_info.set_text(info_str)

    def draw(self):
        # 1. Renderiza os componentes principais do editor (Background, Info, Grid, Pallet)
        self.editor.render()

        # 2. Barra Superior (fundo escuro e friso dourado)
        utils.draw_colored_quad(0, 0, WIDTH, 58, (0.03, 0.04, 0.08, 0.95))
        utils.draw_colored_quad(0, 56, WIDTH, 2, (1.0, 0.84, 0.0, 0.9))

        # 3. Painel Lateral Esquerdo de Ferramentas
        utils.draw_colored_quad(8, 70, 166, 440, (0.04, 0.05, 0.1, 0.85))
        utils.draw_colored_quad(8, 70, 166, 2, (0.2, 0.5, 0.8, 0.8))

        # 4. Barra Inferior de Informações
        utils.draw_colored_quad(0, HEIGHT - 40, WIDTH, 40, (0.03, 0.04, 0.08, 0.9))
        utils.draw_colored_quad(0, HEIGHT - 40, WIDTH, 1, (0.3, 0.3, 0.3, 0.8))

        # 5. Renderiza rótulos e botões interativos
        for label in self.labels:
            label.draw()

        for btn in self.top_buttons:
            btn.draw()

        for btn in self.tool_buttons:
            btn.draw()

    def _destroy_ui(self):
        for btn in self.top_buttons:
            btn.destroy()
        self.top_buttons.clear()

        for btn in self.tool_buttons:
            btn.destroy()
        self.tool_buttons.clear()

        for label in self.labels:
            label.destroy()
        self.labels.clear()

    def exit(self):
        self._destroy_ui()
