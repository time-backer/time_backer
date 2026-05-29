import pygame
from settings import TILE_SIZE, GRAY, SPIKE_COL, EXIT_COL


class Tile:
    _exit_font = None  # 클래스 변수로 폰트 캐싱
    
    def __init__(self, col: int, row: int, tile_type: str) -> None:
        self.col = col
        self.row = row
        self.tile_type = tile_type  # "ground" | "spike" | "exit"
        self.rect = pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)

    def get_rect(self) -> pygame.Rect:
        return self.rect

    def draw(self, surface: pygame.Surface, camera_x: int = 0) -> None:
        draw_rect = self.rect.move(-camera_x, 0)
        if self.tile_type == "ground":
            pygame.draw.rect(surface, GRAY, draw_rect)
            pygame.draw.rect(surface, (100, 100, 100), draw_rect, 1)
        elif self.tile_type == "spike":
            cx = draw_rect.centerx
            points = [
                (draw_rect.left + 4, draw_rect.bottom),
                (cx, draw_rect.top + 4),
                (draw_rect.right - 4, draw_rect.bottom),
            ]
            pygame.draw.polygon(surface, SPIKE_COL, points)
        elif self.tile_type == "exit":
            pygame.draw.rect(surface, EXIT_COL, draw_rect)
            pygame.draw.rect(surface, (200, 255, 200), draw_rect, 2)
            # 폰트 캐싱 (최초 1회만 생성)
            if Tile._exit_font is None:
                Tile._exit_font = pygame.font.SysFont(None, 18)
            label = Tile._exit_font.render("EXIT", True, (0, 0, 0))
            surface.blit(label, (draw_rect.centerx - label.get_width() // 2,
                                 draw_rect.centery - label.get_height() // 2))
