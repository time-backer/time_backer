import pygame
from typing import List
from core.game_state import GameState
from world.tile import Tile
from settings import (
    TILE_SIZE, MOVE_SPEED, JUMP_FORCE, GRAVITY,
    BLUE, WHITE, RED,
)


class Player:
    WIDTH = 24
    HEIGHT = 30
    MAX_HP = 3

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.on_ground = False
        self.hp = self.MAX_HP
        self.facing = 1  # 1=right, -1=left
        self._hurt_timer = 0  # invincibility frames after hit

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.WIDTH, self.HEIGHT)

    # ------------------------------------------------------------------
    # Input & physics
    # ------------------------------------------------------------------
    def handle_input(self, keys) -> None:
        self.vx = 0
        if keys[pygame.K_LEFT]:
            self.vx = -MOVE_SPEED
            self.facing = -1
        if keys[pygame.K_RIGHT]:
            self.vx = MOVE_SPEED
            self.facing = 1
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP]) and self.on_ground:
            self.vy = JUMP_FORCE
            self.on_ground = False

    def update(self, ground_tiles: List[Tile], stage_width: int) -> None:
        self.vy += GRAVITY
        self.x += self.vx
        self._resolve_horizontal(ground_tiles)
        self.y += self.vy
        self.on_ground = False
        self._resolve_vertical(ground_tiles)

        # clamp to stage
        self.x = max(0, min(self.x, stage_width - self.WIDTH))

        if self._hurt_timer > 0:
            self._hurt_timer -= 1

    def _resolve_horizontal(self, tiles: List[Tile]) -> None:
        r = self.rect
        for tile in tiles:
            if tile.tile_type != "ground":
                continue
            tr = tile.get_rect()
            if r.colliderect(tr):
                if self.vx > 0:
                    self.x = tr.left - self.WIDTH
                elif self.vx < 0:
                    self.x = tr.right

    def _resolve_vertical(self, tiles: List[Tile]) -> None:
        r = self.rect
        for tile in tiles:
            if tile.tile_type != "ground":
                continue
            tr = tile.get_rect()
            if r.colliderect(tr):
                if self.vy > 0:
                    self.y = tr.top - self.HEIGHT
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:
                    self.y = tr.bottom
                    self.vy = 0

    # ------------------------------------------------------------------
    # Damage
    # ------------------------------------------------------------------
    def take_damage(self) -> None:
        if self._hurt_timer == 0:
            self.hp -= 1
            self._hurt_timer = 60  # 1 second grace

    def is_dead(self) -> bool:
        return self.hp <= 0

    # ------------------------------------------------------------------
    # Time rewind
    # ------------------------------------------------------------------
    def capture_state(self, rewind_count: int) -> GameState:
        from core.game_state import GameState
        return GameState(
            player_x=self.x,
            player_y=self.y,
            player_vx=self.vx,
            player_vy=self.vy,
            hp=self.hp,
            rewind_count=rewind_count,
        )

    def apply_state(self, state: GameState) -> None:
        self.x = state.player_x
        self.y = state.player_y
        self.vx = state.player_vx
        self.vy = state.player_vy
        self.hp = state.hp
        self._hurt_timer = 0

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface, camera_x: int = 0) -> None:
        draw_x = int(self.x) - camera_x
        draw_y = int(self.y)

        # blink when hurt
        if self._hurt_timer > 0 and (self._hurt_timer // 6) % 2 == 0:
            return

        body_col = BLUE
        pygame.draw.rect(surface, body_col,
                         (draw_x, draw_y, self.WIDTH, self.HEIGHT), border_radius=4)

        # eyes
        eye_y = draw_y + 8
        if self.facing == 1:
            pygame.draw.circle(surface, WHITE, (draw_x + 17, eye_y), 4)
            pygame.draw.circle(surface, (0, 0, 0), (draw_x + 18, eye_y), 2)
        else:
            pygame.draw.circle(surface, WHITE, (draw_x + 7, eye_y), 4)
            pygame.draw.circle(surface, (0, 0, 0), (draw_x + 6, eye_y), 2)

        # HP pips above head
        for i in range(self.MAX_HP):
            col = RED if i < self.hp else (60, 60, 60)
            pygame.draw.circle(surface, col,
                                (draw_x + 4 + i * 10, draw_y - 8), 4)
