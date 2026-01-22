import pandas as pd

def summarize_dataset(df, time_col, feature_cols, label_col="injected_attack"):
    total_rows = len(df)

    time_span = None
    if time_col in df.columns:
        time_span = (
            df[time_col].min(),
            df[time_col].max()
        )

    missing_rate = df[feature_cols].isna().mean().mean()

    injection_ratio = (
        df[label_col].mean() if label_col in df.columns else 0.0
    )

    return {
        "records": total_rows,
        "time_span": time_span,
        "num_features": len(feature_cols),
        "missing_rate": missing_rate,
        "injection_ratio": injection_ratio
    }


# ---- Load processed data ----
features = pd.read_csv("outputs/final_scores.csv")

summary = []

for stream in ["network", "database", "os"]:
    df_s = features[features["source"] == stream]

    numeric_cols = df_s.select_dtypes("number").columns.tolist()
    numeric_cols.remove("anomaly_score")

    stats = summarize_dataset(
        df_s,
        time_col="bucket",
        feature_cols=numeric_cols
    )

    stats["stream"] = stream.capitalize()
    summary.append(stats)

summary_df = pd.DataFrame(summary)
summary_df.to_csv("outputs/dataset_summary.csv", index=False)

print(summary_df)
