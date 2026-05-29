from typing import Optional
from core.game_state import GameState


class TimeStack:
    def __init__(self, max_size: int = 180) -> None:
        self._history: list[GameState] = []
        self._max_size = max_size  # 최대 180프레임 (3초)

    def push(self, state: GameState) -> None:
        self._history.append(state.copy())
        # 최대 크기 초과 시 가장 오래된 것 제거 (FIFO for oldest)
        if len(self._history) > self._max_size:
            self._history.pop(0)

    def pop(self) -> Optional[GameState]:
        if self._history:
            return self._history.pop()
        return None

    def peek(self) -> Optional[GameState]:
        if self._history:
            return self._history[-1]
        return None

    def pop_all(self) -> Optional[GameState]:
        if self._history:
            oldest = self._history[0]
            self._history.clear()
            return oldest
        return None

    def is_empty(self) -> bool:
        return len(self._history) == 0

    def clear(self) -> None:
        self._history.clear()

    def __len__(self) -> int:
        return len(self._history)
