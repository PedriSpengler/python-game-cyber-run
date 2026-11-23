"""Loop principal; cada estado da aplicacao vive em uma cena separada."""

import pygame

from game import config as cfg
from game.systems.audio import Audio
from game.systems.preferences import read_data, write_data


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode(
            (cfg.WIDTH, cfg.HEIGHT),
            # SCALED amplia a imagem, preserva 16:9 e converte as coordenadas do mouse.
            pygame.SCALED | pygame.RESIZABLE | pygame.FULLSCREEN,
        )
        pygame.display.set_caption(cfg.TITLE)
        self.clock = pygame.time.Clock()
        self.audio = Audio()
        volume = read_data("volume.json", 100)
        self.volume = volume if type(volume) is int and volume in range(0, 101, 10) else 100
        self.audio.set_volume(self.volume)
        self.running = True
        self.scene = None
        self.editor = None
        self.change_scene("menu")

    def change_scene(self, name: str, **payload) -> None:
        if self.scene is not None:
            self.scene.close()
        if name in ("menu", "settings", "client"):
            from game.scenes.menu import MenuScene
            self.scene = MenuScene(self, page=name, **payload)
        elif name == "gameplay":
            from game.scenes.gameplay import GameplayScene
            self.scene = GameplayScene(self, **payload)
        elif name == "editor":
            from game.scenes.editor import EditorScene
            if self.editor is None:
                self.editor = EditorScene(self)
            self.scene = self.editor
        elif name == "result":
            from game.scenes.result import ResultScene
            self.scene = ResultScene(self, **payload)
        else:
            raise ValueError(f"Cena desconhecida: {name}")

    def set_volume(self, volume: int) -> None:
        write_data("volume.json", volume)
        self.volume = volume
        self.audio.set_volume(volume)

    def run(self) -> None:
        while self.running:
            dt = min(self.clock.tick(cfg.FPS) / 1000.0, 1 / 30)
            self.handle_events()
            if not self.running:
                break
            self.scene.update(dt)
            self.scene.draw(self.screen)
            pygame.display.flip()
        self.scene.close()
        pygame.quit()

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                break
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                pygame.display.toggle_fullscreen()
            else:
                self.scene.handle_event(event)
