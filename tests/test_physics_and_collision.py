import unittest
from source.modules.collision.collision_system import CollisionSystem
from source.modules.physics.physics_system import PhysicsSystem
from source.modules.entities.player_entity import PlayerEntity, PlayerState
from source.modules.input.input_state import InputState


class MockLevel:
    """Mock leve de level que implementa get_tile_id sem dependências gráficas."""
    def __init__(self, width: int = 50, height: int = 30):
        self.width = width
        self.height = height
        self.grid = [[0 for _ in range(width)] for _ in range(height)]
        self.tiles = self.grid

    def get_tile_id(self, col: int, lin: int) -> int:
        if 0 <= lin < self.height and 0 <= col < self.width:
            return self.grid[lin][col]
        return 0

    def set_solid(self, col: int, lin: int, tile_id: int = 1):
        if 0 <= lin < self.height and 0 <= col < self.width:
            self.grid[lin][col] = tile_id


class TestPhysicsAndCollision(unittest.TestCase):
    def setUp(self):
        self.collision = CollisionSystem(tile_size=32)
        self.physics = PhysicsSystem(self.collision)
        self.level = MockLevel(width=50, height=30)

    def test_horizontal_wall_collision(self):
        """Valida bloqueio de avanço contra parede sólida à direita."""
        # Coloca parede sólida na coluna 10 (x = 320)
        for l in range(30):
            self.level.set_solid(10, l, 2)

        # Jogador posicionado à esquerda da parede (width = 60)
        entity = PlayerEntity(x=250.0, y=300.0, width=60.0, height=100.0, speed=300.0)
        entity.vx = 300.0  # Movendo para a direita

        # Simula 0.5s: 250 + (300 * 0.5) = 400 > 320 -> Deve colidir e parar em x = 320 - 60 = 260
        self.physics.update_entity(entity, dt=0.5, level=self.level)

        self.assertEqual(entity.right, 320.0)
        self.assertEqual(entity.x, 260.0)
        self.assertEqual(entity.vx, 0.0)

    def test_vertical_platform_landing(self):
        """Valida aterrissagem precisa sobre plataforma suspensa."""
        # Cria uma plataforma sólida na linha 15 (y = 15 * 32 = 480)
        for c in range(5, 15):
            self.level.set_solid(c, 15, 1)

        # Jogador caindo diretamente sobre a plataforma (altura = 100)
        entity = PlayerEntity(x=200.0, y=350.0, width=60.0, height=100.0)
        entity.vy = 400.0  # Caindo

        # Atualiza a física
        self.physics.update_entity(entity, dt=0.5, level=self.level)

        # Deve apoiar o pé em y = 480 (topo do tile), logo entity.y = 480 - 100 = 380
        self.assertEqual(entity.bottom, 480.0)
        self.assertEqual(entity.y, 380.0)
        self.assertEqual(entity.vy, 0.0)
        self.assertTrue(entity.is_grounded)
        self.assertEqual(entity.state, PlayerState.IDLE)

    def test_ceiling_collision(self):
        """Valida colisão da cabeça no teto ao pular e cancelamento da velocidade vertical."""
        # Teto sólido na linha 5 (y = 5 * 32 = 160; fundo do tile = 192)
        for c in range(5, 15):
            self.level.set_solid(c, 5, 1)

        # Jogador subindo rapidamente em direção ao teto
        entity = PlayerEntity(x=200.0, y=210.0, width=60.0, height=100.0)
        entity.vy = -500.0  # Subindo

        self.physics.update_entity(entity, dt=0.1, level=self.level)

        # Deve bater a cabeça no fundo do tile (y = 192) e zerar vy
        self.assertEqual(entity.y, 192.0)
        self.assertEqual(entity.vy, 0.0)

    def test_world_left_boundary(self):
        """Garante que a entidade não ultrapasse a margem esquerda do mapa (x < 0)."""
        entity = PlayerEntity(x=20.0, y=300.0, speed=300.0)
        entity.vx = -300.0

        # Tenta avançar para além da borda esquerda
        self.physics.update_entity(entity, dt=0.2, level=self.level)

        self.assertEqual(entity.x, 0.0)
        self.assertEqual(entity.vx, 0.0)

    def test_walk_off_ledge_starts_falling(self):
        """Valida que andar para fora de uma plataforma faz o jogador começar a cair."""
        # Plataforma da coluna 0 a 4 na linha 10 (y = 320)
        for c in range(5):
            self.level.set_solid(c, 10, 1)

        entity = PlayerEntity(x=100.0, y=220.0, width=60.0, height=100.0, speed=200.0, floor_y=992.0)
        entity.is_grounded = True
        entity.bottom = 320.0

        # Move para a direita até sair da plataforma
        inp_right = InputState(move_x=1)
        for _ in range(10):
            self.physics.update_entity(entity, dt=0.1, level=self.level, input_state=inp_right)

        # Agora está no ar além da coluna 4 (x > 160)
        self.assertGreater(entity.x, 160.0)
        self.assertFalse(entity.is_grounded)
        self.assertGreater(entity.vy, 0.0)
        self.assertEqual(entity.state, PlayerState.FALLING)


if __name__ == '__main__':
    unittest.main()
