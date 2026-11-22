import unittest
import time
from source.modules.scenes.manager import SceneManager
from source.modules.scenes.multiplayer_menu import MultiplayerMenuScene
from source.modules.scenes.lobby_scene import LobbyScene
from source.modules.scenes.game_scene import GameScene
from source.modules.network.network_server import NetworkServer
from source.modules.network.network_client import NetworkClient
from source.modules.network.messages import MessageType, NetworkEnvelope
from source.modules.entities.player_entity import PlayerEntity


class TestMultiplayerUIAndGameScene(unittest.TestCase):
    """
    Testes específicos para os Blocos 6 e 7 da Etapa 5:
    - LobbyScene e transições de tela;
    - MultiplayerMenuScene;
    - GameScene com entidades locais e remotas.
    """

    def test_lobby_scene_creation_and_exit(self):
        """Valida inicialização, UI e descarte seguro da LobbyScene."""
        manager = SceneManager()
        manager.register("lobby", LobbyScene)
        manager.register("multiplayer_menu", MultiplayerMenuScene)

        manager.change_scene("lobby", {"is_host": True})
        current = manager.current_scene
        self.assertIsInstance(current, LobbyScene)
        self.assertTrue(current.is_host)
        self.assertEqual(len(current.buttons), 2)

        # Dispara saída
        current._on_leave()
        self.assertIsInstance(manager.current_scene, MultiplayerMenuScene)

    def test_lobby_ready_toggle(self):
        """Valida alternância de prontidão do cliente no Lobby."""
        scene = LobbyScene()
        scene.enter({"is_host": False})
        self.assertTrue(scene.is_ready)
        self.assertEqual(scene.buttons[0].text, "ESTOU PRONTO")

        scene._toggle_ready()
        self.assertFalse(scene.is_ready)
        self.assertEqual(scene.buttons[0].text, "AGUARDANDO...")

        scene._toggle_ready()
        self.assertTrue(scene.is_ready)
        self.assertEqual(scene.buttons[0].text, "ESTOU PRONTO")

    def test_game_scene_multiplayer_remote_entities_handling(self):
        """
        Valida que a GameScene suporta o modo multiplayer,
        instancia entidades remotas e processa snapshots sem erros.
        """
        scene = GameScene()
        client = NetworkClient()
        client.player_id = 1
        client._connected = True
        client._running = True

        # Injeta snapshot com Player 2 (remoto) no buffer de interpolação
        client.interpolation_buffer.add_snapshot({
            "tick": 1,
            "entities": [
                {"id": 1, "x": 200.0, "y": 300.0, "vx": 0.0, "vy": 0.0, "facing": 1, "grounded": True, "state": "idle"},
                {"id": 2, "x": 350.0, "y": 300.0, "vx": 100.0, "vy": 0.0, "facing": -1, "grounded": True, "state": "running"}
            ]
        }, local_receive_time=time.time())

        # Configura cena em modo multiplayer
        scene.is_multiplayer = True
        scene.network_client = client

        # Amostra entidades interpoladas
        entities = client.get_interpolated_entities()
        self.assertIn(1, entities)
        self.assertIn(2, entities)
        self.assertEqual(entities[2].x, 350.0)
        self.assertEqual(entities[2].facing, -1)


if __name__ == '__main__':
    unittest.main()
