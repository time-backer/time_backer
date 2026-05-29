import pygame
from typing import List
from settings import TILE_SIZE, RED, ORANGE, PURPLE, WHITE


class Boss:
    """시간의 수호자 - 최종 보스"""
    WIDTH = 72
    HEIGHT = 72
    MAX_HP = 15
    
    # 패턴 타입
    PATTERN_WAVE = "wave"
    PATTERN_FREEZE = "freeze"
    PATTERN_AFTERIMAGE = "afterimage"
    PATTERN_REVERSE = "reverse"
    
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.hp = self.MAX_HP
        self.alive = True
        
        # Phase 시스템
        self.phase = 1  # 1, 2, 3
        
        # 패턴 관리
        self.pattern_timer = 0
        self.pattern_cooldown = 180  # 3초마다 패턴
        self.current_pattern = None
        self.pattern_active = False
        
        # 타임 리버스 (Phase 3)
        self.reverse_cooldown = 0
        self.reversing = False
        
    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.WIDTH, self.HEIGHT)
    
    def take_damage(self, amount: int = 1) -> None:
        """피격"""
        self.hp -= amount
        if self.hp <= 0:
            self.alive = False
        else:
            # Phase 전환
            if self.hp <= 10 and self.phase == 1:
                self.phase = 2
            elif self.hp <= 5 and self.phase == 2:
                self.phase = 3
    
    def try_reverse(self) -> bool:
        """타임 리버스 시전 (Phase 3)"""
        if self.phase >= 3 and self.reverse_cooldown <= 0:
            self.reversing = True
            self.reverse_cooldown = 600  # 10초 쿨다운
            return True
        return False
    
    def cancel_reverse(self) -> None:
        """플레이어 역행으로 타임 리버스 취소"""
        if self.reversing:
            self.reversing = False
    
    def complete_reverse(self) -> None:
        """타임 리버스 완료 - HP 회복"""
        if self.reversing:
            self.hp = min(self.hp + 3, self.MAX_HP)
            self.reversing = False
    
    def update(self) -> None:
        """보스 AI 업데이트"""
        if not self.alive:
            return
        
        # 쿨다운 감소
        if self.reverse_cooldown > 0:
            self.reverse_cooldown -= 1
        
        # 타임 리버스 진행 중
        if self.reversing:
            self.pattern_timer += 1
            if self.pattern_timer >= 120:  # 2초 후 회복
                self.complete_reverse()
                self.pattern_timer = 0
            return
        
        # 패턴 타이머
        self.pattern_timer += 1
        
        # Phase 3: 타임 리버스 시도
        if self.phase >= 3 and self.hp < self.MAX_HP:
            if self.try_reverse():
                self.pattern_timer = 0
                return
        
        # 일반 패턴 실행
        if self.pattern_timer >= self.pattern_cooldown:
            self._execute_pattern()
            self.pattern_timer = 0
    
    def _execute_pattern(self) -> None:
        """패턴 실행 (간소화 버전 - 실제 공격은 GameScene에서 처리)"""
        patterns = [self.PATTERN_WAVE, self.PATTERN_FREEZE, self.PATTERN_AFTERIMAGE]
        import random
        self.current_pattern = random.choice(patterns)
        self.pattern_active = True
    
    def get_phase_color(self) -> tuple:
        """Phase별 색상"""
        if self.phase == 1:
            return RED
        elif self.phase == 2:
            return ORANGE
        else:
            return PURPLE
    
    def draw(self, surface: pygame.Surface, camera_x: int = 0) -> None:
        """보스 렌더링"""
        if not self.alive:
            return
        
        draw_x = int(self.x) - camera_x
        draw_y = int(self.y)
        
        # 보스 몸체
        color = self.get_phase_color()
        
        # 타임 리버스 중이면 깜빡임
        if self.reversing and (pygame.time.get_ticks() // 100) % 2 == 0:
            color = PURPLE
        
        # 육각형 형태로 그리기
        center_x = draw_x + self.WIDTH // 2
        center_y = draw_y + self.HEIGHT // 2
        radius = self.WIDTH // 2
        
        points = []
        for i in range(6):
            angle = i * 60 * 3.14159 / 180
            px = center_x + radius * pygame.math.Vector2(1, 0).rotate_rad(angle).x
            py = center_y + radius * pygame.math.Vector2(1, 0).rotate_rad(angle).y
            points.append((px, py))
        
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, WHITE, points, 3)
        
        # 눈 (중앙)
        eye_size = 8
        pygame.draw.circle(surface, WHITE, (center_x, center_y), eye_size)
        pygame.draw.circle(surface, color, (center_x, center_y), eye_size - 3)
        
        # HP 바 (화면 하단 중앙)
        self._draw_hp_bar(surface)
    
    def _draw_hp_bar(self, surface: pygame.Surface) -> None:
        """보스 HP 바 (화면 하단)"""
        bar_width = 400
        bar_height = 20
        bar_x = (800 - bar_width) // 2
        bar_y = 480 - 40
        
        # 배경
        pygame.draw.rect(surface, (40, 40, 40), (bar_x, bar_y, bar_width, bar_height))
        
        # HP
        hp_ratio = self.hp / self.MAX_HP
        color = self.get_phase_color()
        pygame.draw.rect(surface, color, (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))
        
        # 테두리
        pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
        
        # HP 텍스트
        font = pygame.font.SysFont(None, 24)
        hp_text = f"BOSS HP: {self.hp}/{self.MAX_HP}"
        text_surf = font.render(hp_text, True, WHITE)
        surface.blit(text_surf, (bar_x + bar_width // 2 - text_surf.get_width() // 2, bar_y - 25))
        
        # Phase 표시
        phase_text = f"PHASE {self.phase}"
        phase_surf = font.render(phase_text, True, color)
        surface.blit(phase_surf, (bar_x + bar_width // 2 - phase_surf.get_width() // 2, bar_y + bar_height + 5))
