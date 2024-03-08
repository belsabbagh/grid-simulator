import os

from matplotlib import pyplot as plt
from src.analytics import plot_demand_and_generation
import pickle


def load_latest_run(runs_folder):
    runs = [os.path.join(runs_folder, run) for run in os.listdir(runs_folder)]
    latest_run = max(runs, key=os.path.getctime)
    with open(latest_run, "rb") as f:
        return latest_run, pickle.load(f)

if __name__ == "__main__":
    runs_folder = "out/runs"
    run_path, run = load_latest_run(runs_folder)
    plot = plot_demand_and_generation(run["states"])
    plot_name = os.path.splitext(os.path.basename(run_path))
    plot.savefig(f"out/plots/{plot_name[0]}.svg", dpi=300, bbox_inches="tight")
