import os
import json
from .sounds import sounds


class Settings:
    """Gerencia e persiste as configuracoes do jogo (Audio, HUD, etc)."""
    def __init__(self):
        self.file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/settings.json"))
        
        # Valores padrao
        self.music_volume: float = 0.2
        self.sfx_volume: float = 0.3
        self.music_enabled: bool = True
        self.sfx_enabled: bool = True
        self.show_fps: bool = True

        self.load()

    def apply(self):
        """Aplica as configuracoes aos subsistemas de audio e tela."""
        effective_music = self.music_volume if self.music_enabled else 0.0
        sounds.set_music_volume(effective_music)

        effective_sfx = self.sfx_volume if self.sfx_enabled else 0.0
        sounds.set_sfx_volume(effective_sfx)

    def save(self):
        """Persiste as configuracoes em arquivo JSON simples."""
        try:
            data = {
                "music_volume": round(self.music_volume, 2),
                "sfx_volume": round(self.sfx_volume, 2),
                "music_enabled": self.music_enabled,
                "sfx_enabled": self.sfx_enabled,
                "show_fps": self.show_fps
            }
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            print(f"Erro ao salvar configuracoes: {e}")
            return False

    def load(self):
        """Carrega as configuracoes salvas do arquivo JSON."""
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.music_volume = float(data.get("music_volume", 0.2))
                self.sfx_volume = float(data.get("sfx_volume", 0.3))
                self.music_enabled = bool(data.get("music_enabled", True))
                self.sfx_enabled = bool(data.get("sfx_enabled", True))
                self.show_fps = bool(data.get("show_fps", True))
                self.apply()
                return True
        except Exception as e:
            print(f"Aviso ao carregar configuracoes: {e}")
        return False


settings = Settings()
