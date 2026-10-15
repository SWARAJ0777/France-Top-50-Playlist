# France Top 50 Playlist - Audience Sensitivity, Content Compliance & Format Preference Analysis

## Project overview
An end-to-end data-science project (validation, cleaning, feature engineering, EDA, KPIs, statistics, interactive dashboard and reports) built on the Atlantic Recording Corporation France Top 50 playlist data. It is an analytics / business-intelligence project; no machine-learning model is used.

## Business objective
Understand how explicit vs clean content, Single vs Album format, song duration and album size relate to popularity and chart rank in France, and which content characteristics concentrate in the Top 10.

## Dataset description
`data/raw/Atlantic_France.csv` - 27,800 rows, 555 snapshot dates (2024-05-18 to 2025-11-27), 50 positions per date.

| Column | Meaning |
|---|---|
| date | playlist snapshot date (DD-MM-YYYY in the raw file) |
| position | chart rank, 1-50 |
| song, artist | title and artist |
| popularity | platform popularity score (0-100) - not streaming volume |
| duration_ms | song length in milliseconds |
| album_type | single / album / compilation |
| total_tracks | number of tracks in the release |
| is_explicit | explicit-content flag (TRUE/FALSE) |
| album_cover_url | artwork URL |

Data-quality issues found and fixed: a duplicated 01-03-2025 snapshot (50 rows removed), 73 zero popularity scores and 1 zero duration (set to missing), 1 blank title, 9 'compilation' rows (kept; grouped with Album), 4 dates without a snapshot (not imputed). Result: **27,750 rows = 555 dates x 50**. See `outputs/tables/02_cleaning_summary.csv`.

## Workflow
Inspect -> Validate -> Clean -> Engineer features -> EDA -> Analyse -> KPIs -> Statistical tests -> Dashboard -> Reports -> Quality check.

## Main analyses
Explicit-content sensitivity; Single vs Album preference; album-structure impact; duration preference; rank-tier content concentration; KPIs; Mann-Whitney U and Spearman tests (with a unique-song robustness check).

## Folder structure
```
france_top50_analysis/
|-- README.md
|-- requirements.txt
|-- app.py                       Streamlit dashboard
|-- .streamlit/config.toml       Streamlit settings (headless, no usage stats)
|-- data/
|   |-- raw/Atlantic_France.csv          original data (never modified)
|   `-- processed/france_top50_cleaned.csv
|-- notebooks/france_top50_analysis.ipynb
|-- src/
|   |-- data_processing.py       load, validate, clean, features
|   `-- analysis_utils.py        profiles, KPIs, indices, tests
|-- reports/
|   |-- research_report.md
|   `-- executive_summary.md
`-- outputs/
    |-- figures/                 9 saved charts (PNG)
    `-- tables/                  26 saved tables (CSV)
```

## Installation
Python 3.11 or newer is required (the pinned pandas 3 needs it).
```
python -m venv .venv
.venv\Scripts\activate          (Windows)   |   source .venv/bin/activate   (macOS / Linux)
pip install -r requirements.txt
```

## How to run the notebook
```
jupyter lab notebooks/france_top50_analysis.ipynb
```
(If JupyterLab is not installed: `pip install jupyterlab`, or simply open the notebook in VS Code.) Run all cells from top to bottom (in VS Code: open the notebook, pick the `.venv` kernel, *Run All*). The notebook rebuilds the cleaned data, the analysis tables (01-24) and all 9 figures; tables 25-26 are the recommendation tables.

To rebuild only the cleaned data and quality tables: `python src/data_processing.py`

## How to run Streamlit
```
streamlit run app.py
```
Sidebar filters: date range, rank tier (Top 10 / 25 / 50), explicit filter, album type, a Reset button and a CSV download of the filtered data. The page shows 8 KPI cards and tabs for Explicit Content, Release Format, Duration, Album Structure, Rank-Tier Profile, a dynamic Compliance Summary and Data Quality & Statistics.

Robustness: the app never writes files (works on read-only hosts); if the cleaned CSV is missing or invalid it rebuilds the data in memory from the raw file; every tab is isolated, so a problem in one section shows a message instead of crashing the page; empty filter results and half-picked date ranges are handled.

## Deploy on Streamlit Community Cloud
1. Push the whole project folder to a GitHub repository (keep `data/`, `src/`, `.streamlit/`, `app.py`, `requirements.txt`).
2. On share.streamlit.io choose **New app**, select the repository and set the main file to `app.py`.
3. Under *Advanced settings* choose Python 3.12 (3.11 or newer is required), then deploy. No secrets or extra configuration are needed.

## KPI definitions
| KPI | Definition |
|---|---|
| Explicit Content Share | Explicit rows / total rows x 100 |
| Clean Content Dominance Ratio | Clean rows / Explicit rows |
| Single vs Album Track Ratio | Single rows / Album-track rows |
| Average Song Duration | mean of duration_ms / 60,000 (minutes) |
| Album Size Impact Index | mean of Spearman rho(total_tracks, popularity) and rho(total_tracks, rank_score); -1 to +1; below 0 = bigger releases go with weaker tracks |
| Content Acceptance Score | 100 x (0.5 x normalised popularity + 0.5 x normalised rank score); project-specific, not an industry metric |

`rank_score = 51 - position` (higher = better). Details and limitations are in the notebook (section 14) and the research report.

## Technologies used
Python, pandas, NumPy, SciPy, Matplotlib, Seaborn, Plotly, Streamlit, Jupyter.

## Main findings
- 56.3% of observations are explicit (Clean Content Dominance Ratio 0.78); 62.4% of the Top 10 is explicit.
- Clean tracks have higher popularity (80.9 vs 73.6); explicit tracks have a slightly better chart position (25.0 vs 26.2), not robust at song level.
- Album tracks hold 52.9% of slots (Single-to-Album ratio 0.89), but singles perform better (popularity 80.8 vs 73.3).
- Average duration 3.09 min; 84.9% of Top 10 rows are 2.5-4 minutes.
- Album Size Impact Index -0.230 (larger releases go with weaker per-track results; -0.088 within albums only).
- Overall Content Acceptance Score 63.3.

## Limitations
Repeated song-day observations; popularity and rank are not streaming volumes; no genre, language, audience, marketing or release-date data; associations, not causation; one market, about 18 months; a few data-handling choices (listed in the research report).
