import os
import pickle


def load_latest_run(runs_folder):
    runs = [os.path.join(runs_folder, run) for run in os.listdir(runs_folder)]
    latest_run = max(runs, key=os.path.getctime)
    with open(latest_run, "rb") as f:
        return latest_run, pickle.load(f)

if __name__ == "__main__":
    runs_folder = "out/runs"
    run_path, run = load_latest_run(runs_folder)

    waste_reduction = 0
    for i in range(len(run["states"][0]["meters"])):
        bef, aft = 0, 0
        for state in run["states"]:
            b, a = state["meters"][i]["surplus"], state["meters"][i]["surplus"] + state["meters"][i]["sent"]
            bef += b
            aft += a
        waste_reduction = max(waste_reduction, (1 - aft/bef) * 100)

    print(waste_reduction)