"""BossStage — stage7.tmx 에서 보스 스테이지 타일맵을 로드한다."""

import pygame
from typing import List, Tuple

from world.tile import Tile
from world.tilemap import load_stage_tmx
from settings import TILE_SIZE


class BossStage:
    def __init__(self) -> None:
        self.stage_num = 7
        data = load_stage_tmx(7)

        self.tiles:        List[Tile] = data["tiles"]
        self.ground_tiles: List[Tile] = data["ground_tiles"]
        self.spike_tiles:  List[Tile] = data["spike_tiles"]
        self.exit_tiles:   List[Tile] = data["exit_tiles"]
        self.switch_tiles: List[Tile] = []   # 보스 스테이지는 스위치 없음
        self._map_w: int = data["map_width"]
        self._map_h: int = data["map_height"]

    @property
    def pixel_width(self) -> int:
        return self._map_w * TILE_SIZE

    @property
    def pixel_height(self) -> int:
        return self._map_h * TILE_SIZE

    def get_player_start(self) -> Tuple[int, int]:
        return (2 * TILE_SIZE, (self._map_h - 2) * TILE_SIZE - TILE_SIZE)

    def get_boss_position(self) -> Tuple[int, int]:
        return (12 * TILE_SIZE - 36, 3 * TILE_SIZE)

    def get_enemy_spawns(self) -> List[Tuple[int, int]]:
        return []

    def check_switches(self, player_rect: pygame.Rect) -> None:
        pass

    def are_all_switches_activated(self) -> bool:
        return True

    def is_clear(self, player_rect: pygame.Rect) -> bool:
        return False   # 보스 처치로만 클리어 (GameScene에서 처리)

    def draw(self, surface: pygame.Surface, camera_x: int = 0, camera_y: int = 0) -> None:
        surface.fill((10, 10, 20))
        for tile in self.tiles:
            tile.draw(surface, camera_x, camera_y)
