import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder


# -------------------------------------------------------------------
# 🔥 100-YEARS-EXPERIENCE SAFE TIMESTAMP PARSER
# -------------------------------------------------------------------
def parse_timestamp(df):
    """
    Tries extremely hard to find and parse any timestamp-like column.
    Returns updated df + detected column name (or None).
    """
    ts_candidates = [
        "timestamp", "time", "ts", "created_at", "log_time", "datetime"
    ]

    # find matching columns
    detected = None
    for col in df.columns:
        if col.lower() in ts_candidates or "time" in col.lower():
            detected = col
            break

    if detected is None:
        return df, None   # No timestamp found

    # multiple parse strategies
    for fmt in [None, "%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S", "%m/%d/%Y %H:%M"]:
        try:
            df[detected] = pd.to_datetime(df[detected], errors="coerce", format=fmt)
            if df[detected].notna().sum() > 0:  # at least some valid timestamps
                df = df.sort_values(by=detected)
                df = df.reset_index(drop=True)
                return df, detected
        except:
            pass

    # If everything fails: remove timestamp column
    df = df.drop(columns=[detected])
    return df, None


# -------------------------------------------------------------------
# 🔥 UNIVERSAL CLEANER / NORMALIZER
# -------------------------------------------------------------------
def normalize_numeric(df):
    """
    Converts numeric-looking columns to float, cleans text noise,
    fills NaNs intelligently.
    """
    for col in df.columns:
        try:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", "")         # remove comma thousands separator
                .str.replace("ms", "")        # remove common units
                .str.replace("KB", "")
                .str.replace("MB", "")
            )
        except:
            pass

    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col], errors="ignore")
        except:
            pass

    # replace all object values "none" / "null" with real NaN
    df = df.replace(["None", "none", "NULL", "null", ""], np.nan)

    # forward fill + backward fill helps log sequences
    df = df.fillna(method="ffill").fillna(method="bfill")

    return df


# -------------------------------------------------------------------
# 🔥 CATEGORICAL ENCODER (SAFE FOR LOGS)
# -------------------------------------------------------------------
def encode_categoricals(df):
    """
    Label-encodes small categorical columns & leaves large text columns untouched.
    """
    for col in df.columns:
        if df[col].dtype == "object" and df[col].nunique() < 50:
            try:
                df[col] = LabelEncoder().fit_transform(df[col].astype(str))
            except:
                pass

    return df


# -------------------------------------------------------------------
# 🔥 NETWORK LOG PREPROCESSOR
# -------------------------------------------------------------------
def preprocess_network(df):
    """
    Handles typical fields:
    - src_ip, dst_ip
    - src_port, dst_port
    - protocol
    - packet_size / bytes / duration
    """
    ip_cols = ["src_ip", "dst_ip"]
    port_cols = ["src_port", "dst_port"]

    # Encode IPs as integers (hash)
    for col in ip_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).apply(lambda x: abs(hash(x)) % (10**9))

    # Convert ports to numeric
    for col in port_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Normalize packet/byte fields
    for col in df.columns:
        if "byte" in col or "size" in col or "len" in col:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(df[col].median())

    return df


# -------------------------------------------------------------------
# 🔥 DATABASE LOG PREPROCESSOR
# -------------------------------------------------------------------
def preprocess_db(df):
    """
    Cleans DB query logs:
    - query_time / rows_examined / bytes_sent
    - user / db / op_type
    """
    numeric_candidate = ["query_time", "rows_examined", "bytes_sent"]

    for col in numeric_candidate:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # encode db user & operations
    for col in ["user", "db", "operation", "command"]:
        if col in df.columns:
            df[col] = LabelEncoder().fit_transform(df[col].astype(str))

    return df


# -------------------------------------------------------------------
# 🔥 OS LOG PREPROCESSOR
# -------------------------------------------------------------------
def preprocess_os(df):
    """
    Handles OS/system logs:
    - event_id / process / pid / system_call / severity
    """
    # convert PIDs
    if "pid" in df.columns:
        df["pid"] = pd.to_numeric(df["pid"], errors="coerce").fillna(0)

    # encode small categorical fields
    for col in ["process", "event", "severity", "system_call", "user"]:
        if col in df.columns:
            try:
                df[col] = LabelEncoder().fit_transform(df[col].astype(str))
            except:
                pass

    return df


# -------------------------------------------------------------------
# 🔥 SCALER
# -------------------------------------------------------------------
def scale_numeric(df):
    """
    Standardizes only real numeric columns (not timestamps or categoricals).
    """
    numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()

    if len(numeric_cols) == 0:
        return df

    scaler = StandardScaler()
    try:
        df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
    except:
        pass

    return df


# -------------------------------------------------------------------
# 🔥 MAIN PREPROCESSOR
# -------------------------------------------------------------------
def preprocess_file(df: pd.DataFrame, dataset_type: str) -> pd.DataFrame:
    """
    Master preprocessing pipeline used by Streamlit app.
    Guarantees:
    - dataframe is cleaned
    - timestamp extracted & sorted
    - numerics normalized
    - categoricals encoded
    - dataset-specific preprocessing applied
    - final scaling
    """

    # universal cleaning
    df = df.copy()
    df = normalize_numeric(df)

    # parse timestamp
    df, timestamp_col = parse_timestamp(df)

    # dataset-specific pipelines
    if dataset_type == "network":
        df = preprocess_network(df)

    elif dataset_type == "db":
        df = preprocess_db(df)

    elif dataset_type == "os":
        df = preprocess_os(df)

    # encode categoricals
    df = encode_categoricals(df)

    # final numeric scaling
    df = scale_numeric(df)

    # ensure no NaNs remain
    df = df.replace([np.inf, -np.inf], np.nan).fillna(0)

    # if timestamp exists, move it to front (helps timeline plots)
    if timestamp_col:
        cols = [timestamp_col] + [c for c in df.columns if c != timestamp_col]
        df = df[cols]

    return df
