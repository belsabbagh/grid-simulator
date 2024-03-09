from typing import Generator, List, Optional, Tuple, TypeVar, Callable

T = TypeVar("T", bound=dict)


def make_buffer() -> Tuple[
    Callable[[T], None],
    Callable[[], Optional[T]],
    Callable[[], Generator[T, None, None]],
    Callable[[], None],
]:
    buffer: List[T] = []

    def append_state(state: T) -> None:
        buffer.append(state)

    def fetch_next_state() -> Optional[T]:
        if not buffer:
            return None
        state = buffer.pop(0)
        # This assumes state has a key "remaining"
        state["remaining"] = len(buffer)
        return state

    def immutable_iterator() -> Generator[T, None, None]:
        for state in buffer:
            yield state.copy()

    def clear_state() -> None:
        buffer.clear()

    return append_state, fetch_next_state, immutable_iterator, clear_state
