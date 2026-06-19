"""pytmx 기반 타일맵 로더

TMX 파일 하나를 읽어서 Tile 객체 리스트를 반환한다.
GID → tile_type 매핑은 TSX 타일셋 id 순서에 의존한다:
  GID 1 = ground, 2 = spike, 3 = exit, 4 = switch_a, 5 = switch_b
"""

import os
import pytmx

from world.tile import Tile

MAPS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "assets", "maps")

VALID_TILE_TYPES = ["ground", "spike", "exit", "switch_a", "switch_b", "gate"]


def load_stage_tmx(stage_num):
    """stage{N}.tmx 를 읽어 tile 리스트 딕셔너리를 반환한다."""
    path = os.path.join(MAPS_DIR, f"stage{stage_num}.tmx")
    tmap = pytmx.TiledMap(path)
    return parse_tmap(tmap)


def parse_tmap(tmap):
    tiles = []
    ground_tiles = []
    spike_tiles = []
    exit_tiles = []
    switch_tiles = []
    gate_tiles = []

    for layer in tmap.layers:
        if not isinstance(layer, pytmx.TiledTileLayer):
            continue
        for col, row, gid in layer:
            if not gid:
                continue
            # pytmx가 GID를 내부적으로 재매핑하므로 TSX 속성에서 type을 읽는다
            props = tmap.get_tile_properties_by_gid(gid) or {}
            tile_type = props.get("type")
            if tile_type not in VALID_TILE_TYPES:
                continue
            t = Tile(col, row, tile_type)
            tiles.append(t)
            if tile_type == "ground":
                ground_tiles.append(t)
            elif tile_type == "spike":
                spike_tiles.append(t)
            elif tile_type == "exit":
                exit_tiles.append(t)
            elif tile_type == "switch_a" or tile_type == "switch_b":
                switch_tiles.append(t)
            elif tile_type == "gate":
                gate_tiles.append(t)

    return {
        "tiles":        tiles,
        "ground_tiles": ground_tiles,
        "spike_tiles":  spike_tiles,
        "exit_tiles":   exit_tiles,
        "switch_tiles": switch_tiles,
        "gate_tiles":   gate_tiles,
        "map_width":    tmap.width,
        "map_height":   tmap.height,
    }
