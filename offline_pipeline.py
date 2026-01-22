import pandas as pd
import numpy as np

from core.csv_loader import clean_dataframe
from core.feature_builder import build_time_features
from core.anomaly_detection import run_anomaly_models
import re

# ------------------------
# 1. LOAD DATASETS
# ------------------------
df_net = clean_dataframe(pd.read_csv("data/network_logs.csv"))
df_db  = clean_dataframe(pd.read_csv("data/db_logs.csv"))
df_os  = clean_dataframe(pd.read_csv("data/os_logs.csv"))

# ------------------------
# 2. COERCE TIMESTAMPS & CLEAN
# ------------------------
def parse_timestamp(df, time_col, tz="Asia/Kolkata"):
    if time_col not in df.columns:
        raise ValueError(f"Missing time column: {time_col}")
    df = df.copy()
    
    # Remove 'IST' if present
    df[time_col] = pd.to_datetime(
        df[time_col].astype(str).str.replace("IST","", regex=False),
        errors="coerce"
    )
    
    # Drop invalid dates
    df = df.dropna(subset=[time_col])

    # Check if already tz-aware
    if df[time_col].dt.tz is None:
        df[time_col] = df[time_col].dt.tz_localize(tz, ambiguous='NaT', nonexistent='shift_forward')
    else:
        df[time_col] = df[time_col].dt.tz_convert(tz)
    
    return df

df_os  = parse_timestamp(df_os, "timestamp")
df_db  = parse_timestamp(df_db, "log_time")
df_net = df_net.copy()  # Network logs already numeric

# ------------------------
# 3. COERTIVE INJECTIONS
# ------------------------
def extract_user(msg):
    m = re.search(r'user\s+([a-zA-Z0-9_-]+)', str(msg))
    return m.group(1) if m else None

df_os["user"] = df_os["message"].apply(extract_user)

from core.offline_injections import inject_covert_network, inject_covert_db, inject_covert_os

df_net = inject_covert_network(df_net)
df_db  = inject_covert_db(df_db)
df_os  = inject_covert_os(df_os)

# ------------------------
# 4. FEATURE PROJECTION
# ------------------------
net_feat = build_time_features(df_net, "frame.time_epoch", source="network")
db_feat  = build_time_features(df_db, "log_time", source="database")
os_feat  = build_time_features(df_os, "timestamp", source="os")

# Fix bucket floor deprecation warning
for df_feat in [net_feat, db_feat, os_feat]:
    if "bucket" in df_feat.columns and pd.api.types.is_datetime64_any_dtype(df_feat["bucket"]):
        df_feat["bucket"] = df_feat["bucket"].dt.floor("s")

# ------------------------
# 5. UNIFIED FEATURE SPACE
# ------------------------
features = pd.concat([net_feat, db_feat, os_feat], ignore_index=True)

# ------------------------
# 6. HANDLE NaNs
# ------------------------
numeric_features = features.select_dtypes(include=[np.number]).fillna(0)

# ------------------------
# 7. ANOMALY DETECTION
# ------------------------
scores = run_anomaly_models(numeric_features, "All")
features["anomaly_score"] = scores["anomaly_score"]


# ------------------------
# 8. SAVE RESULTS
# ------------------------
features.to_csv("outputs/final_scores.csv", index=False)

print("Pipeline completed successfully! Results saved to outputs/final_scores.csv")
