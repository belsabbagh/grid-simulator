import os
import pickle
import json


def dump_pkl(data, f):
    pickle.dump(data, f)


def dump_json(data, f):
    json.dump(data, f, indent=2)


def mk_dumper():
    dumpers = {
        "pkl": {"module": dump_pkl, "binary": True},
        "json": {"module": dump_json, "binary": False},
    }

    def dump(data, file_path):
        extension = os.path.splitext(file_path)[1][1:]  # Get rid of the dot
        if extension not in dumpers:
            return

        selected_dumper = dumpers[extension]
        mode = "w" + "b" * selected_dumper["binary"]
        with open(file_path, mode) as f:
            dumper = selected_dumper["module"]
            dumper(data, f)

    return dump
