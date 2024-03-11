"""This module contains functions for dumping data to files using different formats."""
import os
import pickle
import json
from typing import Any, BinaryIO, Callable, TextIO


def dump_pkl(data:Any, f: BinaryIO) -> None:
    """Dump data to a file using pickle.

    Args:
        data (Any): The data to be dumped.
        f (BinaryIO): The file to dump the data to.
    """
    pickle.dump(data, f)


def dump_json(data: Any, f: TextIO) -> None:
    """Dump data to a file using json.

    Args:
        data (Any): The data to be dumped.
        f (TextIO): The file to dump the data to.
    """
    json.dump(data, f, indent=2)


def mk_dumper() -> Callable[[Any, str], None]:
    dumpers = {
        "pkl": {"module": dump_pkl, "binary": True},
        "json": {"module": dump_json, "binary": False},
    }

    def dump(data: Any, file_path: str) -> None:
        """Dump data to a file.

        Args:
            data (Any): The data to be dumped.
            file_path (str): The path to the file to dump the data to.
        """
        extension = os.path.splitext(file_path)[1][1:]  # Get rid of the dot
        if extension not in dumpers:
            return

        selected_dumper = dumpers[extension]
        mode = "w" + "b" * selected_dumper["binary"]
        with open(file_path, mode) as f:
            dumper = selected_dumper["module"]
            dumper(data, f)

    return dump
