import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

# Define pastel rainbow color palette
pastel_rainbow_palette = sns.color_palette("pastel", 7)

# Define custom seaborn style
custom_style = {
    "axes.facecolor": "white",
    "axes.edgecolor": "black",
    "axes.labelcolor": "black",
    "xtick.color": "black",
    "ytick.color": "black",
    "grid.color": "#F0F0F0",
    "grid.linestyle": "--",
    "font.family": "sans-serif",
    "font.sans-serif": ["Noto Sans"],
    "axes.linewidth": 0.75, 
    "font.size": 9,
}

sns.set_theme(style="whitegrid", palette=pastel_rainbow_palette, rc=custom_style)


def plot_demand_and_generation(states):
    time = list(map(lambda x: x["time"], states))
    generation = map(lambda x: sum(map(lambda y: y["generation"], x["meters"])), states)
    demand = map(lambda x: sum(map(lambda y: y["consumption"], x["meters"])), states)

    sns.lineplot(x=time, y=list(demand), label="Demand")  # type: ignore

    sns.lineplot(x=time, y=list(generation), label="Generation")  # type: ignore
    plt.title("Generation and Demand Over Time")
    plt.xlabel("Time")
    plt.ylabel("Value")
    plt.legend()

    return plt.gcf()


def plot_trade_comparison(before, after):
    sns.lineplot(x=range(len(before)), y=before, label="Before Trade")  # type: ignore

    sns.lineplot(x=range(len(before)), y=after, label="After Trade")  # type: ignore
    plt.title("Surplus and Transferred Over Time")
    plt.xlabel("Time")
    plt.ylabel("Value")
    plt.legend()

    return plt.gcf()
