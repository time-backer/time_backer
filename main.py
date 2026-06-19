import sys
import pygame
import asset_loader
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, DISPLAY_WIDTH, DISPLAY_HEIGHT, FPS, TITLE
from scenes.start_scene import StartScene
from scenes.game_scene import GameScene
from scenes.end_scene import EndScene


def main():
    pygame.init()
    display = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
    # display와 같은 픽셀 포맷으로 생성해야 convert_alpha() 스프라이트가 올바르게 렌더링됨
    game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)).convert()
    asset_loader.load()
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    scenes = {
        "start": StartScene(),
        "game":  GameScene(stage_num=1),
        "end":   None,
    }
    current = "start"
    current_stage = 1  # 현재 진행 중인 스테이지 (1~3)

    while True:
        scene = scenes[current]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            result = scene.handle_event(event)
            if result == "quit":
                pygame.quit()
                sys.exit()
            elif result and result.startswith("dev:"):
                target_stage = int(result.split(":")[1])
                current_stage = target_stage
                scenes["game"] = GameScene(stage_num=target_stage)
                current = "game"
            elif result == "game":
                # 게임 시작 시 스테이지 1부터
                current_stage = 1
                scenes["game"] = GameScene(stage_num=current_stage)
                current = "game"

        if hasattr(scene, "update"):
            update_result = scene.update()
        else:
            update_result = None

        if update_result == "clear":
            game_scene = scenes["game"]
            clear_time = game_scene.get_clear_time()
            rewind_used = game_scene.get_rewind_used()
            if current_stage < 4:
                current_stage += 1
                scenes["game"] = GameScene(stage_num=current_stage)
                current = "game"
            else:
                scenes["end"] = EndScene(True, clear_time, rewind_used)
                current = "end"
        elif update_result == "gameover":
            # 게임오버
            game_scene = scenes["game"]
            clear_time = game_scene.get_clear_time()
            rewind_used = game_scene.get_rewind_used()
            scenes["end"] = EndScene(False, clear_time, rewind_used)
            current = "end"

        scene = scenes[current]
        scene.draw(game_surface)
        pygame.transform.smoothscale(game_surface, (DISPLAY_WIDTH, DISPLAY_HEIGHT), display)

        # EndScene → back to title
        if current == "end":
            pressed = pygame.key.get_pressed()
            if pressed[pygame.K_RETURN] or pressed[pygame.K_SPACE]:
                # 타이틀로 돌아갈 때 스테이지 초기화
                current_stage = 1
                scenes["start"] = StartScene()
                scenes["game"] = GameScene(stage_num=1)
                current = "start"

        pygame.display.flip()  # display에 이미 scale 결과가 blitted 됨
        clock.tick(FPS)


if __name__ == "__main__":
    main()
