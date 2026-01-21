import pandas as pd
import chardet
import io

def _detect_encoding(raw_bytes: bytes) -> str:
    try:
        enc = chardet.detect(raw_bytes).get("encoding") or "utf-8"
        return enc
    except Exception:
        return "utf-8"

def load_csv_auto(uploaded) -> pd.DataFrame:
    """
    Accepts a BytesIO or file-like object (already read bytes or stream).
    Returns a DataFrame or raises.
    """
    # If it's BytesIO, getvalue; if file-like, read; if bytes, use directly
    if hasattr(uploaded, "getvalue"):
        raw = uploaded.getvalue()
    elif hasattr(uploaded, "read"):
        raw = uploaded.read()
    elif isinstance(uploaded, (bytes, bytearray)):
        raw = uploaded
    else:
        raise ValueError("Unsupported uploaded type for load_csv_auto")

    if raw is None or len(raw) == 0:
        return pd.DataFrame()

    enc = _detect_encoding(raw)
    seps = [",", ";", "|", "\t"]
    for sep in seps:
        try:
            df = pd.read_csv(io.BytesIO(raw), encoding=enc, sep=sep)
            if df.shape[1] > 1:
                return df
        except Exception:
            continue

    # Fallback: try python engine and skip bad lines
    try:
        return pd.read_csv(io.BytesIO(raw), encoding=enc, sep=",", engine="python", on_bad_lines="skip")
    except Exception:
        # ultimate fallback
        return pd.read_csv(io.BytesIO(raw), encoding="latin1", sep=",", engine="python", on_bad_lines="skip")


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(df, pd.DataFrame):
        return pd.DataFrame()
    df = df.dropna(axis=1, how="all")
    df = df.dropna(axis=0, how="all")
    df.columns = [str(c).strip().replace(" ", "_").lower() for c in df.columns]
    return df
