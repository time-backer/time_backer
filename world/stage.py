import pygame
from typing import List, Tuple
from world.tile import Tile
from settings import TILE_SIZE, SKY

# Legend:
#   0 = air
#   1 = ground
#   S = spike
#   E = exit (goal)
#   A = switch A (Stage 2)
#   B = switch B (Stage 2)

# Stage 1 - Tutorial: Basic platforming
STAGE_1_MAP: List[str] = [
    "0000000000000000000000000",
    "0000000000000000000000000",
    "0000000000000000000000000",
    "0000000000000000000000000",
    "0000000000111000000000000",
    "0000000000000000000011100",
    "000000000000000000000000E",
    "000111000000000000000000E",
    "000000000011100000000000E",
    "0000000000000000111000000",
    "00S0000000000000000000111",
    "0000000SS0000000000000000",
    "1111111111111111111111111",
]

# Stage 2 - Double Switch Puzzle
# 스위치 B(col6,row8), A(col19,row8) → 플랫폼(row9) → 점프 → 가운데 플랫폼(row5) → 출구(row4)
STAGE_2_MAP: List[str] = [
    "0000000000000000000000000",
    "0000000000000000000000000",
    "0000000000000000000000000",
    "0000000000000000000000000",
    "000000000000E000000000000",
    "0000000011111111110000000",
    "0000000000000000000000000",
    "0000000000000000000000000",
    "000000B000000000000A00000",
    "0000011100000000001110000",
    "0000000000000000000000000",
    "00000000000S0000000000000",
    "1111111111111111111111111",
]

# Stage 3 - Afterimage Mines (simple version)
STAGE_3_MAP: List[str] = [
    "0000000000000000000000000",
    "0000000000000000000000000",
    "0000111000000000000011100",
    "0000000000000000000000000",
    "0000000000000000000000000",
    "00SSS00000000000000000000",
    "0000000000000000000000000",
    "0000000000000000000000000",
    "000000000000000000000000E",
    "000000000000000000000000E",
    "00000000000000000000S000E",
    "0000000000000000000000000",
    "1111111111111111111111111",
]

# Stage 4 - Time Mirror (laser concept - simplified)
STAGE_4_MAP: List[str] = [
    "0000000000000000000000000",
    "0000000000000000000000000",
    "0000111000000000000011100",
    "00S00000000000000000000S0",
    "0011100000000000000001110",
    "0000000000000000000000000",
    "0000000000000000000000000",
    "0000000000000000000000000",
    "0000000000000000000000000",
    "000000000000000000000000E",
    "00000000000000000000S000E",
    "0000000000000000000000000",
    "1111111111111111111111111",
]

# Stage 5 - Absorbing Enemy
STAGE_5_MAP: List[str] = [
    "0000000000000000000000000",
    "0011100111000111000000000",
    "0000000000000000000000000",
    "0000000000000000000000000",
    "00S000111000S000000000000",
    "0000000000000000000000000",
    "0000000000000000000000000",
    "0000000000000000000000000",
    "0000000000000000000000000",
    "000000000000000000000000E",
    "00000000000000000000S000E",
    "0000000000000000000000000",
    "1111111111111111111111111",
]

# Stage 6 - Final Challenge
STAGE_6_MAP: List[str] = [
    "0000000000000000000000000",
    "0000000000000000000000000",
    "0000111000000000000011100",
    "00S00000000000000000000S0",
    "0011100000000000000001110",
    "0000000000000000000000000",
    "00SSS00000000000000000000",
    "0000000000000000000000000",
    "0000000000000000000000000",
    "000000000000000000000000E",
    "00000000000S00000000S000E",
    "0000000000000000000000000",
    "1111111111111111111111111",
]

STAGE_MAPS = [
    STAGE_1_MAP,
    STAGE_2_MAP,
    STAGE_3_MAP,
    STAGE_4_MAP,
    STAGE_5_MAP,
    STAGE_6_MAP,
]


class Stage:
    def __init__(self, stage_num: int = 1, map_data: List[str] = None) -> None:
        # stage_num: 1~6
        if map_data:
            self._map = map_data
        elif 1 <= stage_num <= 6:
            self._map = STAGE_MAPS[stage_num - 1]
        else:
            self._map = STAGE_1_MAP
        
        self.stage_num = stage_num
        self.tiles: List[Tile] = []
        self.ground_tiles: List[Tile] = []
        self.spike_tiles: List[Tile] = []
        self.exit_tiles: List[Tile] = []
        self.switch_tiles: List[Tile] = []  # A, B 스위치
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
                elif cell == "A":
                    t = Tile(col_idx, row_idx, "switch_a")
                    self.tiles.append(t)
                    self.switch_tiles.append(t)
                elif cell == "B":
                    t = Tile(col_idx, row_idx, "switch_b")
                    self.tiles.append(t)
                    self.switch_tiles.append(t)

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

    def check_switches(self, player_rect: pygame.Rect) -> None:
        """플레이어가 스위치를 밟으면 활성화"""
        for switch in self.switch_tiles:
            if player_rect.colliderect(switch.rect):
                switch.activated = True
    
    def are_all_switches_activated(self) -> bool:
        """모든 스위치가 활성화되었는지 확인"""
        if not self.switch_tiles:
            return True  # 스위치가 없으면 항상 통과
        return all(s.activated for s in self.switch_tiles)
    
    def is_clear(self, player_rect: pygame.Rect) -> bool:
        """출구 도달 + 스위치 조건 확인"""
        exit_reached = any(player_rect.colliderect(t.get_rect()) for t in self.exit_tiles)
        # Stage 2는 스위치 조건 필요
        if self.stage_num == 2:
            return exit_reached and self.are_all_switches_activated()
        return exit_reached

    def draw(self, surface: pygame.Surface, camera_x: int = 0) -> None:
        surface.fill(SKY)
        for tile in self.tiles:
            tile.draw(surface, camera_x)
