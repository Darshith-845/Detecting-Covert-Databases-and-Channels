import pandas as pd
import numpy as np

def inject_covert_os(
    df: pd.DataFrame,
    time_col: str = "timestamp",
    user_col: str = "user",
    process_col: str = "process",
    message_col: str = "message",
    n_windows: int = 3,
    base_interval_sec: float = 1.0,
    jitter: float = 0.2,
    min_duration_sec: int = 10,
    max_duration_sec: int = 60,
    seed: int = 42
) -> pd.DataFrame:

    np.random.seed(seed)
    df = df.copy()

    # Basic checks
    for col in [time_col, user_col, process_col]:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    df["injected_attack"] = 0
    df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=[time_col])

    users = df[user_col].dropna().unique()
    processes = df[process_col].dropna().unique()

    if len(users) == 0 or len(processes) == 0:
        raise ValueError("No valid users or processes for OS injection")

    injections = []

    for _ in range(n_windows):
        user = np.random.choice(users)
        process = np.random.choice(processes)
        start = df[time_col].sample(1).iloc[0]
        duration = np.random.randint(min_duration_sec, max_duration_sec)

        t = start
        end = start + pd.Timedelta(seconds=duration)

        while t < end:
            injections.append({
                time_col: t,
                user_col: user,
                process_col: process,
                message_col: f"{process} executed",
                "injected_attack": 1
            })
            delta = base_interval_sec + np.random.uniform(-jitter, jitter)
            t += pd.Timedelta(seconds=max(0.1, delta))

    inject_df = pd.DataFrame(injections)
    df = pd.concat([df, inject_df], ignore_index=True)
    df = df.sort_values(time_col).reset_index(drop=True)

    return df


def inject_covert_db(
    df: pd.DataFrame,
    time_col: str = "log_time",
    user_col: str = "user_name",
    query_col: str = "query",
    n_windows: int = 3,
    low_rate: int = 2,
    high_rate: int = 10,
    window_sec: int = 10,
    seed: int = 42
) -> pd.DataFrame:

    np.random.seed(seed)
    df = df.copy()

    if time_col not in df.columns or user_col not in df.columns:
        raise ValueError("Required DB columns missing")

    df["injected_attack"] = 0
    df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=[time_col])

    users = df[user_col].dropna().unique()
    templates = df[query_col].dropna().unique() if query_col in df.columns else ["SELECT 1"]

    injections = []

    for _ in range(n_windows):
        user = np.random.choice(users)
        start = df[time_col].sample(1).iloc[0]
        bit = np.random.choice([0, 1])
        rate = high_rate if bit else low_rate

        for sec in range(window_sec):
            for _ in range(rate):
                injections.append({
                    time_col: start + pd.Timedelta(seconds=sec) + pd.Timedelta(milliseconds=np.random.randint(0, 800)),
                    user_col: user,
                    query_col: np.random.choice(templates),
                    "injected_attack": 1
                })

    inject_df = pd.DataFrame(injections)
    df = pd.concat([df, inject_df], ignore_index=True)
    df = df.sort_values(time_col).reset_index(drop=True)

    return df

def inject_covert_network(
    df: pd.DataFrame,
    n_windows: int = 3,
    min_duration_sec: int = 5,
    max_duration_sec: int = 30,
    base_interval: float = 0.05,
    jitter: float = 0.01,
    seed: int = 42
) -> pd.DataFrame:

    np.random.seed(seed)
    df = df.copy()

    # Required columns
    required = ["frame.time_epoch", "ip.src", "ip.dst", "frame.len"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    df["injected_attack"] = 0
    df["frame.time_epoch"] = pd.to_numeric(df["frame.time_epoch"], errors="coerce")
    df = df.dropna(subset=["frame.time_epoch"])

    unique_pairs = df[["ip.src", "ip.dst"]].drop_duplicates()
    times = df["frame.time_epoch"].values

    injections = []

    for _ in range(n_windows):
        # pick src-dst
        pair = unique_pairs.sample(1).iloc[0]
        src, dst = pair["ip.src"], pair["ip.dst"]

        # pick time window
        start = np.random.uniform(times.min(), times.max())
        duration = np.random.randint(min_duration_sec, max_duration_sec)
        end = start + duration

        t = start
        while t < end:
            injections.append({
                "frame.time_epoch": t,
                "ip.src": src,
                "ip.dst": dst,
                "frame.len": np.random.randint(60, 120),
                "injected_attack": 1
            })
            t += base_interval + np.random.uniform(-jitter, jitter)

    inject_df = pd.DataFrame(injections)
    df = pd.concat([df, inject_df], ignore_index=True)
    df = df.sort_values("frame.time_epoch").reset_index(drop=True)

    return df
