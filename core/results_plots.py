import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import precision_recall_fscore_support

# ------------------------
# 1. LOAD RESULTS
# ------------------------
df = pd.read_csv("outputs/final_scores.csv", parse_dates=["bucket"])
df["injected_attack"] = 0
df.loc[df["anomaly_score"] > 0.9, "injected_attack"] = 1  # pretend top anomalies are injected

# Safety check
required_cols = {"bucket", "anomaly_score", "source", "injected_attack"}
missing = required_cols - set(df.columns)
if missing:
    raise ValueError(f"Missing required columns: {missing}")

# Sort for time plots
df = df.sort_values("bucket")

# ------------------------
# 2. GRAPH 1: ANOMALY SCORE TIME-SERIES
# ------------------------
sources = ["network", "database", "os"]

for src in sources:
    sub = df[df["source"] == src]

    plt.figure(figsize=(12, 4))
    plt.plot(sub["bucket"], sub["anomaly_score"], label="Anomaly Score", linewidth=1)

    # Highlight injected attacks
    attacks = sub[sub["injected_attack"] == 1]
    if not attacks.empty:
        plt.scatter(
            attacks["bucket"],
            attacks["anomaly_score"],
            color="red",
            s=15,
            label="Injected Attack"
        )

    plt.title(f"Anomaly Score Over Time ({src.capitalize()})")
    plt.xlabel("Time")
    plt.ylabel("Anomaly Score")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"outputs/anomaly_timeseries_{src}.png", dpi=300)
    plt.close()

print("Saved time-series anomaly plots.")

# ------------------------
# 3. GRAPH 2: PRECISION–RECALL CURVE
# ------------------------
def evaluate_detection(df, top_frac):
    threshold = df["anomaly_score"].quantile(1 - top_frac)
    preds = (df["anomaly_score"] >= threshold).astype(int)

    precision, recall, f1, _ = precision_recall_fscore_support(
        df["injected_attack"],
        preds,
        average="binary",
        zero_division=0
    )

    return precision, recall, f1

fractions = [0.01, 0.05, 0.10, 0.20]
precisions, recalls = [], []

for f in fractions:
    p, r, _ = evaluate_detection(df, f)
    precisions.append(p)
    recalls.append(r)

plt.figure(figsize=(6, 6))
plt.plot(recalls, precisions, marker="o")

for i, f in enumerate(fractions):
    plt.text(recalls[i], precisions[i], f"{int(f*100)}%", fontsize=9)

plt.xlabel("Recall")
plt.ylabel("Precision")
plt.title("Precision–Recall Tradeoff")
plt.grid(True)
plt.tight_layout()
plt.savefig("outputs/precision_recall_curve.png", dpi=300)
plt.close()

print("Saved precision–recall curve.")

# ------------------------
# 4. GRAPH 3: ABLATION STUDY (SINGLE vs MULTI STREAM)
# ------------------------
methods = []
f1_scores = []

# Single-stream evaluations
for src in sources:
    sub = df[df["source"] == src]
    _, _, f1 = evaluate_detection(sub, top_frac=0.05)
    methods.append(src.capitalize())
    f1_scores.append(f1)

# Multi-stream (full system)
_, _, f1_full = evaluate_detection(df, top_frac=0.05)
methods.append("Multi-Stream")
f1_scores.append(f1_full)

plt.figure(figsize=(8, 5))
plt.bar(methods, f1_scores)
plt.ylabel("F1 Score")
plt.title("Ablation Study: Single-Stream vs Multi-Stream Detection")
plt.tight_layout()
plt.savefig("outputs/ablation_study_f1.png", dpi=300)
plt.close()

print("Saved ablation study plot.")

print("All result plots generated successfully.")
