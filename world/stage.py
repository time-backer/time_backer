import pygame
from typing import List, Tuple
from world.tile import Tile
from settings import TILE_SIZE, SKY

# Legend:
#   0 = air
#   1 = ground
#   S = spike
#   E = exit (goal)
STAGE_1_MAP: List[str] = [
    "0000000000000000000000000000",
    "0000000000000000000000000000",
    "0000000000000000000000000000",
    "0000000000000000000000000000",
    "0000000000000000000000000000",
    "0000000000111000000000000000",
    "0000000000000000000001110000",
    "000000000000000000000000000E",
    "000111000000000000000000000E",
    "000000000011100000000000000E",
    "0000000000000000111000000000",
    "00S00000000000000000000111000",
    "1111111111111111111111111111",
]


class Stage:
    def __init__(self, map_data: List[str] = None) -> None:
        self._map = map_data or STAGE_1_MAP
        self.tiles: List[Tile] = []
        self.ground_tiles: List[Tile] = []
        self.spike_tiles: List[Tile] = []
        self.exit_tiles: List[Tile] = []
        self._parse()

    def _parse(self) -> None:
        for row_idx, row in enumerate(self._map):
            for col_idx, cell in enumerate(row):
                if cell == "1":
                    t = Tile(col_idx, row_idx, "ground")
                    self.tiles.append(t)
                    self.ground_tiles.append(t)
                elif cell == "S":
                    t = Tile(col_idx, row_idx, "spike")
                    self.tiles.append(t)
                    self.spike_tiles.append(t)
                elif cell == "E":
                    t = Tile(col_idx, row_idx, "exit")
                    self.tiles.append(t)
                    self.exit_tiles.append(t)

    @property
    def pixel_width(self) -> int:
        return len(self._map[0]) * TILE_SIZE

    @property
    def pixel_height(self) -> int:
        return len(self._map) * TILE_SIZE

    def get_player_start(self) -> Tuple[int, int]:
        return (TILE_SIZE, (len(self._map) - 2) * TILE_SIZE - TILE_SIZE)

    def get_enemy_spawns(self) -> List[Tuple[int, int]]:
        return [
            (5 * TILE_SIZE, (len(self._map) - 2) * TILE_SIZE - TILE_SIZE),
            (14 * TILE_SIZE, (len(self._map) - 2) * TILE_SIZE - TILE_SIZE),
        ]

    def is_clear(self, player_rect: pygame.Rect) -> bool:
        return any(player_rect.colliderect(t.get_rect()) for t in self.exit_tiles)

    def draw(self, surface: pygame.Surface, camera_x: int = 0) -> None:
        surface.fill(SKY)
        for tile in self.tiles:
            tile.draw(surface, camera_x)
