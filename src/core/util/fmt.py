"""This module contains utility functions for formatting data."""
from typing import Any, Dict, Tuple


GRID_STATE_PARAMS = [
    "Grid load (GWh)",
    "Grid temperature (C)",
    "Voltage (V)",
    "Global intensity (A)",
]
def fmt_grid_state(grid_state: list[float]) -> dict[str, float]:
    return {key: value for key, value in zip(GRID_STATE_PARAMS, grid_state)}

def make_msg_body(addr: Tuple[str, int], _type: str, **kwargs: Any) -> Dict[str, Any]:
    """Create a message body with specified type and additional keyword arguments."""
    return {"from": addr, "type": _type, **kwargs}
