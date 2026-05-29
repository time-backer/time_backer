import sys
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE
from scenes.start_scene import StartScene
from scenes.game_scene import GameScene
from scenes.end_scene import EndScene


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    scenes: dict = {
        "start": StartScene(),
        "game":  GameScene(stage_num=1),
        "end":   None,
    }
    current = "start"
    selected_stage = 1  # 선택된 스테이지

    while True:
        scene = scenes[current]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

            result = scene.handle_event(event)
            if result == "quit":
                pygame.quit()
                sys.exit()
            elif result == "game":
                current = "game"

        update_result = scene.update() if hasattr(scene, "update") else None

        if update_result in ("clear", "gameover"):
            victory = update_result == "clear"
            game_scene = scenes["game"]
            clear_time = game_scene.get_clear_time()
            rewind_used = game_scene.get_rewind_used()
            scenes["end"] = EndScene(victory, clear_time, rewind_used)
            current = "end"
        elif update_result == "start":
            scenes["start"] = StartScene()
            scenes["game"]  = GameScene(stage_num=selected_stage)
            current = "start"

        scene = scenes[current]
        scene.draw(screen)

        # ENTER to continue from in-game outcome overlay
        if current == "game" and scene._outcome:  # type: ignore[attr-defined]
            pressed = pygame.key.get_pressed()
            if pressed[pygame.K_RETURN] or pressed[pygame.K_SPACE]:
                outcome = scene._outcome  # type: ignore[attr-defined]
                if outcome in ("clear", "gameover"):
                    victory = outcome == "clear"
                    clear_time = scene.get_clear_time()  # type: ignore
                    rewind_used = scene.get_rewind_used()  # type: ignore
                    scenes["end"] = EndScene(victory, clear_time, rewind_used)
                    current = "end"

        # EndScene → back to title
        if current == "end":
            end_result = scene.handle_event(pygame.event.Event(pygame.NOEVENT))
            pressed = pygame.key.get_pressed()
            if pressed[pygame.K_RETURN] or pressed[pygame.K_SPACE]:
                scenes["start"] = StartScene()
                scenes["game"]  = GameScene(stage_num=selected_stage)
                current = "start"

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
