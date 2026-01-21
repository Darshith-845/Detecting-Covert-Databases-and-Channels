import os
import uuid
import matplotlib.pyplot as plt
import seaborn as sns

PLOT_DIR = "plots"
os.makedirs(PLOT_DIR, exist_ok=True)

def set_dark_theme():
    plt.style.use("dark_background")
    sns.set_theme(style="darkgrid")

def plot_scores(scores_df, model_choice: str) -> str:
    if scores_df is None or scores_df.empty:
        raise ValueError("Empty scores_df provided to plot_scores")

    x = scores_df["index"].to_numpy()
    y = scores_df["anomaly_score"].to_numpy()

    fig, ax = plt.subplots(figsize=(12,4))
    ax.plot(x, y, linewidth=1.6, alpha=0.9)
    ax.fill_between(x, y, alpha=0.15)
    ax.set_title(f"Anomaly Scores — {model_choice}")
    ax.set_xlabel("Index / Time")   
    ax.set_ylabel("Anomaly Score (0-1)")
    ax.grid(True, alpha=0.25)
    fname = os.path.join(PLOT_DIR, f"anomaly_{model_choice}_{uuid.uuid4().hex}.png")
    fig.savefig(fname, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return fname
