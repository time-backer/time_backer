import random
import pygame
from settings import TILE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT, RED, ORANGE, PURPLE, WHITE
import asset_loader as A


class Boss:
    WIDTH = 72
    HEIGHT = 72
    MAX_HP = 15
    font = None

    # 패턴 타입
    PATTERN_WAVE = "wave"
    PATTERN_FREEZE = "freeze"
    PATTERN_AFTERIMAGE = "afterimage"
    PATTERN_REVERSE = "reverse"

    def __init__(self, x, y):
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

    def get_rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.WIDTH, self.HEIGHT)

    def take_damage(self, amount=1):
        self.hp -= amount
        if self.hp <= 0:
            self.alive = False
            return

        # Phase 전환
        if self.hp <= 10 and self.phase == 1:
            self.phase = 2
        elif self.hp <= 5 and self.phase == 2:
            self.phase = 3

    def try_reverse(self):
        if self.phase >= 3 and self.reverse_cooldown <= 0:
            self.reversing = True
            self.reverse_cooldown = 600  # 10초 쿨다운
            return True
        return False

    def cancel_reverse(self):
        if self.reversing:
            self.reversing = False

    def complete_reverse(self):
        if self.reversing:
            self.hp = min(self.hp + 3, self.MAX_HP)
            self.reversing = False

    def update(self):
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
            self.execute_pattern()
            self.pattern_timer = 0

    def execute_pattern(self):
        patterns = [self.PATTERN_WAVE, self.PATTERN_FREEZE, self.PATTERN_AFTERIMAGE]
        self.current_pattern = random.choice(patterns)
        self.pattern_active = True

    def get_phase_color(self):
        """Phase별 색상"""
        if self.phase == 1:
            return RED
        elif self.phase == 2:
            return ORANGE
        else:
            return PURPLE

    def draw(self, surface, camera_x=0, camera_y=0):
        if not self.alive:
            return

        draw_x = int(self.x) - camera_x
        draw_y = int(self.y) - camera_y

        # Phase에 따라 스프라이트 선택
        if self.phase == 1:
            frames = A.boss_phase1
        elif self.phase == 2:
            frames = A.boss_phase2
        else:
            frames = A.boss_phase3

        if self.reversing:
            speed = 50
        else:
            speed = 100
        frame = frames[(pygame.time.get_ticks() // speed) % len(frames)]

        if self.reversing and (pygame.time.get_ticks() // 100) % 2 == 0:
            frame = frame.copy()
            frame.set_alpha(100)

        surface.blit(frame, (draw_x, draw_y))

        # HP 바 (화면 하단 중앙)
        self.draw_hp_bar(surface)

    def draw_hp_bar(self, surface):
        if Boss.font is None:
            Boss.font = pygame.font.SysFont(None, 16)

        bar_width = SCREEN_WIDTH // 2
        bar_height = 12
        bar_x = (SCREEN_WIDTH - bar_width) // 2
        bar_y = SCREEN_HEIGHT - 26

        pygame.draw.rect(surface, (40, 40, 40), (bar_x, bar_y, bar_width, bar_height))
        color = self.get_phase_color()
        pygame.draw.rect(surface, color,
                         (bar_x, bar_y, int(bar_width * self.hp / self.MAX_HP), bar_height))
        pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_width, bar_height), 1)

        hp_surf = Boss.font.render(f"BOSS HP: {self.hp}/{self.MAX_HP}", True, WHITE)
        surface.blit(hp_surf, (bar_x + bar_width // 2 - hp_surf.get_width() // 2, bar_y - 14))

        ph_surf = Boss.font.render(f"PHASE {self.phase}", True, color)
        surface.blit(ph_surf, (bar_x + bar_width // 2 - ph_surf.get_width() // 2,
                                bar_y + bar_height + 2))
