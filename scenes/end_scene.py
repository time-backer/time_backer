import pygame
import math
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, CYAN, RED, SKY, YELLOW, MAX_REWIND_COUNT


class EndScene:
    def __init__(self, victory: bool, clear_time: int = 0, rewind_used: int = 0) -> None:
        self.victory    = victory
        self.clear_time = clear_time
        self.rewind_used = rewind_used
        self._font_big  = pygame.font.SysFont(None, 52)
        self._font_med  = pygame.font.SysFont("applesdgothicneo,applegothic", 22)
        self._font_sm   = pygame.font.SysFont("applesdgothicneo,applegothic", 15)
        self._tick = 0
        self._stars = 3 if rewind_used <= 1 else (2 if rewind_used <= 3 else 1)

    def update(self) -> None:
        self._tick += 1

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return "start"
            if event.key == pygame.K_ESCAPE:
                return "quit"
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(SKY)
        cx = SCREEN_WIDTH // 2

        # 결과 타이틀
        msg, color = ("CLEAR!", CYAN) if self.victory else ("GAME OVER", RED)
        title = self._font_big.render(msg, True, color)
        surface.blit(title, (cx - title.get_width() // 2, int(SCREEN_HEIGHT * 0.08)))

        if self.victory:
            # 별 표시
            star_r  = int(SCREEN_HEIGHT * 0.07)
            star_y  = int(SCREEN_HEIGHT * 0.38)
            gap     = star_r * 3
            start_x = cx - gap
            for i in range(3):
                c = YELLOW if i < self._stars else (70, 70, 70)
                self._draw_star(surface, start_x + i * gap, star_y, star_r, c)

            # 클리어 타임
            t_surf = self._font_med.render(f"Clear Time : {self.clear_time}s", True, WHITE)
            surface.blit(t_surf, (cx - t_surf.get_width() // 2, int(SCREEN_HEIGHT * 0.53)))

            # 역행 횟수
            r_surf = self._font_med.render(
                f"Rewind Used : {self.rewind_used} / {MAX_REWIND_COUNT}", True, CYAN)
            surface.blit(r_surf, (cx - r_surf.get_width() // 2, int(SCREEN_HEIGHT * 0.65)))
        else:
            msg_surf = self._font_med.render("역행 횟수 초과!", True, RED)
            surface.blit(msg_surf, (cx - msg_surf.get_width() // 2, int(SCREEN_HEIGHT * 0.45)))

        # 하단 안내 (깜빡임)
        alpha = int(128 + 127 * abs((self._tick % 60) / 30 - 1))
        hint = self._font_sm.render("SPACE/ENTER - 타이틀    ESC - 종료", True, YELLOW)
        hint.set_alpha(alpha)
        surface.blit(hint, (cx - hint.get_width() // 2, int(SCREEN_HEIGHT * 0.87)))

    def _draw_star(self, surface: pygame.Surface, cx: int, cy: int,
                   radius: int, color: tuple) -> None:
        points = []
        for i in range(10):
            angle = math.pi / 2 + (2 * math.pi * i / 10)
            r = radius if i % 2 == 0 else radius * 0.4
            points.append((cx + r * math.cos(angle), cy - r * math.sin(angle)))
        pygame.draw.polygon(surface, color, points)
