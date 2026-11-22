import os
import sys
import unittest
import pygame

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from source.modules.scenes.base import Scene
from source.modules.scenes.manager import SceneManager


class MockSceneA(Scene):
    def __init__(self, manager=None):
        super().__init__(manager)
        self.entered = False
        self.exited = False
        self.last_param = None
        self.events_received = []

    def enter(self, params=None):
        self.entered = True
        self.last_param = params

    def exit(self):
        self.exited = True

    def handle_event(self, event):
        self.events_received.append(event)
        return True

    def draw(self):
        pass


class MockSceneB(Scene):
    def __init__(self, manager=None):
        super().__init__(manager)
        self.is_overlay = True
        self.entered = False
        self.exited = False

    def enter(self, params=None):
        self.entered = True

    def exit(self):
        self.exited = True

    def draw(self):
        pass


class TestSceneManager(unittest.TestCase):
    def setUp(self):
        self.sm = SceneManager()
        self.sm.register("scene_a", MockSceneA)
        self.sm.register("scene_b", MockSceneB)

    def test_register_and_change_scene(self):
        """Valida que change_scene instancia a cena e dispara enter()."""
        self.sm.change_scene("scene_a", {"level": 1})
        self.assertEqual(len(self.sm.scene_stack), 1)
        self.assertIsInstance(self.sm.current_scene, MockSceneA)
        self.assertTrue(self.sm.current_scene.entered)
        self.assertEqual(self.sm.current_scene.last_param, {"level": 1})

    def test_change_scene_calls_exit_on_previous(self):
        """Valida que trocar de cena executa exit() na cena anterior."""
        self.sm.change_scene("scene_a")
        old_scene = self.sm.current_scene

        self.sm.change_scene("scene_b")
        self.assertTrue(old_scene.exited, "A cena anterior deveria ter chamado exit().")
        self.assertIsInstance(self.sm.current_scene, MockSceneB)

    def test_push_and_pop_scene_preserves_bottom_scene(self):
        """Valida o funcionamento da pilha (Pushdown Automata) para o Menu de Pausa."""
        self.sm.change_scene("scene_a")
        bottom_scene = self.sm.current_scene

        # Empilha cena modal (Pause)
        self.sm.push_scene("scene_b")
        self.assertEqual(len(self.sm.scene_stack), 2)
        self.assertIsInstance(self.sm.current_scene, MockSceneB)
        self.assertFalse(bottom_scene.exited, "A cena inferior NÃO pode ser finalizada com exit() no push.")

        # Desempilha (retoma o jogo)
        top_scene = self.sm.current_scene
        self.sm.pop_scene()
        self.assertEqual(len(self.sm.scene_stack), 1)
        self.assertIs(self.sm.current_scene, bottom_scene)
        self.assertTrue(top_scene.exited, "A cena do topo deve ser finalizada ao dar pop.")

    def test_handle_event_routes_to_top_scene(self):
        """Valida que eventos sao entregues exclusivamente para a cena ativa no topo."""
        self.sm.change_scene("scene_a")
        dummy_event = pygame.event.Event(pygame.USEREVENT, {"code": 42})
        self.sm.handle_event(dummy_event)

        scene_a = self.sm.current_scene
        self.assertEqual(len(scene_a.events_received), 1)
        self.assertEqual(scene_a.events_received[0].type, pygame.USEREVENT)


if __name__ == "__main__":
    unittest.main()
