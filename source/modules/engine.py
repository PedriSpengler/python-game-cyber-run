import pygame
from .display import display
from .game import game
from OpenGL.GL import *
from .config.sounds import sounds
from .config.settings import settings
from .scenes.manager import SceneManager
from .scenes.main_menu import MainMenuScene
from .scenes.game_scene import GameScene
from .scenes.editor_scene import EditorScene
from .scenes.pause_menu import PauseMenuScene
from .scenes.settings_scene import SettingsScene
from .scenes.multiplayer_menu import MultiplayerMenuScene
from .scenes.lobby_scene import LobbyScene

class GameEngine:
    """A Engine Pura: Controla o ciclo de vida, janelas, eventos e loops através do SceneManager."""
    def __init__(self):
        self.initialized = False
        self.scene_manager = SceneManager()

    def initialize(self):
        if not self.initialized:
            display.create_display()
            if not pygame.font.get_init():
                pygame.font.init()
            sounds.load_assets()
            settings.apply()

            # Registra todas as cenas na arquitetura baseada em State
            self.scene_manager.register("main_menu", MainMenuScene)
            self.scene_manager.register("game", GameScene)
            self.scene_manager.register("editor", EditorScene)
            self.scene_manager.register("pause", PauseMenuScene)
            self.scene_manager.register("settings", SettingsScene)
            self.scene_manager.register("multiplayer_menu", MultiplayerMenuScene)
            self.scene_manager.register("lobby", LobbyScene)

            self.initialized = True

    def run(self, initial_scene: str = "main_menu"):
        """O Game Loop Principal centralizado pelo SceneManager."""
        self.initialize()
        self.scene_manager.change_scene(initial_scene)

        try:           
            while self.scene_manager.running:
                dt = display.game_tick()                
                
                # Consumo centralizado e ordenado da fila de eventos
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.scene_manager.running = False
                        break
                    self.scene_manager.handle_event(event)

                self.scene_manager.update(dt)
                
                # Renderizacao
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                self.scene_manager.draw()
                pygame.display.flip()

        except Exception as e:
            print(f"Exceção no Game Loop: {e}")
        finally:
            pygame.quit()
        
engine = GameEngine() # singleton 