"""Stage — TMX 파일에서 타일맵을 로드한다.

assets/maps/stage{N}.tmx 를 읽어서 타일 리스트와 게임 로직을 제공한다.
맵 디자인은 Tiled 에디터(무료)로 직접 편집 가능하다.
"""

import pygame
from typing import List, Tuple

from world.tile import Tile
from world.tilemap import load_stage_tmx
from settings import TILE_SIZE, SKY


class Stage:
    def __init__(self, stage_num: int = 1) -> None:
        self.stage_num = stage_num
        data = load_stage_tmx(stage_num)

        self.tiles:        List[Tile] = data["tiles"]
        self.ground_tiles: List[Tile] = data["ground_tiles"]
        self.spike_tiles:  List[Tile] = data["spike_tiles"]
        self.exit_tiles:   List[Tile] = data["exit_tiles"]
        self.switch_tiles: List[Tile] = data["switch_tiles"]
        self._map_w: int = data["map_width"]
        self._map_h: int = data["map_height"]

    # ── 크기 ──────────────────────────────────────────────────────────────

    @property
    def pixel_width(self) -> int:
        return self._map_w * TILE_SIZE

    @property
    def pixel_height(self) -> int:
        return self._map_h * TILE_SIZE

    # ── 스폰 위치 ─────────────────────────────────────────────────────────

    def get_player_start(self) -> Tuple[int, int]:
        return (TILE_SIZE, (self._map_h - 2) * TILE_SIZE - TILE_SIZE)

    def get_enemy_spawns(self) -> List[Tuple[int, int]]:
        y = (self._map_h - 2) * TILE_SIZE - TILE_SIZE
        return [(5 * TILE_SIZE, y), (14 * TILE_SIZE, y)]

    # ── 스위치 로직 ───────────────────────────────────────────────────────

    def check_switches(self, player_rect: pygame.Rect) -> None:
        for sw in self.switch_tiles:
            if player_rect.colliderect(sw.rect):
                sw.activated = True

    def are_all_switches_activated(self) -> bool:
        if not self.switch_tiles:
            return True
        return all(s.activated for s in self.switch_tiles)

    # ── 클리어 판정 ───────────────────────────────────────────────────────

    def is_clear(self, player_rect: pygame.Rect) -> bool:
        exit_reached = any(player_rect.colliderect(t.get_rect()) for t in self.exit_tiles)
        if self.stage_num == 2:
            return exit_reached and self.are_all_switches_activated()
        return exit_reached

    # ── 렌더링 ────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface, camera_x: int = 0, camera_y: int = 0) -> None:
        surface.fill(SKY)
        for tile in self.tiles:
            tile.draw(surface, camera_x, camera_y)
