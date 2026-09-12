"""Loop principal; cada estado da aplicacao vive em uma cena separada."""

import pygame

from game import config as cfg
from game.systems.audio import Audio


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((cfg.WIDTH, cfg.HEIGHT))
        pygame.display.set_caption(cfg.TITLE)
        self.clock = pygame.time.Clock()
        self.audio = Audio()
        self.running = True
        self.scene = None
        self.change_scene("menu")

    def change_scene(self, name: str, **payload) -> None:
        if name == "menu":
            from game.scenes.menu import MenuScene
            self.scene = MenuScene(self)
        elif name == "gameplay":
            from game.scenes.gameplay import GameplayScene
            self.scene = GameplayScene(self)
        elif name == "result":
            from game.scenes.result import ResultScene
            self.scene = ResultScene(self, **payload)
        else:
            raise ValueError(f"Cena desconhecida: {name}")

    def run(self) -> None:
        while self.running:
            dt = min(self.clock.tick(cfg.FPS) / 1000.0, 1 / 30)
            self.handle_events()
            self.scene.update(dt)
            self.scene.draw(self.screen)
            pygame.display.flip()
        pygame.quit()

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            else:
                self.scene.handle_event(event)
