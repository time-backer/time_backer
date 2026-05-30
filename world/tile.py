import pygame
from settings import TILE_SIZE, GRAY, SPIKE_COL, EXIT_COL, YELLOW, GREEN
import asset_loader as A


class Tile:
    _exit_font = None  # 클래스 변수로 폰트 캐싱
    _switch_font = None
    
    def __init__(self, col: int, row: int, tile_type: str) -> None:
        self.col = col
        self.row = row
        self.tile_type = tile_type  # "ground" | "spike" | "exit" | "switch_a" | "switch_b"
        self.rect = pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        self.activated = False  # 스위치 활성화 상태

    def get_rect(self) -> pygame.Rect:
        return self.rect

    def draw(self, surface: pygame.Surface, camera_x: int = 0) -> None:
        draw_rect = self.rect.move(-camera_x, 0)
        if self.tile_type == "ground":
            surface.blit(A.tile_ground, draw_rect.topleft)
        elif self.tile_type == "spike":
            anim = (pygame.time.get_ticks() // 200) % len(A.tile_spike)
            surface.blit(A.tile_spike[anim], draw_rect.topleft)
        elif self.tile_type == "exit":
            anim = (pygame.time.get_ticks() // 150) % len(A.portal)
            surface.blit(A.portal[anim], draw_rect.topleft)
        elif self.tile_type in ("switch_a", "switch_b"):
            frame = A.tile_switch_on if self.activated else A.tile_switch_off
            surface.blit(frame, draw_rect.topleft)
            # 스위치 라벨 (A/B 구분)
            if Tile._switch_font is None:
                Tile._switch_font = pygame.font.SysFont(None, 20)
            label_text = "A" if self.tile_type == "switch_a" else "B"
            label = Tile._switch_font.render(label_text, True, (0, 0, 0))
            surface.blit(label, (draw_rect.centerx - label.get_width() // 2,
                                 draw_rect.centery - label.get_height() // 2))
