"""Carregamento tolerante a falhas dos efeitos sonoros."""

from pathlib import Path

import pygame


class Audio:
    def __init__(self) -> None:
        self.enabled = False
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=1)
            base = Path(__file__).resolve().parents[2] / "assets" / "sounds"
            for name in ("jump", "shoot", "hit", "pickup", "dash"):
                path = base / f"{name}.wav"
                if path.exists():
                    self.sounds[name] = pygame.mixer.Sound(path)
            self.enabled = True
        except pygame.error:
            pass

    def play(self, name: str) -> None:
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

