"""
France Top 50 Playlist - Audience Sensitivity, Content Compliance & Format Preference dashboard
Atlantic Recording Corporation

Run locally :  streamlit run app.py
Deploy      :  push the project to GitHub and point Streamlit Community Cloud at app.py
               (the app needs only data/ , src/ , requirements.txt - no extra setup).
"""

import os
import sys

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# Make src/ importable. Anchored to this file, so it works from any working directory.
APP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(APP_DIR, "src"))

import analysis_utils as au  # noqa: E402
import data_processing as dp  # noqa: E402

st.set_page_config(page_title="France Top 50 - Content & Format Analysis", page_icon=":bar_chart:", layout="wide")

COLORS = {"Explicit": "#eb6834", "Clean": "#2a78d6", "Single": "#1baf7a", "Album": "#6250d6",
          "Short": "#a9c9f0", "Medium": "#5a9be0", "Long": "#1f5fae",
          "Small (1-5)": "#a9c9f0", "Medium (6-12)": "#5a9be0", "Large (13+)": "#1f5fae"}
REQUIRED_COLUMNS = {"date", "position", "song", "artist", "popularity", "duration_min", "duration_group", "rank_score",
                    "is_top10", "is_top25", "rank_band", "explicit_category", "release_format", "total_tracks",
                    "album_size_group", "duration_band", "track_id", "month"}


# ----------------------------------------------------------------------------
# Data loading (cached). Never writes to disk, so it also works on read-only hosts.
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading data...")
def load_data():
    """Cleaned CSV if it is present and valid; otherwise rebuild it in memory from the raw file."""
    try:
        if os.path.exists(dp.CLEAN_PATH):
            frame = dp.load_clean()
            if REQUIRED_COLUMNS.issubset(frame.columns) and len(frame) > 0:
                return frame
    except Exception:
        pass                                   # fall through to the rebuild below
    frame, _, _ = dp.build_clean_dataset()
    return frame


@st.cache_data(show_spinner=False)
def load_quality_tables():
    """Validation checks and cleaning summary: read the saved tables, or recompute from the raw file."""
    paths = [os.path.join(dp.TABLES_DIR, "01_data_validation_checks.csv"),
             os.path.join(dp.TABLES_DIR, "02_cleaning_summary.csv")]
    if all(os.path.exists(p) for p in paths):
        return pd.read_csv(paths[0]).fillna(""), pd.read_csv(paths[1])
    _, validation, summary = dp.build_clean_dataset()
    return validation.fillna(""), summary


@st.cache_data(show_spinner="Running statistical tests...")
def full_data_tests():
    """Statistical tests on the full cleaned data (they do not change with the sidebar filters)."""
    frame = load_data()
    return au.run_group_tests(frame), au.run_correlations(frame)


def fmt(value, spec=".2f", suffix=""):
    """Format a KPI value; show n/a when it cannot be calculated."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "n/a"
    return f"{value:{spec}}{suffix}"


def show_chart(fig):
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), legend_title_text="")
    st.plotly_chart(fig, width="stretch")


def as_text(frame, columns):
    """Plotly works best with plain-text categories."""
    frame = frame.copy()
    for col in columns:
        frame[col] = frame[col].astype(str)
    return frame


def safe(render, *args):
    """Run one dashboard section; if it fails, show a message instead of crashing the whole page."""
    try:
        render(*args)
    except Exception as error:  # noqa: BLE001
        st.error(f"This section could not be displayed for the current filters ({type(error).__name__}: {error}).")


# ----------------------------------------------------------------------------
# Load data
# ----------------------------------------------------------------------------
try:
    full = load_data()
except FileNotFoundError:
    st.error("Data file not found. Make sure data/raw/Atlantic_France.csv (or data/processed/france_top50_cleaned.csv) "
             "is part of the project.")
    st.stop()

bounds = au.acceptance_bounds(full)    # fixed popularity range, so scores stay comparable under any filter
min_date, max_date = full["date"].min().date(), full["date"].max().date()

# ----------------------------------------------------------------------------
# Sidebar filters
# ----------------------------------------------------------------------------
DEFAULTS = {"f_dates": (min_date, max_date), "f_tier": "Top 50", "f_explicit": "All", "f_format": "All"}
for key, value in DEFAULTS.items():
    st.session_state.setdefault(key, value)


def reset_filters():
    for key, value in DEFAULTS.items():
        st.session_state[key] = value


st.sidebar.header("Filters")
st.sidebar.date_input("Date range", min_value=min_date, max_value=max_date, key="f_dates")
st.sidebar.selectbox("Rank tier", ["Top 50", "Top 25", "Top 10"], key="f_tier",
                     help="Top 10 = positions 1-10, Top 25 = positions 1-25, Top 50 = all positions.")
st.sidebar.selectbox("Explicit filter", ["All", "Explicit", "Clean"], key="f_explicit")
st.sidebar.selectbox("Album type", ["All", "Single", "Album"], key="f_format",
                     help="'Album' also includes the 9 rows labelled 'compilation'.")
st.sidebar.button("Reset filters", on_click=reset_filters)

# A date range needs two dates; while the user is still picking the second one, wait.
date_value = st.session_state["f_dates"]
if isinstance(date_value, (tuple, list)):
    if len(date_value) < 2:
        st.info("Select an end date to apply the date range.")
        st.stop()
    start_date, end_date = date_value[0], date_value[1]
else:
    start_date = end_date = date_value

rank_tier = st.session_state["f_tier"]
explicit_choice = st.session_state["f_explicit"]
format_choice = st.session_state["f_format"]

mask = (full["date"] >= pd.Timestamp(start_date)) & (full["date"] <= pd.Timestamp(end_date))
mask &= full["position"] <= au.TIER_LIMITS[rank_tier]
if explicit_choice != "All":
    mask &= full["explicit_category"] == explicit_choice
if format_choice != "All":
    mask &= full["release_format"] == format_choice
data = full[mask].copy()

st.title("France Top 50 Playlist - Content, Compliance & Format Analysis")
st.caption(f"Atlantic Recording Corporation | data from {min_date} to {max_date} | popularity and rank are playlist "
           "measures, not streaming volumes.")

if data.empty:
    st.warning("No observations match the selected filters. Please widen the filters or press 'Reset filters'.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.write(f"**{len(data):,}** of {len(full):,} observations selected")
export = data.drop(columns=["album_cover_url"], errors="ignore").copy()
export["date"] = export["date"].dt.strftime("%Y-%m-%d")
st.sidebar.download_button("Download filtered data (CSV)", export.to_csv(index=False).encode("utf-8"),
                           file_name="france_top50_filtered.csv", mime="text/csv")

# ----------------------------------------------------------------------------
# KPI cards
# ----------------------------------------------------------------------------
kpi = au.compute_kpis(data, bounds)
row1 = st.columns(4)
row1[0].metric("Total observations", f"{kpi['total_observations']:,}", help="Song-day rows in the selection")
row1[1].metric("Explicit Content Share", fmt(kpi["explicit_share_pct"], ".1f", "%"), help="Explicit rows / total rows x 100")
row1[2].metric("Clean Content Dominance Ratio", fmt(kpi["clean_dominance_ratio"]),
               help="Clean rows / Explicit rows. Above 1 = clean is more common.")
row1[3].metric("Single vs Album Ratio", fmt(kpi["single_album_ratio"]), help="Single rows / Album-track rows")
row2 = st.columns(4)
row2[0].metric("Average Duration", fmt(kpi["avg_duration_min"], ".2f", " min"))
row2[1].metric("Average Popularity", fmt(kpi["avg_popularity"], ".1f"), help="Mean popularity score (valid scores only)")
row2[2].metric("Album Size Impact Index", fmt(kpi["album_size_impact_index"], "+.3f"),
               help="Average Spearman correlation of release size with popularity and with rank score (-1 to +1). "
                    "Below 0: bigger releases go with weaker tracks. n/a if release size barely varies in the selection.")
row2[3].metric("Content Acceptance Score", fmt(kpi["content_acceptance_score"], ".1f"),
               help="Project-specific index, 0-100: 0.5 x normalised popularity + 0.5 x normalised rank score. Not an industry metric.")


# ----------------------------------------------------------------------------
# Sections
# ----------------------------------------------------------------------------
def group_columns(col, order, label):
    """Distribution and popularity charts shared by the Explicit and Release-Format sections."""
    profile = au.category_profile(data, col, bounds)
    c1, c2, c3 = st.columns(3)
    with c1:
        fig = px.bar(profile, x="Category", y="Observations", color="Category", color_discrete_map=COLORS,
                     category_orders={"Category": order}, text=profile["Share (%)"].map(lambda v: f"{v:.1f}%"),
                     title=f"{label} distribution")
        fig.update_layout(showlegend=False, xaxis_title="")
        show_chart(fig)
    with c2:
        fig = px.box(as_text(data, [col]), x=col, y="popularity", color=col, color_discrete_map=COLORS, points=False,
                     category_orders={col: order}, title="Popularity comparison")
        fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Popularity (0-100)")
        show_chart(fig)
    return profile, c3


def render_explicit():
    profile, col3 = group_columns("explicit_category", dp.EXPLICIT_ORDER, "Explicit vs Clean")
    with col3:
        bands = au.rank_band_distribution(data, "explicit_category").melt(id_vars="Category", var_name="Band", value_name="% of group")
        bands["Band"] = bands["Band"].str.replace("Band ", "").str.replace(" (%)", "", regex=False)
        fig = px.bar(bands, x="Band", y="% of group", color="Category", barmode="group", color_discrete_map=COLORS,
                     title="Rank comparison: where each group sits", text=bands["% of group"].map(lambda v: f"{v:.1f}"))
        fig.update_layout(xaxis_title="Chart positions")
        show_chart(fig)
    st.dataframe(profile.round(2), hide_index=True, width="stretch")
    st.caption("Top 10 rate = % of the group's rows in positions 1-10. Lift = that rate relative to all selected rows (1.0 = proportional). "
               "Representation, popularity and rank are different questions - a common label is not necessarily a preferred one.")


def render_format():
    profile, col3 = group_columns("release_format", dp.FORMAT_ORDER, "Single vs Album")
    with col3:
        comp = au.tier_composition(data, "release_format").melt(id_vars="Category", var_name="Tier", value_name="% of tier")
        fig = px.bar(comp, x="Tier", y="% of tier", color="Category", color_discrete_map=COLORS,
                     category_orders={"Tier": au.TIER_NAMES, "Category": dp.FORMAT_ORDER},
                     title="Rank-tier comparison", text=comp["% of tier"].map(lambda v: f"{v:.1f}%"))
        fig.update_layout(xaxis_title="")
        show_chart(fig)
    st.dataframe(profile.round(2), hide_index=True, width="stretch")
    st.caption("The 9 'compilation' rows are counted as Album. Tiers overlap (Top 10 is inside Top 25).")


def render_duration():
    c1, c2, c3 = st.columns(3)
    with c1:
        fig = px.histogram(data.dropna(subset=["duration_min"]), x="duration_min", nbins=60, range_x=[0, 6],
                           title="Duration histogram (minutes)", color_discrete_sequence=["#2a78d6"])
        fig.add_vline(x=dp.SHORT_MAX_MIN, line_dash="dash")
        fig.add_vline(x=dp.LONG_MIN_MIN, line_dash="dash")
        fig.update_layout(xaxis_title="Duration (minutes; songs over 6 min not shown)", yaxis_title="Observations")
        show_chart(fig)
    with c2:
        dprofile = au.category_profile(data, "duration_group", bounds)
        fig = px.bar(dprofile, x="Category", y="Share (%)", color="Category", color_discrete_map=COLORS,
                     category_orders={"Category": dp.DURATION_ORDER}, title="Duration categories (share of observations)",
                     text=dprofile["Share (%)"].map(lambda v: f"{v:.1f}%"))
        fig.update_layout(showlegend=False, xaxis_title="")
        show_chart(fig)
    with c3:
        sample = data.dropna(subset=["duration_min", "popularity"])
        if len(sample) > 3000:
            sample = sample.sample(3000, random_state=0)       # keeps the chart fast; same sample every time
        fig = px.scatter(as_text(sample, ["explicit_category"]), x="duration_min", y="popularity", opacity=0.35,
                         color="explicit_category", color_discrete_map=COLORS, range_x=[0, 6],
                         title="Duration vs popularity (sample of up to 3,000)")
        fig.update_layout(xaxis_title="Duration (minutes)", yaxis_title="Popularity")
        show_chart(fig)
    rho_pop, _, n_pop = au.spearman(data["duration_min"], data["popularity"])
    rho_rank, _, n_rank = au.spearman(data["duration_min"], data["rank_score"])
    st.write(f"Spearman correlation of duration with popularity: **{fmt(rho_pop, '+.3f')}** (n = {n_pop:,}); "
             f"with rank score: **{fmt(rho_rank, '+.3f')}** (n = {n_rank:,}). Values near 0 mean no meaningful relationship.")
    st.dataframe(au.duration_band_table(data).round(2), hide_index=True, width="stretch")
    st.caption("Representation index = a band's share of the Top 10 / its share of all selected rows (above 1 = over-represented among the strongest positions).")


def render_album():
    c1, c2 = st.columns(2)
    sprofile = au.category_profile(data, "album_size_group", bounds)
    with c1:
        fig = px.bar(sprofile, x="Category", y="Observations", color="Category", color_discrete_map=COLORS,
                     category_orders={"Category": dp.ALBUM_SIZE_ORDER}, title="Album-size distribution",
                     text=sprofile["Share (%)"].map(lambda v: f"{v:.1f}%"))
        fig.update_layout(showlegend=False, xaxis_title="")
        show_chart(fig)
    with c2:
        by_size = data.assign(total_tracks=data["total_tracks"].astype(float)).groupby("total_tracks").agg(
            observations=("position", "size"), avg_popularity=("popularity", "mean")).reset_index()
        by_size = by_size[by_size["observations"] >= 30]
        fig = px.scatter(by_size, x="total_tracks", y="avg_popularity", size="observations", size_max=30,
                         title="Album size vs popularity (sizes with 30+ observations)",
                         color_discrete_sequence=["#2a78d6"])
        fig.update_layout(xaxis_title="Tracks in the release", yaxis_title="Average popularity")
        show_chart(fig)
    impact = au.album_size_impact(data)
    st.subheader("Album impact summary")
    m = st.columns(3)
    m[0].metric("Album Size Impact Index", fmt(impact["index"], "+.3f"))
    m[1].metric("Spearman: size vs popularity", fmt(impact["rho_popularity"], "+.3f"))
    m[2].metric("Spearman: size vs rank score", fmt(impact["rho_rank_score"], "+.3f"))
    st.write(f"**Reading:** {au.album_size_label(impact['index'])}.")
    st.dataframe(sprofile.round(2), hide_index=True, width="stretch")
    st.caption("This is an association, not proof of cause. The Small group is mostly 1-track singles, so part of the pattern is the "
               "single-vs-album difference; set 'Album type' to Album in the sidebar to see albums only.")


def render_tiers():
    tier_table = au.tier_summary(data)
    band_table = au.band_summary(data)
    st.subheader("Top 10 / Top 25 / Top 50 comparison")
    st.dataframe(tier_table, hide_index=True, width="stretch")
    chart_rows = tier_table[tier_table["Attribute"].isin(["Explicit share (%)", "Single share (%)", "Medium share (%)"])]
    long = chart_rows.melt(id_vars="Attribute", var_name="Tier", value_name="Share (%)")
    long["Share (%)"] = long["Share (%)"].astype(float)
    fig = px.bar(long, x="Attribute", y="Share (%)", color="Tier", barmode="group", title="Content shares by rank tier",
                 text=long["Share (%)"].map(lambda v: f"{v:.1f}"), color_discrete_sequence=["#1f5fae", "#5a9be0", "#a9c9f0"])
    fig.update_layout(xaxis_title="")
    show_chart(fig)
    st.subheader("Mutually exclusive bands (no row counted twice)")
    st.dataframe(band_table, hide_index=True, width="stretch")
    st.caption("Tiers overlap, so the bands give the cleaner comparison. If the Rank tier filter is Top 10 or Top 25, the larger tiers contain the same rows.")


def render_summary():
    st.subheader("Compliance summary for the selected data")
    st.markdown(au.compliance_summary(data, bounds))
    st.info(f"Filters applied: {start_date} to {end_date} | {rank_tier} | Explicit: {explicit_choice} | Album type: {format_choice}")
    st.download_button("Download KPI summary (CSV)", au.kpi_table(data, bounds).to_csv(index=False).encode("utf-8"),
                       file_name="france_top50_kpis.csv", mime="text/csv")
    st.caption("Findings are associations in one playlist. Rank and popularity are not streaming volumes, and the data has no genre, "
               "language, audience or promotion information.")


def render_quality():
    validation, summary = load_quality_tables()
    st.subheader("Data-quality summary")
    st.caption("Issue found in the raw file, the action taken and the rows affected (the raw file itself is never changed).")
    st.dataframe(summary, hide_index=True, width="stretch")
    with st.expander("All validation checks on the raw data"):
        st.dataframe(validation, hide_index=True, width="stretch")
    st.subheader("Statistical tests (full dataset, independent of the filters)")
    group_tests, correlations = full_data_tests()
    st.caption("Mann-Whitney U on song-day rows and on unique songs (robustness). Effect size r: below 0.1 negligible, "
               "0.1-0.3 small, 0.3-0.5 moderate, above 0.5 strong. Rank is tested through rank score (higher = better).")
    st.dataframe(group_tests.drop(columns=["p-value"]), hide_index=True, width="stretch")
    st.dataframe(correlations.drop(columns=["p-value"]).round(4), hide_index=True, width="stretch")


tabs = st.tabs(["Explicit Content", "Release Format", "Duration", "Album Structure", "Rank-Tier Profile",
                "Compliance Summary", "Data Quality & Statistics"])
for tab, render in zip(tabs, [render_explicit, render_format, render_duration, render_album, render_tiers,
                              render_summary, render_quality]):
    with tab:
        safe(render)
