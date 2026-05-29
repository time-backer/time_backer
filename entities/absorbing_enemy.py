import pygame
from typing import List
from core.game_state import EnemyState
from world.tile import Tile
from settings import TILE_SIZE, GRAVITY, ORANGE, RED, PURPLE


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
        
        # HP에 따라 색상 변화 (빨강 → 주황 → 보라)
        if self.hp <= 3:
            color = RED
        elif self.hp <= 5:
            color = ORANGE
        else:
            color = PURPLE
        
        # 몸체
        pygame.draw.rect(surface, color, 
                        (draw_x, draw_y, self.WIDTH, self.HEIGHT), border_radius=6)
        pygame.draw.rect(surface, (255, 255, 255), 
                        (draw_x, draw_y, self.WIDTH, self.HEIGHT), 2, border_radius=6)
        
        # HP 바
        bar_width = 36
        bar_height = 4
        bar_x = draw_x + 2
        bar_y = draw_y - 8
        
        # 배경 (회색)
        pygame.draw.rect(surface, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height))
        # HP (색상)
        hp_ratio = self.hp / max(self.max_hp, 1)
        pygame.draw.rect(surface, color, (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))
