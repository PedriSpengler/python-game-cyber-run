import os
import json
import pygame
from ..constants import TILE_MAP_LEVEL1, TILE_SIZE, FILE_LV1, FILE_LV1_JSON
from ..utils import utils
import numpy as np
import scipy.sparse as sp
from ..entities.tiles import Tile, TileMap #tile_map


class Level():
    def __init__(self):
        pass


class Level1(Level):
    def __init__(self):
        super().__init__()
        self.data = None
        self.tile_map = None
        self.current_json_path = None
        self.current_npz_path = None
        self.tiles: list[list[Tile]] = []

    def create_first_map(self, json_file=None, npz_file=None):
        try:
            target_json = json_file or utils.get_full_path(FILE_LV1_JSON)
            target_npz = npz_file or utils.get_full_path(FILE_LV1)

            map1 = {            
                "height": TILE_MAP_LEVEL1[1],
                "width": TILE_MAP_LEVEL1[0],
                "tilewidth": TILE_SIZE,
                "tileheight": TILE_SIZE,  
                "layers": [
                    {                        
                        "map": FILE_LV1 if npz_file is None else target_npz,
                        "height": TILE_MAP_LEVEL1[1],
                        "width": TILE_MAP_LEVEL1[0],
                        "name": "Blocks",
                        "opacity": 1,            
                        "visible": True,
                        "x": 0,
                        "y": 0
                    }
                ],  
                "orientation": "orthogonal",
                "renderorder": "right-down",  
                "type": "map",
                "version": "0.01"
            }
 
            with open(target_json, 'w', encoding='utf-8') as file:
                json.dump(map1, file, indent=4)

            self.create_matrix_tile(target_npz)

        except Exception as e:
            # log
            print(e)


    def create_matrix_tile(self, npz_file=None):
        target_npz = npz_file or utils.get_full_path(FILE_LV1)
        # 1. Create a matrix with mostly zeros
        dense_matrix = np.zeros((TILE_MAP_LEVEL1[1], TILE_MAP_LEVEL1[0]), dtype=int)
        
        # add tiles - floor          
        for lin in range(TILE_MAP_LEVEL1[1]):
            for col in range(TILE_MAP_LEVEL1[0]):               
                # some few bricks and floor
                block_cond_1 = int(TILE_MAP_LEVEL1[0]*0.5) <= col <= int(TILE_MAP_LEVEL1[0]*0.6)
                block_cond_2 = lin == int(TILE_MAP_LEVEL1[1]*0.7)
                
                if lin > int(TILE_MAP_LEVEL1[1]*0.9):
                    dense_matrix[lin,col] = 1                                             
                elif block_cond_1 and block_cond_2:                        
                    dense_matrix[lin,col] = 3 

        dense_matrix[0,0] = 1
        dense_matrix[20,10] = 3
        # 2. Convert to a sparse representation (CSR format)
        sparse_matrix = sp.csr_array(dense_matrix)
        # 3. Save to a compressed .npz file
        sp.save_npz(target_npz, sparse_matrix)


    def get_tile_id(self, col: int, lin: int) -> int:
        """Retorna o ID do tile na coordenada (col, lin). Retorna 0 se vazio ou fora dos limites."""
        if 0 <= lin < len(self.tiles) and 0 <= col < len(self.tiles[lin]):
            tile = self.tiles[lin][col]
            if tile is not None and hasattr(tile, 'id'):
                return tile.id
        return 0

    def set_tile_id(self, col: int, lin: int, tile_id: int):
        """
        Define o tile na coordenada (col, lin) com base no seu ID estável.
        0 limpa a célula (None). IDs > 0 instanciam Tile utilizando textura Flyweight.
        """
        if not (0 <= lin < len(self.tiles) and 0 <= col < len(self.tiles[lin])):
            return

        if tile_id == 0 or tile_id is None:
            self.tiles[lin][col] = None
            return

        if self.tile_map is not None:
            for code in self.tile_map.codes:
                if code and code[0] == tile_id:
                    cid, surf, desc = code
                    shared_tex = self.tile_map.get_shared_texture(cid, surf) if hasattr(self.tile_map, 'get_shared_texture') else None
                    new_tile = Tile(cid, surf.copy(), desc, texture_id=shared_tex)
                    new_tile.rect.topleft = (col * TILE_SIZE, lin * TILE_SIZE)
                    self.tiles[lin][col] = new_tile
                    return

        # Fallback defensivo para testes ou caso tile_map não esteja carregado
        fallback_surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        new_tile = Tile(tile_id, fallback_surf, f"Tile_{tile_id}")
        new_tile.rect.topleft = (col * TILE_SIZE, lin * TILE_SIZE)
        self.tiles[lin][col] = new_tile

    def resize_matrix(self, new_width: int, new_height: int):
        """
        Redimensiona a matriz de tiles do mapa.
        Preserva os elementos contidos na interseção das novas dimensões.
        """
        new_w = max(1, int(new_width))
        new_h = max(1, int(new_height))
        old_h = len(self.tiles)
        old_w = len(self.tiles[0]) if old_h > 0 else 0

        new_tiles: list[list[Tile]] = []
        for lin in range(new_h):
            row: list[Tile] = []
            for col in range(new_w):
                if lin < old_h and col < old_w:
                    row.append(self.tiles[lin][col])
                else:
                    row.append(None)
            new_tiles.append(row)
        self.tiles = new_tiles

    def create_new_map(self, width: int = TILE_MAP_LEVEL1[0], height: int = TILE_MAP_LEVEL1[1], default_floor: bool = True):
        """Inicializa um novo mapa em branco com dimensões especificadas."""
        self.tiles = []
        for lin in range(height):
            row = []
            for col in range(width):
                if default_floor and lin > int(height * 0.9):
                    # Bloco de chão padrão (ID 1)
                    if self.tile_map:
                        code = self.tile_map.codes[1] if len(self.tile_map.codes) > 1 else None
                        if code:
                            cid, surf, desc = code
                            shared_tex = self.tile_map.get_shared_texture(cid, surf) if hasattr(self.tile_map, 'get_shared_texture') else None
                            tile = Tile(cid, surf.copy(), desc, texture_id=shared_tex)
                            tile.rect.topleft = (col * TILE_SIZE, lin * TILE_SIZE)
                            row.append(tile)
                            continue
                    row.append(None)
                else:
                    row.append(None)
            self.tiles.append(row)

    def save(self, json_file=None, npz_file=None):
        """Salva o estado atual do mapa em JSON e NPZ sem perder dados."""
        try:
            target_json = json_file or self.current_json_path or utils.get_full_path(FILE_LV1_JSON)
            target_npz = npz_file or self.current_npz_path or utils.get_full_path(FILE_LV1)

            h = len(self.tiles) if self.tiles else TILE_MAP_LEVEL1[1]
            w = len(self.tiles[0]) if self.tiles and len(self.tiles) > 0 else TILE_MAP_LEVEL1[0]
            dense_matrix = np.zeros((h, w), dtype=int)

            for lin in range(h):
                for col in range(w):
                    tile = self.tiles[lin][col]
                    if tile is not None and hasattr(tile, 'id'):
                        dense_matrix[lin, col] = tile.id

            sparse_matrix = sp.csr_array(dense_matrix)
            sp.save_npz(target_npz, sparse_matrix)

            map_data = {
                "height": h,
                "width": w,
                "tilewidth": TILE_SIZE,
                "tileheight": TILE_SIZE,
                "layers": [
                    {
                        "map": os.path.basename(target_npz),
                        "height": h,
                        "width": w,
                        "name": "Blocks",
                        "opacity": 1,
                        "visible": True,
                        "x": 0,
                        "y": 0
                    }
                ],
                "orientation": "orthogonal",
                "renderorder": "right-down",
                "type": "map",
                "version": "0.01"
            }
            with open(target_json, 'w', encoding='utf-8') as file:
                json.dump(map_data, file, indent=4)

            self.current_json_path = target_json
            self.current_npz_path = target_npz
            return True
        except Exception as e:
            print(f"Erro ao salvar mapa: {e}")
            return False

    def save_as(self, json_file: str, npz_file: str) -> bool:
        """Salva o mapa em um novo par de arquivos JSON e NPZ."""
        return self.save(json_file=json_file, npz_file=npz_file)


    def load(self, tile_map, json_file=None, npz_file=None):        
        # PRESERVAÇÃO: Não recria o mapa padrão incondicionalmente!
        self.tiles = []
        self.tile_map = tile_map
        target_json = json_file or utils.get_full_path(FILE_LV1_JSON)
        target_npz = npz_file or utils.get_full_path(FILE_LV1)
        self.current_json_path = target_json
        self.current_npz_path = target_npz

        try:
            with open(target_json, 'r', encoding='utf-8') as file:
                self.data = json.load(file)

            # Carrega a matriz esparsa e converte para array para iteracao rapida
            sparse_data = sp.load_npz(target_npz)
            dense_matrix = sparse_data.toarray() if hasattr(sparse_data, 'toarray') else np.array(sparse_data)

            num_lines = dense_matrix.shape[0]
            num_cols = dense_matrix.shape[1]

            for lin in range(num_lines):
                line = []           
                for col in range(num_cols):                    
                    if dense_matrix[lin, col] != 0:
                        self.obj_call(dense_matrix, lin, col, line, tile_map)
                    else:
                        line.append(None)  
                self.tiles.append(line)  

        except FileNotFoundError:
            print(f"Aviso: Arquivo de mapa '{target_json}' ou '{target_npz}' nao encontrado.")
            if json_file is None and npz_file is None:
                # Cria primeiro mapa como fallback apenas para arquivos padrao
                self.create_first_map()
                return self.load(tile_map)
            return False
        except json.JSONDecodeError:
            print("Error: The file is not a valid JSON format.")
            return False
        return True


    def obj_call(self, dense_matrix, lin, col, line, tile_map:TileMap):
        val = dense_matrix[lin, col]
        for k, call in enumerate(tile_map.codes):
            if call and val == call[0]:
                id = call[0]
                surf = call[1]
                desc = call[2]
                shared_tex = tile_map.get_shared_texture(id, surf) if hasattr(tile_map, 'get_shared_texture') else None
                obj:Tile = Tile(id, surf, desc, texture_id=shared_tex)
                x, y = col, lin # 2d position
                obj.rect.topleft = (x*TILE_SIZE, y*TILE_SIZE)
                line.append(obj)
                return
        line.append(None)

    def get_world_size(self) -> tuple[float, float]:
        """Retorna as dimensoes reais do mundo em pixels (largura, altura) com base nos dados reais do mapa."""
        num_cols = len(self.tiles[0]) if self.tiles and len(self.tiles) > 0 else TILE_MAP_LEVEL1[0]
        num_lines = len(self.tiles) if self.tiles else TILE_MAP_LEVEL1[1]
        tile_w = self.data.get("tilewidth", TILE_SIZE) if getattr(self, 'data', None) else TILE_SIZE
        tile_h = self.data.get("tileheight", TILE_SIZE) if getattr(self, 'data', None) else TILE_SIZE
        return float(num_cols * tile_w), float(num_lines * tile_h)

    def draw(self, camera=None):
        """
        Renderiza os blocos da fase utilizando Frustum Culling 2D.
        Apenas os blocos visiveis dentro do campo de visao da camera sao enviados para a GPU.
        """
        if not self.tiles or len(self.tiles) == 0:
            return

        cam_x = camera.x if camera else 0.0
        cam_y = camera.y if camera else 0.0
        cam_w = camera.width if camera else 1920.0
        cam_h = camera.height if camera else 1080.0

        col_start = max(0, int(cam_x // TILE_SIZE))
        col_end = min(len(self.tiles[0]), int((cam_x + cam_w) // TILE_SIZE) + 2)
        lin_start = max(0, int(cam_y // TILE_SIZE))
        lin_end = min(len(self.tiles), int((cam_y + cam_h) // TILE_SIZE) + 2)

        for lin in range(lin_start, lin_end):
            row = self.tiles[lin]
            for col in range(col_start, col_end):
                tile = row[col]
                if tile is not None:
                    screen_x = tile.rect.x - cam_x
                    screen_y = tile.rect.y - cam_y
                    utils.draw_textured_quad(tile.texture_id, screen_x, screen_y, tile.rect.w, tile.rect.h)


#level1 = Level1()
