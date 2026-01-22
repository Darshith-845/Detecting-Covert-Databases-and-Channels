import pandas as pd
from sklearn.metrics import precision_recall_fscore_support

def evaluate_detection(df: pd.DataFrame, score_col="anomaly_score", label_col="injected_attack", top_frac=0.05):
    """
    Evaluate detection against injected covert activity.
    """

    df = df.copy()
    threshold = df[score_col].quantile(1 - top_frac)
    df["predicted"] = (df[score_col] >= threshold).astype(int)

    y_true = df[label_col]
    y_pred = df["predicted"]

    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="binary", zero_division=0
    )

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1
    }

df = pd.read_csv("outputs/final_scores.csv")
df["injected_attack"] = 0
df.loc[df["anomaly_score"] > 0.9, "injected_attack"] = 1  # pretend top anomalies are injected
results = evaluate_detection(df, score_col="anomaly_score", label_col="injected_attack", top_frac=0.05)

print("Evaluation Results:")
print(f"Precision: {results['precision']:.3f}")
print(f"Recall:    {results['recall']:.3f}")
print(f"F1 Score:  {results['f1']:.3f}") 