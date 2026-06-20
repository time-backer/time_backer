import pygame
import pymunk


from core.game_state import GameState
from core.time_stack import TimeStack
from core.physics import PhysicsWorld, STOMP_VY
from entities.player import Player
from entities.enemy import Enemy
from entities.boss import Boss
from world.stage import Stage
from world.boss_stage import BossStage
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE,
    REWIND_FLASH_DURATION, REWIND_FRAMES, MAX_REWIND_COUNT, REWIND_SPEED, FPS,
    WHITE, YELLOW, RED, CYAN, SKY,
)
import asset_loader as A


class GameScene:
    def __init__(self, stage_num=1):
        self.stage_num = stage_num

        # ── 스테이지 생성 ────────────────────────────────────────────────
        if stage_num == 4:
            self.stage = BossStage()
        else:
            self.stage = Stage(stage_num=stage_num)

        # ── 물리 월드 ────────────────────────────────────────────────────
        self.phys = PhysicsWorld()
        self.build_physics()

        # ── 플레이어 ─────────────────────────────────────────────────────
        sx, sy = self.stage.get_player_start()
        p_body = self.phys.add_player_body(sx, sy, Player.WIDTH, Player.HEIGHT)
        self.player = Player(p_body)

        # ── 일반 적 ──────────────────────────────────────────────────────
        self.enemies = []
        for i, spawn in enumerate(self.stage.get_enemy_spawns()):
            ex, ey = spawn
            body = self.phys.add_enemy_body(ex, ey, Enemy.WIDTH, Enemy.HEIGHT)
            self.enemies.append(Enemy(body, i))

        # ── 보스 (Stage 4) ───────────────────────────────────────────────
        self.boss = None
        if stage_num == 4:
            bx, by = self.stage.get_boss_position()
            self.boss = Boss(bx, by)

        # ── 타임 스택 ────────────────────────────────────────────────────
        self.time_stack = TimeStack()
        self.rewind_count = MAX_REWIND_COUNT
        self.frame = 0
        self.start_time = pygame.time.get_ticks()
        self.paused_time = 0

        self.flash_timer = 0
        self.flash_full = False
        self.rewinding = False
        self.rewind_target_frames = 0
        self.rewind_start_time = 0

        self.font_hud = pygame.font.SysFont(None, 16)
        self.font_big = pygame.font.SysFont(None, 32)

        self.outcome = None
        self.dev_open = False
        self.gates_activated = False

        # ── 캐시 Surface ─────────────────────────────────────────────────
        self.outcome_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.outcome_overlay.fill((0, 0, 0, 120))
        self.dev_panel_bg = pygame.Surface((180, 180), pygame.SRCALPHA)
        self.dev_panel_bg.fill((10, 10, 30, 210))

    # ── 물리 월드에 타일 등록 ─────────────────────────────────────────────

    def build_physics(self):
        for tile in self.stage.ground_tiles + self.stage.spike_tiles:
            self.phys.add_static_ground(tile.rect.x, tile.rect.y, TILE_SIZE, TILE_SIZE)
        self.gate_shapes = []
        for tile in self.stage.gate_tiles:
            shape = self.phys.add_gate(tile.rect.x, tile.rect.y, TILE_SIZE, TILE_SIZE)
            self.gate_shapes.append(shape)

    # ── 리셋 ─────────────────────────────────────────────────────────────

    # ai
    def reset(self):
        self.__init__(self.stage_num)

    # ── 외부 접근 ─────────────────────────────────────────────────────────

    # ai
    def get_clear_time(self):
        elapsed = pygame.time.get_ticks() - self.start_time - self.paused_time
        return elapsed // 1000

    # ai
    def get_rewind_used(self):
        return MAX_REWIND_COUNT - self.rewind_count

    # ── 이벤트 ───────────────────────────────────────────────────────────

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.dev_open = not self.dev_open
                return None
            if self.dev_open:
                if event.key == pygame.K_q:
                    return "quit"
                stage_keys = {
                    pygame.K_1: 1, pygame.K_2: 2, pygame.K_3: 3, pygame.K_4: 4,
                }
                if event.key in stage_keys:
                    return f"dev:{stage_keys[event.key]}"
                return None
            if event.key == pygame.K_z:
                self.rewind_one()
            elif event.key == pygame.K_x:
                self.rewind_all()
            elif event.key == pygame.K_r:
                self.reset()
        return None

    # ── 메인 업데이트 ─────────────────────────────────────────────────────

    def update(self):
        if self.dev_open or self.outcome:
            return self.outcome

        if self.rewinding:
            self.process_rewind()
            if self.flash_timer > 0:
                self.flash_timer -= 1
            return None

        keys = pygame.key.get_pressed()
        self.frame += 1

        # 1) 입력 처리 (이전 프레임 on_ground 사용)
        self.player.handle_input(keys)

        # 2) 적 AI 처리
        for enemy in self.enemies:
            enemy.update(self.stage.get_pixel_width())
        if self.boss:
            self.boss.update()

        # 3) 물리 스텝
        self.phys.step()

        # 4) ground 상태 동기화
        self.player.on_ground = self.phys.player_on_ground
        self.resolve_wall_collisions()
        self.player.clamp_to_stage(self.stage.get_pixel_width(), self.stage.get_pixel_height())
        self.player.tick_hurt()

        # 5) 충돌 처리 (rect 기반 — pymunk 외)
        self.handle_spike_hits()
        self.handle_enemy_hits()
        self.stage.check_switches(self.player.get_rect())
        self.activate_gates_if_ready()
        self.handle_boss_collision()

        # 6) 스냅샷 저장
        self.push_snapshot()

        if self.flash_timer > 0:
            self.flash_timer -= 1

        # 7) 승패 판정
        if self.boss and not self.boss.alive:
            self.outcome = "clear"
            return self.outcome

        if self.stage.is_clear(self.player.get_rect()):
            self.outcome = "clear"
            return self.outcome

        if self.player.is_dead() or self.player.get_y() > self.stage.get_pixel_height() + 100:
            self.outcome = "gameover"
            return self.outcome

        return None

    # ── 충돌 처리 헬퍼 ───────────────────────────────────────────────────

    def resolve_wall_collisions(self):
        # pymunk는 매 프레임 입력 속도를 그대로 덮어쓰기 때문에 벽을 천천히
        # 파고들다가 결국 통과해버릴 수 있다. 사각형 기반으로 한 번 더
        # 확실하게 밀어내서 옆벽 통과를 막는다.
        body = self.player.body
        solid_tiles = list(self.stage.ground_tiles)
        for tile in self.stage.gate_tiles:
            if tile.activated:
                solid_tiles.append(tile)

        for tile in solid_tiles:
            pr = self.player.get_rect()
            tr = tile.rect
            if not pr.colliderect(tr):
                continue
            overlap_x = min(pr.right, tr.right) - max(pr.left, tr.left)
            overlap_y = min(pr.bottom, tr.bottom) - max(pr.top, tr.top)
            if overlap_x >= overlap_y:
                continue  # 위/아래 충돌은 pymunk가 처리하므로 건너뜀
            if pr.centerx < tr.centerx:
                body.position = pymunk.Vec2d(body.position.x - overlap_x, body.position.y)
                body.velocity = pymunk.Vec2d(min(0.0, body.velocity.x), body.velocity.y)
            else:
                body.position = pymunk.Vec2d(body.position.x + overlap_x, body.position.y)
                body.velocity = pymunk.Vec2d(max(0.0, body.velocity.x), body.velocity.y)

    # ai
    def is_stomp(self, pr, player_vy, target_rect):
        return player_vy > 0 and pr.bottom < target_rect.centery + 10

    def handle_spike_hits(self):
        pr = self.player.get_rect()
        for spike in self.stage.spike_tiles:
            if pr.colliderect(spike.rect):
                self.player.take_damage()

    def handle_enemy_hits(self):
        pr = self.player.get_rect()
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            if pr.colliderect(enemy.get_rect()):
                if self.is_stomp(pr, self.player.get_vy(), enemy.get_rect()):
                    enemy.die()
                    self.player.set_bounce_velocity(STOMP_VY)
                else:
                    self.player.take_damage()

    # ai
    def activate_gates_if_ready(self):
        if self.gates_activated or not self.stage.are_all_switches_activated():
            return
        for tile, shape in zip(self.stage.gate_tiles, self.gate_shapes):
            tile.activated = True
            self.phys.enable_gate(shape)
        self.gates_activated = True

    def handle_boss_collision(self):
        if not self.boss or not self.boss.alive:
            return
        pr = self.player.get_rect()
        br = self.boss.get_rect()
        if pr.colliderect(br):
            if self.is_stomp(pr, self.player.get_vy(), br):
                self.boss.take_damage(1)
                self.player.set_bounce_velocity(STOMP_VY * 1.2)
            else:
                self.player.take_damage()

    # ── 시간 되감기 ───────────────────────────────────────────────────────

    def push_snapshot(self):
        state = self.player.capture_state(self.rewind_count)
        enemy_states = []
        for e in self.enemies:
            enemy_states.append(e.capture_state())
        state.enemies = enemy_states
        self.time_stack.push(state)

    def apply_state(self, state):
        # 스위치는 한 번 켜지면 역행해도 꺼지지 않고 그대로 유지된다.
        self.player.apply_state(state)
        for i, es in enumerate(state.enemies):
            if i < len(self.enemies):
                self.enemies[i].apply_state(es)

    # ai
    def can_rewind(self):
        return self.rewind_count > 0 and not self.rewinding and len(self.time_stack) > 0

    def start_rewind(self, frames, full):
        if not self.can_rewind():
            return
        if self.boss and self.boss.reversing:
            self.boss.cancel_reverse()
        self.rewinding = True
        self.rewind_target_frames = frames
        self.rewind_count -= 1
        self.flash_timer = REWIND_FLASH_DURATION
        self.flash_full = full
        self.rewind_start_time = pygame.time.get_ticks()

    # ai
    def rewind_one(self):
        self.start_rewind(min(REWIND_FRAMES, len(self.time_stack)), False)

    # ai
    def rewind_all(self):
        self.start_rewind(len(self.time_stack), True)

    def process_rewind(self):
        for _ in range(REWIND_SPEED):
            if self.rewind_target_frames <= 0:
                break
            state = self.time_stack.pop()
            if state is None:
                self.rewind_target_frames = 0
                break
            self.apply_state(state)
            self.rewind_target_frames -= 1

        if self.rewind_target_frames <= 0:
            self.rewinding = False
            self.paused_time += pygame.time.get_ticks() - self.rewind_start_time
            self.player.grant_invincibility(FPS)

    # ── 렌더링 ────────────────────────────────────────────────────────────

    # ai
    def draw(self, surface):
        self.stage.draw(surface, 0, 0)

        for enemy in self.enemies:
            enemy.draw(surface, 0, 0)

        if self.boss:
            self.boss.draw(surface, 0, 0)

        self.player.draw(surface, 0, 0, rewinding=self.rewinding)

        self.draw_hud(surface)

        if self.flash_timer > 0:
            self.draw_rewind_flash(surface)

        if self.outcome:
            self.draw_outcome_overlay(surface)

        if self.dev_open:
            self.draw_dev_panel(surface)

    # ── HUD ──────────────────────────────────────────────────────────────

    # ai
    def draw_hud(self, surface):
        pygame.draw.rect(surface, (10, 10, 25), (0, 0, SCREEN_WIDTH, 36))

        stage_surf = self.font_hud.render(f"STAGE {self.stage_num}", True, CYAN)
        surface.blit(stage_surf, (10, 8))

        hp_label = self.font_hud.render("HP:", True, WHITE)
        surface.blit(hp_label, (72, 6))
        for i in range(Player.MAX_HP):
            if i < self.player.hp:
                icon = A.hud_hp_full
            else:
                icon = A.hud_hp_empty
            surface.blit(icon, (100 + i * 26, 6))

        if self.rewinding:
            rewind_text = f"REWINDING {self.rewind_target_frames}"
            rewind_col = YELLOW
        else:
            rewind_text = f"REWIND: {self.rewind_count} / {MAX_REWIND_COUNT}"
            if self.rewind_count > 0:
                rewind_col = CYAN
            else:
                rewind_col = RED
        rw_surf = self.font_hud.render(rewind_text, True, rewind_col)
        surface.blit(rw_surf, (SCREEN_WIDTH // 2 - rw_surf.get_width() // 2, 8))

        elapsed = self.get_clear_time()
        time_surf = self.font_hud.render(f"TIME: {elapsed}s", True, YELLOW)
        surface.blit(time_surf, (SCREEN_WIDTH - time_surf.get_width() - 10, 8))

    # ── 시각 효과 ─────────────────────────────────────────────────────────

    # ai
    def draw_rewind_flash(self, surface):
        ratio = self.flash_timer / REWIND_FLASH_DURATION
        A.rewind_overlay.set_alpha(int(200 * ratio))
        surface.blit(A.rewind_overlay, (0, 0))

        if self.flash_timer > REWIND_FLASH_DURATION // 2:
            banner = A.hud_rewind_banner
            surface.blit(banner, (
                SCREEN_WIDTH // 2 - banner.get_width() // 2,
                SCREEN_HEIGHT // 2 - banner.get_height() // 2,
            ))

    # ai
    def draw_dev_panel(self, surface):
        panel_w, panel_h = 180, 180
        px = SCREEN_WIDTH // 2 - panel_w // 2
        py = SCREEN_HEIGHT // 2 - panel_h // 2

        surface.blit(self.dev_panel_bg, (px, py))
        pygame.draw.rect(surface, CYAN, (px, py, panel_w, panel_h), 1)

        title = self.font_hud.render("[ DEV MODE ]", True, YELLOW)
        surface.blit(title, (px + panel_w // 2 - title.get_width() // 2, py + 8))

        hint = self.font_hud.render("1-4: jump stage  Q: quit", True, WHITE)
        surface.blit(hint, (px + panel_w // 2 - hint.get_width() // 2, py + 24))

        stage_labels = {1: "Normal", 2: "Switch", 3: "Golem", 4: "Boss"}
        for i, label_name in stage_labels.items():
            y = py + 42 + (i - 1) * 18
            if i == self.stage_num:
                color = CYAN
                marker = ">"
            else:
                color = WHITE
                marker = " "
            label = self.font_hud.render(f"{marker} {i}: Stage {i}  {label_name}", True, color)
            surface.blit(label, (px + 12, y))

        esc_hint = self.font_hud.render("ESC: close", True, (150, 150, 150))
        surface.blit(esc_hint, (px + panel_w // 2 - esc_hint.get_width() // 2, py + panel_h - 16))

    # ai
    def draw_outcome_overlay(self, surface):
        surface.blit(self.outcome_overlay, (0, 0))

        msg_map = {
            "clear":    ("VICTORY!", CYAN),
            "gameover": ("GAME OVER", RED),
        }
        msg, col = msg_map.get(self.outcome, ("???", WHITE))
        label = self.font_big.render(msg, True, col)
        surface.blit(label, (SCREEN_WIDTH // 2 - label.get_width() // 2,
                              SCREEN_HEIGHT // 2 - 30))
        hint = self.font_hud.render("Press ENTER to continue", True, YELLOW)
        surface.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2,
                             SCREEN_HEIGHT // 2 + 30))
