import pygame
from typing import List
from core.game_state import EnemyState
from world.tile import Tile
from settings import TILE_SIZE, ORANGE, GRAVITY


class Enemy:
    WIDTH = 24
    HEIGHT = 28
    SPEED = 1.5
    PATROL_RANGE = 4  # tiles

    def __init__(self, x: float, y: float, index: int = 0) -> None:
        self.index = index
        self.x = x
        self.y = y
        self.vy: float = 0.0
        self.direction = 1  # 1=right, -1=left
        self.alive = True
        self._start_x = x

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.WIDTH, self.HEIGHT)

    def update(self, ground_tiles: List[Tile], stage_width: int) -> None:
        if not self.alive:
            return

        self.vy += GRAVITY
        self.x += self.direction * self.SPEED
        self.y += self.vy

        self._resolve_vertical(ground_tiles)

        # patrol bounds
        if abs(self.x - self._start_x) > self.PATROL_RANGE * TILE_SIZE:
            self.direction *= -1

        self.x = max(0, min(self.x, stage_width - self.WIDTH))

    def _resolve_vertical(self, tiles: List[Tile]) -> None:
        r = self.rect
        for tile in tiles:
            if tile.tile_type != "ground":
                continue
            tr = tile.get_rect()
            if r.colliderect(tr):
                if self.vy >= 0:
                    self.y = tr.top - self.HEIGHT
                    self.vy = 0

    def capture_state(self) -> EnemyState:
        return EnemyState(self.x, self.y, self.direction, self.alive)

    def apply_state(self, state: EnemyState) -> None:
        self.x = state.x
        self.y = state.y
        self.direction = state.direction
        self.alive = state.alive

    def draw(self, surface: pygame.Surface, camera_x: int = 0) -> None:
        if not self.alive:
            return
        dx = int(self.x) - camera_x
        dy = int(self.y)
        pygame.draw.rect(surface, ORANGE,
                         (dx, dy, self.WIDTH, self.HEIGHT), border_radius=3)
        # angry eyes
        eye_y = dy + 8
        if self.direction == 1:
            pygame.draw.circle(surface, (255, 255, 255), (dx + 17, eye_y), 4)
            pygame.draw.circle(surface, (0, 0, 0), (dx + 18, eye_y), 2)
        else:
            pygame.draw.circle(surface, (255, 255, 255), (dx + 7, eye_y), 4)
            pygame.draw.circle(surface, (0, 0, 0), (dx + 6, eye_y), 2)
        # frown
        pygame.draw.arc(surface, (0, 0, 0),
                        (dx + 6, dy + 16, 12, 8), 3.14, 6.28, 2)
