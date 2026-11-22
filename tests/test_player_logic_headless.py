import unittest
import sys
from source.modules.input.input_state import InputState
from source.modules.entities.player_entity import PlayerEntity, PlayerState


class TestPlayerLogicHeadless(unittest.TestCase):
    """
    Testes unitários para PlayerEntity e InputState:
    - Execução 100% headless (sem Pygame, PyOpenGL ou display gráfico);
    - Física determinística (movimento, gravidade e pulo);
    - Estados lógicos do jogador (IDLE, RUNNING, JUMPING, FALLING);
    - Imutabilidade do InputState.
    """

    def test_player_entity_has_no_pygame_dependency(self):
        """Verifica se PlayerEntity pode ser importado e instanciado de forma puramente lógica."""
        entity = PlayerEntity(x=100.0, y=200.0)
        self.assertEqual(entity.x, 100.0)
        self.assertEqual(entity.y, 200.0)
        # Garante que PlayerEntity não tem referências a texturas ou superfícies gráficas
        self.assertFalse(hasattr(entity, 'image'))
        self.assertFalse(hasattr(entity, 'texture_stand'))
        self.assertFalse(hasattr(entity, 'textures_walk_right'))

    def test_input_state_immutability(self):
        """Garante que o InputState é uma estrutura de dados imutável (frozen)."""
        input_state = InputState(move_x=1, jump=True, tick=42)
        self.assertEqual(input_state.move_x, 1)
        self.assertTrue(input_state.jump)
        self.assertEqual(input_state.tick, 42)

        with self.assertRaises(Exception):
            input_state.move_x = -1  # Não pode ser modificado

    def test_horizontal_movement_and_facing(self):
        """Valida a movimentação horizontal e direção do personagem."""
        entity = PlayerEntity(x=100.0, y=500.0, height=100.0, speed=300.0, floor_y=600.0)
        entity.is_grounded = True
        entity.bottom = 600.0

        # Move para a direita
        inp_right = InputState(move_x=1)
        entity.update(dt=0.1, input_state=inp_right)

        self.assertEqual(entity.vx, 300.0)
        self.assertEqual(entity.x, 130.0)  # 100 + (300 * 0.1)
        self.assertEqual(entity.facing, 1)
        self.assertEqual(entity.state, PlayerState.RUNNING)

        # Move para a esquerda
        inp_left = InputState(move_x=-1)
        entity.update(dt=0.1, input_state=inp_left)

        self.assertEqual(entity.vx, -300.0)
        self.assertEqual(entity.x, 100.0)  # 130 - (300 * 0.1)
        self.assertEqual(entity.facing, -1)
        self.assertEqual(entity.state, PlayerState.RUNNING)

        # Parado
        inp_idle = InputState(move_x=0)
        entity.update(dt=0.1, input_state=inp_idle)

        self.assertEqual(entity.vx, 0.0)
        self.assertEqual(entity.state, PlayerState.IDLE)

    def test_jump_physics_and_gravity(self):
        """Valida a física de pulo, aplicação da gravidade e aterrissagem no chão."""
        floor_y = 600.0
        entity = PlayerEntity(x=100.0, y=500.0, height=100.0, gravity=1200.0, jump_speed=-600.0, floor_y=floor_y)
        entity.is_grounded = True
        entity.bottom = floor_y  # y = 500

        # Dispara pulo
        inp_jump = InputState(jump=True)
        entity.update(dt=0.016, input_state=inp_jump)

        self.assertTrue(entity.just_jumped)
        self.assertFalse(entity.is_grounded)
        self.assertLess(entity.vy, 0)
        self.assertEqual(entity.state, PlayerState.JUMPING)

        # Avança o tempo até o ápice do pulo e início da queda
        for _ in range(35):
            entity.update(dt=0.016, input_state=InputState())

        self.assertGreater(entity.vy, 0)  # Agora está caindo
        self.assertEqual(entity.state, PlayerState.FALLING)

        # Avança tempo suficiente para aterrissar no chão
        for _ in range(50):
            entity.update(dt=0.016, input_state=InputState())

        self.assertTrue(entity.is_grounded)
        self.assertEqual(entity.bottom, floor_y)
        self.assertEqual(entity.vy, 0.0)
        self.assertEqual(entity.state, PlayerState.IDLE)


if __name__ == '__main__':
    unittest.main()
