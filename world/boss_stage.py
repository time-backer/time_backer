import pygame
from typing import List, Tuple
from world.tile import Tile
from settings import TILE_SIZE


# Boss Stage Map
BOSS_MAP: List[str] = [
    "0000000000000000000000000",
    "0000000000000000000000000",
    "0000000000000000000000000",
    "0000000000000000000000000",
    "0000111000000000000111000",
    "0000000000000000000000000",
    "0111000000000000000000110",
    "0000000000000000000000000",
    "1110000000000000000000111",
    "0000000000000000000000000",
    "0000000000000000000000000",
    "0000000000000000000000000",
    "1111111111111111111111111",
]


class BossStage:
    """보스 스테이지 - 시간의 수호자"""
    def __init__(self) -> None:
        self._map = BOSS_MAP
        self.stage_num = 7  # Boss stage
        self.tiles: List[Tile] = []
        self.ground_tiles: List[Tile] = []
        self.spike_tiles: List[Tile] = []
        self.exit_tiles: List[Tile] = []
        self.switch_tiles: List[Tile] = []
        self._parse()
    
    def _parse(self) -> None:
        for row_idx, row in enumerate(self._map):
            for col_idx, cell in enumerate(row):
                if cell == "1":
                    t = Tile(col_idx, row_idx, "ground")
                    self.tiles.append(t)
                    self.ground_tiles.append(t)
    
    @property
    def pixel_width(self) -> int:
        return len(self._map[0]) * TILE_SIZE
    
    @property
    def pixel_height(self) -> int:
        return len(self._map) * TILE_SIZE
    
    def get_player_start(self) -> Tuple[int, int]:
        """플레이어 시작 위치 (좌하단)"""
        return (2 * TILE_SIZE, (len(self._map) - 2) * TILE_SIZE - TILE_SIZE)
    
    def get_boss_position(self) -> Tuple[int, int]:
        """보스 위치 (중앙 상단)"""
        return (12 * TILE_SIZE - 36, 3 * TILE_SIZE)
    
    def get_enemy_spawns(self) -> List[Tuple[int, int]]:
        """보스 스테이지는 일반 적 없음"""
        return []
    
    def check_switches(self, player_rect: pygame.Rect) -> None:
        """보스 스테이지는 스위치 없음"""
        pass
    
    def are_all_switches_activated(self) -> bool:
        return True
    
    def is_clear(self, player_rect: pygame.Rect) -> bool:
        """보스 스테이지는 보스 처치로 클리어 (GameScene에서 처리)"""
        return False
    
    def draw(self, surface: pygame.Surface, camera_x: int = 0) -> None:
        # 어두운 배경 (보스 스테이지)
        surface.fill((10, 10, 20))
        for tile in self.tiles:
            tile.draw(surface, camera_x)
