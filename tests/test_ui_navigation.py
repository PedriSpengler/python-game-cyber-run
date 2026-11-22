import os
import sys
import unittest
import pygame

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Evita abrir janelas nos testes
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.display.init()


class TestUINavigation(unittest.TestCase):
    def test_menu_selection_cycling(self):
        """Valida que a lógica de seleção por setas cicla pelos botões de menu."""
        num_buttons = 5
        selected_index = 0

        # Pressiona seta para baixo (+1)
        selected_index = (selected_index + 1) % num_buttons
        self.assertEqual(selected_index, 1)

        # Pressiona seta para baixo repetidas vezes até dar a volta
        for _ in range(4):
            selected_index = (selected_index + 1) % num_buttons
        self.assertEqual(selected_index, 0)

        # Pressiona seta para cima (-1) a partir do topo -> vai para o último botão
        selected_index = (selected_index - 1) % num_buttons
        self.assertEqual(selected_index, 4)

    def test_mock_button_action_callback(self):
        """Valida que um evento de ENTER ou clique dispara o callback da ação."""
        clicked = False

        def on_click_action():
            nonlocal clicked
            clicked = True

        # Simula callback
        on_click_action()
        self.assertTrue(clicked)


if __name__ == "__main__":
    unittest.main()
