"""
analysis_utils.py
-----------------
Reusable analysis functions for the France Top 50 project: group profiles, rank-tier
summaries, KPIs, the two project-specific indices and the statistical tests.

Both the notebook and the Streamlit dashboard use these functions, so the numbers
always match. Every function expects the cleaned + featured DataFrame produced by
data_processing.py.

Reading guide
-------------
position      : chart rank (1 = best)
rank_score    : 51 - position (higher = better)
popularity    : 0-100 score supplied with the data (NOT streaming volume)
"""

import numpy as np
import pandas as pd
from scipy import stats

# Content Acceptance Score weights (equal weight on popularity and chart rank)
WEIGHT_POPULARITY = 0.5
WEIGHT_RANK = 0.5
RANK_SCORE_MIN, RANK_SCORE_MAX = 1, 50

TIER_NAMES = ["Top 10", "Top 25", "Top 50"]
TIER_LIMITS = {"Top 10": 10, "Top 25": 25, "Top 50": 50}


# ----------------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------------
def pct(part, whole):
    """Percentage that is safe when the denominator is zero."""
    return 100.0 * part / whole if whole else np.nan


def safe_ratio(a, b):
    """a / b that returns NaN when b is zero."""
    return a / b if b else np.nan


def fmt_p(p):
    """Readable p-value."""
    if p is None or np.isnan(p):
        return "n/a"
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


def effect_label(r):
    """Verbal size of an effect (rank-biserial r or Spearman rho)."""
    a = abs(r)
    if a < 0.1:
        return "negligible"
    if a < 0.3:
        return "small"
    if a < 0.5:
        return "moderate"
    return "strong"


# ----------------------------------------------------------------------------
# Overall summary (section 3 of the brief)
# ----------------------------------------------------------------------------
def dataset_summary(df):
    """One-table overview of the (filtered) dataset."""
    rows = [
        ("Total observations (song-day rows)", f"{len(df):,}"),
        ("Unique dates", f"{df['date'].nunique():,}"),
        ("Date range", f"{df['date'].min().date()} to {df['date'].max().date()}"),
        ("Unique songs (title + artist)", f"{df['track_id'].nunique():,}"),
        ("Unique artists", f"{df['artist'].nunique():,}"),
        ("Average popularity", f"{df['popularity'].mean():.2f}"),
        ("Median popularity", f"{df['popularity'].median():.1f}"),
        ("Average duration (min)", f"{df['duration_min'].mean():.2f}"),
        ("Median duration (min)", f"{df['duration_min'].median():.2f}"),
        ("Explicit share (%)", f"{pct((df['explicit_category'] == 'Explicit').sum(), len(df)):.1f}"),
        ("Clean share (%)", f"{pct((df['explicit_category'] == 'Clean').sum(), len(df)):.1f}"),
        ("Single share (%)", f"{pct((df['release_format'] == 'Single').sum(), len(df)):.1f}"),
        ("Album-track share (%)", f"{pct((df['release_format'] == 'Album').sum(), len(df)):.1f}"),
        ("Average album size (tracks)", f"{df['total_tracks'].astype(float).mean():.2f}"),
        ("Median album size (tracks)", f"{df['total_tracks'].astype(float).median():.1f}"),
    ]
    return pd.DataFrame(rows, columns=["Metric", "Value"])


# ----------------------------------------------------------------------------
# Content Acceptance Score (project-specific index)
# ----------------------------------------------------------------------------
def acceptance_bounds(df):
    """
    Min and max popularity of the FULL cleaned dataset. They are fixed once and reused for
    every subset, so scores stay comparable when the dashboard filters change.
    """
    return {"pop_min": float(df["popularity"].min()), "pop_max": float(df["popularity"].max())}


def content_acceptance_score(df, bounds):
    """
    Content Acceptance Score (0-100) = 100 x (0.5 x Normalised Popularity + 0.5 x Normalised Rank Score)
      Normalised Popularity   = (mean popularity - pop_min) / (pop_max - pop_min)
      Normalised Rank Score   = (mean rank_score - 1) / (50 - 1)
    A higher value means the group is both more popular and higher up the chart.
    """
    mean_pop = df["popularity"].mean()
    mean_rank = df["rank_score"].mean()
    if np.isnan(mean_pop) or np.isnan(mean_rank):
        return np.nan
    norm_pop = (mean_pop - bounds["pop_min"]) / (bounds["pop_max"] - bounds["pop_min"])
    norm_rank = (mean_rank - RANK_SCORE_MIN) / (RANK_SCORE_MAX - RANK_SCORE_MIN)
    return 100 * (WEIGHT_POPULARITY * norm_pop + WEIGHT_RANK * norm_rank)


# ----------------------------------------------------------------------------
# Group profile: used for Explicit/Clean, Single/Album, duration groups, album-size groups
# ----------------------------------------------------------------------------
def category_profile(df, col, bounds):
    """
    Performance table for every category of `col`.

    Representation  : Observations, Share (%)
    Popularity      : Avg / Median popularity
    Rank performance: Avg position, Avg rank score, Top 10 / Top 25 rate, Top 10 lift
    Combined        : Content Acceptance Score

    'Top 10 rate' = % of that category's observations that sit in positions 1-10.
    'Top 10 lift' = Top 10 rate divided by the Top 10 rate of ALL rows in df
                    (1.0 = proportional, > 1 = over-represented in the Top 10).
    """
    base_top10 = df["is_top10"].mean() * 100 if len(df) else np.nan
    categories = df[col].cat.categories if hasattr(df[col], "cat") else sorted(df[col].dropna().unique())
    rows = []
    for cat in categories:
        g = df[df[col] == cat]
        n = len(g)
        top10_rate = g["is_top10"].mean() * 100 if n else np.nan
        rows.append({
            "Category": cat,
            "Observations": n,
            "Share (%)": pct(n, len(df)),
            "Unique tracks": g["track_id"].nunique(),
            "Avg popularity": g["popularity"].mean(),
            "Median popularity": g["popularity"].median(),
            "Avg position": g["position"].mean(),
            "Avg rank score": g["rank_score"].mean(),
            "Top 10 rate (%)": top10_rate,
            "Top 25 rate (%)": g["is_top25"].mean() * 100 if n else np.nan,
            "Top 10 lift (x)": safe_ratio(top10_rate, base_top10) if n else np.nan,
            "Content Acceptance Score": content_acceptance_score(g, bounds) if n else np.nan,
        })
    return pd.DataFrame(rows)


def rank_band_distribution(df, col):
    """For each category of `col`: what % of its observations fall in rank bands 1-10, 11-25, 26-50."""
    table = pd.crosstab(df[col], df["rank_band"], normalize="index") * 100
    table.columns = [f"Band {c} (%)" for c in table.columns]
    return table.reset_index().rename(columns={col: "Category"})


def tier_composition(df, col):
    """For Top 10 / Top 25 / Top 50: % of observations belonging to each category of `col`."""
    out = {}
    for tier in TIER_NAMES:
        sub = df[df["position"] <= TIER_LIMITS[tier]]
        out[tier] = sub[col].value_counts(normalize=True).mul(100)
    table = pd.DataFrame(out)
    table.index.name = "Category"
    return table.reset_index()


# ----------------------------------------------------------------------------
# Rank-tier profile (section 8)
# ----------------------------------------------------------------------------
def _profile_of_subset(sub):
    """Attribute values for one subset of rows (a rank tier or a rank band)."""
    n = len(sub)
    dur_share = sub["duration_group"].value_counts(normalize=True) * 100
    return {
        "Observations": n,
        "Explicit share (%)": pct((sub["explicit_category"] == "Explicit").sum(), n),
        "Clean share (%)": pct((sub["explicit_category"] == "Clean").sum(), n),
        "Single share (%)": pct((sub["release_format"] == "Single").sum(), n),
        "Album-track share (%)": pct((sub["release_format"] == "Album").sum(), n),
        "Avg popularity": sub["popularity"].mean(),
        "Avg duration (min)": sub["duration_min"].mean(),
        "Short share (%)": dur_share.get("Short", 0.0),
        "Medium share (%)": dur_share.get("Medium", 0.0),
        "Long share (%)": dur_share.get("Long", 0.0),
        "Avg album size (tracks)": sub["total_tracks"].astype(float).mean(),
    }


def _tidy(table):
    """Counts as whole numbers, everything else rounded to 2 decimals (clean display and CSV)."""
    table = table.astype(object)
    for attribute in table.index:
        if attribute == "Observations":
            table.loc[attribute] = [int(v) for v in table.loc[attribute]]
        else:
            table.loc[attribute] = [round(float(v), 2) for v in table.loc[attribute]]
    return table


def tier_summary(df):
    """Cumulative tiers (Top 10 is contained in Top 25, which is contained in Top 50)."""
    cols = {tier: _profile_of_subset(df[df["position"] <= TIER_LIMITS[tier]]) for tier in TIER_NAMES}
    table = _tidy(pd.DataFrame(cols))
    table.index.name = "Attribute"
    return table.reset_index()


def band_summary(df):
    """Mutually exclusive bands (1-10, 11-25, 26-50): no row is counted twice."""
    cols = {}
    for band in df["rank_band"].cat.categories:
        cols[band] = _profile_of_subset(df[df["rank_band"] == band])
    table = _tidy(pd.DataFrame(cols))
    table.index.name = "Attribute"
    return table.reset_index()


# ----------------------------------------------------------------------------
# Album size
# ----------------------------------------------------------------------------
def spearman(x, y):
    """Spearman correlation on rows where both values exist. Returns (rho, p, n)."""
    pair = pd.DataFrame({"x": pd.to_numeric(x, errors="coerce"),
                         "y": pd.to_numeric(y, errors="coerce")}).dropna()
    n = len(pair)
    if n < 10 or pair["x"].nunique() < 2 or pair["y"].nunique() < 2:
        return np.nan, np.nan, n
    res = stats.spearmanr(pair["x"], pair["y"])
    return float(res.statistic), float(res.pvalue), n


def album_size_impact(df):
    """
    Album Size Impact Index = average of two Spearman correlations
        rho(total_tracks, popularity)  and  rho(total_tracks, rank_score)
    Range -1 to +1.
      > 0 : bigger releases go with stronger track performance
      < 0 : bigger releases go with weaker track performance ('dilution')
      ~ 0 : little relationship
    Spearman is used because album size is heavily skewed and the relationship may not be linear.
    """
    sizes = df["total_tracks"].astype(float)
    rho_pop, p_pop, n_pop = spearman(sizes, df["popularity"])
    rho_rank, p_rank, n_rank = spearman(sizes, df["rank_score"])
    index = np.nanmean([rho_pop, rho_rank]) if not (np.isnan(rho_pop) and np.isnan(rho_rank)) else np.nan
    return {"rho_popularity": rho_pop, "p_popularity": p_pop, "n_popularity": n_pop,
            "rho_rank_score": rho_rank, "p_rank_score": p_rank, "n_rank_score": n_rank,
            "index": index}


def album_size_label(index):
    """Plain-English reading of the Album Size Impact Index."""
    if index is None or np.isnan(index):
        return "Not available (album size does not vary enough in the selected data)"
    size = effect_label(index)
    if size == "negligible":
        return "Little or no meaningful relationship"
    direction = ("larger releases go with STRONGER track performance" if index > 0
                 else "larger releases go with WEAKER track performance (dilution)")
    return f"{size.capitalize()} association: {direction}"


def album_size_distribution(df):
    """Number of observations by exact track count (1, 2, 3 ...)."""
    out = df["total_tracks"].astype(float).value_counts().sort_index().rename_axis("total_tracks")
    return out.rename("Observations").reset_index()


# ----------------------------------------------------------------------------
# Duration
# ----------------------------------------------------------------------------
def duration_stats(df):
    """Mean, median, min, max and spread of duration (minutes)."""
    d = df["duration_min"].dropna()
    return pd.DataFrame({"Metric": ["Mean", "Median", "Std. deviation", "Minimum", "Maximum",
                                    "25th percentile", "75th percentile"],
                         "Minutes": [d.mean(), d.median(), d.std(), d.min(), d.max(),
                                     d.quantile(0.25), d.quantile(0.75)]})


def duration_band_table(df):
    """
    0.5-minute duration bands. 'Share of Top 10' is the composition of the Top 10; compared with
    'Share of all rows' it shows which bands are over-represented among the strongest positions.
    """
    valid = df[df["duration_band"].notna()]
    top10 = valid[valid["position"] <= 10]
    rows = []
    for band in valid["duration_band"].cat.categories:
        g = valid[valid["duration_band"] == band]
        share_all = pct(len(g), len(valid))
        share_top10 = pct((top10["duration_band"] == band).sum(), len(top10))
        rows.append({
            "Duration band (min)": band,
            "Observations": len(g),
            "Share of all rows (%)": share_all,
            "Share of Top 10 (%)": share_top10,
            "Top 10 rate (%)": g["is_top10"].mean() * 100 if len(g) else np.nan,
            "Representation index": safe_ratio(share_top10, share_all),
            "Avg popularity": g["popularity"].mean(),
            "Avg rank score": g["rank_score"].mean(),
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# Time trend
# ----------------------------------------------------------------------------
def explicit_over_time(df):
    """Monthly explicit share (all rows and Top 10 rows). First/last months are partial."""
    rows = []
    for month, g in df.groupby("month"):
        top10 = g[g["position"] <= 10]
        rows.append({
            "Month": month,
            "Snapshot days": g["date"].nunique(),
            "Explicit share - all rows (%)": pct((g["explicit_category"] == "Explicit").sum(), len(g)),
            "Explicit share - Top 10 (%)": pct((top10["explicit_category"] == "Explicit").sum(), len(top10)),
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# KPIs (section 9)
# ----------------------------------------------------------------------------
def compute_kpis(df, bounds):
    """All required KPIs for the given (possibly filtered) data. Zero denominators give NaN."""
    n = len(df)
    n_explicit = int((df["explicit_category"] == "Explicit").sum())
    n_clean = int((df["explicit_category"] == "Clean").sum())
    n_single = int((df["release_format"] == "Single").sum())
    n_album = int((df["release_format"] == "Album").sum())
    impact = album_size_impact(df)
    return {
        "total_observations": n,
        "explicit_share_pct": pct(n_explicit, n),
        "clean_dominance_ratio": safe_ratio(n_clean, n_explicit),
        "single_album_ratio": safe_ratio(n_single, n_album),
        "avg_duration_min": df["duration_min"].mean(),
        "avg_popularity": df["popularity"].mean(),
        "album_size_impact_index": impact["index"],
        "content_acceptance_score": content_acceptance_score(df, bounds),
    }


def kpi_table(df, bounds):
    """KPI summary table with definitions (saved to outputs/tables)."""
    k = compute_kpis(df, bounds)
    rows = [
        ("Total observations", k["total_observations"], "Song-day rows (one row = one song on one date)"),
        ("Explicit Content Share (%)", k["explicit_share_pct"], "Explicit rows / total rows x 100"),
        ("Clean Content Dominance Ratio", k["clean_dominance_ratio"], "Clean rows / Explicit rows"),
        ("Single vs Album Track Ratio", k["single_album_ratio"], "Single rows / Album-track rows"),
        ("Average Song Duration (min)", k["avg_duration_min"], "Mean of duration_ms / 60,000"),
        ("Average Popularity", k["avg_popularity"], "Mean popularity (valid scores only)"),
        ("Album Size Impact Index", k["album_size_impact_index"],
         "Mean of Spearman rho(total_tracks, popularity) and rho(total_tracks, rank_score); -1 to +1"),
        ("Content Acceptance Score", k["content_acceptance_score"],
         "100 x (0.5 x normalised popularity + 0.5 x normalised rank score)"),
    ]
    return pd.DataFrame(rows, columns=["KPI", "Value", "Definition"])


# ----------------------------------------------------------------------------
# Track-level view (robustness check)
# ----------------------------------------------------------------------------
def track_level(df):
    """
    One row per unique song (title + artist). A song normally stays on the chart for many days, so
    the song-day rows are not independent. Testing at track level gives a more conservative check.
    """
    tmp = df.assign(explicit_category=df["explicit_category"].astype(str),
                    release_format=df["release_format"].astype(str),
                    total_tracks=df["total_tracks"].astype(float))

    def mode(s):
        return s.mode().iloc[0]

    return tmp.groupby("track_id").agg(
        days_on_chart=("date", "size"),
        avg_popularity=("popularity", "mean"),
        avg_position=("position", "mean"),
        avg_rank_score=("rank_score", "mean"),
        best_position=("position", "min"),
        avg_duration_min=("duration_min", "mean"),
        total_tracks=("total_tracks", "median"),
        explicit_category=("explicit_category", mode),
        release_format=("release_format", mode),
    ).reset_index()


# ----------------------------------------------------------------------------
# Statistical tests (section 10)
# ----------------------------------------------------------------------------
def mann_whitney(a, b):
    """
    Two-sided Mann-Whitney U test of group a against group b.
    Effect size = rank-biserial correlation r = 2U/(n1 n2) - 1  (positive: a tends to be larger than b).
    """
    a = pd.Series(a).dropna().astype(float)
    b = pd.Series(b).dropna().astype(float)
    res = stats.mannwhitneyu(a, b, alternative="two-sided")
    r = 2 * res.statistic / (len(a) * len(b)) - 1
    return {"U": float(res.statistic), "p": float(res.pvalue), "n_a": len(a), "n_b": len(b),
            "median_a": a.median(), "median_b": b.median(), "mean_a": a.mean(), "mean_b": b.mean(), "r": float(r)}


def _test_row(level, question, test_name, a_name, b_name, metric, res, higher_is_better_text):
    """Turn a Mann-Whitney result into one readable row."""
    significant = res["p"] < 0.05
    size = effect_label(res["r"])
    if significant:
        stat_text = f"Significant difference (p {fmt_p(res['p'])}); effect size {size} (r = {res['r']:+.2f})"
        higher = a_name if res["r"] > 0 else b_name
        business = (f"{higher} tracks tend to have {higher_is_better_text}: median {res['median_a']:.1f} "
                    f"({a_name}) vs {res['median_b']:.1f} ({b_name}). The gap is {size} in practical terms.")
    else:
        stat_text = f"No significant difference (p = {fmt_p(res['p'])}); effect size {size} (r = {res['r']:+.2f})"
        business = (f"No reliable difference between {a_name} and {b_name} on {metric} "
                    f"(medians {res['median_a']:.1f} vs {res['median_b']:.1f}).")
    return {"Level": level, "Question": question, "Test": test_name,
            "Test statistic (U)": res["U"], "p-value": res["p"], "p-value (display)": fmt_p(res["p"]),
            "Effect size (r)": res["r"],
            "n (group A / B)": f"{res['n_a']:,} / {res['n_b']:,}",
            "Statistical conclusion": stat_text, "Business interpretation": business}


def group_tests(df, level):
    """The four required group comparisons for one data level (song-day rows or unique tracks)."""
    if level.startswith("Observation"):
        pop, rank = "popularity", "rank_score"
        exp, fmt = "explicit_category", "release_format"
    else:
        pop, rank = "avg_popularity", "avg_rank_score"
        exp, fmt = "explicit_category", "release_format"

    rows = []
    for col, a, b, label in [(exp, "Explicit", "Clean", "Explicit vs Clean"),
                             (fmt, "Single", "Album", "Single vs Album")]:
        ga, gb = df[df[col].astype(str) == a], df[df[col].astype(str) == b]
        res = mann_whitney(ga[pop], gb[pop])
        rows.append(_test_row(level, f"Is popularity different for {label}?", "Mann-Whitney U",
                              a, b, "popularity", res, "higher popularity"))
        res = mann_whitney(ga[rank], gb[rank])
        rows.append(_test_row(level, f"Is chart rank different for {label}? (rank score; higher = better)",
                              "Mann-Whitney U", a, b, "rank score", res, "a better (higher) rank score"))
    return rows


def run_group_tests(df):
    """Group tests at both levels: song-day rows (as asked) and unique tracks (robustness)."""
    rows = group_tests(df, "Observation (song-day)")
    rows += group_tests(track_level(df), "Unique track (robustness)")
    return pd.DataFrame(rows)


def run_correlations(df, album_only=False):
    """Spearman correlations between rank, duration, album size and popularity."""
    data = df[df["release_format"].astype(str) == "Album"] if album_only else df
    sizes = data["total_tracks"].astype(float)
    pairs = [
        ("Popularity vs rank score", data["popularity"], data["rank_score"]),
        ("Duration (min) vs popularity", data["duration_min"], data["popularity"]),
        ("Duration (min) vs rank score", data["duration_min"], data["rank_score"]),
        ("Album size vs popularity", sizes, data["popularity"]),
        ("Album size vs rank score", sizes, data["rank_score"]),
        ("Album size vs duration (min)", sizes, data["duration_min"]),
    ]
    rows = []
    for name, x, y in pairs:
        rho, p, n = spearman(x, y)
        size = effect_label(rho) if not np.isnan(rho) else "n/a"
        direction = "positive" if rho > 0 else "negative"
        rows.append({
            "Relationship": name,
            "Spearman rho": rho,
            "p-value": p,
            "p-value (display)": fmt_p(p),
            "n": n,
            "Strength": size,
            "Statistical conclusion": (f"{size.capitalize()} {direction} monotonic relationship (p {fmt_p(p)})"
                                       if size != "negligible" else f"Negligible relationship (p {fmt_p(p)})"),
        })
    return pd.DataFrame(rows)


def normality_check(df):
    """Evidence for choosing a non-parametric test: skewness and D'Agostino normality test."""
    rows = []
    for name, s in [("Popularity", df["popularity"]), ("Rank score", df["rank_score"]),
                    ("Duration (min)", df["duration_min"])]:
        s = s.dropna().astype(float)
        k2, p = stats.normaltest(s)
        rows.append({"Variable": name, "Skewness": float(stats.skew(s)),
                     "Normality test p-value": float(p),
                     "Conclusion": "Not normal -> use Mann-Whitney U / Spearman" if p < 0.05 else "Approximately normal"})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# Dynamic text used by the dashboard's Compliance Summary
# ----------------------------------------------------------------------------
def compliance_summary(df, bounds):
    """Short, data-driven summary (markdown bullets) of the selected data."""
    n = len(df)
    if n == 0:
        return "No data for the selected filters."
    lines = []
    k = compute_kpis(df, bounds)

    # Explicit content
    exp = df[df["explicit_category"] == "Explicit"]
    cln = df[df["explicit_category"] == "Clean"]
    line = (f"**Explicit content:** {k['explicit_share_pct']:.1f}% of the {n:,} selected observations are "
            f"explicit and {100 - k['explicit_share_pct']:.1f}% are clean.")
    if len(exp) and len(cln):
        line += (f" Average popularity is {exp['popularity'].mean():.1f} (explicit) vs "
                 f"{cln['popularity'].mean():.1f} (clean); average chart position is "
                 f"{exp['position'].mean():.1f} (explicit) vs {cln['position'].mean():.1f} (clean).")
    lines.append(line)

    # Release format
    sg = df[df["release_format"] == "Single"]
    al = df[df["release_format"] == "Album"]
    line = (f"**Release format:** Singles are {pct(len(sg), n):.1f}% of observations and album tracks "
            f"{pct(len(al), n):.1f}%.")
    if len(sg) and len(al):
        line += (f" Average popularity is {sg['popularity'].mean():.1f} (singles) vs "
                 f"{al['popularity'].mean():.1f} (album tracks); average position is "
                 f"{sg['position'].mean():.1f} vs {al['position'].mean():.1f}.")
    lines.append(line)

    # Duration
    dur_share = df["duration_group"].value_counts(normalize=True) * 100
    if dur_share.size:
        top_group = dur_share.idxmax()
        lines.append(f"**Duration:** the average song lasts {k['avg_duration_min']:.2f} minutes "
                     f"(median {df['duration_min'].median():.2f}). The most common group is "
                     f"{top_group} ({dur_share.max():.1f}% of observations).")

    # Album structure
    lines.append(f"**Album structure:** Album Size Impact Index = "
                 f"{'n/a' if np.isnan(k['album_size_impact_index']) else format(k['album_size_impact_index'], '+.3f')}"
                 f" -> {album_size_label(k['album_size_impact_index'])}. This is an association, not proof of cause.")

    # Combined
    lines.append(f"**Content Acceptance Score:** {k['content_acceptance_score']:.1f} / 100 for the selection "
                 f"(a project-specific index, not an industry metric).")
    return "\n\n".join(lines)
