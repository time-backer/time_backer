from dataclasses import dataclass, field
from typing import List


@dataclass
class EnemyState:
    x: float
    y: float
    direction: int
    alive: bool


@dataclass
class GameState:
    player_x: float
    player_y: float
    player_vx: float
    player_vy: float
    hp: int
    rewind_count: int
    enemies: List[EnemyState] = field(default_factory=list)

    def copy(self) -> "GameState":
        return GameState(
            player_x=self.player_x,
            player_y=self.player_y,
            player_vx=self.player_vx,
            player_vy=self.player_vy,
            hp=self.hp,
            rewind_count=self.rewind_count,
            enemies=[EnemyState(e.x, e.y, e.direction, e.alive) for e in self.enemies],
        )
