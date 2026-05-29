from typing import Optional
from core.game_state import GameState


class TimeStack:
    def __init__(self) -> None:
        self._history: list[GameState] = []

    def push(self, state: GameState) -> None:
        self._history.append(state.copy())

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

    def rewind_by_frames(self, frames: int) -> Optional[GameState]:
        """
        특정 프레임 수만큼 과거로 되돌림
        frames: 되돌릴 프레임 수 (예: 180 = 3초 전)
        """
        if len(self._history) >= frames:
            # frames만큼 pop하고 마지막 상태 반환
            for _ in range(frames - 1):
                self._history.pop()
            return self._history.pop() if self._history else None
        elif self._history:
            # 저장된 상태가 frames보다 적으면 가장 오래된 상태로
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
