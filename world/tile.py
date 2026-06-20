import pygame
from settings import TILE_SIZE, GRAY, SPIKE_COL, EXIT_COL, YELLOW, GREEN, CYAN
import asset_loader as A


class Tile:
    exit_font = None  # 클래스 변수로 폰트 캐싱
    switch_font = None

    def __init__(self, col, row, tile_type):
        self.col = col
        self.row = row
        self.tile_type = tile_type  # "ground" | "spike" | "exit" | "switch_a" | "switch_b"
        self.rect = pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        self.activated = False  # 스위치 활성화 상태

    # ai
    def draw(self, surface, camera_x=0, camera_y=0):
        draw_rect = self.rect.move(-camera_x, -camera_y)
        if self.tile_type == "ground":
            surface.blit(A.tile_ground, draw_rect.topleft)
        elif self.tile_type == "spike":
            anim = (pygame.time.get_ticks() // 200) % len(A.tile_spike)
            surface.blit(A.tile_spike[anim], draw_rect.topleft)
        elif self.tile_type == "exit":
            anim = (pygame.time.get_ticks() // 150) % len(A.portal)
            surface.blit(A.portal[anim], draw_rect.topleft)
        elif self.tile_type == "switch_a" or self.tile_type == "switch_b":
            if self.activated:
                frame = A.tile_switch_on
            else:
                frame = A.tile_switch_off
            surface.blit(frame, draw_rect.topleft)
            # 스위치 라벨 (A/B 구분)
            if Tile.switch_font is None:
                Tile.switch_font = pygame.font.SysFont(None, 20)
            if self.tile_type == "switch_a":
                label_text = "A"
            else:
                label_text = "B"
            label = Tile.switch_font.render(label_text, True, (0, 0, 0))
            surface.blit(label, (draw_rect.centerx - label.get_width() // 2,
                                 draw_rect.centery - label.get_height() // 2))
        elif self.tile_type == "gate" and self.activated:
            pygame.draw.rect(surface, CYAN, draw_rect)
            pygame.draw.rect(surface, (0, 180, 180), draw_rect, 2)
