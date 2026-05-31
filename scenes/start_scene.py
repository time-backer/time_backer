import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, CYAN, YELLOW, SKY


class StartScene:
    def __init__(self) -> None:
        self._font_big = pygame.font.SysFont(None, 46)
        self._font_med = pygame.font.SysFont(None, 22)
        self._font_sm  = pygame.font.SysFont("applesdgothicneo,applegothic", 16)
        self._tick = 0

    def update(self) -> None:
        self._tick += 1

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            return "game"
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(SKY)

        cx = SCREEN_WIDTH // 2

        # 타이틀
        title = self._font_big.render("TIME BACKER", True, CYAN)
        surface.blit(title, (cx - title.get_width() // 2, int(SCREEN_HEIGHT * 0.14)))

        # 시작 안내 (펄스)
        alpha = int(128 + 127 * abs((self._tick % 60) / 30 - 1))
        sub = self._font_med.render("PRESS SPACE / ENTER to START", True, WHITE)
        sub.set_alpha(alpha)
        surface.blit(sub, (cx - sub.get_width() // 2, int(SCREEN_HEIGHT * 0.42)))

        # 조작 설명
        controls = [
            ("Arrow / Space", "이동 / 점프"),
            ("Z",             "3초 되감기"),
            ("X",             "시작 위치로 되감기"),
            ("*",             "스테이지당 역행 5회"),
        ]
        y = int(SCREEN_HEIGHT * 0.57)
        spacing = int(SCREEN_HEIGHT * 0.1)
        for key, desc in controls:
            k_surf = self._font_sm.render(f"[{key}]", True, YELLOW)
            d_surf = self._font_sm.render(f"  {desc}", True, WHITE)
            x_off  = cx - (k_surf.get_width() + d_surf.get_width()) // 2
            surface.blit(k_surf, (x_off, y))
            surface.blit(d_surf, (x_off + k_surf.get_width(), y))
            y += spacing
