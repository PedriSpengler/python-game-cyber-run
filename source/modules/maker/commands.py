from abc import ABC, abstractmethod
from typing import Any


class IEditCommand(ABC):
    """Interface abstrata para o padrão de projeto Command no Level Editor."""

    @abstractmethod
    def execute(self) -> bool:
        """Executa a operação. Retorna True se houve alteração efetiva."""
        pass

    @abstractmethod
    def undo(self) -> bool:
        """Reverte a operação realizada pelo execute()."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Descrição legível da ação (ex.: 'Pintar Bloco', 'Preenchimento')."""
        pass


class TileChangeCommand(IEditCommand):
    """
    Comando que registra alterações pontuais ou em lote na grade de tiles.
    IMPORTANTE: Armazena apenas coordenadas e IDs estáveis (inteiros),
    desacoplado de instâncias de Tile e de recursos OpenGL da GPU.
    """
    def __init__(self, level, changes: list[tuple[int, int, int, int]], description: str = "Alterar Tiles"):
        """
        :param level: Instância de Level1 contendo a matriz de tiles e referência ao tile_map.
        :param changes: Lista de tuplas (col, lin, old_id, new_id).
        :param description: Nome descritivo da ação.
        """
        self.level = level
        # Filtra apenas mudanças onde old_id != new_id para otimizar memória e histórico
        self.changes = [c for c in changes if c[2] != c[3]]
        self._desc = description

    @property
    def description(self) -> str:
        return self._desc

    def execute(self) -> bool:
        if not self.changes:
            return False
        for col, lin, _, new_id in self.changes:
            self.level.set_tile_id(col, lin, new_id)
        return True

    def undo(self) -> bool:
        if not self.changes:
            return False
        # Reverte na ordem inversa para consistência
        for col, lin, old_id, _ in reversed(self.changes):
            self.level.set_tile_id(col, lin, old_id)
        return True


class ResizeMapCommand(IEditCommand):
    """
    Comando estrutural de redimensionamento do mapa.
    Armazena o snapshot das dimensões e a matriz de IDs antes e depois.
    """
    def __init__(self, level, new_w: int, new_h: int, description: str = "Redimensionar Mapa"):
        self.level = level
        self.new_w = new_w
        self.new_h = new_h
        self.old_w = len(level.tiles[0]) if level.tiles and len(level.tiles) > 0 else 0
        self.old_h = len(level.tiles) if level.tiles else 0
        self.old_ids: list[list[int]] = []
        self._desc = description

        # Captura snapshot dos IDs anteriores
        for row in level.tiles:
            self.old_ids.append([t.id if t is not None else 0 for t in row])

    @property
    def description(self) -> str:
        return self._desc

    def execute(self) -> bool:
        if self.new_w == self.old_w and self.new_h == self.old_h:
            return False
        self.level.resize_matrix(self.new_w, self.new_h)
        return True

    def undo(self) -> bool:
        self.level.resize_matrix(self.old_w, self.old_h)
        # Restaura os IDs anteriores nas posições
        for lin in range(min(self.old_h, len(self.level.tiles))):
            for col in range(min(self.old_w, len(self.level.tiles[lin]))):
                self.level.set_tile_id(col, lin, self.old_ids[lin][col])
        return True


class CommandHistory:
    """
    Gerenciador do histórico de operações (Undo/Redo) com limite configurável.
    Controla com precisão o estado de alterações não salvas (clean_index).
    """
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.undo_stack: list[IEditCommand] = []
        self.redo_stack: list[IEditCommand] = []
        self.clean_index: int = 0  # Índice da pilha no momento do último salvamento

    def execute(self, command: IEditCommand) -> bool:
        """Executa um comando e o adiciona à pilha de desfazer."""
        if command.execute():
            self.undo_stack.append(command)
            self.redo_stack.clear()

            # Descarta comandos mais antigos se ultrapassar o limite configurado
            if len(self.undo_stack) > self.max_history:
                self.undo_stack.pop(0)
                if self.clean_index is not None:
                    self.clean_index -= 1

            return True
        return False

    def undo(self) -> bool:
        """Desfaz a última operação registrada."""
        if not self.can_undo():
            return False
        cmd = self.undo_stack.pop()
        if cmd.undo():
            self.redo_stack.append(cmd)
            return True
        return False

    def redo(self) -> bool:
        """Refaz a operação desfeita mais recente."""
        if not self.can_redo():
            return False
        cmd = self.redo_stack.pop()
        if cmd.execute():
            self.undo_stack.append(cmd)
            return True
        return False

    def can_undo(self) -> bool:
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        return len(self.redo_stack) > 0

    def mark_saved(self):
        """Marca o estado atual como salvo no disco."""
        self.clean_index = len(self.undo_stack)

    def has_unsaved_changes(self) -> bool:
        """Retorna True se o estado atual diverge do último estado salvo."""
        return len(self.undo_stack) != self.clean_index

    def clear(self):
        """Limpa todo o histórico."""
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.clean_index = 0
