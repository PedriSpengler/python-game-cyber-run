import math
from .constants import WIDTH, HEIGHT


class Camera2D:
    """
    Câmera 2D desacoplada da lógica de renderização.
    Responsável pelo acompanhamento suave do jogador através de interpolação
    independente da taxa de FPS (alpha = 1 - exp(-smooth_speed * dt)) e pela
    conversão entre coordenadas do mundo (World Space) e da tela (Screen Space).
    """
    def __init__(self, viewport_width: float = WIDTH, viewport_height: float = HEIGHT):
        self.width: float = float(viewport_width)
        self.height: float = float(viewport_height)
        self.x: float = 0.0
        self.y: float = 0.0
        self.target_x: float = 0.0
        self.target_y: float = 0.0

        # Limites do mundo em pixels (obtidos dinamicamente da fase)
        self.world_w: float = float(viewport_width)
        self.world_h: float = float(viewport_height)

        # Configurações de suavização
        self.smooth_speed: float = 5.0
        self.lead_ratio_x: float = 0.35  # Mantém o jogador a ~35% da tela à esquerda

    def set_world_bounds(self, world_w: float, world_h: float):
        """Define os limites reais do mundo para clamping."""
        self.world_w = max(self.width, float(world_w))
        self.world_h = max(self.height, float(world_h))

    def follow(self, target_rect, dt: float):
        """
        Acompanha o alvo suavemente utilizando decaimento exponencial:
        alpha = 1.0 - exp(-smooth_speed * dt).
        Garante que a posição da câmera convirja sem saltos e sem alterar a física do alvo.
        """
        # Posição ideal: manter o jogador na linha visual de lead_ratio_x
        target_center_x = target_rect.x if hasattr(target_rect, 'x') else target_rect[0]
        desired_x = target_center_x - (self.width * self.lead_ratio_x)

        # Clamping com os limites reais do mundo
        max_cam_x = max(0.0, self.world_w - self.width)
        self.target_x = max(0.0, min(desired_x, max_cam_x))

        # Interpolação independente de framerate
        if dt > 0:
            alpha = 1.0 - math.exp(-self.smooth_speed * dt)
            self.x += (self.target_x - self.x) * alpha
        else:
            self.x = self.target_x

        # Clamping final defensivo
        self.x = max(0.0, min(self.x, max_cam_x))

    def world_to_screen(self, world_x: float, world_y: float) -> tuple[float, float]:
        """Converte coordenadas do mundo para coordenadas da tela."""
        return world_x - self.x, world_y - self.y

    def screen_to_world(self, screen_x: float, screen_y: float) -> tuple[float, float]:
        """Converte coordenadas da tela para coordenadas do mundo."""
        return screen_x + self.x, screen_y + self.y

    def get_viewport(self) -> tuple[float, float, float, float]:
        """Retorna o retângulo visível da câmera no mundo: (x, y, w, h)."""
        return self.x, self.y, self.width, self.height
