"""This module contains utility functions for working with datetime."""
from typing import Generator, Any
import pandas as pd
import datetime as dt

def date_range(
    start: dt.datetime, end: dt.datetime, delta: dt.timedelta
) -> Generator[pd.Timestamp, Any, None]:
    """Generate a sequence of Pandas Timestamp objects within a given range at specified intervals.

    Args:
        start (datetime.datetime): The start datetime.
        end (datetime.datetime): The end datetime.
        delta (datetime.timedelta): The interval between datetime objects.

    Yields:
        pd.Timestamp: The generated Timestamp objects.
    """
    yield from pd.date_range(start, end, freq=delta)


def sub_time(t1: pd.Timestamp, t2: pd.Timestamp) -> dt.timedelta:
    """Calculate the time difference between two Pandas Timestamp objects.

    Args:
        t1 (pd.Timestamp): The first timestamp.
        t2 (pd.Timestamp): The second timestamp.

    Returns:
        datetime.timedelta: The time difference between t1 and t2.
    """
    a: dt.time = t1.time()
    b: dt.time = t2.time()
    return dt.timedelta(
        hours=a.hour - b.hour,
        minutes=a.minute - b.minute,
        seconds=a.second - b.second,
    )
