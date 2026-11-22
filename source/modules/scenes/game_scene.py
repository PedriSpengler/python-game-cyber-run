import pygame
from .base import Scene
from ..game import game
from ..config.sounds import sounds
from ..config.settings import settings
from ..constants import WIDTH, HEIGHT, SIZE_PLAYER
from ..camera import Camera2D
from ..ui.parallax import ParallaxBackground
from ..rendering.player_view import PlayerView
from ..entities.player_entity import PlayerEntity, PlayerState
from ..network.messages import MessageType


class GameScene(Scene):
    """
    Cena de Jogo que encapsula a partida ativa do TAC3.
    Integra a Camera2D com acompanhamento suave e o ParallaxBackground multicamadas.
    """
    def __init__(self, manager=None):
        super().__init__(manager)
        self.initialized = False
        self.is_playtest = False
        self.camera = Camera2D()
        self.parallax = ParallaxBackground()

        # Suporte a Multiplayer em LAN (Bloco 6)
        self.is_multiplayer: bool = False
        self.network_client = None
        self.network_server = None
        self.remote_views: dict[int, PlayerView] = {}
        self.remote_entities: dict[int, PlayerEntity] = {}

    def _find_safe_spawn(self, level) -> tuple[float, float]:
        """Localiza a primeira coluna com chão sólido para evitar spawn no vazio."""
        from ..constants import TILE_SIZE, SIZE_PLAYER
        if level and level.tiles:
            num_cols = len(level.tiles[0]) if len(level.tiles) > 0 else 0
            num_lines = len(level.tiles)
            for c in range(min(50, num_cols)):
                for l in range(num_lines):
                    if level.tiles[l][c] is not None:
                        spawn_x = c * TILE_SIZE
                        spawn_y = max(0, (l * TILE_SIZE) - SIZE_PLAYER[1])
                        return float(spawn_x), float(spawn_y)
        return 100.0, 500.0

    def enter(self, params=None):
        should_restart = params.get("restart", False) if params else False
        self.is_playtest = params.get("playtest", False) if params else False
        self.is_multiplayer = bool(params.get("is_multiplayer", False)) if params else False
        self.network_client = params.get("network_client") if params else None
        self.network_server = params.get("network_server") if params else None

        if not self.initialized or should_restart or self.is_playtest or self.is_multiplayer:
            game.init_assets()
            self.initialized = True
            sounds.play_music()

            # Posicionamento inicial
            if self.is_playtest and params and "level" in params:
                game.level1 = params["level"]
                spawn_x, spawn_y = self._find_safe_spawn(game.level1)
                if hasattr(game, 'player') and game.player:
                    game.player.rect.topleft = (int(spawn_x), int(spawn_y))
                    game.player.x = spawn_x
                    game.player.y = spawn_y
            elif self.is_multiplayer and self.network_client:
                # Posições de spawn distintas por jogador
                pid = self.network_client.player_id or 1
                spawn_x = 200.0 if pid == 1 else 350.0
                spawn_y = 300.0
                if hasattr(game, 'player') and game.player:
                    game.player.rect.topleft = (int(spawn_x), int(spawn_y))
                    game.player.entity.x = spawn_x
                    game.player.entity.y = spawn_y

            # Obtem dimensoes reais da fase para a camera
            world_w, world_h = game.level1.get_world_size()
            self.camera.set_world_bounds(world_w, world_h)

            # Inicializa camadas Parallax (nuvens, montanhas, arvores)
            self.parallax.initialize_default_layers(enable_cloud_drift=True)

            # Posiciona a camera inicialmente sobre o jogador
            if hasattr(game, 'player') and game.player:
                self.camera.follow(game.player.rect, dt=0.0)
        else:
            # Retorno da pausa: despausa a musica
            sounds.unpause_music()

    def handle_event(self, event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                sounds.pause_music()
                if self.manager:
                    self.manager.push_scene("pause")
                return True
        return False

    def update(self, dt: float):
        if hasattr(game, 'player') and game.player:
            # Modo Multiplayer
            if self.is_multiplayer and self.network_client:
                # 1. Checa desconexão do servidor
                if not self.network_client.is_connected():
                    if self.manager:
                        self.manager.change_scene("multiplayer_menu")
                    return

                # 2. Transmite comandos locais do jogador via UDP
                if hasattr(game, 'input_manager') and game.input_manager:
                    input_state = game.input_manager.get_current_state()
                    self.network_client.send_input(
                        move_x=input_state.move_x,
                        jump=input_state.jump,
                        jump_held=input_state.jump_held,
                        tick=input_state.tick
                    )

                # 3. Atualiza simulação física local
                game.player.update(dt, level=getattr(game, 'level1', None))

                # 4. Amostra e interpola entidades remotas recebidas da rede
                entities = self.network_client.get_interpolated_entities()
                my_pid = self.network_client.player_id

                # Reconciliação suave do jogador local
                if my_pid and my_pid in entities:
                    srv_e = entities[my_pid]
                    drift_x = srv_e.x - game.player.entity.x
                    drift_y = srv_e.y - game.player.entity.y
                    if abs(drift_x) > 30.0 or abs(drift_y) > 30.0:
                        game.player.entity.x += drift_x * 0.25
                        game.player.entity.y += drift_y * 0.25
                        game.player.rect.topleft = (int(game.player.entity.x), int(game.player.entity.y))

                # Atualiza jogadores remotos com Flyweight de texturas
                shared_view = getattr(game.player, 'view', None)
                for eid, remote_e in entities.items():
                    if eid != my_pid:
                        if eid not in self.remote_views:
                            self.remote_views[eid] = PlayerView(shared_view=shared_view)
                            self.remote_entities[eid] = PlayerEntity(x=remote_e.x, y=remote_e.y)

                        rent = self.remote_entities[eid]
                        rent.x = remote_e.x
                        rent.y = remote_e.y
                        rent.vx = remote_e.vx
                        rent.vy = remote_e.vy
                        rent.facing = remote_e.facing
                        rent.is_grounded = remote_e.grounded
                        rent.state = PlayerState(remote_e.state) if remote_e.state in ("idle", "running", "jumping", "falling") else PlayerState.IDLE
                        self.remote_views[eid].update(dt, rent)

            else:
                # Modo Single Player tradicional
                game.player.update(dt, level=getattr(game, 'level1', None))

            # A camera acompanha suavemente o jogador local
            self.camera.follow(game.player.rect, dt)

        # Atualiza camadas Parallax (movimento autonomo suave)
        self.parallax.update(dt)

        if settings.show_fps and hasattr(game, 'panel') and game.panel:
            game.panel.update(dt)

    def draw(self):
        # 1. Renderiza o cenario Parallax com as velocidades relativas
        self.parallax.draw(self.camera.x)

        # 2. Renderiza os blocos da fase visiveis na camera (Frustum Culling 2D)
        if hasattr(game, 'level1') and game.level1:
            game.level1.draw(self.camera)

        # 3. Renderiza o jogador local com a transformacao da camera
        if hasattr(game, 'player') and game.player:
            game.player.draw((self.camera.x, self.camera.y))

            # Badge indicativo do Jogador Local (P1 azul ou P2 verde)
            if self.is_multiplayer and self.network_client:
                pid = self.network_client.player_id or 1
                badge_color = (0.2, 0.6, 1.0, 0.9) if pid == 1 else (0.2, 0.9, 0.4, 0.9)
                sx = game.player.entity.x - self.camera.x + 18
                sy = game.player.entity.y - self.camera.y - 12
                utils.draw_colored_quad(sx, sy, 24, 8, badge_color)

        # 4. Renderiza jogadores remotos (Multiplayer)
        if self.is_multiplayer:
            for eid, r_view in self.remote_views.items():
                if eid in self.remote_entities:
                    rent = self.remote_entities[eid]
                    r_view.draw(rent, (self.camera.x, self.camera.y))
                    # Badge indicativo do Jogador Remoto
                    badge_color = (0.2, 0.6, 1.0, 0.9) if eid == 1 else (0.2, 0.9, 0.4, 0.9)
                    sx = rent.x - self.camera.x + 18
                    sy = rent.y - self.camera.y - 12
                    utils.draw_colored_quad(sx, sy, 24, 8, badge_color)

        # 5. Renderiza a interface de usuario (HUD fixo na tela)
        if settings.show_fps and hasattr(game, 'panel') and game.panel:
            game.panel.draw()

    def exit(self):
        sounds.stop_music()
        self.parallax.destroy()
        for r_view in self.remote_views.values():
            r_view.destroy()
        self.remote_views.clear()
        self.remote_entities.clear()

        if self.is_multiplayer:
            if self.network_client:
                self.network_client.disconnect()
                self.network_client = None
            if self.network_server:
                self.network_server.shutdown()
                self.network_server = None

        self.initialized = False
