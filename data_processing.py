"""
data_processing.py
------------------
Loading, validation, cleaning and feature engineering for the
France Top 50 Playlist project (Atlantic Recording Corporation).

Run this file directly to rebuild the cleaned dataset and the data-quality tables:

    python src/data_processing.py

The raw file in data/raw/ is NEVER modified. The cleaned data is written to
data/processed/france_top50_cleaned.csv.
"""

import os

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------
# Portable paths (work on Windows, macOS and Linux)
# ----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH = os.path.join(BASE_DIR, "data", "raw", "Atlantic_France.csv")
CLEAN_PATH = os.path.join(BASE_DIR, "data", "processed", "france_top50_cleaned.csv")
TABLES_DIR = os.path.join(BASE_DIR, "outputs", "tables")
FIGURES_DIR = os.path.join(BASE_DIR, "outputs", "figures")

# ----------------------------------------------------------------------------
# Business thresholds (kept in one place so they are easy to change)
# ----------------------------------------------------------------------------
SHORT_MAX_MIN = 2.5      # Short  : duration  < 2.5 minutes
LONG_MIN_MIN = 4.0       # Long   : duration  > 4.0 minutes (Medium = 2.5 to 4.0 inclusive)

DURATION_ORDER = ["Short", "Medium", "Long"]
ALBUM_SIZE_ORDER = ["Small (1-5)", "Medium (6-12)", "Large (13+)"]
RANK_BAND_ORDER = ["1-10", "11-25", "26-50"]
FORMAT_ORDER = ["Single", "Album"]
EXPLICIT_ORDER = ["Explicit", "Clean"]

# Finer 0.5-minute duration bands used for the duration-distribution analysis
DURATION_BAND_EDGES = [0, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, np.inf]
DURATION_BAND_LABELS = ["<2.0", "2.0-2.5", "2.5-3.0", "3.0-3.5", "3.5-4.0", "4.0-4.5", "4.5+"]

EXPECTED_COLUMNS = [
    "date", "position", "song", "artist", "popularity",
    "duration_ms", "album_type", "total_tracks", "is_explicit", "album_cover_url",
]

MISSING_TOKENS = {"", "nan", "null", "none", "n/a"}
TRUE_TOKENS = {"true", "t", "1", "yes", "y", "explicit"}
FALSE_TOKENS = {"false", "f", "0", "no", "n", "clean"}


# ----------------------------------------------------------------------------
# 1. Loading
# ----------------------------------------------------------------------------
def load_raw(path=RAW_PATH):
    """Read the raw CSV with every column as text, so no problem is hidden by auto-typing."""
    raw = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing_cols = [c for c in EXPECTED_COLUMNS if c not in raw.columns]
    if missing_cols:
        raise ValueError(f"Raw file is missing expected columns: {missing_cols}")
    return raw


def _is_missing(series):
    """True where a text value is blank or a 'null-like' token."""
    return series.str.strip().str.lower().isin(MISSING_TOKENS)


# ----------------------------------------------------------------------------
# 2. Validation (read-only: reports problems, changes nothing)
# ----------------------------------------------------------------------------
def validate_raw(raw):
    """Run all data-quality checks on the raw data and return a tidy table."""
    checks = []

    def add(check, result, detail=""):
        checks.append({"Check": check, "Result": result, "Details": detail})

    add("Rows x columns", f"{raw.shape[0]:,} x {raw.shape[1]}", ", ".join(raw.columns))

    # Dates
    dates = pd.to_datetime(raw["date"], format="%d-%m-%Y", errors="coerce")
    add("Unparseable dates (format DD-MM-YYYY)", int(dates.isna().sum()))
    add("Date range", f"{dates.min().date()} to {dates.max().date()}",
        f"{dates.nunique()} unique dates")
    all_days = pd.date_range(dates.min(), dates.max())
    missing_days = all_days.difference(pd.DatetimeIndex(dates.dropna().unique()))
    add("Calendar dates with no snapshot", len(missing_days),
        ", ".join(d.strftime("%Y-%m-%d") for d in missing_days) or "none")

    # 50 entries per date
    per_date = raw.groupby("date").size()
    bad_dates = per_date[per_date != 50]
    add("Dates that do not have exactly 50 rows", len(bad_dates),
        "; ".join(f"{d}: {n} rows" for d, n in bad_dates.items()) or "none")

    # Rank checks
    position = pd.to_numeric(raw["position"], errors="coerce")
    add("Non-numeric positions", int(position.isna().sum()))
    add("Positions outside 1-50", int(((position < 1) | (position > 50)).sum()))
    add("Duplicate ranks within the same date (rows beyond the first)",
        int(raw.duplicated(["date", "position"]).sum()))
    add("Exact duplicate rows", int(raw.duplicated().sum()))

    # Missing values
    for col in raw.columns:
        n_missing = int(_is_missing(raw[col]).sum())
        if n_missing:
            add(f"Missing / blank values in '{col}'", n_missing)
    add("Total missing / blank cells", int(sum(_is_missing(raw[c]).sum() for c in raw.columns)))

    # Numeric fields
    for col in ["popularity", "duration_ms", "total_tracks"]:
        num = pd.to_numeric(raw[col], errors="coerce")
        add(f"Non-numeric values in '{col}'", int(num.isna().sum()))
    popularity = pd.to_numeric(raw["popularity"], errors="coerce")
    duration = pd.to_numeric(raw["duration_ms"], errors="coerce")
    tracks = pd.to_numeric(raw["total_tracks"], errors="coerce")
    add("Popularity outside 1-100 (0 = score not available)",
        int(((popularity < 1) | (popularity > 100)).sum()),
        f"min={popularity.min():.0f}, max={popularity.max():.0f}")
    add("Duration <= 0 ms", int((duration <= 0).sum()))
    add("Duration < 60 s (reviewed - plausible intros/interludes)", int(((duration > 0) & (duration < 60000)).sum()))
    add("total_tracks < 1", int((tracks < 1).sum()), f"min={tracks.min():.0f}, max={tracks.max():.0f}")

    # Categorical consistency
    add("Distinct album_type labels", raw["album_type"].nunique(),
        ", ".join(f"{k}={v:,}" for k, v in raw["album_type"].value_counts().items()))
    add("Distinct is_explicit labels", raw["is_explicit"].nunique(),
        ", ".join(f"{k}={v:,}" for k, v in raw["is_explicit"].value_counts().items()))
    add("Text with leading/trailing spaces (song, artist)",
        int((raw["song"] != raw["song"].str.strip()).sum() + (raw["artist"] != raw["artist"].str.strip()).sum()))
    single_multi = (raw["album_type"].str.lower().str.strip() == "single") & (tracks > 1)
    add("Releases labelled 'single' with more than 1 track (EP-style, kept as labelled)", int(single_multi.sum()))

    return pd.DataFrame(checks)


# ----------------------------------------------------------------------------
# 3. Cleaning
# ----------------------------------------------------------------------------
def _clean_explicit(series):
    """Map many possible explicit-content labels to True / False (NaN if unknown)."""
    s = series.astype(str).str.strip().str.lower()
    out = pd.Series(np.nan, index=series.index, dtype="object")
    out[s.isin(TRUE_TOKENS)] = True
    out[s.isin(FALSE_TOKENS)] = False
    return out


def clean_data(raw):
    """
    Clean the raw data. Returns (clean_df, cleaning_summary).
    The input `raw` is not modified. Steps 1-6 standardise values on ALL raw rows;
    steps 7-8 then remove invalid ranks and duplicate snapshots.
    """
    df = raw.copy()
    log = []

    def add(issue, action, rows):
        log.append({"Issue": issue, "Action Taken": action, "Rows Affected": int(rows)})

    # --- 1. Text formatting --------------------------------------------------
    text_cols = ["song", "artist", "album_type", "album_cover_url"]
    for col in text_cols:
        df[col] = df[col].astype(str)
    changed = ((df["song"] != df["song"].str.strip()) | (df["artist"] != df["artist"].str.strip())).sum()
    for col in text_cols:
        df[col] = df[col].str.strip()
    add("Leading/trailing spaces in song or artist", "Stripped whitespace", changed)

    # --- 2. Dates ------------------------------------------------------------
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
    add("Dates stored as text (DD-MM-YYYY)", "Converted to datetime (saved as YYYY-MM-DD)", len(df))
    n_bad_dates = df["date"].isna().sum()
    add("Unparseable dates", "Drop rows (none found)" if n_bad_dates == 0 else "Dropped rows", n_bad_dates)
    df = df[df["date"].notna()].copy()

    # --- 3. Numeric fields ---------------------------------------------------
    n_coerced = 0
    for col in ["position", "popularity", "duration_ms", "total_tracks"]:
        was_blank = df[col].astype(str).str.strip().str.lower().isin(MISSING_TOKENS)
        df[col] = pd.to_numeric(df[col], errors="coerce")
        n_coerced += int((df[col].isna() & ~was_blank).sum())
    add("Non-numeric values in numeric columns", "Converted to numbers; invalid -> missing", n_coerced)

    # --- 4. Labels: album_type and is_explicit -------------------------------
    lower_type = df["album_type"].str.lower()
    type_map = {"single": "Single", "album": "Album", "compilation": "Compilation"}
    n_relabel = (df["album_type"] != lower_type.map(type_map)).sum()
    df["album_type"] = lower_type.map(type_map)
    add("Lower-case album_type labels (single / album / compilation)", "Standardised to Title Case", n_relabel)
    add("Unrecognised album_type labels", "Set to missing (none found)", df["album_type"].isna().sum())
    add("'Compilation' releases (neither Single nor Album)",
        "Kept as 'Compilation' in album_type; grouped with Album in release_format",
        (df["album_type"] == "Compilation").sum())

    df["is_explicit"] = _clean_explicit(df["is_explicit"])
    add("is_explicit stored as text (TRUE/FALSE)", "Converted to boolean (True = Explicit, False = Clean)", len(df))
    add("Unrecognised is_explicit labels", "Set to missing (none found)", df["is_explicit"].isna().sum())

    # --- 5. Missing text -----------------------------------------------------
    blank_song = _is_missing(df["song"])
    df.loc[blank_song, "song"] = "Unknown Song"
    add("Blank song title", "Filled with 'Unknown Song'; row kept for rank and format analysis", blank_song.sum())

    # --- 6. Invalid values ---------------------------------------------------
    bad_pop = (df["popularity"] < 1) | (df["popularity"] > 100) | df["popularity"].isna()
    df.loc[bad_pop, "popularity"] = np.nan
    add("Popularity = 0 (score not available) or outside 1-100",
        "Set to missing; row kept, excluded from popularity statistics only", bad_pop.sum())

    bad_dur = (df["duration_ms"] <= 0) | df["duration_ms"].isna()
    df.loc[bad_dur, "duration_ms"] = np.nan
    add("Duration <= 0 ms", "Set to missing; row kept, excluded from duration statistics only", bad_dur.sum())

    bad_tracks = (df["total_tracks"] < 1) | df["total_tracks"].isna()
    df.loc[bad_tracks, "total_tracks"] = np.nan
    add("total_tracks < 1 or missing", "Set to missing (none found)" if bad_tracks.sum() == 0 else "Set to missing",
        bad_tracks.sum())

    short = ((df["duration_ms"] > 0) & (df["duration_ms"] < 60000)).sum()
    add("Very short tracks (< 60 seconds)", "Reviewed and retained (genuine intros/interludes)", short)

    # --- 7. Rank range -------------------------------------------------------
    bad_rank = ~df["position"].between(1, 50)
    add("Position outside 1-50", "Drop rows (none found)" if bad_rank.sum() == 0 else "Dropped rows", bad_rank.sum())
    df = df[~bad_rank].copy()
    df["position"] = df["position"].astype(int)

    # --- 8. Duplicates -------------------------------------------------------
    n_exact = df.duplicated().sum()
    df = df.drop_duplicates(keep="first")
    add("Exact duplicate rows", "Dropped (kept first occurrence)", n_exact)

    dup_mask = df.duplicated(["date", "position"], keep=False)
    dup_dates = df.loc[dup_mask, "date"].dt.strftime("%d-%m-%Y").unique()
    n_rank_dup = df.duplicated(["date", "position"]).sum()
    df = df.drop_duplicates(["date", "position"], keep="first")
    add(f"Duplicate ranks on one date: a second, slightly different snapshot for {', '.join(dup_dates) or 'n/a'}",
        "Kept the first snapshot (one row per date and rank); dropped the later one", n_rank_dup)

    # --- 9. Information only (no data change) --------------------------------
    n_missing_days = len(pd.date_range(df["date"].min(), df["date"].max()).difference(
        pd.DatetimeIndex(df["date"].unique())))
    add("Calendar dates with no snapshot", "Not imputed; analysed as observed (stated as a limitation)", n_missing_days)

    df = df.sort_values(["date", "position"]).reset_index(drop=True)
    df["is_explicit"] = df["is_explicit"].astype("boolean")
    df["popularity"] = df["popularity"].astype(float)
    df["duration_ms"] = df["duration_ms"].astype(float)
    df["total_tracks"] = df["total_tracks"].astype("Int64")

    return df, pd.DataFrame(log)


# ----------------------------------------------------------------------------
# 4. Feature engineering
# ----------------------------------------------------------------------------
def add_features(df):
    """Add all analytical features. Returns a new DataFrame."""
    df = df.copy()

    # Duration
    df["duration_min"] = df["duration_ms"] / 60000
    dur = df["duration_min"]
    group = np.where(dur < SHORT_MAX_MIN, "Short", np.where(dur <= LONG_MIN_MIN, "Medium", "Long"))
    df["duration_group"] = pd.Series(group, index=df.index).where(dur.notna())
    df["duration_band"] = pd.cut(dur, bins=DURATION_BAND_EDGES, labels=DURATION_BAND_LABELS, right=False)

    # Rank features
    df["rank_score"] = 51 - df["position"]
    df["is_top10"] = df["position"] <= 10
    df["is_top25"] = df["position"] <= 25
    df["rank_band"] = pd.cut(df["position"], bins=[0, 10, 25, 50], labels=RANK_BAND_ORDER)

    # Explicit category and release format
    df["explicit_category"] = np.where(df["is_explicit"].astype(bool), "Explicit", "Clean")
    df["release_format"] = np.where(df["album_type"] == "Single", "Single", "Album")

    # Album size group
    tracks = df["total_tracks"].astype(float)
    size = np.where(tracks <= 5, "Small (1-5)", np.where(tracks <= 12, "Medium (6-12)", "Large (13+)"))
    df["album_size_group"] = pd.Series(size, index=df.index).where(tracks.notna())

    # Helper columns
    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["track_id"] = df["song"] + " | " + df["artist"]

    return _set_categories(df)


def _set_categories(df):
    """Give the grouping columns a fixed, logical order (used in tables and charts)."""
    for col, order in [("duration_group", DURATION_ORDER), ("album_size_group", ALBUM_SIZE_ORDER),
                       ("explicit_category", EXPLICIT_ORDER), ("release_format", FORMAT_ORDER),
                       ("rank_band", RANK_BAND_ORDER), ("duration_band", DURATION_BAND_LABELS)]:
        df[col] = pd.Categorical(df[col], categories=order, ordered=True)
    return df


# ----------------------------------------------------------------------------
# 5. Pipeline helpers
# ----------------------------------------------------------------------------
def build_clean_dataset(raw_path=RAW_PATH):
    """Raw CSV -> (cleaned + featured data, validation table, cleaning summary)."""
    raw = load_raw(raw_path)
    validation = validate_raw(raw)
    clean, summary = clean_data(raw)
    clean = add_features(clean)
    return clean, validation, summary


def load_clean(path=CLEAN_PATH):
    """Load the saved cleaned CSV and restore date / category types."""
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
    df["is_explicit"] = df["is_explicit"].astype("boolean")
    df["total_tracks"] = df["total_tracks"].astype("Int64")
    return _set_categories(df)


def save_clean_outputs():
    """Run the whole pipeline and save the cleaned data and quality tables."""
    clean, validation, summary = build_clean_dataset()
    os.makedirs(os.path.dirname(CLEAN_PATH), exist_ok=True)
    os.makedirs(TABLES_DIR, exist_ok=True)
    out = clean.copy()
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    out.to_csv(CLEAN_PATH, index=False)
    validation.to_csv(os.path.join(TABLES_DIR, "01_data_validation_checks.csv"), index=False)
    summary.to_csv(os.path.join(TABLES_DIR, "02_cleaning_summary.csv"), index=False)
    return clean, validation, summary


if __name__ == "__main__":
    clean_df, validation_df, summary_df = save_clean_outputs()
    print(validation_df.to_string(index=False))
    print()
    print(summary_df.to_string(index=False))
    print()
    print(f"Cleaned data saved to: {CLEAN_PATH}  ({len(clean_df):,} rows)")
