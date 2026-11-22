import os
import pygame
from ..utils import utils
from ..constants import WIDTH, HEIGHT, COLOR_BG


class ParallaxLayer:
    """
    Camada individual do cenário Parallax com fator de deslocamento próprio.
    Gerencia sua textura na GPU e repetição contínua na horizontal.
    """
    def __init__(self, surface: pygame.Surface, factor_x: float, scale_factor: float = 4.0,
                 y_offset: float = 0.0, autoscroll_speed: float = 0.0):
        self.factor_x: float = float(factor_x)
        self.autoscroll_speed: float = float(autoscroll_speed)
        self.drift_x: float = 0.0
        self.y_offset: float = float(y_offset)

        # Escala proporcional para pixel art
        orig_w, orig_h = surface.get_size()
        self.scaled_w: int = int(orig_w * scale_factor)
        self.scaled_h: int = int(orig_h * scale_factor)
        scaled_surf = pygame.transform.scale(surface, (self.scaled_w, self.scaled_h))

        self.texture_id = utils.surface_to_texture(scaled_surf)

    def update(self, dt: float):
        if self.autoscroll_speed != 0.0 and dt > 0:
            self.drift_x = (self.drift_x + self.autoscroll_speed * dt) % self.scaled_w

    def draw(self, camera_x: float, viewport_w: float = WIDTH):
        # Deslocamento total na horizontal
        total_offset = (camera_x * self.factor_x + self.drift_x) % self.scaled_w

        # Inicia desenhando uma cópia antes para cobrir a margem esquerda
        draw_x = -total_offset
        if draw_x > 0:
            draw_x -= self.scaled_w

        # Desenha cópias adjacentes até cobrir toda a largura da tela
        while draw_x < viewport_w:
            utils.draw_textured_quad(self.texture_id, draw_x, self.y_offset, self.scaled_w, self.scaled_h)
            draw_x += self.scaled_w

    def destroy(self):
        """Libera com seguranca a textura da camada na GPU."""
        if self.texture_id is not None:
            utils.delete_texture(self.texture_id)
            self.texture_id = None


class ParallaxBackground:
    """
    Gerenciador das camadas Parallax do TAC3.
    Combina o céu arcade, nuvens distantes, montanhas e vegetação intermediária.
    """
    def __init__(self):
        self.layers: list[ParallaxLayer] = []
        # Cor de céu padrão retro (#5C94FC)
        self.sky_color: tuple[float, float, float, float] = (92 / 255.0, 148 / 255.0, 252 / 255.0, 1.0)

    def initialize_default_layers(self, enable_cloud_drift: bool = True):
        """Carrega e configura as camadas Parallax a partir dos recursos de assets/image/."""
        self.destroy()

        try:
            # 1. Nuvens (Plano mais distante) - Recorte do Painel 0 (768x248)
            clouds_path = utils.get_full_path("assets/image/bg-clouds-cutout.png")
            if os.path.exists(clouds_path):
                img_clouds = pygame.image.load(clouds_path)
                slice_clouds = img_clouds.subsurface((0, 0, 768, 248))
                drift_speed = 15.0 if enable_cloud_drift else 0.0
                self.layers.append(ParallaxLayer(slice_clouds, factor_x=0.10, scale_factor=4.0, y_offset=0.0, autoscroll_speed=drift_speed))

            # 2. Montanhas (Plano intermediário distante) - Recorte do Painel 0 com colorkey para transparência do céu
            mountains_path = utils.get_full_path("assets/image/bg-mountains.png")
            if os.path.exists(mountains_path):
                img_mountains = pygame.image.load(mountains_path)
                slice_mountains = img_mountains.subsurface((0, 0, 768, 248)).copy()
                slice_mountains.set_colorkey((0, 41, 140))
                slice_mountains = slice_mountains.convert_alpha()
                self.layers.append(ParallaxLayer(slice_mountains, factor_x=0.30, scale_factor=4.0, y_offset=0.0))

            # 3. Árvores e Vegetação (Plano intermediário próximo) - Recorte do Painel 0 com transparência alfa
            trees_path = utils.get_full_path("assets/image/bg-trees-cutout.png")
            if os.path.exists(trees_path):
                img_trees = pygame.image.load(trees_path)
                slice_trees = img_trees.subsurface((0, 0, 768, 248))
                self.layers.append(ParallaxLayer(slice_trees, factor_x=0.60, scale_factor=4.0, y_offset=0.0))

        except Exception as e:
            print(f"Aviso ao inicializar camadas de Parallax: {e}")

    def update(self, dt: float):
        for layer in self.layers:
            layer.update(dt)

    def draw(self, camera_x: float, viewport_w: float = WIDTH, viewport_h: float = HEIGHT):
        # 1. Renderiza o céu base
        utils.draw_colored_quad(0, 0, viewport_w, viewport_h, self.sky_color)

        # 2. Renderiza as camadas na ordem correta de profundidade (nuvens -> montanhas -> árvores)
        for layer in self.layers:
            layer.draw(camera_x, viewport_w)

    def destroy(self):
        """Libera apenas os recursos que possui na GPU."""
        for layer in self.layers:
            layer.destroy()
        self.layers.clear()
