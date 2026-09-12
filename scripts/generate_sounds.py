"""Gera efeitos WAV simples apenas com a biblioteca padrao."""

from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path

RATE = 44100
OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "sounds"


def write_tone(name: str, duration: float, start_hz: float, end_hz: float, waveform: str = "square") -> None:
    frames = bytearray()
    total = int(RATE * duration)
    rng = random.Random(42)
    phase = 0.0
    for index in range(total):
        progress = index / max(1, total - 1)
        hz = start_hz + (end_hz - start_hz) * progress
        phase += 2 * math.pi * hz / RATE
        envelope = min(1.0, index / (RATE * 0.008)) * (1.0 - progress) ** 1.5
        if waveform == "noise":
            sample = rng.uniform(-1, 1)
        elif waveform == "sine":
            sample = math.sin(phase)
        else:
            sample = 1.0 if math.sin(phase) >= 0 else -1.0
        frames.extend(struct.pack("<h", int(11000 * envelope * sample)))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUTPUT / f"{name}.wav"), "wb") as wav:
        wav.setparams((1, 2, RATE, total, "NONE", "not compressed"))
        wav.writeframes(frames)


if __name__ == "__main__":
    write_tone("jump", 0.18, 240, 680, "square")
    write_tone("shoot", 0.10, 760, 240, "square")
    write_tone("hit", 0.17, 190, 65, "noise")
    write_tone("pickup", 0.20, 520, 1050, "sine")
    write_tone("dash", 0.16, 120, 420, "noise")
    print(f"Efeitos gerados em {OUTPUT}")

