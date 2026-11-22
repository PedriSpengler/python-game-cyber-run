class CollisionSystem:
    """
    Sistema de detecção e resolução de colisões espaciais (Swept AABB vs Tilemap).
    Totalmente desacoplado de Pygame e PyOpenGL.
    Opera em World Space com resolução contínua por eixos (Horizontal e Vertical),
    eliminando o efeito de tunelamento em variações de delta time.
    """
    def __init__(self, tile_size: int = 32):
        self.tile_size = int(tile_size)

    def is_tile_solid(self, col: int, lin: int, level) -> bool:
        """Determina se uma célula do mapa contém um bloco sólido."""
        if level is None:
            return False
        if hasattr(level, 'get_tile_id'):
            return level.get_tile_id(col, lin) > 0
        elif hasattr(level, 'tiles') and 0 <= lin < len(level.tiles) and 0 <= col < len(level.tiles[lin]):
            tile = level.tiles[lin][col]
            return tile is not None and getattr(tile, 'id', 0) > 0
        return False

    def resolve_horizontal(self, entity, level, prev_x: float = None) -> bool:
        """
        Resolve colisões no eixo X considerando o intervalo de varredura [prev_x .. new_x].
        """
        collided = False
        ts = self.tile_size

        # 1. Limite esquerdo do mundo
        if entity.x < 0:
            entity.x = 0.0
            entity.vx = 0.0
            return True

        # 2. Limite direito do mundo
        if level and hasattr(level, 'tiles') and level.tiles and len(level.tiles[0]) > 0:
            world_w = len(level.tiles[0]) * ts
            if entity.right > world_w:
                entity.right = float(world_w)
                entity.vx = 0.0
                return True

        if level is None:
            return False

        old_x = prev_x if prev_x is not None else entity.x
        lin_start = int(entity.y // ts)
        lin_end = int((entity.bottom - 0.001) // ts)

        if entity.vx > 0:  # Movendo para a direita
            col_min = int((old_x + entity.width) // ts)
            col_max = int((entity.right - 0.001) // ts)

            for c in range(col_min, col_max + 1):
                for l in range(lin_start, lin_end + 1):
                    if self.is_tile_solid(c, l, level):
                        entity.right = float(c * ts)
                        entity.vx = 0.0
                        return True

        elif entity.vx < 0:  # Movendo para a esquerda
            col_max = int(old_x // ts)
            col_min = int(entity.x // ts)

            for c in range(col_max, col_min - 1, -1):
                for l in range(lin_start, lin_end + 1):
                    if self.is_tile_solid(c, l, level):
                        entity.x = float((c + 1) * ts)
                        entity.vx = 0.0
                        return True

        return collided

    def resolve_vertical(self, entity, level, prev_y: float = None) -> bool:
        """
        Resolve colisões no eixo Y considerando o intervalo de varredura [prev_y .. new_y].
        """
        ts = self.tile_size
        old_y = prev_y if prev_y is not None else entity.y
        col_start = int(entity.x // ts)
        col_end = int((entity.right - 0.001) // ts)

        if level is not None:
            if entity.vy > 0:  # Caindo
                lin_min = int((old_y + entity.height) // ts)
                lin_max = int((entity.bottom - 0.001) // ts)

                for l in range(lin_min, lin_max + 1):
                    for c in range(col_start, col_end + 1):
                        if self.is_tile_solid(c, l, level):
                            entity.bottom = float(l * ts)
                            entity.vy = 0.0
                            entity.is_grounded = True
                            return True

            elif entity.vy < 0:  # Subindo
                lin_max = int(old_y // ts)
                lin_min = int(entity.y // ts)

                for l in range(lin_max, lin_min - 1, -1):
                    for c in range(col_start, col_end + 1):
                        if self.is_tile_solid(c, l, level):
                            entity.y = float((l + 1) * ts)
                            entity.vy = 0.0
                            return True

        # Fallback para o chão padrão caso não haja colisão com blocos
        if entity.bottom >= entity.floor_y:
            entity.bottom = entity.floor_y
            entity.vy = 0.0
            entity.is_grounded = True
            return True

        return False
