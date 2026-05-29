import pygame
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    WHITE, CYAN, YELLOW, SKY,
)


class StartScene:
    def __init__(self) -> None:
        self._font_big = pygame.font.SysFont(None, 72)
        self._font_med = pygame.font.SysFont(None, 36)
        self._font_sm  = pygame.font.SysFont(None, 26)
        self._tick = 0

    def update(self) -> None:
        self._tick += 1

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            return "game"
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(SKY)

        # title
        title = self._font_big.render("TIME BACKER", True, CYAN)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))

        # subtitle pulse
        alpha = int(128 + 127 * abs((self._tick % 60) / 30 - 1))
        sub = self._font_med.render("PRESS SPACE / ENTER to START", True, WHITE)
        sub.set_alpha(alpha)
        surface.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 210))

        # controls
        controls = [
            ("Arrow Keys / Space", "Move / Jump"),
            ("Z",                  "Rewind 3 seconds back"),
            ("X",                  "Rewind to START"),
            ("",                   "Max 5 rewinds per stage!"),
        ]
        y = 290
        for key, desc in controls:
            k_surf = self._font_sm.render(f"[{key}]", True, YELLOW)
            d_surf = self._font_sm.render(f"  {desc}", True, WHITE)
            x_off = SCREEN_WIDTH // 2 - (k_surf.get_width() + d_surf.get_width()) // 2
            surface.blit(k_surf, (x_off, y))
            surface.blit(d_surf, (x_off + k_surf.get_width(), y))
            y += 34
