import os

from matplotlib import pyplot as plt
from src import analytics
import pickle


def load_latest_run(runs_folder):
    runs = [os.path.join(runs_folder, run) for run in os.listdir(runs_folder)]
    latest_run = max(runs, key=os.path.getctime)
    with open(latest_run, "rb") as f:
        return latest_run, pickle.load(f)

if __name__ == "__main__":
    runs_folder = "out/runs"
    run_path, run = load_latest_run(runs_folder)
    plot_name = os.path.splitext(os.path.basename(run_path))
    plot_dir = f"out/plots/{plot_name[0]}"
    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)
    # plot = analytics.plot_demand_and_generation(run["states"])
    # plot_name = os.path.splitext(os.path.basename(run_path))
    # plot.savefig(f"out/plots/{plot_name[0]}.svg", dpi=300, bbox_inches="tight")

    trade_comparison_dir = os.path.join(plot_dir, "trade_comparison")
    if not os.path.exists(trade_comparison_dir):
        os.makedirs(trade_comparison_dir)
    for i in range(len(run["states"][0]["meters"])):
        before = []
        after = []
        for state in run["states"]:
            b, a = state["meters"][i]["surplus"], state["meters"][i]["surplus"] + state["meters"][i]["sent"]
            if b == a:
                continue
            before.append(b)
            after.append(a)
        plot = analytics.plot_trade_comparison(before, after)
        plot.savefig(f"{trade_comparison_dir}/{i}.svg", dpi=300, bbox_inches="tight")
        plt.clf()
    print(f"Waste reduced by {((1 - waste_after/waste_before) * 100):.3f}%")
    