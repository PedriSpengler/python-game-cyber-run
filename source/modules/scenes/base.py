from abc import ABC, abstractmethod


class Scene(ABC):
    """
    Classe base abstrata para todas as cenas do jogo (Padrão State).
    Define o contrato de ciclo de vida, eventos, atualização e renderização.
    """
    def __init__(self, manager=None):
        self.manager = manager
        self.is_overlay: bool = False  # True para cenas modais como PauseMenu

    def enter(self, params=None):
        """Inicializacao da cena e preparo de recursos especificos."""
        pass

    def exit(self):
        """Encerramento e liberacao dos recursos que a cena possui."""
        pass

    def handle_event(self, event) -> bool:
        """
        Trata um evento do Pygame. Retorna True se o evento foi consumido,
        impedindo que chegue a outras camadas.
        """
        return False

    def update(self, dt: float):
        """Atualizacao da logica da cena baseada no delta-time."""
        pass

    @abstractmethod
    def draw(self):
        """Renderizacao da cena no contexto OpenGL."""
        pass
