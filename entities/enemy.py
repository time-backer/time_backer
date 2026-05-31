import pygame
import pymunk
from typing import Optional

from core.game_state import EnemyState
from core.physics import MOVE_VX
from settings import TILE_SIZE
import asset_loader as A


class Enemy:
    WIDTH       = 24
    HEIGHT      = 28
    SPEED_VX    = MOVE_VX * 0.5   # 적은 플레이어 절반 속도
    PATROL_RANGE = 4               # 타일 단위

    def __init__(self, body: pymunk.Body, index: int = 0) -> None:
        self._body = body
        self.index = index
        self.direction = 1   # 1=right, -1=left
        self.alive = True
        self._start_x = float(body.position.x)

    # ── 위치 ──────────────────────────────────────────────────────────────

    @property
    def x(self) -> float:
        return self._body.position.x - self.WIDTH / 2

    @property
    def y(self) -> float:
        return self._body.position.y - self.HEIGHT / 2

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.WIDTH, self.HEIGHT)

    # ── AI 업데이트 ───────────────────────────────────────────────────────

    def update(self, stage_width: int) -> None:
        if not self.alive:
            return

        # 순찰 범위 초과 → 방향 전환
        if abs(self._body.position.x - self._start_x) > self.PATROL_RANGE * TILE_SIZE:
            self.direction *= -1

        # 수평 속도 적용 (수직은 pymunk 중력에 맡김)
        self._body.velocity = pymunk.Vec2d(
            self.direction * self.SPEED_VX,
            self._body.velocity.y,
        )

        # 스테이지 경계 클램프
        half_w = self.WIDTH / 2
        if self._body.position.x < half_w:
            self._body.position = pymunk.Vec2d(half_w, self._body.position.y)
            self.direction = 1
        elif self._body.position.x > stage_width - half_w:
            self._body.position = pymunk.Vec2d(stage_width - half_w, self._body.position.y)
            self.direction = -1

    def die(self) -> None:
        """적을 죽이고 물리 바디를 화면 밖으로 이동."""
        self.alive = False
        self._body.velocity = pymunk.Vec2d(0, 0)
        self._body.position = pymunk.Vec2d(-5000, 0)

    # ── 시간 되감기 ───────────────────────────────────────────────────────

    def capture_state(self) -> EnemyState:
        return EnemyState(self.x, self.y, self.direction, self.alive)

    def apply_state(self, state: EnemyState) -> None:
        self.alive = state.alive
        self.direction = state.direction
        if self.alive:
            self._body.position = pymunk.Vec2d(
                state.x + self.WIDTH / 2,
                state.y + self.HEIGHT / 2,
            )
            self._body.velocity = pymunk.Vec2d(0, 0)
        else:
            self._body.position = pymunk.Vec2d(-5000, 0)
            self._body.velocity = pymunk.Vec2d(0, 0)

    # ── 렌더링 ────────────────────────────────────────────────────────────

    SPRITE_SIZE = 48

    def draw(self, surface: pygame.Surface, camera_x: int = 0, camera_y: int = 0) -> None:
        if not self.alive:
            return
        dx = int(self.x) - camera_x
        dy = int(self.y) - camera_y

        frame = A.patrol[(pygame.time.get_ticks() // 150) % len(A.patrol)]
        if self.direction == -1:
            frame = pygame.transform.flip(frame, True, False)

        sz = self.SPRITE_SIZE
        scaled = pygame.transform.scale(frame, (sz, sz))
        ox = dx + self.WIDTH  // 2 - sz // 2
        oy = dy + self.HEIGHT // 2 - sz // 2
        surface.blit(scaled, (ox, oy))
