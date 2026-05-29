import pygame
from typing import List
from core.game_state import BossState
from world.tile import Tile
from settings import TILE_SIZE, GRAVITY

_RED    = (200, 40,  40)
_DARK   = (120, 20,  20)
_RAGE   = (240, 80,  0)
_WHITE  = (255, 255, 255)
_BLACK  = (0,   0,   0)
_YELLOW = (240, 210, 50)


class Boss:
    WIDTH  = 48
    HEIGHT = 52
    MAX_HP = 5

    _SPEED_1       = 2.0
    _SPEED_2       = 3.8
    _CHARGE_SPEED  = 11
    _CHARGE_CD     = 240   # frames between charges (4 s)
    _WARN_FRAMES   = 60    # pre-charge warning flash
    _PATROL_RANGE  = 7     # tiles each side

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.vx: float = -self._SPEED_1
        self.vy: float = 0.0
        self.hp = self.MAX_HP
        self.phase = 1
        self.direction = -1
        self.charging = False
        self.charge_cooldown = self._CHARGE_CD
        self._start_x = x
        self._charge_target_x = 0.0
        self._hurt_flash = 0   # white flash on hit

    @property
    def alive(self) -> bool:
        return self.hp > 0

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.WIDTH, self.HEIGHT)

    # ------------------------------------------------------------------
    def update(self, ground_tiles: List[Tile], stage_width: int,
               player_x: float) -> None:
        if not self.alive:
            return

        # phase transition
        if self.hp <= 2 and self.phase == 1:
            self.phase = 2
            self.charge_cooldown = self._WARN_FRAMES  # rage immediately charges

        # hurt flash
        if self._hurt_flash > 0:
            self._hurt_flash -= 1

        speed = self._SPEED_1 if self.phase == 1 else self._SPEED_2

        if self.charging:
            self.vx = self._CHARGE_SPEED * self.direction
            # stop when reached target or wall
            if self.direction == 1 and self.x >= self._charge_target_x:
                self._end_charge()
            elif self.direction == -1 and self.x <= self._charge_target_x:
                self._end_charge()
        else:
            # patrol
            self.vx = speed * self.direction
            if abs(self.x - self._start_x) > self._PATROL_RANGE * TILE_SIZE:
                self.direction *= -1

            # phase-2 charge countdown
            if self.phase == 2:
                self.charge_cooldown -= 1
                if self.charge_cooldown <= 0:
                    self._begin_charge(player_x)

        # gravity
        self.vy += GRAVITY
        self.x += self.vx
        self.y += self.vy

        self._resolve_vertical(ground_tiles)

        # wall clamp
        self.x = max(0.0, min(self.x, float(stage_width - self.WIDTH)))
        if self.x <= 0 or self.x >= stage_width - self.WIDTH:
            if self.charging:
                self._end_charge()
            self.direction *= -1

    def _begin_charge(self, player_x: float) -> None:
        self.charging = True
        self.direction = 1 if player_x > self.x else -1
        self._charge_target_x = player_x

    def _end_charge(self) -> None:
        self.charging = False
        self.charge_cooldown = self._CHARGE_CD
        # bounce back
        self.direction *= -1

    def _resolve_vertical(self, tiles: List[Tile]) -> None:
        r = self.rect
        for tile in tiles:
            if tile.tile_type != "ground":
                continue
            tr = tile.get_rect()
            if r.colliderect(tr):
                if self.vy >= 0:
                    self.y = float(tr.top - self.HEIGHT)
                    self.vy = 0.0
                elif self.vy < 0:
                    self.y = float(tr.bottom)
                    self.vy = 0.0

    # ------------------------------------------------------------------
    def take_hit(self) -> None:
        if self.hp > 0:
            self.hp -= 1
            self._hurt_flash = 20

    def capture_state(self) -> BossState:
        return BossState(self.x, self.y, self.vx, self.vy,
                         self.hp, self.phase, self.direction,
                         self.charging, self.charge_cooldown)

    def apply_state(self, s: BossState) -> None:
        self.x, self.y     = s.x, s.y
        self.vx, self.vy   = s.vx, s.vy
        self.hp            = s.hp
        self.phase         = s.phase
        self.direction     = s.direction
        self.charging      = s.charging
        self.charge_cooldown = s.charge_cooldown
        self._hurt_flash   = 0

    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface, camera_x: int = 0) -> None:
        if not self.alive:
            return
        dx = int(self.x) - camera_x
        dy = int(self.y)

        # body color
        if self._hurt_flash > 0 and (self._hurt_flash // 4) % 2 == 0:
            body_col = _WHITE
        elif self.charging:
            body_col = _RAGE
        elif self.phase == 2:
            body_col = _RAGE
        else:
            body_col = _RED

        pygame.draw.rect(surface, body_col,
                         (dx, dy, self.WIDTH, self.HEIGHT), border_radius=6)
        pygame.draw.rect(surface, _DARK,
                         (dx, dy, self.WIDTH, self.HEIGHT), 2, border_radius=6)

        # eyes (always angry)
        eye_y = dy + 14
        for ex, pupil_dx in [(dx + 10, -1), (dx + 34, 1)]:
            pygame.draw.circle(surface, _WHITE, (ex, eye_y), 6)
            pygame.draw.circle(surface, _BLACK, (ex + pupil_dx, eye_y + 1), 3)

        # frown
        pygame.draw.arc(surface, _BLACK,
                        (dx + 10, dy + 28, 28, 12), 3.14, 6.28, 3)

        # charge warning: flickering outline
        if self.phase == 2 and not self.charging and self.charge_cooldown <= self._WARN_FRAMES:
            if (self.charge_cooldown // 6) % 2 == 0:
                pygame.draw.rect(surface, _YELLOW,
                                 (dx - 3, dy - 3, self.WIDTH + 6, self.HEIGHT + 6),
                                 3, border_radius=8)

        # HP pips above head
        self._draw_hp_pips(surface, dx, dy)

    def _draw_hp_pips(self, surface: pygame.Surface, dx: int, dy: int) -> None:
        pip_w, pip_h = 14, 8
        gap = 4
        total_w = self.MAX_HP * pip_w + (self.MAX_HP - 1) * gap
        start_x = dx + self.WIDTH // 2 - total_w // 2
        for i in range(self.MAX_HP):
            col = _RED if i < self.hp else (50, 20, 20)
            pygame.draw.rect(surface, col,
                             (start_x + i * (pip_w + gap), dy - 14, pip_w, pip_h),
                             border_radius=2)
