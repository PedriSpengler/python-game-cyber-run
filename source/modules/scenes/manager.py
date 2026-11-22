import pygame
from .base import Scene


class SceneManager:
    """
    Gerenciador Central de Cenas baseado no padrao State com pilha (Pushdown Automata).
    Controla o ciclo de vida, transicoes e sobreposicoes (ex: Menu de Pausa).
    """
    def __init__(self):
        self.scenes_registry: dict[str, type[Scene]] = {}
        self.scene_stack: list[Scene] = []
        self.running: bool = True

    def register(self, name: str, scene_class: type[Scene]):
        """Registra uma classe de cena na fábrica do gerenciador."""
        self.scenes_registry[name] = scene_class

    register_scene = register

    @property
    def stack(self) -> list[Scene]:
        return self.scene_stack

    def get_current_scene(self) -> Scene | None:
        return self.current_scene

    @property
    def current_scene(self) -> Scene | None:
        return self.scene_stack[-1] if self.scene_stack else None

    def change_scene(self, name: str, params=None):
        """
        Substitui toda a pilha pela nova cena especificada.
        Chama exit() em todas as cenas anteriores antes de descartar.
        """
        if name not in self.scenes_registry:
            raise KeyError(f"Cena '{name}' nao foi registrada no SceneManager.")

        # Desaloca recursos das cenas ativas na pilha
        while self.scene_stack:
            old_scene = self.scene_stack.pop()
            try:
                old_scene.exit()
            except Exception as e:
                print(f"Erro ao sair da cena {old_scene}: {e}")

        # Instancia e ativa a nova cena
        scene_cls = self.scenes_registry[name]
        new_scene = scene_cls(manager=self)
        self.scene_stack.append(new_scene)
        new_scene.enter(params)

    def push_scene(self, name: str, params=None):
        """
        Empilha uma cena sobre a atual (ex: Menu de Pausa).
        A cena anterior permanece intacta na memoria, preservando seu estado.
        """
        if name not in self.scenes_registry:
            raise KeyError(f"Cena '{name}' nao foi registrada no SceneManager.")

        scene_cls = self.scenes_registry[name]
        new_scene = scene_cls(manager=self)
        self.scene_stack.append(new_scene)
        new_scene.enter(params)

    def pop_scene(self):
        """
        Desempilha a cena do topo (ex: fechar Pausa), retomando a cena anterior.
        """
        if len(self.scene_stack) > 1:
            top_scene = self.scene_stack.pop()
            try:
                top_scene.exit()
            except Exception as e:
                print(f"Erro ao sair da cena {top_scene}: {e}")
        elif len(self.scene_stack) == 1:
            # Não desempilha a única cena existente sem trocar
            pass

    def handle_event(self, event):
        """Entrega o evento para a cena ativa no topo da pilha."""
        if event.type == pygame.QUIT:
            self.running = False
            return True

        if self.current_scene:
            return self.current_scene.handle_event(event)
        return False

    def update(self, dt: float):
        """Atualiza a logica da cena ativa no topo."""
        if self.current_scene:
            self.current_scene.update(dt)

    def draw(self):
        """
        Renderiza a cena. Se a cena do topo for um overlay modal (ex: Pausa),
        desenha primeiro a cena inferior e depois sobrepoe o menu.
        """
        if not self.scene_stack:
            return

        top = self.scene_stack[-1]
        if top.is_overlay and len(self.scene_stack) >= 2:
            # Desenha a cena de baixo (ex: o jogo congelado ao fundo)
            self.scene_stack[-2].draw()

        # Desenha a cena do topo
        top.draw()

    def quit(self):
        """Encerra o loop da aplicacao."""
        self.running = False
