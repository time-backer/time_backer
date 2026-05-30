import pygame
from typing import List
from core.game_state import EnemyState
from world.tile import Tile
from settings import TILE_SIZE, GRAVITY, ORANGE, RED, PURPLE
import asset_loader as A


class AbsorbingEnemy:
    """역행 횟수를 흡수해서 HP가 증가하는 특수 적"""
    WIDTH = 40
    HEIGHT = 40
    
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.alive = True
        self.hp = 3  # 기본 HP
        self.max_hp = 3
        
    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.WIDTH, self.HEIGHT)
    
    def absorb_rewind(self) -> None:
        """역행 사용 시 HP 증가"""
        self.hp += 1
        self.max_hp += 1
    
    def take_damage(self) -> None:
        """피격 시 HP 감소"""
        self.hp -= 1
        if self.hp <= 0:
            self.alive = False
    
    def update(self, ground_tiles: List[Tile], stage_width: int) -> None:
        if not self.alive:
            return
        
        # 중력 적용
        self.vy += GRAVITY
        self.y += self.vy
        
        # 바닥 충돌
        for tile in ground_tiles:
            tr = tile.get_rect()
            if self.rect.colliderect(tr):
                if self.vy >= 0:
                    self.y = tr.top - self.HEIGHT
                    self.vy = 0
    
    def capture_state(self) -> EnemyState:
        return EnemyState(self.x, self.y, 1, self.alive)
    
    def apply_state(self, state: EnemyState) -> None:
        self.x = state.x
        self.y = state.y
        self.alive = state.alive
    
    def draw(self, surface: pygame.Surface, camera_x: int = 0) -> None:
        if not self.alive:
            return

        draw_x = int(self.x) - camera_x
        draw_y = int(self.y)

        # 스프라이트 선택: HP에 따라 golem 변형 사용
        if self.hp <= 1:
            frames = A.golem_lowhp   # 48×48
            sw, sh = 48, 48
        elif self.hp > 3:
            frames = A.golem_highhp  # 48×48
            sw, sh = 48, 48
        else:
            frames = A.golem         # 32×32
            sw, sh = 32, 32

        frame = frames[(pygame.time.get_ticks() // 200) % len(frames)]
        # center sprite on the 40×40 hitbox
        ox = draw_x + self.WIDTH // 2 - sw // 2
        oy = draw_y + self.HEIGHT // 2 - sh // 2
        surface.blit(frame, (ox, oy))

        # HP 바
        bar_w, bar_h = 36, 4
        bar_x = draw_x + 2
        bar_y = draw_y - 10
        pygame.draw.rect(surface, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h))
        hp_ratio = self.hp / max(self.max_hp, 1)
        bar_col = RED if self.hp <= 1 else (ORANGE if self.hp <= 3 else PURPLE)
        pygame.draw.rect(surface, bar_col,
                         (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))
