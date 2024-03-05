import json
import pickle

def pkl2json(pkl_file: str, json_file: str) -> None:
    with open(pkl_file, "rb") as f:
        data = pickle.load(f)
    with open(json_file, "w") as g:
        json.dump(data, g, default=str, indent=2)


if __name__ == "__main__":
  pkl2json("out/server_dump.pkl", "out/server_dump.json")
