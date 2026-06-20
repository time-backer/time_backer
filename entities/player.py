import pygame
import pymunk

from core.game_state import GameState
from core.physics import MOVE_VX, JUMP_VY
from settings import RED, FPS
import asset_loader as A


class Player:
    WIDTH = 24
    HEIGHT = 30
    MAX_HP = 3
    SPRITE_SIZE = 48   # 원본 32×32 → 1.5배 표시

    def __init__(self, body):
        self.body = body
        self.hp = self.MAX_HP
        self.facing = 1          # 1=right, -1=left
        self.on_ground = False   # game_scene이 매 스텝 후 갱신
        self.hurt_timer = 0
        self.anim_state = "idle"
        self.state_start = 0

    # ── 위치·속도 (pymunk 바디에서 읽기) ──────────────────────────────────

    # ai
    def get_x(self):
        return self.body.position.x - self.WIDTH / 2

    # ai
    def get_y(self):
        return self.body.position.y - self.HEIGHT / 2

    # ai
    def get_vy(self):
        return self.body.velocity.y / 60

    # ai
    def get_rect(self):
        return pygame.Rect(int(self.get_x()), int(self.get_y()), self.WIDTH, self.HEIGHT)

    # ── 입력 처리 ─────────────────────────────────────────────────────────

    def handle_input(self, keys):
        vx = 0.0
        if keys[pygame.K_LEFT]:
            vx = -MOVE_VX
            self.facing = -1
        if keys[pygame.K_RIGHT]:
            vx = MOVE_VX
            self.facing = 1

        # 수평 속도만 교체, 수직은 pymunk에 맡김
        self.body.velocity = pymunk.Vec2d(vx, self.body.velocity.y)

        if (keys[pygame.K_SPACE] or keys[pygame.K_UP]) and self.on_ground:
            self.body.velocity = pymunk.Vec2d(vx, JUMP_VY)
            self.on_ground = False   # 이 프레임 이중 점프 방지

    # ai
    def clamp_to_stage(self, stage_width, stage_height):
        px, py = self.body.position
        vx, vy = self.body.velocity
        if px - self.WIDTH / 2 < 0:
            px = self.WIDTH / 2
            vx = max(0.0, vx)
        elif px + self.WIDTH / 2 > stage_width:
            px = stage_width - self.WIDTH / 2
            vx = min(0.0, vx)
        if py - self.HEIGHT / 2 < 0:
            py = self.HEIGHT / 2
            vy = max(0.0, vy)
        self.body.position = pymunk.Vec2d(px, py)
        self.body.velocity = pymunk.Vec2d(vx, vy)

    # ── 피격 / 스톰프 ─────────────────────────────────────────────────────

    def take_damage(self):
        if self.hurt_timer == 0:
            self.hp -= 1
            self.hurt_timer = 60

    # ai
    def tick_hurt(self):
        if self.hurt_timer > 0:
            self.hurt_timer -= 1

    # ai
    def is_dead(self):
        return self.hp <= 0

    # ai
    def set_bounce_velocity(self, vy):
        self.body.velocity = pymunk.Vec2d(self.body.velocity.x, vy)

    # ai
    def grant_invincibility(self, frames=FPS):
        self.hurt_timer = frames

    # ── 시간 되감기 ───────────────────────────────────────────────────────

    def capture_state(self, rewind_count):
        return GameState(
            player_x=self.get_x(),
            player_y=self.get_y(),
            player_vx=self.body.velocity.x,   # px/s 단위
            player_vy=self.body.velocity.y,
            hp=self.hp,
            rewind_count=rewind_count,
        )

    def apply_state(self, state):
        self.body.position = pymunk.Vec2d(
            state.player_x + self.WIDTH / 2,
            state.player_y + self.HEIGHT / 2,
        )
        self.body.velocity = pymunk.Vec2d(state.player_vx, state.player_vy)
        self.hp = state.hp
        self.hurt_timer = 0

    # ── 렌더링 ────────────────────────────────────────────────────────────

    # ai
    def draw(self, surface, camera_x=0, camera_y=0, rewinding=False):
        if self.hurt_timer > 0 and (self.hurt_timer // 6) % 2 == 0:
            return

        draw_x = int(self.get_x()) - camera_x
        draw_y = int(self.get_y()) - camera_y

        if rewinding:
            new_state = "rewind"
        elif not self.on_ground:
            new_state = "jump"
        elif abs(self.body.velocity.x) > 10:
            new_state = "run"
        else:
            new_state = "idle"

        if new_state != self.anim_state:
            self.anim_state = new_state
            self.state_start = pygame.time.get_ticks()

        frames = {
            "idle":   A.player_idle,
            "run":    A.player_run,
            "jump":   A.player_jump,
            "rewind": A.player_rewind,
        }[self.anim_state]

        elapsed = pygame.time.get_ticks() - self.state_start
        frame = frames[(elapsed // 150) % len(frames)]
        if self.facing == -1:
            frame = pygame.transform.flip(frame, True, False)

        # 1.5배 확대, 히트박스 중심 정렬
        sz = self.SPRITE_SIZE
        scaled = pygame.transform.scale(frame, (sz, sz))
        ox = draw_x + self.WIDTH // 2 - sz // 2
        oy = draw_y + self.HEIGHT // 2 - sz // 2
        surface.blit(scaled, (ox, oy))
