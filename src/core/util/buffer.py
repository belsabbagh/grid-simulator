"""This module contains utility functions for creating a buffer."""
from typing import Generator, List, Optional, Tuple, TypeVar, Callable

T = TypeVar("T", bound=dict)
ImmutableIterator = Generator[T, None, None]

BufferAppendState = Callable[[T], None]
BufferFetchNextState = Callable[[], Optional[T]]
BufferImmutableIterator = Callable[[], ImmutableIterator[T]]
BufferClear = Callable[[], None]


def make_buffer() -> Tuple[
    BufferAppendState[T],
    BufferFetchNextState[T],
    BufferImmutableIterator[T],
    BufferClear,
]:
    """Create a buffer that can be used to store and retrieve states.

    Returns:
        Tuple[ BufferAppendState[T], BufferFetchNextState[T], BufferImmutableIterator[T], BufferClear, ]: A tuple containing the functions to append a state, fetch the next state, create an immutable iterator, and clear the buffer.

    """
    buffer: List[T] = []

    def append_state(state: T) -> None:
        """Append a state to the buffer.

        Args:
            state (T): The state to append to the buffer.
        """
        buffer.append(state)

    def fetch_next_state() -> Optional[T]:
        """Fetch the next state in the buffer.

        Returns:
            Optional[T]: The next state in the buffer or None if the buffer is empty.
        """
        if not buffer:
            return None
        state = buffer.pop(0)
        # This assumes state has a key "remaining"
        state["remaining"] = len(buffer)
        return state

    def immutable_iterator() -> ImmutableIterator[T]:
        """A generator that yields copies of the states in the buffer.

        Yields:
            ImmutableIterator[T]: A copy of the state in the buffer.
        """
        for state in buffer:
            yield state.copy()

    def clear_state() -> None:
        """Clear the buffer."""
        buffer.clear()

    return append_state, fetch_next_state, immutable_iterator, clear_state
