import pygame
from ..constants import SIZE_PLAYER
from ..utils import utils
from ..config.sounds import sounds
from ..entities.player_entity import PlayerEntity, PlayerState


class PlayerView:
    """
    Camada de renderização do jogador (View).
    Gerencia carregamento de imagens, texturas na GPU OpenGL,
    avanço de animações de sprites e desenho visual via Camera2D.
    """
    def __init__(self, size: tuple[int, int] = SIZE_PLAYER, shared_view: 'PlayerView' = None):
        self.size = size
        self.frame_index: int = 0
        self.frame_speed: float = 16.0
        self.current_frame: float = 0.0

        if shared_view is not None:
            self.textures_walk_right = shared_view.textures_walk_right
            self.textures_walk_left = shared_view.textures_walk_left
            self.textures_jump_right = shared_view.textures_jump_right
            self.textures_jump_left = shared_view.textures_jump_left
            self.texture_stand = shared_view.texture_stand
            self.texture_jump_stand = shared_view.texture_jump_stand
            self.owns_textures = False
        else:
            # Coleções de texturas na GPU (Flyweight)
            self.textures_walk_right: list[int] = []
            self.textures_walk_left: list[int] = []
            self.textures_jump_right: list[int] = []
            self.textures_jump_left: list[int] = []
            self.texture_stand: int = 0
            self.texture_jump_stand: int = 0
            self.owns_textures = True
            self._load_textures()

    def _load_textures(self):
        # 1. Sprites de Caminhada (14 quadros)
        for i in range(14):
            img = utils.load_image(f"assets/image/walk/frame{i:04d}.png")
            img_scaled = pygame.transform.smoothscale(img, self.size)
            img_mirror = pygame.transform.flip(img_scaled, True, False)
            self.textures_walk_right.append(utils.surface_to_texture(img_scaled))
            self.textures_walk_left.append(utils.surface_to_texture(img_mirror))

        # 2. Sprites de Pulo (3 quadros)
        for i in range(1, 4):
            img = utils.load_image(f"assets/image/walk/jump{i}.png")
            img_scaled = pygame.transform.smoothscale(img, self.size)
            img_mirror = pygame.transform.flip(img_scaled, True, False)
            self.textures_jump_right.append(utils.surface_to_texture(img_scaled))
            self.textures_jump_left.append(utils.surface_to_texture(img_mirror))

        # 3. Posturas Estáticas
        stand_img = utils.load_image("assets/image/walk/stand.png")
        self.texture_stand = utils.surface_to_texture(pygame.transform.smoothscale(stand_img, self.size))

        jump_stand_img = utils.load_image("assets/image/walk/jump_stand.png")
        self.texture_jump_stand = utils.surface_to_texture(pygame.transform.smoothscale(jump_stand_img, self.size))

    def update(self, dt: float, entity: PlayerEntity):
        """Atualiza a animação de acordo com o delta time e dispara áudio de pulo."""
        if entity.just_jumped:
            sounds.play_sound(sounds.sound_jump, 2)

        # Atualiza índice do frame de caminhada
        if entity.state == PlayerState.RUNNING:
            self.current_frame += self.frame_speed * dt
            if self.current_frame >= len(self.textures_walk_right):
                self.current_frame = 0.0
            self.frame_index = int(self.current_frame)
        else:
            self.current_frame = 0.0
            self.frame_index = 0

    def draw(self, entity: PlayerEntity, camera_offset: tuple[float, float] = (0.0, 0.0)):
        """Desenha o jogador no plano da câmera OpenGL."""
        cam_x, cam_y = camera_offset
        screen_x = entity.x - cam_x
        screen_y = entity.y - cam_y
        w = entity.width
        h = entity.height

        texture = self.texture_stand

        if not entity.is_grounded:
            texture = self.texture_jump_stand
            if abs(entity.vx) > 0.001:
                # Movendo horizontalmente no ar
                if entity.facing == 1:
                    if entity.vy > 0:  # Descendo
                        if entity.jump_min <= entity.bottom <= entity.jump_max:
                            texture = self.textures_jump_right[2]
                        else:
                            texture = self.textures_jump_right[1]
                    else:  # Subindo
                        if entity.jump_min <= entity.bottom <= entity.jump_max:
                            texture = self.textures_jump_right[0]
                        else:
                            texture = self.textures_jump_right[1]
                elif entity.facing == -1:
                    if entity.vy > 0:  # Descendo
                        if entity.jump_min <= entity.bottom <= entity.jump_max:
                            texture = self.textures_jump_left[2]
                        else:
                            texture = self.textures_jump_left[1]
                    else:  # Subindo
                        if entity.jump_min <= entity.bottom <= entity.jump_max:
                            texture = self.textures_jump_left[0]
                        else:
                            texture = self.textures_jump_left[1]
        else:
            if entity.state == PlayerState.RUNNING:
                if entity.facing == 1:
                    texture = self.textures_walk_right[self.frame_index]
                elif entity.facing == -1:
                    texture = self.textures_walk_left[self.frame_index]

        utils.draw_textured_quad(texture, screen_x, screen_y, w, h)

    def destroy(self):
        """Desaloca com segurança todas as texturas de animação na GPU se for proprietário."""
        if not getattr(self, 'owns_textures', True):
            self.textures_walk_right.clear()
            self.textures_walk_left.clear()
            self.textures_jump_right.clear()
            self.textures_jump_left.clear()
            self.texture_stand = 0
            self.texture_jump_stand = 0
            return
        for tid in self.textures_walk_right + self.textures_walk_left + self.textures_jump_right + self.textures_jump_left:
            utils.delete_texture(tid)
        self.textures_walk_right.clear()
        self.textures_walk_left.clear()
        self.textures_jump_right.clear()
        self.textures_jump_left.clear()

        if self.texture_stand:
            utils.delete_texture(self.texture_stand)
            self.texture_stand = 0
        if self.texture_jump_stand:
            utils.delete_texture(self.texture_jump_stand)
            self.texture_jump_stand = 0
