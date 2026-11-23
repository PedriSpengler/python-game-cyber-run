"""Editor local da fase e entrada para o teste jogável."""

from dataclasses import asdict, replace

import pygame

from game import config as cfg
from game.scenes.base import Scene
from game.systems.preferences import read_data, write_data
from game.world.scenery import IndustrialScenery
from game.world.stage_data import EnemySpawn, ItemSpawn, LEGACY_CODE_DUNGEON

FILENAME = "custom-stage.json"
TOOLS = ("Plataforma", "Início", "Saída", "Inimigo", "Item")


def load_stage():
    base = replace(LEGACY_CODE_DUNGEON, name="FASE PERSONALIZADA")
    data = read_data(FILENAME)
    try:
        start = tuple(data["start"])
        exit_x = data["exit_x"]
        platforms = tuple(tuple(rect) for rect in data["platforms"])
        enemies = tuple(EnemySpawn(**spawn) for spawn in data["enemies"])
        items = tuple(ItemSpawn(**spawn) for spawn in data["items"])
        if not valid_point(*start, base.width):
            return base
        if not valid_point(exit_x, 0, base.width):
            return base
        for x, y, width, height in platforms:
            if not valid_point(x, y, base.width):
                return base
            if type(width) is not int or type(height) is not int:
                return base
            if not 0 < width <= base.width - x or not 0 < height <= cfg.HEIGHT:
                return base
        for spawn in enemies:
            if (not valid_point(spawn.x, spawn.y, base.width)
                    or type(spawn.patrol_left) is not int or type(spawn.patrol_right) is not int
                    or not 0 <= spawn.patrol_left <= spawn.x <= spawn.patrol_right <= base.width):
                return base
        for item in items:
            if not valid_point(item.x, item.y, base.width) or item.kind not in ("data", "patch"):
                return base
        return replace(base, start=start, exit_x=exit_x, platforms=platforms,
                       enemies=enemies, items=items)
    except (KeyError, TypeError, ValueError):
        return base


def valid_point(x, y, width):
    return type(x) is int and type(y) is int and 0 <= x < width and 0 <= y < cfg.HEIGHT


class EditorScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.stage = load_stage()
        self.camera = 0
        self.drag_start = None
        self.tool = 0
        self.history = []
        self.message = ""
        self.scenery = IndustrialScenery()
        self.font = pygame.font.Font(None, 23)
        self.buttons = [(name, lambda i=i: self.select(i)) for i, name in enumerate(TOOLS)]
        self.buttons += [("Salvar", self.save), ("Testar", self.play), ("Menu", self.back)]

    def select(self, tool):
        self.tool = tool
        self.drag_start = None

    def save(self):
        try:
            write_data(FILENAME, asdict(self.stage))
        except OSError:
            self.message = "Não foi possível salvar a fase."
        else:
            self.message = "Fase salva."

    def play(self):
        self.drag_start = None
        self.game.change_scene("gameplay", stage=self.stage, editor=self)

    def back(self):
        self.drag_start = None
        self.game.change_scene("menu")

    def change_stage(self, **changes):
        self.history.append(self.stage)
        self.stage = replace(self.stage, **changes)
        self.message = "Alterações ainda não salvas."

    def point(self, pos):
        return min(max(0, pos[0] + self.camera), self.stage.width - 1), min(max(76, pos[1]), 503)

    def platform(self, end):
        x, y = self.drag_start
        left, right = sorted((x, end[0]))
        top, bottom = sorted((y, end[1]))
        return left, top, min(self.stage.width - left, max(16, right - left)), max(16, bottom - top)

    def place(self, pos):
        x, y = pos
        if self.tool == 1:
            self.change_stage(start=(x, y))
        elif self.tool == 2:
            self.change_stage(exit_x=x)
        elif self.tool == 3:
            spawn = EnemySpawn(x, y, max(0, x - 80), min(self.stage.width, x + 80))
            self.change_stage(enemies=(*self.stage.enemies, spawn))
        elif self.tool == 4:
            self.change_stage(items=(*self.stage.items, ItemSpawn(x, y)))

    def erase(self, point):
        for field in ("items", "enemies", "platforms"):
            entries = getattr(self.stage, field)
            for index in reversed(range(len(entries))):
                entry = entries[index]
                rect = pygame.Rect(*entry) if field == "platforms" else pygame.Rect(entry.x - 10, entry.y - 10, 20, 20)
                if rect.collidepoint(point):
                    self.change_stage(**{field: entries[:index] + entries[index + 1:]})
                    return

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.back()
            elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                step = -240 if event.key == pygame.K_LEFT else 240
                self.camera = max(0, min(self.camera + step, self.stage.width - cfg.WIDTH))
            elif pygame.K_1 <= event.key <= pygame.K_5:
                self.select(event.key - pygame.K_1)
            elif event.key == pygame.K_s and event.mod & pygame.KMOD_CTRL:
                self.save()
            elif event.key == pygame.K_z and event.mod & pygame.KMOD_CTRL and self.history:
                self.stage = self.history.pop()
                self.message = "Última edição desfeita."
            elif event.key == pygame.K_RETURN:
                self.play()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.pos[1] < 70:
                if event.button == 1:
                    for index, (_, action) in enumerate(self.buttons):
                        if self.button_rect(index).collidepoint(event.pos):
                            action()
                            break
            elif event.pos[1] < 504:
                point = self.point(event.pos)
                if event.button == 3:
                    self.erase(point)
                elif event.button == 1 and self.tool == 0:
                    self.drag_start = point
                elif event.button == 1:
                    self.place(point)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.drag_start:
            rect = self.platform(self.point(event.pos))
            self.drag_start = None
            self.change_stage(platforms=(*self.stage.platforms, rect))

    @staticmethod
    def button_rect(index):
        return pygame.Rect(12 + index * 117, 12, 110, 38)

    def marker(self, surface, label, x, y, color):
        center = (x - self.camera, y)
        pygame.draw.circle(surface, color, center, 10, 2)
        surface.blit(self.font.render(label, True, color), (center[0] + 12, y - 9))

    def draw(self, surface):
        platforms = [pygame.Rect(*rect) for rect in self.stage.platforms]
        self.scenery.draw(surface, self.camera, platforms)
        if self.drag_start:
            rect = pygame.Rect(*self.platform(self.point(pygame.mouse.get_pos())))
            pygame.draw.rect(surface, cfg.YELLOW, rect.move(-self.camera, 0), 2)
        self.marker(surface, "Início", *self.stage.start, cfg.GREEN)
        for enemy in self.stage.enemies:
            self.marker(surface, "Inimigo", enemy.x, enemy.y, cfg.RED)
        for item in self.stage.items:
            self.marker(surface, "Item", item.x, item.y, cfg.YELLOW)
        exit_x = self.stage.exit_x - self.camera
        pygame.draw.line(surface, cfg.MAGENTA, (exit_x, 70), (exit_x, 503), 2)
        self.marker(surface, "Saída", self.stage.exit_x, 92, cfg.MAGENTA)
        pygame.draw.rect(surface, cfg.BG, (0, 0, cfg.WIDTH, 70))
        pygame.draw.rect(surface, cfg.BG, (0, 504, cfg.WIDTH, 36))
        for index, (label, _) in enumerate(self.buttons):
            rect = self.button_rect(index)
            active = index == self.tool
            pygame.draw.rect(surface, cfg.CYAN if active else cfg.STEEL, rect)
            text = self.font.render(label, True, cfg.BG if active else cfg.INK)
            surface.blit(text, text.get_rect(center=rect.center))
        hint = "Setas  Percorrer fase    Botão direito  Remover    Ctrl+Z  Desfazer"
        surface.blit(self.font.render(hint, True, cfg.INK), (12, 515))
        surface.blit(self.font.render(self.message, True, cfg.YELLOW), (650, 515))
