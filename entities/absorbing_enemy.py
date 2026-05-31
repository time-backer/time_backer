import pygame
import pymunk

from core.game_state import EnemyState
from settings import ORANGE, RED, PURPLE
import asset_loader as A


class AbsorbingEnemy:
    """역행 횟수를 흡수해서 HP가 증가하는 특수 적 (golem)"""
    WIDTH  = 40
    HEIGHT = 40

    def __init__(self, body: pymunk.Body) -> None:
        self._body = body
        self.alive  = True
        self.hp     = 3
        self.max_hp = 3

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

    # ── 게임 로직 ─────────────────────────────────────────────────────────

    def absorb_rewind(self) -> None:
        self.hp     += 1
        self.max_hp += 1

    def take_damage(self) -> None:
        self.hp -= 1
        if self.hp <= 0:
            self.alive = False
            self._body.position = pymunk.Vec2d(-5000, 0)
            self._body.velocity = pymunk.Vec2d(0, 0)

    # ── 시간 되감기 ───────────────────────────────────────────────────────

    def capture_state(self) -> EnemyState:
        return EnemyState(self.x, self.y, 1, self.alive)

    def apply_state(self, state: EnemyState) -> None:
        self.alive = state.alive
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

    def draw(self, surface: pygame.Surface, camera_x: int = 0, camera_y: int = 0) -> None:
        if not self.alive:
            return

        draw_x = int(self.x) - camera_x
        draw_y = int(self.y) - camera_y

        t = pygame.time.get_ticks()
        if self.hp <= 1:
            frames = A.golem_lowhp
            sw, sh = 48, 48
        elif self.hp > 3:
            frames = A.golem_highhp
            sw, sh = 48, 48
        else:
            frames = A.golem
            sw, sh = 32, 32

        frame = frames[(t // 150) % len(frames)]
        ox = draw_x + self.WIDTH  // 2 - sw // 2
        oy = draw_y + self.HEIGHT // 2 - sh // 2
        surface.blit(frame, (ox, oy))

        # HP 바
        bar_w, bar_h = 36, 4
        bar_x = draw_x + 2
        bar_y = draw_y - 10
        pygame.draw.rect(surface, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h))
        ratio = self.hp / max(self.max_hp, 1)
        col = RED if self.hp <= 1 else (ORANGE if self.hp <= 3 else PURPLE)
        pygame.draw.rect(surface, col, (bar_x, bar_y, int(bar_w * ratio), bar_h))
