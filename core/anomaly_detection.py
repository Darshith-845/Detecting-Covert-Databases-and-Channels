import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM

def _get_numeric_matrix(df: pd.DataFrame):
    num = df.select_dtypes(include=["int64", "float64"])
    if num.empty:
        # try to get numeric-like columns by coercion
        coerced = df.apply(pd.to_numeric, errors="coerce")
        num = coerced.select_dtypes(include=["int64", "float64"])
    cols = num.columns.tolist()
    if num.empty:
        return np.empty((0,0)), []
    return num.values.astype(float), cols

def _normalize_for_output(arr):
    if arr.size == 0:
        return arr
    a = np.array(arr).astype(float).reshape(-1)
    flipped = a.max() - a
    denom = flipped.max() - flipped.min()
    if denom == 0:
        return np.zeros_like(flipped)
    return (flipped - flipped.min()) / denom

def run_anomaly_models(df: pd.DataFrame, model_choice: str) -> pd.DataFrame:
    X, cols = _get_numeric_matrix(df)
    if X.size == 0:
        raise ValueError("No numeric features for anomaly detection.")

    n = X.shape[0]

    def iforest():
        model = IsolationForest(n_estimators=200, contamination=0.05, random_state=42)
        model.fit(X)
        return -model.score_samples(X)

    def lof():
        model = LocalOutlierFactor(n_neighbors=min(20, max(2, n//10)), contamination=0.05)
        out = model.fit_predict(X)
        return np.where(out == -1, 1.0, 0.0)

    def ocsvm():
        model = OneClassSVM(kernel="rbf", nu=0.05, gamma="scale")
        model.fit(X)
        return -model.decision_function(X)

    results = []
    if model_choice == "IsolationForest":
        results.append(iforest())
    elif model_choice == "LocalOutlierFactor":
        results.append(lof())
    elif model_choice == "OneClassSVM":
        results.append(ocsvm())
    elif model_choice == "All":
        results.extend([iforest(), lof(), ocsvm()])
    else:
        raise ValueError("Unknown model choice")

    normalized = [ _normalize_for_output(np.array(r)) for r in results ]
    final = np.mean(np.vstack(normalized), axis=0) if len(normalized) > 0 else np.zeros(n)

    return pd.DataFrame({"index": df.index, "anomaly_score": final})


# -----------------------
# Heuristic covert DB / channel detection
# -----------------------
def detect_covert_db_and_channel(raw_merged: pd.DataFrame, processed_df: pd.DataFrame, resample_sec: int = 1):
    """
    Heuristic rules:
    - Covert DB: look for database names containing 'covert' OR
      time-bucketed query frequency spikes ( > mean + 3*std ) at DB-level
    - Covert Channel (network): look for periodic fast inter-arrival times (low std of IAT),
      or repeated small packets to same dst with consistent intervals.
    Returns dict with flags, times and reasons.
    """
    report = {
        "covert_db_found": False,
        "covert_db_times": [],
        "covert_db_reasons": [],
        "covert_channel_found": False,
        "covert_channel_times": [],
        "covert_channel_reasons": []
    }

    # 1) Covert DB detection
    # If raw_merged has database / database_name or similar
    db_col_candidates = [c for c in raw_merged.columns if "database" in c or "db" == c]
    if db_col_candidates:
        dbc = db_col_candidates[0]
        # check for explicit name containing 'covert'
        matches = raw_merged[raw_merged[dbc].astype(str).str.contains("covert", case=False, na=False)]
        if not matches.empty:
            report["covert_db_found"] = True
            report["covert_db_times"] = list(pd.to_datetime(matches.iloc[:,0], errors="coerce").dropna().astype(str).head(10))
            report["covert_db_reasons"].append(f"Database name contains 'covert' in column {dbc}")
    # frequency-based detection
    time_candidates = [c for c in raw_merged.columns if "time" in c or "timestamp" in c or "epoch" in c]
    if time_candidates and any(c in processed_df.columns for c in time_candidates):
        tc = [c for c in processed_df.columns if c in time_candidates][0]
        try:
            ts = pd.to_datetime(processed_df[tc], errors="coerce")
            freq = ts.dt.floor(f"{resample_sec}S").value_counts().sort_index()
            if not freq.empty:
                mu = freq.mean(); sigma = freq.std()
                spikes = freq[freq > (mu + 3*sigma)]
                if not spikes.empty:
                    report["covert_db_found"] = True
                    report["covert_db_times"].extend([str(t) for t in spikes.index[:10]])
                    report["covert_db_reasons"].append("High-frequency query spikes detected (freq > mean+3*std)")
        except Exception:
            pass

    # 2) Covert channel — network heuristics
    # Look for numeric epoch times and TCP packets to same dst with repeated small packets
    if any(k in " ".join(raw_merged.columns).lower() for k in ["frame.time_epoch", "ip.src", "ip.dst", "_ws.col.protocol"]):
        # try to extract epoch column
        epoch_cols = [c for c in raw_merged.columns if "frame.time_epoch" in c or "epoch" in c or "time_epoch" in c]
        if epoch_cols:
            ec = epoch_cols[0]
            try:
                raw_merged[ec] = pd.to_numeric(raw_merged[ec], errors="coerce")
                net_df = raw_merged.dropna(subset=[ec]).copy()
                net_df['_dt'] = pd.to_datetime(net_df[ec].values.astype(float), unit='s', errors='coerce')
                # compute IAT grouped by src-dst pairs for TCP/UDP if protocol present
                proto_col = next((c for c in net_df.columns if "_ws.col.protocol" in c or "protocol" in c), None)
                if proto_col:
                    # focus on TCP or UDP
                    candidates = net_df[net_df[proto_col].isin(["TCP","UDP","tcp","udp"])].copy()
                else:
                    candidates = net_df.copy()

                if not candidates.empty:
                    # compute inter-arrival times per src-dst
                    candidates = candidates.sort_values('_dt')
                    candidates['_iat'] = candidates[ec].diff()  # epoch diff in seconds
                    # look for long stretches of small iat with low std
                    window = candidates['_iat'].rolling(window=5, min_periods=3)
                    std_series = window.std().fillna(1e9)
                    low_std_spans = std_series[std_series < 0.01]  # very small jitter -> possibly covert periodic channel
                    if not low_std_spans.empty:
                        report["covert_channel_found"] = True
                        times = candidates.loc[low_std_spans.index, '_dt'].dropna().astype(str).unique().tolist()[:10]
                        report["covert_channel_times"].extend(times)
                        report["covert_channel_reasons"].append("Low-variance inter-arrival times detected (periodic small IATs)")

                    # repeated small packets to same dst
                    if 'frame.len' in candidates.columns:
                        small = candidates[candidates['frame.len'].astype(float) <= 200]  # small packets threshold
                        repeated_dst = small.groupby(['ip.dst']).size().sort_values(ascending=False)
                        if not repeated_dst.empty and repeated_dst.iloc[0] > 20:
                            report["covert_channel_found"] = True
                            report["covert_channel_reasons"].append(f"Many small packets to same dest ({repeated_dst.index[0]})")
            except Exception:
                pass

    return report
