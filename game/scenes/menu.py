"""Menu principal e telas de configuração do CTRL//REVOLT."""

import pygame

from game import config as cfg
from game.scenes.base import Scene
from game.systems.lan import PORT, LanSession
from game.world.scenery import IndustrialScenery


class MenuScene(Scene):
    def __init__(self, game, page="menu", message="", address=""):
        super().__init__(game)
        self.page = page
        self.message = message
        self.selected = 0
        self.address = address
        self.title_font = pygame.font.Font(None, 78)
        self.font = pygame.font.Font(None, 30)
        self.small = pygame.font.Font(None, 23)
        self.scenery = IndustrialScenery()

    def options(self):
        if self.page == "settings":
            return (
                (f"Volume dos efeitos  {self.game.volume}%", self.cycle_volume),
                ("Voltar", self.back),
            )
        if self.page == "client":
            return (("Conectar", self.connect), ("Voltar", self.back))
        return (
            ("Novo jogo", lambda: self.game.change_scene("gameplay")),
            ("Editor de fases", lambda: self.game.change_scene("editor")),
            ("Hospedar partida LAN", lambda: self.connect(host=True)),
            ("Entrar em partida LAN", lambda: self.game.change_scene("client")),
            ("Configurações", lambda: self.game.change_scene("settings")),
        )

    def back(self):
        if self.page == "menu":
            self.game.running = False
        else:
            self.game.change_scene("menu")

    def cycle_volume(self, direction=1):
        try:
            self.game.set_volume((self.game.volume + direction * 10) % 110)
        except OSError:
            self.message = "Não foi possível salvar o volume."
        else:
            self.message = ""

    def connect(self, host=False):
        try:
            session = LanSession(None if host else self.address.strip())
        except (OSError, ValueError):
            self.message = "Não foi possível abrir a porta LAN." if host else "Digite o IPv4 do servidor."
            return
        self.game.change_scene("gameplay", lan=session)

    def button(self, index):
        y = 227 if self.page == "client" else 177
        return pygame.Rect(62, y + index * 53, 370, 45)

    def handle_event(self, event):
        options = self.options()
        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
            for index, (_, action) in enumerate(options):
                if self.button(index).collidepoint(event.pos):
                    self.selected = index
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        action()
                    return
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self.back()
        elif event.key in (pygame.K_UP, pygame.K_DOWN):
            step = -1 if event.key == pygame.K_UP else 1
            self.selected = (self.selected + step) % len(options)
        elif event.key == pygame.K_RETURN:
            options[self.selected][1]()
        elif self.page == "settings" and self.selected == 0 and event.key in (pygame.K_LEFT, pygame.K_RIGHT):
            self.cycle_volume(-1 if event.key == pygame.K_LEFT else 1)
        elif self.page == "client":
            if event.key == pygame.K_BACKSPACE:
                self.address = self.address[:-1]
            elif len(event.unicode) == 1 and event.unicode in "0123456789." and len(self.address) < 15:
                self.address += event.unicode

    def update(self, dt):
        self.scenery.update(dt)

    def draw(self, surface):
        self.scenery.draw(surface, 0, [])
        panel = pygame.Surface((488, cfg.HEIGHT), pygame.SRCALPHA)
        panel.fill((*cfg.BG, 248))
        surface.blit(panel, (0, 0))
        pygame.draw.line(surface, cfg.PURPLE, (487, 0), (487, cfg.HEIGHT))
        heading = {"menu": "CTRL//REVOLT", "settings": "Configurações", "client": "Entrar na LAN"}
        surface.blit(self.title_font.render(heading[self.page], True, cfg.CYAN), (58, 58))
        if self.page == "menu":
            surface.blit(self.font.render("Industrial Cyber-Run", True, cfg.MAGENTA), (62, 124))
        elif self.page == "client":
            surface.blit(self.small.render(f"IPv4 do servidor  •  UDP {PORT}", True, cfg.INK), (62, 134))
            field = pygame.Rect(62, 160, 370, 44)
            pygame.draw.rect(surface, cfg.STEEL, field)
            address = self.address + "|" if self.address else "Ex. 192.168.1.10"
            color = cfg.INK if self.address else (171, 190, 218)
            surface.blit(self.font.render(address, True, color), (76, 172))
        for index, (label, _) in enumerate(self.options()):
            rect = self.button(index)
            active = index == self.selected
            pygame.draw.rect(surface, cfg.CYAN if active else cfg.STEEL, rect)
            surface.blit(self.font.render(label, True, cfg.BG if active else cfg.INK),
                         (rect.x + 15, rect.y + 11))
        hint = "Setas  Navegar     Enter  Selecionar     Esc  " + ("Sair" if self.page == "menu" else "Voltar")
        surface.blit(self.small.render(hint, True, cfg.INK), (62, 498))
        if self.message:
            surface.blit(self.small.render(self.message, True, cfg.YELLOW), (62, 455))
