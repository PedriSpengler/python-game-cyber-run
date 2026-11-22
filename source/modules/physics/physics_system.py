from ..collision.collision_system import CollisionSystem
from ..entities.player_entity import PlayerState


class PhysicsSystem:
    """
    Sistema físico determinístico para entidades 2D em plataforma.
    Aplica forças, integra velocidades e coordena a resolução contínua de colisões
    em passos discretos por eixo (Horizontal e depois Vertical).
    Isolado de Pygame e PyOpenGL.
    """
    def __init__(self, collision_system: CollisionSystem = None):
        self.collision_system = collision_system or CollisionSystem()

    def update_entity(self, entity, dt: float, level=None, input_state=None):
        """
        Executa um passo completo de simulação física sobre a entidade:
        1. Aplicação de inputs (se fornecido);
        2. Integração horizontal e resolução de colisões em X (swept);
        3. Aplicação de gravidade, integração vertical e resolução de colisões em Y (swept);
        4. Atualização do estado de animação/lógica.
        """
        if dt <= 0:
            return

        # 1. Comandos de Entrada
        if input_state is not None and hasattr(entity, 'apply_input'):
            entity.apply_input(input_state)

        # 2. Movimentação e Colisão Horizontal (Eixo X)
        prev_x = entity.x
        entity.x += entity.vx * dt
        self.collision_system.resolve_horizontal(entity, level, prev_x=prev_x)

        # 3. Gravidade, Movimentação e Colisão Vertical (Eixo Y)
        prev_y = entity.y
        entity.apply_gravity(dt)
        entity.y += entity.vy * dt

        # Redefine grounded antes de testar aterrissagem neste ciclo
        entity.is_grounded = False
        self.collision_system.resolve_vertical(entity, level, prev_y=prev_y)

        # 4. Atualização de Estado Lógico (State Machine)
        if hasattr(entity, 'state'):
            if not entity.is_grounded:
                if entity.vy < 0:
                    entity.state = PlayerState.JUMPING
                else:
                    entity.state = PlayerState.FALLING
            else:
                if abs(entity.vx) > 0.001:
                    entity.state = PlayerState.RUNNING
                else:
                    entity.state = PlayerState.IDLE
