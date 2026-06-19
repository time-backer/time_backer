class EnemyState:
    def __init__(self, x, y, direction, alive):
        self.x = x
        self.y = y
        self.direction = direction
        self.alive = alive


class GameState:
    def __init__(self, player_x, player_y, player_vx, player_vy, hp, rewind_count):
        self.player_x = player_x
        self.player_y = player_y
        self.player_vx = player_vx
        self.player_vy = player_vy
        self.hp = hp
        self.rewind_count = rewind_count
        self.enemies = []

    def copy(self):
        new_state = GameState(
            self.player_x,
            self.player_y,
            self.player_vx,
            self.player_vy,
            self.hp,
            self.rewind_count,
        )
        new_enemies = []
        for e in self.enemies:
            new_enemies.append(EnemyState(e.x, e.y, e.direction, e.alive))
        new_state.enemies = new_enemies
        return new_state
