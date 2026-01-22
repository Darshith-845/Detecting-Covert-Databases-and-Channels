import pandas as pd
import numpy as np

def build_time_features(
    df: pd.DataFrame,
    time_col: str,
    bucket_sec: int = 1,
    source: str = "unknown"
) -> pd.DataFrame:
    """
    Project heterogeneous logs into a common time-indexed feature space.

    Output columns:
    - bucket (time)
    - count (events per bucket)
    - mean_iat
    - std_iat
    - source
    """

    df = df.copy()
    df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=[time_col])

    if df.empty:
        return pd.DataFrame(columns=["bucket", "count", "mean_iat", "std_iat", "source"])

    df = df.sort_values(time_col)
    df["iat"] = df[time_col].diff().dt.total_seconds()

    df["bucket"] = df[time_col].dt.floor(f"{bucket_sec}S")

    agg = df.groupby("bucket").agg(
        count=("bucket", "size"),
        mean_iat=("iat", "mean"),
        std_iat=("iat", "std")
    ).reset_index()

    agg["source"] = source
    return agg
