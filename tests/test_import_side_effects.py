import os
import sys
import unittest

# Adiciona a raiz do projeto ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestImportSideEffects(unittest.TestCase):
    def test_import_engine_does_not_initialize_display(self):
        """Verifica que a importação de engine não inicializa a janela ou hardware."""
        import pygame
        from source.modules.display import display
        from source.modules.engine import engine

        # display.is_initialized deve ser False antes de engine.initialize() ser chamado
        self.assertFalse(display.is_initialized, "Display não deveria estar inicializado logo após o import.")
        self.assertFalse(engine.initialized, "Engine não deveria estar inicializado logo após o import.")
        self.assertIsNone(display.screen, "Display.screen deveria ser None antes da inicialização explícita.")


if __name__ == "__main__":
    unittest.main()
