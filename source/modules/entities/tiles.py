import pygame
from ..utils import utils
from ..constants import TILE_SIZE, TILE_CROP, FILE_MAP_1


class Tile():
    def __init__(self,
                 id:int, 
                 surf:pygame.Surface,
                 desc:str,
                 w=TILE_SIZE,
                 h=TILE_SIZE,
                 texture_id=None):
        
        self.id = id
        self.image = surf
        self.desc = desc

        if self.image is not None and (w != TILE_CROP or h != TILE_CROP):
            self.image = pygame.transform.smoothscale(self.image, (w,h))
        self.rect = self.image.get_rect() if self.image is not None else pygame.Rect(0, 0, w, h)

        # Converte e guarda o ID da GPU (Flyweight se fornecido)
        if texture_id is not None:
            self.texture_id = texture_id
            self.owns_texture = False
        else:
            self.texture_id = utils.surface_to_texture(self.image)
            self.owns_texture = True
       
    def draw(self):
        x,y,w,h = self.rect.x, self.rect.y, self.rect.w, self.rect.h        
        utils.draw_textured_quad(self.texture_id, x,y,w,h)


class TileMap():
    def __init__(self):
        self.shared_textures: dict[int, int] = {}
        self.codes = []
        self.map_items = None

    def load_sprite_maps(self):
        self.map_items = utils.load_image(FILE_MAP_1)

        # items
        self.floor1 = self.map_items.subsurface((0,208,TILE_CROP,TILE_CROP))
        self.floor2 = self.map_items.subsurface((768,448,TILE_CROP,TILE_CROP))
        self.brick1 = self.map_items.subsurface((320,144,TILE_CROP,TILE_CROP))
        self.brick2 = self.map_items.subsurface((832,400,TILE_CROP,TILE_CROP))

        #pygame.image.save(self.floor1,"1.png")
      
        # object codes
        self.codes = [            
            None,   # code by index - 0 draw nothing
            (1, self.floor1, "floor1"),     # id, surface, description
            (2, self.floor2, "floor2"),
            (3, self.brick1, "brick1"),
            (4, self.brick2, "brick2")
        ]

    def get_shared_texture(self, tile_id: int, surf: pygame.Surface) -> int:
        """Retorna ou cria uma textura compartilhada na GPU (Padrao Flyweight)."""
        if tile_id not in self.shared_textures:
            scaled = pygame.transform.smoothscale(surf, (TILE_SIZE, TILE_SIZE))
            self.shared_textures[tile_id] = utils.surface_to_texture(scaled)
        return self.shared_textures[tile_id]

    def release_textures(self):
        """Libera com seguranca todas as texturas compartilhadas da GPU."""
        for tid in self.shared_textures.values():
            utils.delete_texture(tid)
        self.shared_textures.clear()

#tile_map = TileMap()