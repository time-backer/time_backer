import pygame
import pymunk
from typing import List, Optional

from core.game_state import GameState
from core.time_stack import TimeStack
from core.physics import PhysicsWorld, STOMP_VY
from entities.player import Player
from entities.enemy import Enemy
from entities.absorbing_enemy import AbsorbingEnemy
from entities.boss import Boss
from world.stage import Stage
from world.boss_stage import BossStage
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE,
    REWIND_FLASH_DURATION, REWIND_FRAMES, MAX_REWIND_COUNT, REWIND_SPEED,
    WHITE, YELLOW, RED, CYAN, BLACK, SKY, FPS,
)
import asset_loader as A


class GameScene:
    def __init__(self, stage_num: int = 1) -> None:
        self._stage_num = stage_num

        # ── 스테이지 생성 ────────────────────────────────────────────────
        if stage_num == 7:
            self._stage = BossStage()
        else:
            self._stage = Stage(stage_num=stage_num)

        # ── 물리 월드 ────────────────────────────────────────────────────
        self._phys = PhysicsWorld()
        self._build_physics()

        # ── 플레이어 ─────────────────────────────────────────────────────
        sx, sy = self._stage.get_player_start()
        p_body = self._phys.add_player_body(sx, sy, Player.WIDTH, Player.HEIGHT)
        self._player = Player(p_body)

        # ── 일반 적 ──────────────────────────────────────────────────────
        self._enemies: List[Enemy] = []
        for i, (ex, ey) in enumerate(self._stage.get_enemy_spawns()):
            body = self._phys.add_enemy_body(ex, ey, Enemy.WIDTH, Enemy.HEIGHT)
            self._enemies.append(Enemy(body, i))

        # ── 흡수 적 (Stage 5) ────────────────────────────────────────────
        self._absorbing_enemy: Optional[AbsorbingEnemy] = None
        if stage_num == 5:
            ax, ay = 12 * TILE_SIZE, 5 * TILE_SIZE
            ab_body = self._phys.add_enemy_body(ax, ay, AbsorbingEnemy.WIDTH,
                                                AbsorbingEnemy.HEIGHT)
            self._absorbing_enemy = AbsorbingEnemy(ab_body)

        # ── 보스 (Stage 7) ───────────────────────────────────────────────
        self._boss: Optional[Boss] = None
        if stage_num == 7:
            bx, by = self._stage.get_boss_position()
            self._boss = Boss(bx, by)

        # ── 타임 스택 ────────────────────────────────────────────────────
        self._time_stack = TimeStack()
        self._rewind_count = MAX_REWIND_COUNT
        self._frame = 0
        self._start_time = pygame.time.get_ticks()
        self._paused_time = 0

        self._flash_timer = 0
        self._flash_full  = False
        self._rewinding   = False
        self._rewind_target_frames = 0
        self._rewind_start_time    = 0

        self._font_hud = pygame.font.SysFont(None, 16)   # 내부 288px 기준
        self._font_big = pygame.font.SysFont(None, 32)

        self._camera_x = 0
        self._camera_y = 0
        self._outcome: Optional[str] = None

    # ── 물리 월드에 타일 등록 ─────────────────────────────────────────────

    def _build_physics(self) -> None:
        for tile in self._stage.ground_tiles:
            self._phys.add_static_ground(tile.rect.x, tile.rect.y, TILE_SIZE, TILE_SIZE)

    # ── 리셋 ─────────────────────────────────────────────────────────────

    def reset(self) -> None:
        self.__init__(self._stage_num)

    # ── 외부 접근 ─────────────────────────────────────────────────────────

    def get_clear_time(self) -> int:
        elapsed = pygame.time.get_ticks() - self._start_time - self._paused_time
        return elapsed // 1000

    def get_rewind_used(self) -> int:
        return MAX_REWIND_COUNT - self._rewind_count

    # ── 이벤트 ───────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_z:
                self._rewind_one()
            elif event.key == pygame.K_x:
                self._rewind_all()
            elif event.key == pygame.K_r:
                self.reset()
        return None

    # ── 메인 업데이트 ─────────────────────────────────────────────────────

    def update(self) -> Optional[str]:
        if self._outcome:
            return self._outcome

        if self._rewinding:
            self._process_rewind()
            if self._flash_timer > 0:
                self._flash_timer -= 1
            return None

        keys = pygame.key.get_pressed()
        self._frame += 1

        # 1) 입력 처리 (이전 프레임 on_ground 사용)
        self._player.handle_input(keys)

        # 2) 적 AI 처리
        for enemy in self._enemies:
            enemy.update(self._stage.pixel_width)
        if self._boss:
            self._boss.update()

        # 3) 물리 스텝
        self._phys.step()

        # 4) ground 상태 동기화
        self._player.on_ground = self._phys.player_on_ground
        self._player.clamp_x(self._stage.pixel_width)
        self._player.tick_hurt()

        # 5) 충돌 처리 (rect 기반 — pymunk 외)
        self._handle_spike_hits()
        self._handle_enemy_hits()
        self._handle_switch_hits()
        self._handle_absorbing_enemy()
        self._handle_boss_collision()

        # 6) 스냅샷 저장
        self._push_snapshot()

        if self._flash_timer > 0:
            self._flash_timer -= 1

        # 7) 승패 판정
        if self._boss and not self._boss.alive:
            self._outcome = "clear"
            return self._outcome

        if self._stage.is_clear(self._player.rect):
            self._outcome = "clear"
            return self._outcome

        if self._player.is_dead() or self._player.y > self._stage.pixel_height + 100:
            self._outcome = "gameover"
            return self._outcome

        # 8) 카메라 (수평 + 수직)
        target_cx = int(self._player.x) - SCREEN_WIDTH // 3
        self._camera_x = max(0, min(target_cx,
                                    self._stage.pixel_width - SCREEN_WIDTH))

        target_cy = int(self._player.y) + Player.HEIGHT // 2 - SCREEN_HEIGHT // 2
        self._camera_y = max(0, min(target_cy,
                                    self._stage.pixel_height - SCREEN_HEIGHT))
        return None

    # ── 충돌 처리 헬퍼 ───────────────────────────────────────────────────

    def _handle_spike_hits(self) -> None:
        pr = self._player.rect
        for spike in self._stage.spike_tiles:
            if pr.colliderect(spike.get_rect()):
                self._player.take_damage()

    def _handle_enemy_hits(self) -> None:
        pr = self._player.rect
        for enemy in self._enemies:
            if not enemy.alive:
                continue
            if pr.colliderect(enemy.rect):
                if self._player.vy > 0 and pr.bottom < enemy.rect.centery + 10:
                    enemy.die()
                    body = self._player._body
                    body.velocity = pymunk.Vec2d(body.velocity.x, STOMP_VY)
                else:
                    self._player.take_damage()

    def _handle_switch_hits(self) -> None:
        self._stage.check_switches(self._player.rect)

    def _handle_absorbing_enemy(self) -> None:
        if not self._absorbing_enemy or not self._absorbing_enemy.alive:
            return
        pr = self._player.rect
        ar = self._absorbing_enemy.rect
        if pr.colliderect(ar):
            if self._player.vy > 0 and pr.bottom < ar.centery + 10:
                self._absorbing_enemy.take_damage()
                body = self._player._body
                body.velocity = pymunk.Vec2d(body.velocity.x, STOMP_VY)
            else:
                self._player.take_damage()

    def _handle_boss_collision(self) -> None:
        if not self._boss or not self._boss.alive:
            return
        pr = self._player.rect
        br = self._boss.rect
        if pr.colliderect(br):
            if self._player.vy > 0 and pr.bottom < br.centery + 10:
                self._boss.take_damage(1)
                body = self._player._body
                body.velocity = pymunk.Vec2d(body.velocity.x, STOMP_VY * 1.2)
            else:
                self._player.take_damage()

    # ── 시간 되감기 ───────────────────────────────────────────────────────

    def _push_snapshot(self) -> None:
        state = self._player.capture_state(self._rewind_count)
        state.enemies = [e.capture_state() for e in self._enemies]
        state.switch_states = [s.activated for s in self._stage.switch_tiles]
        self._time_stack.push(state)

    def _apply_state(self, state: GameState) -> None:
        self._player.apply_state(state)
        for i, es in enumerate(state.enemies):
            if i < len(self._enemies):
                self._enemies[i].apply_state(es)
        for i, activated in enumerate(state.switch_states):
            if i < len(self._stage.switch_tiles):
                self._stage.switch_tiles[i].activated = activated

    def _rewind_one(self) -> None:
        if self._rewind_count <= 0 or self._rewinding:
            return
        if len(self._time_stack) == 0:
            return
        if self._absorbing_enemy and self._absorbing_enemy.alive:
            self._absorbing_enemy.absorb_rewind()
        if self._boss and self._boss.reversing:
            self._boss.cancel_reverse()
        self._rewinding           = True
        self._rewind_target_frames = min(REWIND_FRAMES, len(self._time_stack))
        self._rewind_count        -= 1
        self._flash_timer         = REWIND_FLASH_DURATION
        self._flash_full          = False
        self._rewind_start_time   = pygame.time.get_ticks()

    def _rewind_all(self) -> None:
        if self._rewind_count <= 0 or self._rewinding:
            return
        if len(self._time_stack) == 0:
            return
        self._rewinding           = True
        self._rewind_target_frames = len(self._time_stack)
        self._rewind_count        -= 1
        self._flash_timer         = REWIND_FLASH_DURATION
        self._flash_full          = True
        self._rewind_start_time   = pygame.time.get_ticks()

    def _process_rewind(self) -> None:
        if self._rewind_target_frames <= 0:
            self._rewinding = False
            self._paused_time += pygame.time.get_ticks() - self._rewind_start_time
            self._player._hurt_timer = FPS   # 역행 후 1초 무적
            return

        for _ in range(REWIND_SPEED):
            if self._rewind_target_frames <= 0:
                break
            state = self._time_stack.pop()
            if state is None:
                self._rewinding = False
                self._rewind_target_frames = 0
                self._player._hurt_timer = FPS   # 역행 후 1초 무적
                return
            self._apply_state(state)
            self._rewind_target_frames -= 1

    # ── 렌더링 ────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        cx, cy = self._camera_x, self._camera_y

        self._stage.draw(surface, cx, cy)

        for enemy in self._enemies:
            enemy.draw(surface, cx, cy)

        if self._absorbing_enemy:
            self._absorbing_enemy.draw(surface, cx, cy)

        if self._boss:
            self._boss.draw(surface, cx, cy)

        self._player.draw(surface, cx, cy, rewinding=self._rewinding)

        self._draw_hud(surface)

        if self._flash_timer > 0:
            self._draw_rewind_flash(surface)

        if self._outcome:
            self._draw_outcome_overlay(surface)

    # ── HUD ──────────────────────────────────────────────────────────────

    def _draw_hud(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, (10, 10, 25), (0, 0, SCREEN_WIDTH, 36))

        stage_surf = self._font_hud.render(f"STAGE {self._stage_num}", True, CYAN)
        surface.blit(stage_surf, (10, 8))

        hp_label = self._font_hud.render("HP:", True, WHITE)
        surface.blit(hp_label, (72, 6))
        for i in range(Player.MAX_HP):
            icon = A.hud_hp_full if i < self._player.hp else A.hud_hp_empty
            surface.blit(icon, (100 + i * 26, 6))

        if self._rewinding:
            rewind_text = f"REWINDING {self._rewind_target_frames}"
            rewind_col  = YELLOW
        else:
            rewind_text = f"REWIND: {self._rewind_count} / {MAX_REWIND_COUNT}"
            rewind_col  = CYAN if self._rewind_count > 0 else RED
        rw_surf = self._font_hud.render(rewind_text, True, rewind_col)
        surface.blit(rw_surf, (SCREEN_WIDTH // 2 - rw_surf.get_width() // 2, 8))

        elapsed   = self.get_clear_time()
        time_surf = self._font_hud.render(f"TIME: {elapsed}s", True, YELLOW)
        surface.blit(time_surf, (SCREEN_WIDTH - time_surf.get_width() - 10, 8))

    # ── 시각 효과 ─────────────────────────────────────────────────────────

    def _draw_rewind_flash(self, surface: pygame.Surface) -> None:
        ratio = self._flash_timer / REWIND_FLASH_DURATION
        overlay = A.rewind_overlay.copy()
        overlay.set_alpha(int(200 * ratio))
        surface.blit(overlay, (0, 0))

        if self._flash_timer > REWIND_FLASH_DURATION // 2:
            banner = A.hud_rewind_banner
            surface.blit(banner, (
                SCREEN_WIDTH  // 2 - banner.get_width()  // 2,
                SCREEN_HEIGHT // 2 - banner.get_height() // 2,
            ))

    def _draw_outcome_overlay(self, surface: pygame.Surface) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surface.blit(overlay, (0, 0))

        msg_map = {
            "clear":    ("VICTORY!", CYAN),
            "gameover": ("GAME OVER", RED),
        }
        msg, col = msg_map.get(self._outcome, ("???", WHITE))
        label = self._font_big.render(msg, True, col)
        surface.blit(label, (SCREEN_WIDTH  // 2 - label.get_width()  // 2,
                              SCREEN_HEIGHT // 2 - 30))
        hint = self._font_hud.render("Press ENTER to continue", True, YELLOW)
        surface.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2,
                             SCREEN_HEIGHT // 2 + 30))
