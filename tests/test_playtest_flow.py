import unittest
from unittest.mock import MagicMock
import pygame
from source.modules.scenes.manager import SceneManager
from source.modules.scenes.game_scene import GameScene
from source.modules.scenes.pause_menu import PauseMenuScene
from source.modules.scenes.editor_scene import EditorScene
from source.modules.ui.levels import Level1


class TestPlaytestFlow(unittest.TestCase):
    """
    Testes de integração do fluxo de Playtest:
    - Transição da EditorScene para GameScene via push_scene();
    - Localização determinística de spawn seguro para o jogador;
    - Detecção de Playtest no PauseMenu;
    - Retorno seguro ao editor via pop_scene(), preservando o estado e alterações não salvas.
    """

    def setUp(self):
        self.manager = SceneManager()
        self.manager.register_scene("editor", EditorScene)
        self.manager.register_scene("game", GameScene)
        self.manager.register_scene("pause", PauseMenuScene)

    def test_safe_spawn_calculation(self):
        """Valida que o spawn é calculado acima do primeiro bloco sólido encontrado."""
        game_scene = GameScene(self.manager)
        level = Level1()
        level.create_new_map(width=20, height=20, default_floor=False)

        # Coloca um bloco sólido na coluna 5, linha 12
        level.set_tile_id(5, 12, 1)

        spawn_x, spawn_y = game_scene._find_safe_spawn(level)
        self.assertEqual(spawn_x, 5 * 32)
        # Deve estar acima da linha 12: (12 * 32) - 100 = 384 - 100 = 284
        self.assertEqual(spawn_y, (12 * 32) - 100)

    def test_playtest_push_and_return_to_editor(self):
        """Valida que o ciclo de Playtest mantém a EditorScene na pilha e retorna sem corrupção."""
        # 1. Entra na EditorScene
        self.manager.change_scene("editor")
        editor_scene = self.manager.get_current_scene()
        self.assertIsInstance(editor_scene, EditorScene)

        # Simula alteração no editor
        editor_scene.editor.has_unsaved_changes = True

        # 2. Inicia Playtest empilhando GameScene
        editor_scene._on_playtest()
        current_scene = self.manager.get_current_scene()
        self.assertIsInstance(current_scene, GameScene)
        self.assertTrue(current_scene.is_playtest)
        self.assertEqual(len(self.manager.stack), 2)  # [EditorScene, GameScene]

        # 3. Abre PauseMenu durante Playtest
        self.manager.push_scene("pause")
        pause_scene = self.manager.get_current_scene()
        self.assertIsInstance(pause_scene, PauseMenuScene)
        self.assertEqual(len(self.manager.stack), 3)  # [EditorScene, GameScene, PauseMenuScene]

        # Verifica se a última opção é "RETORNAR AO EDITOR"
        last_button = pause_scene.buttons[-1]
        self.assertEqual(last_button.text, "RETORNAR AO EDITOR")

        # 4. Clica em "RETORNAR AO EDITOR"
        pause_scene._on_exit_game()

        # Deve ter desempilhado PauseMenu e GameScene, retornando para EditorScene
        self.assertEqual(len(self.manager.stack), 1)
        resumed_editor = self.manager.get_current_scene()
        self.assertIs(resumed_editor, editor_scene)
        self.assertTrue(resumed_editor.editor.has_unsaved_changes)


if __name__ == '__main__':
    unittest.main()
