# Audience Sensitivity, Content Compliance & Format Preference Analysis of the France Top 50 Playlist

**Prepared for:** Atlantic Recording Corporation  |  **Data:** `Atlantic_France.csv`, 555 daily snapshots, 2024-05-18 to 2025-11-27
**Method:** Data -> Evidence -> Interpretation -> Business Recommendation. Every number below was calculated from the uploaded dataset by the project code (see the notebook and `outputs/tables`).

---

## 1. Executive Summary

- **Explicit content is the slight majority:** 56.3% of 27,750 playlist observations (clean 43.7%; Clean Content Dominance Ratio 0.78). It is 62.4% of the Top 10.
- **Clean vs explicit is a mixed picture:** clean tracks have higher popularity scores (80.9 vs 73.6), while explicit tracks sit slightly higher on the chart (average position 25.0 vs 26.2), a rank gap that is small and not robust at song level.
- **Format:** album tracks fill slightly more slots (52.9% vs 47.1%), but singles perform better, especially on popularity (80.8 vs 73.3).
- **Duration:** the strongest tracks cluster between 2.5 and 4 minutes (84.9% of Top 10 rows); songs over 4 minutes are under-represented in the Top 10.
- **Album structure:** larger releases go with weaker per-track results (Album Size Impact Index -0.230), largely because singles do well; within albums only the link is weak (-0.088).
- **Caution:** findings are associations in one playlist; they are not streaming volumes or causal effects.

## 2. Introduction

Atlantic Recording Corporation wants to know how content and release structure perform in the French market. This report analyses the France Top 50 playlist to answer six questions: explicit vs clean performance, Single vs Album preference, the most common duration among stronger tracks, the influence of album size, what is concentrated in the Top 10, and which content profile appears most accepted. The analysis is exploratory and descriptive; no predictive model was built.

## 3. Business Problem

The company needs evidence-based guidance for France-specific releases on: explicit-content strategy, availability of clean versions, playlist pitching, single-vs-album strategy, song length, album structure and localisation. The conclusions must follow the data, not assumptions about the French market.

## 4. Dataset

| Item | Value |
|---|---|
| File | `Atlantic_France.csv` (raw copy kept unchanged in `data/raw/`) |
| Raw size | 27,800 rows x 10 columns |
| Fields | date, position, song, artist, popularity, duration_ms, album_type, total_tracks, is_explicit, album_cover_url |
| Cleaned size | 27,750 rows (555 dates x 50 positions) |
| Songs / artists | 725 unique songs (title + artist) / 324 artists |
| One observation | one song on one snapshot date |

## 5. Data Preparation

**Data.** The raw data was loaded as text and validated before any change.

| Check | Result | Details |
|---|---|---|
| Rows x columns | 27,800 x 10 | date, position, song, artist, popularity, duration_ms, album_type, total_tracks, is_explicit, album_cover_url |
| Unparseable dates (format DD-MM-YYYY) | 0 |  |
| Date range | 2024-05-18 to 2025-11-27 | 555 unique dates |
| Calendar dates with no snapshot | 4 | 2025-03-14, 2025-03-25, 2025-07-11, 2025-08-13 |
| Dates that do not have exactly 50 rows | 1 | 01-03-2025: 100 rows |
| Non-numeric positions | 0 |  |
| Positions outside 1-50 | 0 |  |
| Duplicate ranks within the same date (rows beyond the first) | 50 |  |
| Exact duplicate rows | 19 |  |
| Missing / blank values in 'song' | 1 |  |
| Total missing / blank cells | 1 |  |
| Non-numeric values in 'popularity' | 0 |  |
| Non-numeric values in 'duration_ms' | 0 |  |
| Non-numeric values in 'total_tracks' | 0 |  |
| Popularity outside 1-100 (0 = score not available) | 73 | min=0, max=100 |
| Duration <= 0 ms | 1 |  |
| Duration < 60 s (reviewed - plausible intros/interludes) | 7 |  |
| total_tracks < 1 | 0 | min=1, max=119 |
| Distinct album_type labels | 3 | album=14,695, single=13,096, compilation=9 |
| Distinct is_explicit labels | 2 | TRUE=15,640, FALSE=12,160 |
| Text with leading/trailing spaces (song, artist) | 0 |  |
| Releases labelled 'single' with more than 1 track (EP-style, kept as labelled) | 1761 |  |

**Cleaning summary.**

| Issue | Action Taken | Rows Affected |
|---|---|---|
| Leading/trailing spaces in song or artist | Stripped whitespace | 0 |
| Dates stored as text (DD-MM-YYYY) | Converted to datetime (saved as YYYY-MM-DD) | 27,800 |
| Unparseable dates | Drop rows (none found) | 0 |
| Non-numeric values in numeric columns | Converted to numbers; invalid -> missing | 0 |
| Lower-case album_type labels (single / album / compilation) | Standardised to Title Case | 27,800 |
| Unrecognised album_type labels | Set to missing (none found) | 0 |
| 'Compilation' releases (neither Single nor Album) | Kept as 'Compilation' in album_type; grouped with Album in release_format | 9 |
| is_explicit stored as text (TRUE/FALSE) | Converted to boolean (True = Explicit, False = Clean) | 27,800 |
| Unrecognised is_explicit labels | Set to missing (none found) | 0 |
| Blank song title | Filled with 'Unknown Song'; row kept for rank and format analysis | 1 |
| Popularity = 0 (score not available) or outside 1-100 | Set to missing; row kept, excluded from popularity statistics only | 73 |
| Duration <= 0 ms | Set to missing; row kept, excluded from duration statistics only | 1 |
| total_tracks < 1 or missing | Set to missing (none found) | 0 |
| Very short tracks (< 60 seconds) | Reviewed and retained (genuine intros/interludes) | 7 |
| Position outside 1-50 | Drop rows (none found) | 0 |
| Exact duplicate rows | Dropped (kept first occurrence) | 19 |
| Duplicate ranks on one date: a second, slightly different snapshot for 01-03-2025 | Kept the first snapshot (one row per date and rank); dropped the later one | 31 |
| Calendar dates with no snapshot | Not imputed; analysed as observed (stated as a limitation) | 4 |

**Evidence.** **What the checks found.** The raw file has 27,800 rows and 10 columns covering 555 snapshot dates (2024-05-18 to 2025-11-27). The data is mostly clean, but not perfectly: (1) **01-03-2025 holds two snapshots (100 rows)** with duplicate ranks - 19 rows are exact copies and the rest differ slightly; (2) **73 rows have popularity = 0** (the score had not been calculated yet, e.g. a big release day) and **1 row has a 0 ms duration and a blank title**; (3) **9 rows are labelled 'compilation'**, which is neither Single nor Album; (4) **4 calendar dates have no snapshot** (2025-03-14, 2025-03-25, 2025-07-11, 2025-08-13). Positions are all within 1-50, there are no unparseable dates or non-numeric numbers, and the labels for `is_explicit` are consistent (TRUE/FALSE).

**Interpretation.** **Result.** 50 duplicate rows were removed (19 exact copies + 31 conflicting rows from the second 01-03-2025 snapshot), leaving **27,750 rows = 555 dates x 50 positions**. Invalid popularity (73) and duration (1) values were set to missing instead of dropping the rows, so those songs still count for rank, format and explicit-content analysis. The raw file was not changed.

**Features created.** `duration_min`; `duration_group` (Short < 2.5, Medium 2.5-4, Long > 4 min); 0.5-minute `duration_band`; `rank_score = 51 - position`; Top 10 / Top 25 flags; `rank_band` (1-10, 11-25, 26-50); `explicit_category`; `release_format` (Single / Album); `album_size_group` (Small 1-5, Medium 6-12, Large 13+). **Result.** All features were created and the cleaned file was saved to `data/processed/france_top50_cleaned.csv` (27,750 rows). The duration thresholds (Short < 2.5 min, Medium 2.5-4 min, Long > 4 min) were kept: they split the data into 12.9% / 81.7% / 5.4% - uneven, but the median (3.00 min) sits inside the Medium band and the dataset gives no strong reason to move the boundaries.

## 6. Exploratory Data Analysis

| Metric | Value |
|---|---|
| Total observations (song-day rows) | 27,750 |
| Unique dates | 555 |
| Date range | 2024-05-18 to 2025-11-27 |
| Unique songs (title + artist) | 725 |
| Unique artists | 324 |
| Average popularity | 76.84 |
| Median popularity | 75.0 |
| Average duration (min) | 3.09 |
| Median duration (min) | 3.00 |
| Explicit share (%) | 56.3 |
| Clean share (%) | 43.7 |
| Single share (%) | 47.1 |
| Album-track share (%) | 52.9 |
| Average album size (tracks) | 9.00 |
| Median album size (tracks) | 10.0 |

![Overview](../outputs/figures/fig01_eda_overview.png)

**Interpretation.** **Interpretation.** The playlist holds 725 different songs by 324 artists across 555 days, so the same song appears on many days (on average 38.3 song-day rows per song). 56.3% of rows are explicit, 47.1% are singles, and the average song lasts 3.09 minutes. Popularity is concentrated between about 70 and 85 (mean 76.8, median 75.0). Because songs repeat across days, the 27,750 rows are **not** 27,750 independent observations - this matters for the statistics (section 15).

## 7. Explicit Content Analysis

**Data -> Evidence.**

| Category | Observations | Share (%) | Avg popularity | Median popularity | Avg position | Avg rank score | Top 10 rate (%) | Top 25 rate (%) | Top 10 lift (x) | Content Acceptance Score |
|---|---|---|---|---|---|---|---|---|---|---|
| Explicit | 15,614 | 56.27 | 73.65 | 74.00 | 24.99 | 26.01 | 22.19 | 51.27 | 1.11 | 62.21 |
| Clean | 12,136 | 43.73 | 80.93 | 81.00 | 26.16 | 24.84 | 17.18 | 48.37 | 0.86 | 64.70 |

Rank-band distribution (% of each group's rows; equal performance would be 20 / 30 / 50):

| Category | Band 1-10 (%) | Band 11-25 (%) | Band 26-50 (%) |
|---|---|---|---|
| Explicit | 22.19 | 29.08 | 48.73 |
| Clean | 17.18 | 31.19 | 51.63 |

![Explicit vs Clean](../outputs/figures/fig02_explicit_vs_clean.png)
![Explicit share over time](../outputs/figures/fig03_explicit_share_over_time.png)

**Interpretation - three separate questions.**

- **Representation:** explicit rows are the majority (56.3% vs 43.7% clean; Clean Content Dominance Ratio = 0.78, i.e. clean is *not* dominant). Explicit also makes up 62.4% of the Top 10.
- **Popularity:** clean tracks score higher (mean 80.9 vs 73.6; median 81 vs 74).
- **Chart rank:** explicit tracks sit slightly higher (average position 25.0 vs 26.2; 22.2% of explicit rows are in the Top 10 vs 17.2% of clean rows).

So neither label wins on every measure. The explicit share is also not stable over time: it ranged from 45.3% (2025-07) to 67.0% (2024-10) across full months.

**Business implication.** Explicit content is not a barrier to French Top 50 presence. A clean version may still be a useful complement given the higher popularity of clean tracks, but this data cannot prove it would help a given song.

## 8. Release Format Analysis

| Category | Observations | Share (%) | Avg popularity | Median popularity | Avg position | Avg rank score | Top 10 rate (%) | Top 25 rate (%) | Top 10 lift (x) | Content Acceptance Score |
|---|---|---|---|---|---|---|---|---|---|---|
| Single | 13,069 | 47.10 | 80.80 | 78.00 | 24.12 | 26.88 | 21.55 | 54.12 | 1.08 | 66.71 |
| Album | 14,681 | 52.90 | 73.31 | 73.00 | 26.73 | 24.27 | 18.62 | 46.33 | 0.93 | 60.26 |

| Format | Unique songs | Average days on chart per song |
|---|---|---|
| Single | 228 | 56.1 |
| Album | 497 | 30.1 |

![Single vs Album](../outputs/figures/fig04_single_vs_album.png)

**Interpretation.** Album tracks hold a modest majority of chart slots (52.9% vs 47.1%; Single-to-Album ratio 0.89) and a clear majority of distinct songs (497 album-track songs vs 228 single songs, using each song's most frequent format). However, singles stay on the chart much longer per song (average 56.1 days vs 30.1) and perform better: higher popularity (80.8 vs 73.3), a better average position (24.1 vs 26.7) and a higher Top 10 rate (21.6% vs 18.6%). **Conclusion:** slightly stronger album-track *representation*, but stronger single *performance*.

**Business implication.** Lead with singles or focus tracks when popularity and Top 10 entry are the goal; album tracks still occupy more than half of all slots, so albums remain viable.

## 9. Album Structure Analysis

| Category | Observations | Share (%) | Avg popularity | Median popularity | Avg position | Avg rank score | Top 10 rate (%) | Top 25 rate (%) | Top 10 lift (x) | Content Acceptance Score |
|---|---|---|---|---|---|---|---|---|---|---|
| Small (1-5) | 12,536 | 45.17 | 81.06 | 79.00 | 24.01 | 26.99 | 21.97 | 54.35 | 1.10 | 66.95 |
| Medium (6-12) | 4,143 | 14.93 | 75.24 | 74.00 | 25.59 | 25.41 | 18.56 | 51.00 | 0.93 | 62.41 |
| Large (13+) | 11,071 | 39.90 | 72.65 | 73.00 | 27.15 | 23.85 | 18.31 | 44.70 | 0.92 | 59.50 |

| Data | rho (size vs popularity) | rho (size vs rank score) | Album Size Impact Index |
|---|---|---|---|
| All observations | -0.349 | -0.111 | -0.230 |
| Album-type releases only | -0.111 | -0.064 | -0.088 |

![Album size](../outputs/figures/fig05_album_size.png)

**Interpretation.** Larger releases are associated with weaker per-track results: Spearman rho with popularity = -0.349, with rank score = -0.111; the Album Size Impact Index is **-0.230** (Small association: larger releases go with WEAKER track performance (dilution)). By size group, the Content Acceptance Score falls from 66.9 (Small) to 62.4 (Medium) and 59.5 (Large), and the Top 10 rate from 22.0% to 18.3%. **Important caveat:** the Small group is mostly singles (1-track releases), so much of this is the single-vs-album gap. Looking at album-type releases only, the index shrinks to -0.088 (popularity rho -0.111, rank-score rho -0.064) - a weak relationship. This is an association; it does not prove that a bigger album *causes* weaker tracks.

**Business implication.** For album projects, concentrate promotion on a few focus tracks. Do not read this as proof that adding tracks harms performance.

## 10. Duration Analysis

| Metric | Minutes |
|---|---|
| Mean | 3.09 |
| Median | 3.00 |
| Std. deviation | 0.54 |
| Minimum | 0.67 |
| Maximum | 9.12 |
| 25th percentile | 2.76 |
| 75th percentile | 3.46 |

| Category | Observations | Share (%) | Avg popularity | Median popularity | Avg position | Avg rank score | Top 10 rate (%) | Top 25 rate (%) | Top 10 lift (x) | Content Acceptance Score |
|---|---|---|---|---|---|---|---|---|---|---|
| Short | 3,576 | 12.89 | 77.20 | 74.00 | 26.12 | 24.88 | 17.73 | 48.77 | 0.89 | 62.85 |
| Medium | 22,673 | 81.70 | 76.67 | 75.00 | 25.14 | 25.86 | 20.77 | 50.95 | 1.04 | 63.58 |
| Long | 1,500 | 5.41 | 78.51 | 76.00 | 29.41 | 21.59 | 13.67 | 38.53 | 0.68 | 60.16 |

| Duration band (min) | Observations | Share of all rows (%) | Share of Top 10 (%) | Top 10 rate (%) | Representation index | Avg popularity | Avg rank score |
|---|---|---|---|---|---|---|---|
| <2.0 | 179 | 0.65 | 0.50 | 15.64 | 0.78 | 77.82 | 23.75 |
| 2.0-2.5 | 3,397 | 12.24 | 10.92 | 17.84 | 0.89 | 77.17 | 24.94 |
| 2.5-3.0 | 10,265 | 36.99 | 36.22 | 19.58 | 0.98 | 75.19 | 25.54 |
| 3.0-3.5 | 7,381 | 26.60 | 29.25 | 21.99 | 1.10 | 76.98 | 25.67 |
| 3.5-4.0 | 5,027 | 18.12 | 19.41 | 21.42 | 1.07 | 79.27 | 26.77 |
| 4.0-4.5 | 1,200 | 4.32 | 2.92 | 13.50 | 0.68 | 80.54 | 21.30 |
| 4.5+ | 300 | 1.08 | 0.77 | 14.33 | 0.72 | 70.29 | 22.78 |

![Duration](../outputs/figures/fig06_duration.png)

**Interpretation.** Songs last 3.09 minutes on average (median 3.00, range 0.67-9.12). Medium songs (2.5-4 min) make up 81.7% of all rows and 84.9% of Top 10 rows; Long songs (> 4 min) are under-represented in the Top 10 (3.7% vs 5.4% overall). The largest single share of the Top 10 is the 2.5-3.0 min band (36.2%), while the bands most over-represented relative to their overall presence are 3.0-3.5 and 3.5-4.0 min (representation index 1.10 and 1.07). Duration has essentially no monotonic link with rank score (rho = -0.008), so the data supports a *preferred range* (about 2.5-4 minutes), not an exact ideal length.

**Business implication.** Aim for roughly 2.5-4 minutes; tracks over 4 minutes are under-represented in the Top 10.

## 11. Rank-Tier Analysis

Cumulative tiers (Top 10 is inside Top 25, which is inside Top 50):

| Attribute | Top 10 | Top 25 | Top 50 |
|---|---|---|---|
| Observations | 5,550 | 13,875 | 27,750 |
| Explicit share (%) | 62.43 | 57.69 | 56.27 |
| Clean share (%) | 37.57 | 42.31 | 43.73 |
| Single share (%) | 50.76 | 50.98 | 47.10 |
| Album-track share (%) | 49.24 | 49.02 | 52.90 |
| Avg popularity | 78.50 | 78.22 | 76.84 |
| Avg duration (min) | 3.09 | 3.08 | 3.09 |
| Short share (%) | 11.43 | 12.57 | 12.89 |
| Medium share (%) | 84.88 | 83.26 | 81.71 |
| Long share (%) | 3.69 | 4.17 | 5.41 |
| Avg album size (tracks) | 8.04 | 8.24 | 9.00 |

Mutually exclusive bands:

| Attribute | 1-10 | 11-25 | 26-50 |
|---|---|---|---|
| Observations | 5,550 | 8,325 | 13,875 |
| Explicit share (%) | 62.43 | 54.53 | 54.84 |
| Clean share (%) | 37.57 | 45.47 | 45.16 |
| Single share (%) | 50.76 | 51.12 | 43.21 |
| Album-track share (%) | 49.24 | 48.88 | 56.79 |
| Avg popularity | 78.50 | 78.03 | 75.47 |
| Avg duration (min) | 3.09 | 3.08 | 3.10 |
| Short share (%) | 11.43 | 13.33 | 13.20 |
| Medium share (%) | 84.88 | 82.19 | 80.15 |
| Long share (%) | 3.69 | 4.48 | 6.65 |
| Avg album size (tracks) | 8.04 | 8.37 | 9.76 |

![Rank bands](../outputs/figures/fig07_rank_band_profile.png)

**Interpretation.** The Top 10 differs from the rest of the chart in a few ways: it is more explicit (62.4% in positions 1-10 vs 54.5% and 54.8% in the other bands), more single-heavy (50.8% vs 43.2% in positions 26-50), more popular (average 78.5 vs 75.5) and built from smaller releases (average 8.0 vs 9.8 tracks). Average duration is practically identical across bands (3.09 vs 3.10 min). Cumulative tiers (Top 10 inside Top 25 inside Top 50) are shown for reference; the mutually exclusive bands avoid double counting and give the cleaner comparison.

## 12. KPIs

| KPI | Value | Definition |
|---|---|---|
| Total observations | 27,750 | Song-day rows (one row = one song on one date) |
| Explicit Content Share (%) | 56.267 | Explicit rows / total rows x 100 |
| Clean Content Dominance Ratio | 0.777 | Clean rows / Explicit rows |
| Single vs Album Track Ratio | 0.890 | Single rows / Album-track rows |
| Average Song Duration (min) | 3.091 | Mean of duration_ms / 60,000 |
| Average Popularity | 76.840 | Mean popularity (valid scores only) |
| Album Size Impact Index | -0.230 | Mean of Spearman rho(total_tracks, popularity) and rho(total_tracks, rank_score); -1 to +1 |
| Content Acceptance Score | 63.303 | 100 x (0.5 x normalised popularity + 0.5 x normalised rank score) |

Content Acceptance Score by group:

| Comparison | Category | Avg popularity | Avg rank score | Content Acceptance Score |
|---|---|---|---|---|
| Explicit vs Clean | Explicit | 73.65 | 26.01 | 62.21 |
| Explicit vs Clean | Clean | 80.93 | 24.84 | 64.70 |
| Single vs Album | Single | 80.80 | 26.88 | 66.71 |
| Single vs Album | Album | 73.31 | 24.27 | 60.26 |
| Duration group | Short | 77.20 | 24.88 | 62.85 |
| Duration group | Medium | 76.67 | 25.86 | 63.58 |
| Duration group | Long | 78.51 | 21.59 | 60.16 |
| Album-size group | Small (1-5) | 81.06 | 26.99 | 66.95 |
| Album-size group | Medium (6-12) | 75.24 | 25.41 | 62.41 |
| Album-size group | Large (13+) | 72.65 | 23.85 | 59.50 |

![Content Acceptance Score](../outputs/figures/fig08_content_acceptance_score.png)

**Interpretation.** Explicit content is 56.3% of rows; the Clean Content Dominance Ratio of 0.78 means there are fewer clean than explicit rows. The Single vs Album Track Ratio is 0.89. The average song lasts 3.09 minutes. The overall Content Acceptance Score is 63.3; it is a *relative* index, so compare groups with each other rather than reading 63 as 'good' or 'bad'. By group: Clean 64.7 vs Explicit 62.2; Single 66.7 vs Album 60.3; Medium duration 63.6 (best) vs Long 60.2; Small releases 66.9 vs Large 59.5. Clean scores above Explicit because of its higher popularity, even though explicit tracks hold slightly better chart positions - the score blends the two.

**Album Size Impact Index**

- *Formula:* `Index = (rho(total_tracks, popularity) + rho(total_tracks, rank_score)) / 2`, where rho is the Spearman rank correlation. Range -1 to +1.
- *Interpretation:* above 0 = bigger releases go with stronger tracks; below 0 = bigger releases go with weaker tracks ('dilution'); about 0 = no real relationship. Size labels follow the usual convention: |index| < 0.1 negligible, 0.1-0.3 small, 0.3-0.5 moderate, > 0.5 strong.
- *Limitations:* it is a correlation, not a cause; singles (1 track) dominate the low end, so it mixes 'single vs album' with 'album size' (see the albums-only check); popularity is a platform score, not streams; repeated daily rows of the same song are treated as separate observations.

**Content Acceptance Score** (project-specific index, *not* an industry metric)

- *Formula:* `CAS = 100 x (0.5 x Normalised Popularity + 0.5 x Normalised Rank Score)`, with Normalised Popularity = (mean popularity - 1) / (100 - 1) and Normalised Rank Score = (mean rank score - 1) / 49. The popularity minimum and maximum come from the full cleaned dataset, so scores stay comparable across filters.
- *Interpretation:* higher = the group is both more popular and higher on the chart. A group with average popularity and an average chart position scores about 63 here.
- *Limitations:* the 50/50 weighting is a modelling choice; the score has no significance test of its own; it inherits every limitation of popularity and rank.

## 13. Statistical Analysis

Distributions are not normal (D'Agostino test p < 0.001 for popularity, rank score and duration), so Mann-Whitney U and Spearman correlation were used instead of t-tests. Rank is tested through `rank_score` (higher = better). Effect size r is the rank-biserial correlation (< 0.1 negligible, 0.1-0.3 small, 0.3-0.5 moderate, > 0.5 strong). 'Group A / B' are Explicit / Clean or Single / Album.

**Song-day rows (as requested):**

| Question | Test statistic (U) | p-value (display) | Effect size (r) | n (group A / B) | Statistical conclusion | Business interpretation |
|---|---|---|---|---|---|---|
| Is popularity different for Explicit vs Clean? | 57,450,697.50 | < 0.001 | -0.39 | 15,546 / 12,131 | Significant difference (p < 0.001); effect size moderate (r = -0.39) | Clean tracks tend to have higher popularity: median 74.0 (Explicit) vs 81.0 (Clean). The gap is moderate in practical terms. |
| Is chart rank different for Explicit vs Clean? (rank score; higher = better) | 99,158,557.00 | < 0.001 | 0.05 | 15,614 / 12,136 | Significant difference (p < 0.001); effect size negligible (r = +0.05) | Explicit tracks tend to have a better (higher) rank score: median 26.0 (Explicit) vs 25.0 (Clean). The gap is negligible in practical terms. |
| Is popularity different for Single vs Album? | 134,251,970.00 | < 0.001 | 0.41 | 13,060 / 14,617 | Significant difference (p < 0.001); effect size moderate (r = +0.41) | Single tracks tend to have higher popularity: median 78.0 (Single) vs 73.0 (Album). The gap is moderate in practical terms. |
| Is chart rank different for Single vs Album? (rank score; higher = better) | 105,950,467.00 | < 0.001 | 0.10 | 13,069 / 14,681 | Significant difference (p < 0.001); effect size small (r = +0.10) | Single tracks tend to have a better (higher) rank score: median 27.0 (Single) vs 23.0 (Album). The gap is small in practical terms. |

**Unique songs (robustness check - songs repeat across days):**

| Question | Test statistic (U) | p-value (display) | Effect size (r) | n (group A / B) | Statistical conclusion | Business interpretation |
|---|---|---|---|---|---|---|
| Is popularity different for Explicit vs Clean? | 29,071.00 | < 0.001 | -0.48 | 458 / 246 | Significant difference (p < 0.001); effect size moderate (r = -0.48) | Clean tracks tend to have higher popularity: median 65.7 (Explicit) vs 75.3 (Clean). The gap is moderate in practical terms. |
| Is chart rank different for Explicit vs Clean? (rank score; higher = better) | 64,373.00 | 0.051 | 0.09 | 477 / 248 | No significant difference (p = 0.051); effect size negligible (r = +0.09) | No reliable difference between Explicit and Clean on rank score (medians 18.6 vs 15.9). |
| Is popularity different for Single vs Album? | 70,752.50 | < 0.001 | 0.31 | 225 / 479 | Significant difference (p < 0.001); effect size moderate (r = +0.31) | Single tracks tend to have higher popularity: median 73.1 (Single) vs 66.9 (Album). The gap is moderate in practical terms. |
| Is chart rank different for Single vs Album? (rank score; higher = better) | 59,037.50 | 0.364 | 0.04 | 228 / 497 | No significant difference (p = 0.364); effect size negligible (r = +0.04) | No reliable difference between Single and Album on rank score (medians 19.0 vs 17.3). |

**Spearman correlations (all observations):**

| Relationship | Spearman rho | p-value (display) | n | Strength |
|---|---|---|---|---|
| Popularity vs rank score | 0.18 | < 0.001 | 27,677 | small |
| Duration (min) vs popularity | 0.10 | < 0.001 | 27,677 | negligible |
| Duration (min) vs rank score | -0.01 | 0.195 | 27,749 | negligible |
| Album size vs popularity | -0.35 | < 0.001 | 27,677 | moderate |
| Album size vs rank score | -0.11 | < 0.001 | 27,750 | small |
| Album size vs duration (min) | 0.12 | < 0.001 | 27,749 | small |

**Spearman correlations (album-type releases only):**

| Relationship | Spearman rho | p-value (display) | n | Strength |
|---|---|---|---|---|
| Popularity vs rank score | 0.12 | < 0.001 | 14,617 | small |
| Duration (min) vs popularity | 0.20 | < 0.001 | 14,617 | small |
| Duration (min) vs rank score | -0.06 | < 0.001 | 14,681 | negligible |
| Album size vs popularity | -0.11 | < 0.001 | 14,617 | small |
| Album size vs rank score | -0.06 | < 0.001 | 14,681 | negligible |
| Album size vs duration (min) | 0.02 | 0.017 | 14,681 | negligible |

![Spearman heatmap](../outputs/figures/fig09_spearman_heatmap.png)

**Interpretation.** With ~27,750 rows almost any difference becomes 'statistically significant', so the **effect size (r)** matters more than the p-value, and because songs repeat day after day the row-level p-values are overstated. The unique-track rows are the more conservative check.

- **Explicit vs Clean popularity:** robust. Clean is higher at both levels (r = -0.39 rows, -0.48 tracks; negative = explicit lower).
- **Explicit vs Clean rank:** significant at row level but negligible (r = +0.05) and **not** significant at track level (p = 0.051). Treat as a slight, not robust, edge.
- **Single vs Album popularity:** robust. Singles are higher at both levels (r = +0.41 rows, +0.31 tracks).
- **Single vs Album rank:** small at row level (r = +0.10) and **not** significant at track level (p = 0.364). Modest, not robust.
- **Spearman:** album size vs popularity rho = -0.349 (moderate negative); album size vs rank score rho = -0.111 (small negative); duration vs rank score rho = -0.008 (negligible); popularity vs rank score rho = 0.179 (small positive).

## 14. Key Findings - Answers to the Ten Final Questions


### Q1. What percentage of observations are explicit?
- **Result:** 56.3% (15,614 of 27,750 rows); 43.7% are clean.
- **Evidence:** Clean Content Dominance Ratio = 0.78. Explicit share of the Top 10 = 62.4%. Across full calendar months the explicit share moved between 45.3% (2025-07) and 67.0% (2024-10).
- **Interpretation:** explicit tracks are a slim majority, but the share is not constant over time.
- **Recommendation:** do not treat explicit content as an obstacle to French Top 50 presence.

### Q2. Do Clean or Explicit tracks perform better?
- **Result:** neither wins on every measure. Clean is higher on **popularity**; explicit is slightly higher on **chart position**.
- **Evidence:** average popularity 80.9 (clean) vs 73.6 (explicit), robust at row and track level. Average position 25.0 (explicit) vs 26.2 (clean); Top 10 rate 22.2% vs 17.2%, but the rank effect is negligible (r = +0.05) and not significant at track level. Content Acceptance Score: Clean 64.7 vs Explicit 62.2.
- **Interpretation:** representation (explicit is more common), popularity (clean is higher) and rank (explicit marginally higher) point in different directions, so the data does not show one label to be 'preferred'.
- **Recommendation:** decide explicit vs clean on artistic and commercial grounds; consider a clean version as a low-cost complement, not a replacement.

### Q3. Are Singles or Album tracks more represented?
- **Result:** slightly more album tracks - 52.9% of rows vs 47.1% singles.
- **Evidence:** Single-to-Album ratio 0.89; 497 album-track songs vs 228 single songs (68.6% album); but singles last longer on the chart per song (56.1 vs 30.1 days).
- **Interpretation:** a modest album-track edge in chart slots, not a strong one; singles are present for fewer songs but for longer.
- **Recommendation:** do not assume the French chart is a singles-only market; both routes reach the Top 50.

### Q4. Which release format performs better?
- **Result:** Singles.
- **Evidence:** average popularity 80.8 vs 73.3 (robust at both levels, r = +0.41 rows / +0.31 tracks); average position 24.1 vs 26.7; Top 10 rate 21.6% vs 18.6%; Content Acceptance Score 66.7 vs 60.3.
- **Interpretation:** the popularity advantage is solid; the rank advantage is modest and not significant at track level (p = 0.364).
- **Recommendation:** lead with singles or focus tracks when the goal is popularity and Top 10 entry.

### Q5. Which duration range is most represented among stronger tracks?
- **Result:** 2.5-4.0 minutes (Medium).
- **Evidence:** 84.9% of Top 10 rows are Medium vs 81.7% overall; Long songs are 3.7% of the Top 10 vs 5.4% overall. Largest single band in the Top 10: 2.5-3.0 min (36.2%); most over-represented: 3.0-3.5 and 3.5-4.0 min.
- **Interpretation:** a preferred range, not an exact ideal; duration is practically unrelated to rank score (rho = -0.008).
- **Recommendation:** aim for roughly 2.5-4 minutes; avoid assuming longer tracks help.

### Q6. Do larger albums help or weaken individual track performance?
- **Result:** larger releases are associated with *weaker* per-track results (Album Size Impact Index -0.230), mostly because singles do well.
- **Evidence:** Content Acceptance Score Small 66.9 > Medium 62.4 > Large 59.5. Within album-type releases only, the index is -0.088 (weak).
- **Interpretation:** a dilution-like pattern exists but is modest once singles are set aside; correlation does not prove causation.
- **Recommendation:** for album projects, concentrate promotion on a few focus tracks.

### Q7. Which attributes are concentrated in the Top 10?
- **Result:** explicit content, singles, higher popularity and smaller releases.
- **Evidence:** explicit 62.4% (vs 56.3% overall); singles 50.8% (vs 47.1%); average popularity 78.5 (vs 76.8); average album size 8.0 tracks (vs 9.0); Medium duration 84.9% (vs 81.7%). Average duration is the same (3.09 min).
- **Interpretation:** the Top 10 leans explicit, single-led and medium-length, but the differences are moderate rather than dramatic.
- **Recommendation:** use these as pitching guidelines, not rules.

### Q8. What is the observed preferred content profile?
- **Result:** a medium-length (2.5-4 min) track from a small release (single or up to 5 tracks). The explicit/clean label does not separate winners clearly.
- **Evidence:** highest Content Acceptance Scores - Medium duration 63.6, Single 66.7, Small release 66.9. For explicit vs clean the score favours Clean (64.7 vs 62.2) because of popularity, while explicit leads on Top 10 presence. The average Top 10 row is 62.4% explicit, 50.8% single, 84.9% medium length.
- **Interpretation:** descriptive only; the data shows what charts, not why.
- **Recommendation:** use as a starting profile for France-specific releases.

### Q9. What should Atlantic Recording Corporation consider for France-specific releases?
- **Result:** keep explicit content available, lead with singles, target 2.5-4 minutes, and keep album promotion focused.
- **Evidence:** see Q1-Q8. This dataset covers only the France playlist, so it cannot show what is *different* about France.
- **Interpretation:** the points above describe French chart behaviour; whether they differ from other markets needs a side-by-side comparison with other countries' playlists.
- **Recommendation:** run the same analysis on other markets' Top 50 data, and add genre, language and streaming data before finalising localisation decisions.

### Q10. What conclusions cannot be made from this dataset?
- **Result:** several tempting conclusions are not supported.
- **Evidence and limits:**
  - *Causation* - explicit content, format, length or album size cause chart success. Only associations are measured.
  - *Audience preference or regulation* - the data has no listener, demographic, skip-rate, streaming-volume or legal/regulatory information; the 'compliance' angle here is only the explicit flag.
  - *Streaming volume* - rank and popularity are not play counts.
  - *Genre or language effects* - not in the data. For example, the higher popularity of clean tracks may reflect which songs are clean, not the label itself.
  - *Stability over time* - the explicit share swings by more than 20 percentage points between months.
  - *Independent observations* - the same song appears on many days, which inflates significance.
- **Recommendation:** treat findings as a French-chart baseline and collect the missing data listed in the report.


## 15. Recommendations

### High confidence (strongly supported by the dataset)
- **Explicit-content strategy** - Do not remove or soften explicit content to qualify for the French Top 50. *(56.3% of rows and 62.4% of the Top 10 are explicit; explicit Top 10 rate 22.2% vs 17.2% clean.)*
- **Song duration** - Aim for roughly 2.5-4 minutes; treat tracks over 4 minutes as a risk to Top 10 presence. *(Medium = 84.9% of Top 10 vs 81.7% overall; Long = 3.7% vs 5.4%.)*
- **Single vs Album release strategy** - Lead with singles or clear focus tracks when popularity and Top 10 entry are the goal; albums remain viable. *(Singles: popularity 80.8 vs 73.3 (robust at track level); rank advantage modest and not robust.)*

### Moderate confidence (supported by patterns, more evidence needed)
- **Availability of clean versions** - Keep a clean version available as a low-cost complement to an explicit release. *(Clean rows have higher popularity (80.9 vs 73.6) but not better chart positions; the data cannot show whether adding a clean version helps the same song.)*
- **Playlist pitching** - Pitch both explicit and clean material; emphasise single-led, medium-length tracks for the top positions. *(Top 10 is 50.8% single and 84.9% medium length; differences are moderate.)*
- **Album structure** - For album projects, concentrate promotion on a few focus tracks rather than the whole tracklist. *(Album Size Impact Index -0.230 overall, -0.088 within albums only (weak); correlation, not causation.)*

### Further data needed
- **France-specific localisation** - Use this analysis as the French baseline and compare it with other markets before localising. *(Only the France playlist is analysed; genre, language and artist origin are not in the data.)*

| Data needed | Why it matters |
|---|---|
| Streaming counts | Rank and popularity are not volumes; counts would show real consumption. |
| Skip rate and completion rate | Would show whether long or explicit tracks lose listeners. |
| Genre and language | Likely confounds explicit status, duration and popularity. |
| Listener demographics | Needed to speak about audience sensitivity or acceptance. |
| Marketing spend | Chart success may reflect promotion, not content. |
| Release timing | Release day and season affect chart entry. |
| Artist-level popularity | A few very popular artists may drive results. |
| Other markets' playlists | Needed to say what is specific to France. |

Full table: `outputs/tables/25_final_recommendations.csv`.

## 16. Limitations

1. **Repeated observations.** 27,750 rows come from only 725 songs (38.3 days per song on average), so rows are not independent and row-level p-values are overstated. Unique-song tests are reported as a check.
2. **Popularity is a platform score**, not streams, and rank is a playlist position, not volume. Neither measures listener demand.
3. **No genre, language, artist-origin, audience, marketing or release-date data.** For example, the higher popularity of clean songs may reflect which songs are clean (for instance international hits) rather than the label itself.
4. **Compliance angle is limited** to the explicit flag; no regulatory, age-rating or broadcast-rule data is available.
5. **Time instability.** The explicit share varied between 45.3% and 67.0% across full months, so any single average hides change.
6. **Data handling choices:** one duplicated snapshot (01-03-2025) was reduced to its first copy; 73 zero popularity scores and 1 zero duration were treated as missing; 9 'compilation' rows were grouped with Album; 4 calendar dates have no snapshot and were not imputed; 1,761 rows labelled 'single' carry more than one track (EP-style) and were kept as labelled. None of these affects more than 0.3% of rows, except the single/album label question, which follows the source labelling.
7. **One market, about 18 months** (2024-05-18 to 2025-11-27); nothing here compares France with other countries.
8. **Associations only.** No result proves that explicit content, format, duration or album size *causes* chart performance.
9. **Song-level views** use each song's most frequent label (explicit/clean, single/album) because a few songs change label between days.


## 17. Conclusion

In the France Top 50, explicit content is the slight majority and is over-represented in the Top 10, but clean tracks carry higher popularity scores, so the explicit/clean label does not by itself decide success. Album tracks fill slightly more chart slots, yet singles perform better. Medium-length songs (2.5-4 minutes) dominate the strongest positions, and larger releases show weaker per-track results, mostly through the single-vs-album gap. These are associations from one playlist; adding streaming, genre, language, audience and other-market data is the next step before final localisation decisions.
