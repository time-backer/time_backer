import os
import pygame

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def _img(subpath: str) -> pygame.Surface:
    return pygame.image.load(os.path.join(_ASSETS, subpath)).convert_alpha()


def _cut(sheet: pygame.Surface, fw: int, fh: int) -> list:
    cols = sheet.get_width() // fw
    return [sheet.subsurface(pygame.Rect(i * fw, 0, fw, fh)) for i in range(cols)]


# ── Player (32×32 frames) ────────────────────────────────────────────────
player_idle:   list = []
player_run:    list = []
player_jump:   list = []
player_rewind: list = []

# ── Enemies ─────────────────────────────────────────────────────────────
patrol:       list = []
golem:        list = []
golem_highhp: list = []
golem_lowhp:  list = []

# ── Boss (72×72 frames) ──────────────────────────────────────────────────
boss_phase1: list = []
boss_phase2: list = []
boss_phase3: list = []

# ── Tiles ───────────────────────────────────────────────────────────────
tile_ground:     pygame.Surface = None  # type: ignore[assignment]
tile_iron:       pygame.Surface = None  # type: ignore[assignment]
tile_spike:      list = []
tile_switch_off: pygame.Surface = None  # type: ignore[assignment]
tile_switch_on:  pygame.Surface = None  # type: ignore[assignment]

# ── Effects ─────────────────────────────────────────────────────────────
portal:         list = []
rewind_overlay: pygame.Surface = None  # type: ignore[assignment]

# ── HUD ─────────────────────────────────────────────────────────────────
hud_hp_full:       pygame.Surface = None  # type: ignore[assignment]
hud_hp_empty:      pygame.Surface = None  # type: ignore[assignment]
hud_rewind_frames: list = []
hud_rewind_banner: pygame.Surface = None  # type: ignore[assignment]

_loaded = False


def load() -> None:
    global _loaded
    global player_idle, player_run, player_jump, player_rewind
    global patrol, golem, golem_highhp, golem_lowhp
    global boss_phase1, boss_phase2, boss_phase3
    global tile_ground, tile_iron, tile_spike, tile_switch_off, tile_switch_on
    global portal, rewind_overlay
    global hud_hp_full, hud_hp_empty, hud_rewind_frames, hud_rewind_banner

    if _loaded:
        return

    # Player
    player_idle   = _cut(_img("player/player_idle.png"),   32, 32)
    player_run    = _cut(_img("player/player_run.png"),    32, 32)
    player_jump   = _cut(_img("player/player_jump.png"),   32, 32)
    player_rewind = _cut(_img("player/player_rewind.png"), 32, 32)

    # Enemies
    patrol       = _cut(_img("enemies/patrol.png"),       32, 32)
    golem        = _cut(_img("enemies/golem.png"),        32, 32)
    golem_highhp = _cut(_img("enemies/golem_highhp.png"), 48, 48)
    golem_lowhp  = _cut(_img("enemies/golem_lowhp.png"),  48, 48)

    # Boss
    boss_phase1 = _cut(_img("boss/boss_phase1.png"), 72, 72)
    boss_phase2 = _cut(_img("boss/boss_phase2.png"), 72, 72)
    boss_phase3 = _cut(_img("boss/boss_phase3.png"), 72, 72)

    # Tiles
    tile_ground = _img("tiles/tiles.png").subsurface(pygame.Rect(0, 0, 32, 32))
    tile_iron   = _img("tiles/tiles_iron.png").subsurface(pygame.Rect(0, 0, 32, 32))
    tile_spike  = _cut(_img("tiles/spike.png"), 32, 32)

    sw_sheet        = _img("tiles/switch.png")
    tile_switch_off = sw_sheet.subsurface(pygame.Rect(0,  0, 32, 32))
    tile_switch_on  = sw_sheet.subsurface(pygame.Rect(32, 0, 32, 32))

    # Effects
    portal         = _cut(_img("effects/portal.png"), 32, 32)
    rewind_overlay = _img("effects/rewind_overlay.png")

    # HUD
    hp_sheet     = _img("hud/hud_hp.png")
    hud_hp_full  = hp_sheet.subsurface(pygame.Rect(0,  0, 24, 24))
    hud_hp_empty = hp_sheet.subsurface(pygame.Rect(24, 0, 24, 24))

    hud_rewind_frames = _cut(_img("hud/hud_rewind.png"), 24, 24)
    hud_rewind_banner = _img("hud/hud_rewind_banner.png")

    _loaded = True
