from typing import TypedDict


class UIUpdate(TypedDict):
    time: str
    meters: dict[tuple[str, int], float]
