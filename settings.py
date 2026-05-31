# 내부 렌더링 해상도 (480×288 = 15×9 타일)
# 최종 표시는 DISPLAY_WIDTH×DISPLAY_HEIGHT 로 확대 (5/3배)
SCREEN_WIDTH  = 480
SCREEN_HEIGHT = 288
DISPLAY_WIDTH  = 800
DISPLAY_HEIGHT = 480
FPS = 60
TITLE = "Time Backer"

GRAVITY = 0.6
JUMP_FORCE = -13
MOVE_SPEED = 3

REWIND_FLASH_DURATION = 60   # 1 second at 60 fps
REWIND_TIME_SECONDS = 3      # 3 seconds to rewind
REWIND_FRAMES = 180          # 3 seconds at 60 fps (3 * 60)
MAX_REWIND_COUNT = 5         # Maximum rewind uses per stage
REWIND_SPEED = 3             # Frames to pop per update (higher = faster rewind)

TILE_SIZE = 32

# Colors
WHITE     = (255, 255, 255)
BLACK     = (0,   0,   0)
GRAY      = (80,  80,  80)
DARK_GRAY = (40,  40,  40)
RED       = (220, 60,  60)
GREEN     = (60,  200, 80)
BLUE      = (60,  120, 220)
CYAN      = (80,  220, 220)
YELLOW    = (240, 210, 50)
ORANGE    = (240, 140, 40)
PURPLE    = (160, 60,  220)
SPIKE_COL = (200, 50,  50)
SKY       = (20,  20,  40)
EXIT_COL  = (50,  230, 130)
