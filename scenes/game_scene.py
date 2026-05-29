import pygame
from typing import List, Optional

from core.game_state import GameState
from core.time_stack import TimeStack
from entities.player import Player
from entities.enemy import Enemy
from entities.absorbing_enemy import AbsorbingEnemy
from entities.boss import Boss
from world.stage import Stage
from world.boss_stage import BossStage
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE,
    REWIND_FLASH_DURATION, REWIND_FRAMES, MAX_REWIND_COUNT, REWIND_SPEED,
    WHITE, YELLOW, RED, CYAN, BLACK, SKY,
)


class GameScene:
    def __init__(self, stage_num: int = 1) -> None:
        self._stage_num = stage_num
        
        # 보스 스테이지 (7) vs 일반 스테이지 (1~6)
        if stage_num == 7:
            self._stage = BossStage()
        else:
            self._stage = Stage(stage_num=stage_num)

        sx, sy = self._stage.get_player_start()
        self._player = Player(sx, sy)

        self._enemies = [
            Enemy(x, y, idx)
            for idx, (x, y) in enumerate(self._stage.get_enemy_spawns())
        ]
        
        # Stage 5: 흡수 적 추가
        self._absorbing_enemy = None
        if stage_num == 5:
            # 중앙에 흡수 적 배치
            self._absorbing_enemy = AbsorbingEnemy(12 * TILE_SIZE, 5 * TILE_SIZE)
        
        # Stage 7: 보스 추가
        self._boss = None
        if stage_num == 7:
            bx, by = self._stage.get_boss_position()
            self._boss = Boss(bx, by)

        self._time_stack = TimeStack()
        self._rewind_count = MAX_REWIND_COUNT  # 남은 역행 횟수
        self._frame = 0
        self._start_time = pygame.time.get_ticks()  # 클리어 타임 측정
        self._paused_time = 0  # 역행 중 정지된 시간

        self._flash_timer = 0
        self._flash_full = False
        
        # 시간 역행 애니메이션
        self._rewinding = False
        self._rewind_target_frames = 0
        self._rewind_start_time = 0

        self._font_hud = pygame.font.SysFont(None, 28)
        self._font_big = pygame.font.SysFont(None, 52)

        self._camera_x = 0
        self._outcome: Optional[str] = None  # "next_stage" | "clear" | "gameover"

    # ------------------------------------------------------------------
    def reset(self) -> None:
        self.__init__(self._stage_num)

    # ------------------------------------------------------------------
    # Getters for external access
    # ------------------------------------------------------------------
    def get_clear_time(self) -> int:
        """클리어 타임 반환 (초 단위)"""
        elapsed = pygame.time.get_ticks() - self._start_time - self._paused_time
        return elapsed // 1000
    
    def get_rewind_used(self) -> int:
        """사용한 역행 횟수 반환"""
        return MAX_REWIND_COUNT - self._rewind_count

    # ------------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_z:
                self._rewind_one()
            elif event.key == pygame.K_x:
                self._rewind_all()
            elif event.key == pygame.K_r:
                self.reset()
        return None

    def update(self) -> Optional[str]:
        if self._outcome:
            return self._outcome

        keys = pygame.key.get_pressed()
        
        # 역행 중이면 게임 로직 스킵하고 되감기만 수행
        if self._rewinding:
            self._process_rewind()
            if self._flash_timer > 0:
                self._flash_timer -= 1
            return None
        
        self._frame += 1

        # 매 프레임마다 스냅샷 저장 (3초 = 180프레임 저장)
        self._push_snapshot()

        self._player.handle_input(keys)
        self._player.update(self._stage.ground_tiles, self._stage.pixel_width)

        for enemy in self._enemies:
            enemy.update(self._stage.ground_tiles, self._stage.pixel_width)
        
        # 흡수 적 업데이트
        if self._absorbing_enemy:
            self._absorbing_enemy.update(self._stage.ground_tiles, self._stage.pixel_width)
        
        # 보스 업데이트
        if self._boss:
            self._boss.update()

        self._check_spike_collisions()
        self._check_enemy_collisions()
        self._check_absorbing_enemy_collision()
        self._check_boss_collision()
        
        # 스위치 체크 (Stage 2)
        self._stage.check_switches(self._player.rect)

        if self._flash_timer > 0:
            self._flash_timer -= 1

        # --- win / lose ---
        # 보스 스테이지: 보스 처치 시 클리어
        if self._boss and not self._boss.alive:
            self._outcome = "clear"
            return self._outcome
        
        # 일반 스테이지: 출구 도달 시 클리어
        if self._stage.is_clear(self._player.rect):
            self._outcome = "clear"
            return self._outcome

        # death handling
        if self._player.is_dead() or self._player.y > self._stage.pixel_height + 100:
            self._outcome = "gameover"
            return self._outcome

        # camera
        target_cx = int(self._player.x) - SCREEN_WIDTH // 3
        self._camera_x = max(0, min(target_cx,
                                    self._stage.pixel_width - SCREEN_WIDTH))
        return None

    def draw(self, surface: pygame.Surface) -> None:
        self._stage.draw(surface, self._camera_x)

        for enemy in self._enemies:
            enemy.draw(surface, self._camera_x)
        
        # 흡수 적 렌더링
        if self._absorbing_enemy:
            self._absorbing_enemy.draw(surface, self._camera_x)
        
        # 보스 렌더링
        if self._boss:
            self._boss.draw(surface, self._camera_x)

        self._player.draw(surface, self._camera_x)

        self._draw_hud(surface)

        if self._flash_timer > 0:
            self._draw_rewind_flash(surface)

        if self._outcome:
            self._draw_outcome_overlay(surface)

    # ------------------------------------------------------------------
    # Rewind
    # ------------------------------------------------------------------
    def _push_snapshot(self) -> None:
        state = self._player.capture_state(0)
        state.enemies = [e.capture_state() for e in self._enemies]
        state.switch_states = [s.activated for s in self._stage.switch_tiles]
        self._time_stack.push(state)

    def _apply_state(self, state: GameState) -> None:
        self._player.apply_state(state)
        for i, es in enumerate(state.enemies):
            if i < len(self._enemies):
                self._enemies[i].apply_state(es)
        # 스위치 상태 복원
        for i, activated in enumerate(state.switch_states):
            if i < len(self._stage.switch_tiles):
                self._stage.switch_tiles[i].activated = activated

    def _rewind_one(self) -> None:
        """Z키: 3초 전으로 역행 (애니메이션)"""
        if self._rewind_count <= 0 or self._rewinding:
            return
        if len(self._time_stack) == 0:
            return
        
        # 흡수 적이 있으면 HP 증가
        if self._absorbing_enemy and self._absorbing_enemy.alive:
            self._absorbing_enemy.absorb_rewind()
        
        # 보스 타임 리버스 취소 (Phase 3 핵심 메커니즘)
        if self._boss and self._boss.reversing:
            self._boss.cancel_reverse()
        
        # 역행 애니메이션 시작
        self._rewinding = True
        self._rewind_target_frames = min(REWIND_FRAMES, len(self._time_stack))
        self._rewind_count -= 1
        self._flash_timer = REWIND_FLASH_DURATION
        self._flash_full = False
        self._rewind_start_time = pygame.time.get_ticks()  # 역행 시작 시간 기록

    def _rewind_all(self) -> None:
        """X키: 시작 위치로 완전 복귀 (애니메이션)"""
        if self._rewind_count <= 0 or self._rewinding:
            return
        if len(self._time_stack) == 0:
            return
        
        # 전체 역행 애니메이션 시작
        self._rewinding = True
        self._rewind_target_frames = len(self._time_stack)
        self._rewind_count -= 1
        self._flash_timer = REWIND_FLASH_DURATION
        self._flash_full = True
        self._rewind_start_time = pygame.time.get_ticks()  # 역행 시작 시간 기록
    
    def _process_rewind(self) -> None:
        """매 프레임마다 호출되어 역행 애니메이션 처리"""
        if self._rewind_target_frames <= 0:
            self._rewinding = False
            # 역행 종료 시 정지된 시간 누적
            self._paused_time += pygame.time.get_ticks() - self._rewind_start_time
            return
        
        # 빠르게 되감기 (매 프레임마다 여러 프레임 pop)
        for _ in range(REWIND_SPEED):
            if self._rewind_target_frames <= 0:
                break
            
            state = self._time_stack.pop()
            if state is None:
                self._rewinding = False
                self._rewind_target_frames = 0
                return
            
            self._apply_state(state)
            self._rewind_target_frames -= 1

    # ------------------------------------------------------------------
    # Collisions
    # ------------------------------------------------------------------
    def _check_spike_collisions(self) -> None:
        pr = self._player.rect
        for spike in self._stage.spike_tiles:
            if pr.colliderect(spike.get_rect()):
                self._player.take_damage()

    def _check_enemy_collisions(self) -> None:
        pr = self._player.rect
        for enemy in self._enemies:
            if not enemy.alive:
                continue
            if pr.colliderect(enemy.rect):
                if self._player.vy > 0 and pr.bottom < enemy.rect.centery + 10:
                    enemy.alive = False
                    self._player.vy = -8
                else:
                    self._player.take_damage()
    
    def _check_absorbing_enemy_collision(self) -> None:
        """흡수 적 충돌 처리"""
        if not self._absorbing_enemy or not self._absorbing_enemy.alive:
            return
        
        pr = self._player.rect
        if pr.colliderect(self._absorbing_enemy.rect):
            # 위에서 밟으면 데미지
            if self._player.vy > 0 and pr.bottom < self._absorbing_enemy.rect.centery + 10:
                self._absorbing_enemy.take_damage()
                self._player.vy = -8
            else:
                # 옆에서 부딪히면 플레이어 피격
                self._player.take_damage()
    
    def _check_boss_collision(self) -> None:
        """보스 충돌 처리"""
        if not self._boss or not self._boss.alive:
            return
        
        pr = self._player.rect
        if pr.colliderect(self._boss.rect):
            # 위에서 밟으면 보스에게 데미지
            if self._player.vy > 0 and pr.bottom < self._boss.rect.centery + 10:
                self._boss.take_damage(1)
                self._player.vy = -10  # 높게 튕김
            else:
                # 옆에서 부딪히면 플레이어 피격
                self._player.take_damage()

    # ------------------------------------------------------------------
    # HUD
    # ------------------------------------------------------------------
    def _draw_hud(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, (10, 10, 25), (0, 0, SCREEN_WIDTH, 36))

        # Stage number (left)
        stage_text = f"STAGE {self._stage_num}"
        stage_surf = self._font_hud.render(stage_text, True, CYAN)
        surface.blit(stage_surf, (10, 8))

        # HP
        hp_label = self._font_hud.render("HP:", True, WHITE)
        surface.blit(hp_label, (120, 8))
        for i in range(Player.MAX_HP):
            col = RED if i < self._player.hp else (60, 60, 60)
            pygame.draw.rect(surface, col, (155 + i * 22, 10, 16, 16), border_radius=3)

        # Rewind count (center)
        if self._rewinding:
            # 역행 중일 때 진행 상태 표시
            rewind_text = f"REWINDING {self._rewind_target_frames}"
            rewind_col = YELLOW
        else:
            rewind_text = f"REWIND: {self._rewind_count} / {MAX_REWIND_COUNT}"
            rewind_col = CYAN if self._rewind_count > 0 else RED
        rw_surf = self._font_hud.render(rewind_text, True, rewind_col)
        surface.blit(rw_surf, (SCREEN_WIDTH // 2 - rw_surf.get_width() // 2, 8))

        # Time (역행 중 정지된 시간 제외)
        elapsed = self.get_clear_time()
        time_text = f"TIME: {elapsed}s"
        time_surf = self._font_hud.render(time_text, True, YELLOW)
        surface.blit(time_surf, (SCREEN_WIDTH - time_surf.get_width() - 10, 8))

    # ------------------------------------------------------------------
    # Visual effects
    # ------------------------------------------------------------------
    def _draw_rewind_flash(self, surface: pygame.Surface) -> None:
        max_frames = REWIND_FLASH_DURATION
        ratio = self._flash_timer / max_frames
        alpha = int(160 * ratio)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        if self._flash_full:
            overlay.fill((80, 40, 180, alpha))
        else:
            overlay.fill((40, 80, 220, alpha))
        surface.blit(overlay, (0, 0))

        if self._flash_timer > max_frames // 2:
            text = "<<< FULL REWIND" if self._flash_full else "<< REWIND"
            label = self._font_big.render(text, True, (200, 220, 255))
            surface.blit(label, (SCREEN_WIDTH // 2 - label.get_width() // 2,
                                  SCREEN_HEIGHT // 2 - label.get_height() // 2))

    def _draw_outcome_overlay(self, surface: pygame.Surface) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surface.blit(overlay, (0, 0))

        msg_map = {
            "clear":      ("VICTORY!", CYAN),
            "next_stage": ("STAGE CLEAR!", CYAN),
            "gameover":   ("GAME OVER",   RED),
        }
        msg, col = msg_map.get(self._outcome, ("???", WHITE))
        label = self._font_big.render(msg, True, col)
        surface.blit(label, (SCREEN_WIDTH // 2 - label.get_width() // 2,
                              SCREEN_HEIGHT // 2 - 30))

        hint = self._font_hud.render("Press ENTER to continue", True, YELLOW)
        surface.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2,
                             SCREEN_HEIGHT // 2 + 30))
