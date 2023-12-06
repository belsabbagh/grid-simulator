from typing import TypedDict


class UIUpdate(TypedDict):
    type: str
    time: str
    meters: dict[tuple[str, int], float]
