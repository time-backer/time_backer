"""Stage — TMX 파일에서 타일맵을 로드한다.

assets/maps/stage{N}.tmx 를 읽어서 타일 리스트와 게임 로직을 제공한다.
맵 디자인은 Tiled 에디터(무료)로 직접 편집 가능하다.
"""

import pygame

from world.tile import Tile
from world.tilemap import load_stage_tmx
from settings import TILE_SIZE, SKY


class Stage:
    def __init__(self, stage_num=1):
        self.stage_num = stage_num
        data = load_stage_tmx(stage_num)

        self.tiles = data["tiles"]
        self.ground_tiles = data["ground_tiles"]
        self.spike_tiles = data["spike_tiles"]
        self.exit_tiles = data["exit_tiles"]
        self.switch_tiles = data["switch_tiles"]
        self.gate_tiles = data["gate_tiles"]
        self.map_w = data["map_width"]
        self.map_h = data["map_height"]

    # ── 크기 ──────────────────────────────────────────────────────────────

    # ai
    def get_pixel_width(self):
        return self.map_w * TILE_SIZE

    # ai
    def get_pixel_height(self):
        return self.map_h * TILE_SIZE

    # ── 스폰 위치 ─────────────────────────────────────────────────────────

    def get_player_start(self):
        return (TILE_SIZE, (self.map_h - 2) * TILE_SIZE - TILE_SIZE)

    def get_enemy_spawns(self):
        if self.stage_num == 2:
            return []
        y = (self.map_h - 2) * TILE_SIZE - TILE_SIZE
        return [(5 * TILE_SIZE, y), (14 * TILE_SIZE, y)]

    # ── 스위치 로직 ───────────────────────────────────────────────────────

    def check_switches(self, player_rect):
        for sw in self.switch_tiles:
            if player_rect.colliderect(sw.rect):
                sw.activated = True

    # ai
    def are_all_switches_activated(self):
        if not self.switch_tiles:
            return True
        for s in self.switch_tiles:
            if not s.activated:
                return False
        return True

    # ── 클리어 판정 ───────────────────────────────────────────────────────

    def is_clear(self, player_rect):
        exit_reached = False
        for t in self.exit_tiles:
            if player_rect.colliderect(t.rect):
                exit_reached = True
                break
        return exit_reached and self.are_all_switches_activated()

    # ── 렌더링 ────────────────────────────────────────────────────────────

    # ai
    def draw(self, surface, camera_x=0, camera_y=0):
        surface.fill(SKY)
        for tile in self.tiles:
            tile.draw(surface, camera_x, camera_y)
