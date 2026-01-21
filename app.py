# app.py
import streamlit as st
import io
import pandas as pd
import traceback

# Use your existing modules. These must exist in core/
from core.csv_loader import load_csv_auto, clean_dataframe
from core.preprocessing import preprocess_file            # your preprocessing pipeline
from core.anomaly_detection import run_anomaly_models, detect_covert_db_and_channel
from core.plot_utils import set_dark_theme, plot_scores
from core.eda_utils import run_full_eda                  # we'll replace eda_utils with the provided file

# ----------------------
# Page config + theme
# ----------------------
st.set_page_config(page_title="Covert Channel Detection", layout="wide")
set_dark_theme()  # apply dark style defined in core/plot_utils.py

st.title("🕵️ Covert Channel Detection Dashboard")
st.markdown(
    """
    Upload one or more CSV log files (Network, DB, OS). The app will:
    1. Auto-detect encoding & separator  
    2. Show per-file EDA (separate panels)  
    3. Run preprocessing (keeps your preprocessing pipeline)  
    4. Run anomaly detection (unchanged) and covert detection (unchanged)
    """
)

# ----------------------
# Sidebar controls
# ----------------------
st.sidebar.header("Options")
resample_sec = st.sidebar.slider("Time-series resolution (seconds)", 1, 300, 1)
model_choice = st.sidebar.selectbox("Anomaly model", ["IsolationForest", "LocalOutlierFactor", "OneClassSVM", "All"])
run_all_btn = st.sidebar.button("Run EDA & Detection for uploads")

# ----------------------
# File uploader (multiple)
# ----------------------
uploads = st.file_uploader("Upload CSV log file(s) — network / db / os", type=["csv"], accept_multiple_files=True)

if not uploads:
    st.info("Upload one or more CSV files (click top-left menu to reopen uploader).")
    st.stop()

# ----------------------
# Read + show uploaded file list
# ----------------------
st.sidebar.write("Uploaded files:")
for f in uploads:
    st.sidebar.write(f"- {f.name}")

# ----------------------
# Process each file separately (preserve isolation)
# ----------------------
for uploaded in uploads:
    st.markdown(f"---\n##  File: **{uploaded.name}**")

    # Read raw bytes safely (Streamlit files are file-like)
    try:
        raw = uploaded.read()
        if raw is None or len(raw) == 0:
            st.error(f"{uploaded.name} seems empty — skipping.")
            continue

        # Use the existing csv loader (you said not to replace it)
        df = load_csv_auto(io.BytesIO(raw))
        df = clean_dataframe(df)

    except Exception as e:
        st.error(f"Failed to load {uploaded.name}")
        st.code(traceback.format_exc())
        continue

    if df is None or df.empty:
        st.warning(f"{uploaded.name} loaded but contains no rows/columns after cleaning.")
        continue

    # Show brief info block
    with st.expander("File summary & quick stats", expanded=True):
        st.write(f"**Filename:** {uploaded.name}")
        st.write("Shape:", df.shape)
        st.write("Columns:", list(df.columns))
        st.dataframe(df.head(10), use_container_width=True)

    # ----------------------
    # Per-file EDA (rich, separate)
    # ----------------------
    try:
        st.markdown("### 🔎 Exploratory Data Analysis")
        run_full_eda(df, resample_sec=resample_sec)
    except Exception:
        st.error("EDA failed for this file.")
        st.code(traceback.format_exc())

    # ----------------------
    # Preprocessing using your pipeline (kept unchanged)
    # ----------------------
    try:
        st.markdown("### Preprocessing")
        processed_df = preprocess_file(df.copy(), dataset_type=None)  # your preprocess_file expects dataset_type; if it requires one, it will handle or auto-detect internally
        st.success("Preprocessing completed.")
        st.dataframe(processed_df.head(10), use_container_width=True)
    except TypeError:
        # In case your preprocess_file signature is preprocess_file(df, dataset_type)
        try:
            detected_type = None
            # if you have a detect function in eda_utils, try to use it; otherwise pass None
            try:
                from core.eda_utils import detect_file_type
                detected_type = detect_file_type(df)
            except Exception:
                detected_type = None
            processed_df = preprocess_file(df.copy(), detected_type)
            st.success("Preprocessing completed.")
            st.dataframe(processed_df.head(10), use_container_width=True)
        except Exception:
            st.error("Preprocessing failed.")
            st.code(traceback.format_exc())
            processed_df = df.copy()
    except Exception:
        st.error("Preprocessing failed.")
        st.code(traceback.format_exc())
        processed_df = df.copy()

    # ----------------------
    # Anomaly detection (unchanged function usage)
    # ----------------------
    try:
        st.markdown("###  Anomaly Detection (unchanged)")
        scores_df = run_anomaly_models(processed_df, model_choice)

        if scores_df is None or scores_df.empty:
            st.info("Anomaly model returned no results.")
        else:
            st.write("Anomaly scores snapshot")
            st.dataframe(scores_df.head(20), use_container_width=True)
            # plot timeline (plot_scores returns image path)
            try:
                img_path = plot_scores(scores_df, model_choice)
                st.image(img_path, use_column_width=True)
            except Exception:
                st.warning("Failed to render anomaly timeline.")
                st.code(traceback.format_exc())

    except Exception:
        st.error("Anomaly detection failed.")
        st.code(traceback.format_exc())

    # ----------------------
    # Covert DB / Channel detection (unchanged function usage)
    # ----------------------
    try:
        st.markdown("###  Covert DB & Channel Heuristics (unchanged)")
        covert_report = detect_covert_db_and_channel(df.copy(), processed_df.copy(), resample_sec=resample_sec)

        # present results clearly
        if covert_report.get("covert_db_found") or covert_report.get("covert_channel_found"):
            if covert_report.get("covert_db_found"):
                st.success("Covert database activity detected.")
                st.write("Times:", covert_report.get("covert_db_times", []))
                st.write("Reasons:", covert_report.get("covert_db_reasons", []))
            else:
                st.info("No covert database activity detected.")

            if covert_report.get("covert_channel_found"):
                st.success("Covert channel-like network behavior detected.")
                st.write("Times:", covert_report.get("covert_channel_times", []))
                st.write("Reasons:", covert_report.get("covert_channel_reasons", []))
            else:
                st.info("No covert channel-like behavior detected.")
        else:
            st.info("No covert database or covert channel detected for this file.")

    except Exception:
        st.error("Covert detection failed.")
        st.code(traceback.format_exc())

    st.markdown("---")

st.sidebar.success("Processing complete for uploaded files.")
