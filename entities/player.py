import pygame
import pymunk
from typing import List

from core.game_state import GameState
from core.physics import MOVE_VX, JUMP_VY
from settings import RED
import asset_loader as A


class Player:
    WIDTH  = 24
    HEIGHT = 30
    MAX_HP = 3

    def __init__(self, body: pymunk.Body) -> None:
        self._body = body
        self.hp = self.MAX_HP
        self.facing = 1          # 1=right, -1=left
        self.on_ground = False   # game_scene이 매 스텝 후 갱신
        self._hurt_timer = 0
        self._anim_state = "idle"
        self._state_start = 0

    # ── 위치·속도 (pymunk 바디에서 읽기) ──────────────────────────────────

    @property
    def x(self) -> float:
        return self._body.position.x - self.WIDTH / 2

    @property
    def y(self) -> float:
        return self._body.position.y - self.HEIGHT / 2

    @property
    def vx(self) -> float:
        return self._body.velocity.x / 60   # px/s → px/frame (호환용)

    @property
    def vy(self) -> float:
        return self._body.velocity.y / 60

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.WIDTH, self.HEIGHT)

    # ── 입력 처리 ─────────────────────────────────────────────────────────

    def handle_input(self, keys) -> None:
        vx = 0.0
        if keys[pygame.K_LEFT]:
            vx = -MOVE_VX
            self.facing = -1
        if keys[pygame.K_RIGHT]:
            vx = MOVE_VX
            self.facing = 1

        # 수평 속도만 교체, 수직은 pymunk에 맡김
        self._body.velocity = pymunk.Vec2d(vx, self._body.velocity.y)

        if (keys[pygame.K_SPACE] or keys[pygame.K_UP]) and self.on_ground:
            self._body.velocity = pymunk.Vec2d(vx, JUMP_VY)
            self.on_ground = False   # 이 프레임 이중 점프 방지

    def clamp_x(self, stage_width: int) -> None:
        if self.x < 0:
            self._body.position = pymunk.Vec2d(self.WIDTH / 2, self._body.position.y)
        elif self.x + self.WIDTH > stage_width:
            self._body.position = pymunk.Vec2d(
                stage_width - self.WIDTH / 2, self._body.position.y)

    # ── 피격 ──────────────────────────────────────────────────────────────

    def take_damage(self) -> None:
        if self._hurt_timer == 0:
            self.hp -= 1
            self._hurt_timer = 60

    def tick_hurt(self) -> None:
        if self._hurt_timer > 0:
            self._hurt_timer -= 1

    def is_dead(self) -> bool:
        return self.hp <= 0

    # ── 시간 되감기 ───────────────────────────────────────────────────────

    def capture_state(self, rewind_count: int) -> GameState:
        return GameState(
            player_x=self.x,
            player_y=self.y,
            player_vx=self._body.velocity.x,   # px/s 단위
            player_vy=self._body.velocity.y,
            hp=self.hp,
            rewind_count=rewind_count,
        )

    def apply_state(self, state: GameState) -> None:
        self._body.position = pymunk.Vec2d(
            state.player_x + self.WIDTH / 2,
            state.player_y + self.HEIGHT / 2,
        )
        self._body.velocity = pymunk.Vec2d(state.player_vx, state.player_vy)
        self.hp = state.hp
        self._hurt_timer = 0

    # ── 렌더링 ────────────────────────────────────────────────────────────

    SPRITE_SIZE = 48   # 원본 32×32 → 1.5배 표시

    def draw(self, surface: pygame.Surface, camera_x: int = 0, camera_y: int = 0,
             rewinding: bool = False) -> None:
        if self._hurt_timer > 0 and (self._hurt_timer // 6) % 2 == 0:
            return

        draw_x = int(self.x) - camera_x
        draw_y = int(self.y) - camera_y

        new_state = (
            "rewind" if rewinding
            else "jump"  if not self.on_ground
            else "run"   if abs(self._body.velocity.x) > 10
            else "idle"
        )
        if new_state != self._anim_state:
            self._anim_state = new_state
            self._state_start = pygame.time.get_ticks()

        frames = {
            "idle":   A.player_idle,
            "run":    A.player_run,
            "jump":   A.player_jump,
            "rewind": A.player_rewind,
        }[self._anim_state]

        elapsed = pygame.time.get_ticks() - self._state_start
        frame = frames[(elapsed // 150) % len(frames)]
        if self.facing == -1:
            frame = pygame.transform.flip(frame, True, False)

        # 1.5배 확대, 히트박스 중심 정렬
        sz = self.SPRITE_SIZE
        scaled = pygame.transform.scale(frame, (sz, sz))
        ox = draw_x + self.WIDTH  // 2 - sz // 2
        oy = draw_y + self.HEIGHT // 2 - sz // 2
        surface.blit(scaled, (ox, oy))
