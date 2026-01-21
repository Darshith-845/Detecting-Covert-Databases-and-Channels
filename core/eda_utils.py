# core/eda_utils.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional

sns.set_style("darkgrid")


def detect_file_type(df: pd.DataFrame) -> str:
    """
    Best-effort file type detection. Returns 'network', 'db', 'os' or 'unknown'.
    """
    cols = " ".join([c.lower() for c in df.columns])
    if any(k in cols for k in ["frame.time_epoch", "ip.src", "_ws.col.protocol", "tcp.srcport", "udp.srcport", "frame.len"]):
        return "network"
    if any(k in cols for k in ["log_time", "user_name", "database", "command_tag", "session_start_time"]):
        return "db"
    if any(k in cols for k in ["timestamp", "kernel", "cron", "process", "message"]):
        return "os"
    return "unknown"


# ---------------------------
# Robust datetime extraction
# ---------------------------
def _get_datetime_series(df: pd.DataFrame) -> (Optional[pd.Series], Optional[str]):
    """
    Try common timestamp-like columns:
    - numeric epoch (frame.time_epoch)
    - ISO / human-readable timestamps
    Returns (datetime_series, column_name) or (None, None).
    """
    candidates = [c for c in df.columns if "time" in c.lower() or "timestamp" in c.lower() or "epoch" in c.lower()]
    for c in candidates:
        s = df[c]
        # If numeric-like -> treat as epoch seconds
        if pd.api.types.is_numeric_dtype(s) or s.dropna().map(lambda x: isinstance(x, (int, float))).all():
            try:
                dt = pd.to_datetime(s.astype(float).to_numpy(), unit="s", errors="coerce")
                if dt.notna().sum() > 0:
                    return dt, c
            except Exception:
                pass
        # otherwise try normal parsing
        try:
            dt = pd.to_datetime(s, errors="coerce", utc=False)
            if dt.notna().sum() > 0:
                return dt, c
        except Exception:
            continue
    return None, None


# ---------------------------
# Safe plotting helpers
# ---------------------------
def _plot_timeseries(dt_index: pd.DatetimeIndex, counts: pd.Series, title: str, width=900, height=250):
    """
    Use matplotlib but always pass numpy arrays to avoid pandas indexing pitfalls.
    """
    fig, ax = plt.subplots(figsize=(12, 3))
    ax.plot(dt_index.to_numpy(), counts.to_numpy(), linewidth=1.6)
    ax.fill_between(dt_index.to_numpy(), counts.to_numpy(), alpha=0.12)
    ax.set_title(title)
    ax.set_ylabel("events")
    ax.grid(alpha=0.25)
    st.pyplot(fig)


# ---------------------------
# Main per-file EDA function
# ---------------------------
def run_full_eda(df: pd.DataFrame, resample_sec: int = 1):
    """
    Runs a compact but informative EDA pipeline and renders output to Streamlit.
    - prints head & shape
    - shows column types & missing
    - numeric distributions
    - time-series (if timestamps present)
    - protocol/ports summary for network logs
    - correlation heatmap for numeric features
    """
    st.subheader("Quick preview")
    st.write("Rows:", df.shape[0], "Columns:", df.shape[1])
    st.dataframe(df.head(8), use_container_width=True)

    st.write("**Column dtypes**")
    st.dataframe(df.dtypes, use_container_width=True)

    st.write("**Missing values (per column)**")
    st.dataframe(df.isna().sum(), use_container_width=True)

    # Numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # Correlation heatmap
    if len(numeric_cols) >= 2:
        st.subheader("Correlation heatmap")
        corr = df[numeric_cols].corr()
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.heatmap(corr, cmap="coolwarm", ax=ax, vmin=-1, vmax=1)
        st.pyplot(fig)

    # Distributions (top numeric columns)
    if numeric_cols:
        st.subheader("Numeric distributions")
        show_count = min(len(numeric_cols), 6)
        for col in numeric_cols[:show_count]:
            fig, ax = plt.subplots(figsize=(6, 2))
            ax.hist(df[col].dropna(), bins=30)
            ax.set_title(col)
            st.pyplot(fig)

    # Categorical top-k
    if len(cat_cols) > 0:
        st.subheader("Top categorical values (sample)")
        for col in cat_cols[:6]:
            top = df[col].value_counts().head(10)
            st.write(f"**{col}** — top {len(top)}")
            st.bar_chart(top)

    # Time series: aggregated events over resample_sec
    dt_series, used_col = _get_datetime_series(df)
    if dt_series is not None:
        st.subheader("Events over time")
        try:
            idx = pd.DatetimeIndex(dt_series)
            s = pd.Series(1, index=idx)
            series = s.resample(f"{resample_sec}S").sum()
            _plot_timeseries(series.index, series, f"Events over time (resampled every {resample_sec}s)")
        except Exception as e:
            st.warning("Time-series plotting failed.")
            st.write(e)
    else:
        st.info("No usable timestamp column found for time-series.")

    # Network-specific EDA (protocols / ports / packet sizes)
    detected = detect_file_type(df)
    if detected == "network":
        st.subheader("Network-specific summary")

        # protocol distribution
        proto_col = next((c for c in df.columns if "_ws.col.protocol" in c or "protocol" == c or "protocol" in c.lower()), None)
        if proto_col:
            st.write("Protocol distribution")
            st.bar_chart(df[proto_col].value_counts().head(30))

        # port summary
        port_cols = [c for c in df.columns if "port" in c.lower()]
        if port_cols:
            st.write("Top ports across available port columns")
            combined = pd.Series(dtype=float)
            for p in port_cols:
                try:
                    vc = pd.to_numeric(df[p], errors="coerce").value_counts()
                    combined = combined.add(vc, fill_value=0)
                except Exception:
                    continue
            if not combined.empty:
                st.bar_chart(combined.sort_values(ascending=False).head(30))

        # frame.len / size histogram
        size_col = next((c for c in df.columns if "frame.len" in c or "len" == c or "size" in c or "bytes" in c), None)
        if size_col:
            st.write("Packet/frame size distribution")
            fig, ax = plt.subplots(figsize=(8, 3))
            ax.hist(pd.to_numeric(df[size_col], errors="coerce").dropna(), bins=50)
            st.pyplot(fig)

    # final note
    st.write("EDA completed.")
