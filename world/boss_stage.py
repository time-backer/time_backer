import pygame
from typing import Tuple
from world.stage import Stage
from settings import TILE_SIZE

# 30 tiles wide × 13 rows — boss arena, no exit tile
BOSS_MAP = [
    "000000000000000000000000000000",
    "000000000000000000000000000000",
    "000000000000000000000000000000",
    "000111000000000000000001110000",  # high side platforms
    "000000000000000000000000000000",
    "000000001110000001110000000000",  # mid platforms
    "000000000000000000000000000000",
    "000000000000000000000000000000",
    "001110000000000000000000011100",  # low side platforms
    "000000000000000000000000000000",
    "000000000000000000000000000000",
    "000000000000000000000000000000",
    "111111111111111111111111111111",  # floor
]


class BossStage(Stage):
    def __init__(self) -> None:
        super().__init__(BOSS_MAP)

    def get_player_start(self) -> Tuple[int, int]:
        return (2 * TILE_SIZE, 11 * TILE_SIZE - Player_H)

    def get_boss_spawn(self) -> Tuple[int, int]:
        return (24 * TILE_SIZE, 11 * TILE_SIZE - 52)

    def is_clear(self, player_rect: pygame.Rect) -> bool:
        return False  # cleared by defeating the boss, not a tile

    def draw(self, surface: pygame.Surface, camera_x: int = 0) -> None:
        from settings import SKY
        surface.fill((10, 5, 20))  # darker sky for boss stage
        for tile in self.tiles:
            tile.draw(surface, camera_x)


# small sentinel for tile calculation (avoids circular import)
Player_H = 30
