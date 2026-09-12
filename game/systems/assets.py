"""Sprites pixel-art construidos em memoria, sem arquivos externos."""

from __future__ import annotations

import pygame

from game import config as cfg


def pixel_sprite(pattern: list[str], palette: dict[str, tuple[int, int, int]], scale: int = 4) -> pygame.Surface:
    width = max(len(row) for row in pattern)
    surface = pygame.Surface((width * scale, len(pattern) * scale), pygame.SRCALPHA)
    for y, row in enumerate(pattern):
        for x, symbol in enumerate(row):
            if symbol != ".":
                pygame.draw.rect(surface, palette[symbol], (x * scale, y * scale, scale, scale))
    return surface


def player_sprite() -> pygame.Surface:
    return pixel_sprite([
        "...CCCC...", "..CCCCCC..", "..CWWCCC..", "..CCCCCC..",
        "....CC....", "..MMMMMM..", ".MMCCCCMM.", ".M.CCCC.M.",
        "...C..C...", "..CC..CC..", "..CC..CC..", ".CCC..CCC.",
    ], {"C": cfg.CYAN, "M": cfg.MAGENTA, "W": cfg.INK}, 4)


def enemy_sprite() -> pygame.Surface:
    return pixel_sprite([
        "..RRRRRR..", ".RRRRRRRR.", ".RYYRRYYR.", ".RRRRRRRR.",
        "...RRRR...", "..PPPPPP..", ".PPRRRRPP.", ".P.RRRR.P.",
        "...R..R...", "..RR..RR..", ".RRR..RRR.",
    ], {"R": cfg.RED, "P": cfg.PURPLE, "Y": cfg.YELLOW}, 4)


def item_sprite(kind: str) -> pygame.Surface:
    if kind == "health":
        return pixel_sprite(["..GG..", ".GGGG.", "GGGGGG", ".GGGG.", "..GG.."], {"G": cfg.GREEN}, 4)
    return pixel_sprite(["..YY..", ".YWWY.", "YWYYWY", ".YWWY.", "..YY.."], {"Y": cfg.YELLOW, "W": cfg.INK}, 4)

