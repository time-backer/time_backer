from world.stage import Stage
from settings import TILE_SIZE


class BossStage(Stage):
    def __init__(self):
        super().__init__(stage_num=4)
        self.switch_tiles = []

    def get_player_start(self):
        return (2 * TILE_SIZE, (self.map_h - 2) * TILE_SIZE - TILE_SIZE)

    def get_boss_position(self):
        return (12 * TILE_SIZE - 36, 6 * TILE_SIZE)

    def get_enemy_spawns(self):
        return []

    def is_clear(self, player_rect):
        return False

    def draw(self, surface, camera_x=0, camera_y=0):
        surface.fill((10, 10, 20))
        for tile in self.tiles:
            tile.draw(surface, camera_x, camera_y)
