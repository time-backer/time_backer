import pygame
import math
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, CYAN, RED, SKY, YELLOW, MAX_REWIND_COUNT


class EndScene:
    def __init__(self, victory: bool, clear_time: int = 0, rewind_used: int = 0) -> None:
        self.victory = victory
        self.clear_time = clear_time  # seconds
        self.rewind_used = rewind_used
        self._font_big = pygame.font.SysFont(None, 80)
        self._font_med = pygame.font.SysFont(None, 36)
        self._font_sm = pygame.font.SysFont(None, 28)
        self._tick = 0
        
        # Calculate star rating (3 stars if 0-1 rewinds, 2 stars if 2-3, 1 star if 4-5)
        if rewind_used <= 1:
            self._stars = 3
        elif rewind_used <= 3:
            self._stars = 2
        else:
            self._stars = 1

    def update(self) -> None:
        self._tick += 1

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                return "start"
            if event.key == pygame.K_ESCAPE:
                return "quit"
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(SKY)

        if self.victory:
            msg   = "CLEAR!"
            color = CYAN
        else:
            msg   = "GAME OVER"
            color = RED

        title = self._font_big.render(msg, True, color)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 80))

        # Victory stats
        if self.victory:
            # Stars - draw as shapes instead of unicode
            star_y = 180
            star_size = 40
            total_width = 3 * star_size + 2 * 20  # 3 stars + 2 gaps
            start_x = SCREEN_WIDTH // 2 - total_width // 2
            
            for i in range(3):
                x = start_x + i * (star_size + 20)
                if i < self._stars:
                    # Filled star
                    self._draw_star(surface, x + star_size // 2, star_y + star_size // 2, 
                                   star_size // 2, YELLOW)
                else:
                    # Empty star
                    self._draw_star(surface, x + star_size // 2, star_y + star_size // 2, 
                                   star_size // 2, (80, 80, 80))
            
            # Clear time
            time_text = f"Clear Time: {self.clear_time}s"
            time_surf = self._font_med.render(time_text, True, WHITE)
            surface.blit(time_surf, (SCREEN_WIDTH // 2 - time_surf.get_width() // 2, 260))
            
            # Rewind used
            rewind_text = f"Rewind Used: {self.rewind_used} / {MAX_REWIND_COUNT}"
            rewind_surf = self._font_med.render(rewind_text, True, CYAN)
            surface.blit(rewind_surf, (SCREEN_WIDTH // 2 - rewind_surf.get_width() // 2, 300))
        else:
            # Game Over - show rewind exhausted message
            msg_text = "Rewind Count Exhausted!"
            msg_surf = self._font_med.render(msg_text, True, RED)
            surface.blit(msg_surf, (SCREEN_WIDTH // 2 - msg_surf.get_width() // 2, 200))

        alpha = int(128 + 127 * abs((self._tick % 60) / 30 - 1))
        sub = self._font_sm.render("SPACE / ENTER - Title    ESC - Quit", True, YELLOW)
        sub.set_alpha(alpha)
        surface.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 380))
    
    def _draw_star(self, surface: pygame.Surface, cx: int, cy: int, radius: int, color: tuple) -> None:
        """별 모양 그리기 (5각별)"""
        points = []
        for i in range(10):
            angle = math.pi / 2 + (2 * math.pi * i / 10)
            r = radius if i % 2 == 0 else radius * 0.4
            x = cx + r * math.cos(angle)
            y = cy - r * math.sin(angle)
            points.append((x, y))
        pygame.draw.polygon(surface, color, points)
