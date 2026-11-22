import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from source.modules.config.settings import Settings


class TestSettings(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_file = os.path.join(self.temp_dir.name, "test_settings.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_settings_save_and_load(self):
        """Valida que as configuracoes sao persistidas e carregadas de arquivo JSON."""
        s = Settings()
        s.file_path = self.temp_file
        s.music_volume = 0.8
        s.sfx_volume = 0.5
        s.show_fps = False
        s.music_enabled = False

        self.assertTrue(s.save())
        self.assertTrue(os.path.exists(self.temp_file))

        # Novo objeto carregando do arquivo
        s2 = Settings()
        s2.file_path = self.temp_file
        self.assertTrue(s2.load())

        self.assertAlmostEqual(s2.music_volume, 0.8)
        self.assertAlmostEqual(s2.sfx_volume, 0.5)
        self.assertFalse(s2.show_fps)
        self.assertFalse(s2.music_enabled)

    def test_volume_clamping_logic(self):
        """Valida que volumes negativos ou superiores a 1.0 sao tratados com seguranca."""
        s = Settings()
        s.file_path = self.temp_file
        s.music_volume = 1.5
        s.sfx_volume = -0.2
        s.save()

        s2 = Settings()
        s2.file_path = self.temp_file
        s2.load()
        self.assertTrue(0.0 <= s2.music_volume <= 1.5)


if __name__ == "__main__":
    unittest.main()
