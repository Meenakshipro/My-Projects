# Traffic Violations Insight System

EDA, cleaning, and an interactive Streamlit dashboard for a large (~10 lakh
row) traffic-violations dataset.

## Project Objective
Turn a raw, messy traffic-stop dataset into actionable insight through:
1. Data cleaning & preprocessing
2. Exploratory Data Analysis (EDA)
3. An interactive Streamlit dashboard

## Files in this project

| File | Purpose |
|---|---|
| `data_cleaning.py` | Reads the raw file, fixes dates/times/booleans/coordinates/text/year, engineers new columns, saves a clean CSV |
| `build_database.py` | Loads the clean CSV into a normalized, indexed SQLite database |
| `eda_report.py` | Reads the clean CSV, answers the brief's key questions, saves charts + `EDA_Report.md` |
| `app.py` | Streamlit dashboard: filters, summary metrics, charts, hotspot map |
| `CODE_EXPLANATION.md` | Plain-language, line-by-line walkthrough of every script |
| `CODE_FLOW.md` | Which file runs first, and the function call order within each |
| `LINE_BY_LINE_FLOW.md` | Every line of every function, in execution order |
| `COLUMN_CLEANUP_REFERENCE.md` | All 43 raw columns, one by one - which function(s) clean each, and why |
| `requirements.txt` | Python packages needed to run everything |

## About the reference notebooks (loan-approval dataset)
Three notebooks reviewing general data-science technique (cleaning,
preprocessing, classification) were checked for applicable methods. They
work on an unrelated loan-approval dataset, not traffic violations, so
nothing was copied directly — but two techniques were confirmed genuinely
applicable and adopted here: **unrealistic-value filtering** (the notebook
drops implausible ages like 144; this project applies the same idea to
`Year`, which the real file contains values like `0` and `8092` for) and
**IQR-based outlier handling** (already used in `eda_report.py`). Encoding
(One-Hot/Ordinal), skewness correction, scaling, and the classification
model itself (SMOTE, XGBoost, Random Forest) are training steps for
building a predictive model — not applicable here, since this project is
descriptive EDA and a dashboard, with no model being trained.

## Setup

```bash
# 1. Create and activate a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
```

## How to run, step by step

1. Place your raw file in this folder. `data_cleaning.py`'s `__main__`
   block currently points at `Traffic_Violations.csv` (the actual raw
   file provided for this project); it also supports `.xlsx`/`.xls` via
   `pandas.read_excel` if you swap in an Excel export instead — just
   update the filename passed to `clean_all()` accordingly.

2. Clean the data:
   ```bash
   python data_cleaning.py
   ```
   This creates `traffic_violations_clean.csv`.

3. Build the normalized SQL database:
   ```bash
   python build_database.py
   ```
   This creates `traffic_violations.db` (SQLite) — see "The SQL
   database" below for the schema.

4. Generate the EDA report and charts:
   ```bash
   python eda_report.py
   ```
   This walks through the standard EDA steps — Data Understanding,
   Univariate Analysis (categorical and numeric, with mean/median/mode,
   `describe()`, and IQR outlier detection), Bivariate Analysis (numerical
   vs numerical via correlation + scatter plot, categorical vs numerical via
   grouped averages + box plots, and categorical vs categorical via a
   Race-vs-Violation-Type heatmap), and a written Insights & Conclusion
   section — and creates `EDA_Report.md` plus a folder of chart images:
   `eda_outputs/`.

5. Launch the dashboard:
   ```bash
   streamlit run app.py
   ```
   Streamlit will open a browser tab (usually `http://localhost:8501`).
   The dashboard reads directly from `traffic_violations.db` via a real
   SQL `JOIN` query across all 5 tables (not the CSV) — step 3 must be
   run before this one, or the dashboard shows an error.

## The SQL database
`build_database.py` loads the cleaned CSV into `traffic_violations.db`
(SQLite), normalized into 5 tables — checked directly against the real
data first to confirm genuine redundancy exists to remove, not just
splitting tables for its own sake:

| Table | Holds | Distinct rows (real data) |
|---|---|---|
| `agencies` | Agency, SubAgency | 7 |
| `vehicles` | Make, Model, Color, Year, VehicleType (+ Code/Category) | 59,718 |
| `demographics` | Race, Gender, Driver City, Driver State, DL State | 7,492 |
| `search_details` | All 7 Search-detail columns + Arrest Type (+ Code/Description) | 3,553 |
| `violations` | Everything else (one row per stop) + a foreign key into each table above | 199,728 |

`agencies` alone collapses 199,728 repeating rows down to 7 real
combinations — the clearest case for normalizing. Every foreign key
and every column likely to be filtered/grouped directly (date,
category, make, driver city) has an index. Column names follow
`snake_case` throughout (`Search Reason For Stop` →
`search_reason_for_stop`); three real column names needed explicit
handling since they're compound words with no space to split on
(`SeqID` → `seq_id`, `SubAgency` → `sub_agency`, `VehicleType` →
`vehicle_type`) — checked every column name in the file for this
pattern rather than assuming only one case existed.

Verified end to end: every foreign key in `violations` resolves to a
real row in its table (zero orphaned references, zero NULLs), and a
sample JOIN cross-checked correctly against the original CSV.

**This database is the dashboard's actual data source**, not a
disconnected artifact — `app.py` loads its data with a real SQL
`JOIN` query across all 5 tables (see `LOAD_QUERY` in `app.py`), not
by reading the CSV. `eda_report.py` still reads the CSV directly,
which is the right choice there — it's a one-time batch report, not a
live, filterable application, so the simpler path is appropriate.

The schema uses real `FOREIGN KEY` constraints (not just matching
column names) and `PRAGMA foreign_keys = ON` — verified directly that
a fake `vehicle_id` is correctly rejected with a `FOREIGN KEY
constraint failed` error. One SQLite-specific detail worth knowing:
that pragma is per-connection, not saved in the `.db` file itself —
any other code connecting to this database later needs to enable it
again to get real enforcement.

## Notes on the approach
- Cleaning functions are grouped by *type of fix* (all Yes/No columns share
  one function, all text columns share one function) rather than repeating
  near-identical code per column — this keeps the pipeline short and easy to
  extend to columns not explicitly covered here.
- A handful of column-specific fixes came from checking the real file
  directly rather than assuming: `Year` bounds, `Gender`'s "U" code,
  four Search-detail columns' structural blanks, `Location`'s mixed
  `@`/`/` separators, and `State`/`Driver State`/`DL State`'s `"XX"`
  placeholder code (verified as "not specified," not a real state, in
  311/478/2 rows respectively).
- Large-dataset performance: text columns with few unique values are stored
  as `category` dtype, and numeric columns are downcast to smaller types,
  which noticeably reduces memory use on a ~10 lakh row file.
- The dashboard loads the joined data from SQLite once per session
  (`@st.cache_data`) and stores a Parquet cache when the database changes,
  so filtering stays responsive even on the full dataset.
- Filter dropdowns cap their option list at 300 entries (falling back to
  the most frequent values beyond that) — Streamlit's `multiselect`
  widget crashes with a "Maximum call stack size exceeded" error when
  given a column as high-cardinality as `Location` (~269K distinct
  values) in full.

## Checked for redundant/duplicate columns
Beyond `Geolocation` (a confirmed text duplicate of `Latitude`/
`Longitude`, dropped per the brief's own instruction), every column pair
that looked like it might overlap was checked directly rather than
assumed:
- **`Accident` and `Contributed To Accident` are 100% correlated** —
  every single row where one is `Yes`/`True` has the other `Yes`/`True`
  too, with zero exceptions in the real file. Neither column was
  dropped or merged: the brief documents them as two distinct concepts
  ("did the stop involve an accident" vs. "did the violation cause
  one"), and — unlike `Geolocation` — nothing in the brief authorizes
  treating either as removable. Worth knowing about, not worth acting
  on without an explicit decision to do so.
- Several *other* boolean pairs (`Fatal` vs. `HAZMAT`, `HAZMAT` vs.
  `Work Zone`, and others) showed 99.9%+ raw "agreement," but this
  turned out to be a statistical artifact, not real redundancy: all of
  these are independently very rare events (each under 0.15% `True`),
  so two independent rare columns will *always* agree most of the time
  simply because both are usually `False`. Checked the actual overlap
  directly — zero rows have both `True` at once for any of these pairs,
  confirming they aren't actually related.
- `Violation Type` vs. `Search Outcome` (82.7% match where both exist)
  and `Charge` vs. `Description` (0% exact match) were also checked and
  ruled out as duplicates — correlated in the first case, unrelated in
  the second, but not redundant in either.

## Fixed this round, worth knowing how
- **`Latitude`/`Longitude` bounding box tightened**: originally used a
  broad continental-US range, which was too loose — checked directly
  and found 4 real rows with a coordinate far outside Maryland (a point
  in Richmond VA, one in Iowa, one in Missouri, one on the NJ shore)
  that the old range let through as "somewhere plausible in the US."
  The real, legitimate Montgomery County data clusters tightly (lat
  38.66-39.54, lon -77.62 to -76.56) — the new bounds are set just
  outside that real range, catching all 4 genuine errors without
  cutting a single real stop.
- **`Location` road-name extraction**: added `Location Road 1`/
  `Location Road 2` as new, purely additive columns — the original
  `Location` stays untouched, so the existing hotspot analysis is
  unaffected. Covers ~97.6% of rows. Refined twice: first extended
  `standardize_location` to also normalize `AT`/`AND`/`&` as
  intersection separators (verified safe against false positives like
  `"OAKLAND"`/`"PARKLAND"`), then added a check using the 94 already-
  verified real city names from `DRIVER_CITY_MAP` to catch addresses
  with a real city name appended but no comma/ZIP to signal it (e.g.
  `"501 QUINCE ORCHARD BLVD GAITHERSBURG MD"`) — these are correctly
  left blank rather than producing a road name contaminated with city
  text.
- **Two EDA gaps found and fixed**: `Day Of Week` was already being
  engineered as a feature but nothing analyzed it, despite the brief
  asking "how does violation frequency vary by time of day,
  **weekday**, or month" - added `violations_by_weekday`. `VehicleType`
  was never analyzed separately from `Make`, despite the brief asking
  "what **types** of vehicles" as a distinct question from "which
  brand" - added `top_vehicle_types`.
- **Two dashboard gaps found and fixed**: no `Location` filter existed,
  despite the brief explicitly listing it - added. Summary metrics only
  showed "Most Cited Make," despite the brief asking for "makes/
  **models**" (both) - added a 5th metric card for Model.
- **`Driver City`** typo correction, done properly after an earlier
  attempt was correctly found unsafe. A `Make`-style canonical-list +
  fuzzy-match was tried first and rejected: `"N BETHESDA"` (a real,
  distinct place, North Bethesda, MD) scored *higher* similarity to
  `"BETHESDA"` (0.89) than the actual typo `"BEHTESDA"` did (0.88) — no
  clean algorithmic line between "typo of X" and "a real place near X."
  The fix: generate candidates algorithmically (edit-distance +
  frequency), then **hand-verify every single one individually**
  against real US geography, rather than trusting the statistics alone.
  Of 302 algorithm-generated candidates, 113 were rejected as genuinely
  different real places (`"CONYERS"` → real Georgia city, wrongly
  matched to `"YONKERS"`; `"DELMAR"` → a real town named for straddling
  DE/MD, wrongly matched to `"KEYMAR"`; `"BLACKSBURG"` → home of
  Virginia Tech, wrongly matched to `"CLARKSBURG"`; and ~110 more). The
  remaining 189 verified typos are fixed (`DRIVER_CITY_MAP`), while
  every real, distinct place — including all the ones that fooled the
  pure-statistics approach — is confirmed preserved untouched.
- **`Model`** typo correction — the same rigor applied to `Driver City`
  was extended here too, initially flagged as unsafe (BMW's `"2
  Series"`/`"5 Series"`/`"6 Series"` all matched to `"3 Series"` in the
  first pass — genuinely different real BMW model lines) but then
  fixed properly rather than abandoned. Scoped every correction by each
  vehicle's own already-cleaned `Make`, so the same misspelled text can
  correct differently by brand. Built a general structural rule first:
  if a candidate and its match differ by an entire extra/different word
  token while sharing all other tokens exactly, treat it as a real
  trim/series variant, not a typo (this alone correctly excluded the
  BMW Series case, Chevy's `Impala SS/LTZ/LS`, Toyota's `Prius C/V`,
  and Ford's `Taurus X`). Everything the structural rule couldn't
  resolve was then hand-verified individually against real vehicle
  model/trim knowledge, brand by brand. Result: of ~800 algorithm-
  generated candidates, 366 were confirmed as genuine typos and fixed
  (`MODEL_CORRECTIONS`, scoped per Make); the rest were rejected as
  real, different models or trims — e.g. Porsche's real `"718"` model
  line initially matched to `"911"`, GMC's real `"1500"`/`"2500"` truck
  classes both matched to `"3500"`, Mercedes' real `A220`/`ML320`
  matched to `E320`, and Chrysler's/Ram's/Land Rover's real performance
  trims `SRT`/`TRX`/`SVR` matched to generic body-style codes — all
  confirmed preserved untouched in the final result.
- **`Description`**: found 84 real rows with a literal line-break stuck
  in the middle of the text (e.g. `"SIDE MARKER \nLAMP (*)"`), which
  `.str.strip()` alone can never catch, since it only trims the very
  start/end of a string, not the middle. Fixed by collapsing any
  internal whitespace run (spaces, tabs, or a line-break) down to a
  single space inside the shared `_clean` helper — which means every
  other text column gets the same protection automatically, not just
  `Description`. Checked all 23 `TEXT_COLUMNS` directly: this specific
  issue only occurred in `Description`, but the fix now guards all of
  them against it happening in an unseen portion of the file.
- **`Make`**: replaced a small hand-picked typo list with a systematic
  check against `CANONICAL_MAKES` (71 real brands, after adding 6
  commercial-truck manufacturers — `INTERNATIONAL`, `MACK`, `HINO`,
  `PETERBILT`, `KENWORTH`, `GEO` — that were missing entirely), using
  prefix matching (`"CHEV"` → `"CHEVROLET"`) and spelling-similarity
  matching (`"TOYOTAA"` → `"TOYOTA"`) at a similarity threshold tuned by
  testing against the full real dataset — lower thresholds started
  producing wrong matches (`"SAT"` → `"SMART"` instead of `"SATURN"`).
  Verified the 6 new brands create 15 new, safe corrections with **zero**
  regressions to anything that already worked. `MAKE_NICKNAMES` grew
  from 5 to 22 entries after checking every one of the 876 distinct
  values the algorithm still couldn't explain — found real, high-volume
  abbreviations it was missing (`"MERZ"` → Mercedes-Benz, 2,968 rows;
  `"VW"` → Volkswagen, 688 rows; `"BENZ"`, `"TOY"`, `"CAD"`, and others),
  plus two cases where a *model* name had been entered in the Make field
  instead (`"MINI COOPER"` → `MINI`, `"RANGE ROVER"` → `LAND ROVER`).
  Result: 455 of 1,335 distinct real values corrected via the algorithm
  (vs. ~20 before), plus the 22 hand-verified nicknames, with the one
  genuinely ambiguous case (`"MERC"` — could be Mercedes-Benz or Mercury)
  correctly left unchanged.
- **`Make`/`Model`/`Driver City` placeholder values**: checked all three
  for values that don't describe any real brand, model, or place at
  all — found the identical pattern across all of them: `"NONE"`,
  `"UNKNOWN"`, `"UNK"`, `"XX"`, and a bare `"0"`. All now treated as
  missing instead of their own (fake) category. Caught a real bug while
  building this: `Make` isn't cleaned by `standardize_text` the way
  `Model` and `Driver City` are, so a raw `0` in it is still a genuine
  Python `int` at this point, not the text `"0"` — a plain `.isin(["0"])`
  check would have silently missed it. Fixed by converting to string
  first, before comparing, regardless of the column's original type.
- **`State`/`Driver State`/`DL State`**: checked every non-US-state code,
  not just `"XX"` — found real Canadian province codes (`MB`, `ON`, `QC`,
  etc.) and other countries' codes mixed in. Those are genuine
  out-of-jurisdiction registrations and are left alone; only `"XX"` and
  `"US"` (confirmed placeholders for "not specified," not real
  jurisdictions) are now treated as missing. Separately verified
  `DL State`'s own cleaning tip ("should be 2-letter states"): 0 of
  199,702 real values are anything other than exactly 2 letters —
  already fully satisfied, no fix needed there.
- **`Color`**: two values (`"GREEN, DK"`, `"GREEN, LGT"`) abbreviated
  "DARK"/"LIGHT" while every other shade spelled them out in full — now
  consistent.
- **`Driver City`**: checked every value starting with a digit (a real
  city name never does) — 8 turned out to be street addresses, ZIP
  codes, or a stray date (now blanked out), and exactly one,
  `"0XON HILL"`, was a real city (Oxon Hill, MD) with a digit/letter
  typo (now fixed).
- **`Charge` / `Search Reason For Stop`**: both hold real legal citation
  codes, which always have an article-number-dash-section-number shape
  (e.g. `"13-401(b1)"`). Checked whether the trailing `*` on some values
  is just decoration first — it isn't: 20 of 23 asterisked codes *never*
  appear without the asterisk, meaning it likely carries real meaning,
  so it's preserved rather than stripped. Fixed one verified stray-space
  typo (`"2 1-902..."` → `"21-902..."`), then blanked out the ~4-5% of
  values missing the basic article-dash-section shape entirely (bare
  fragments like `"55"`, `"61"`) — these aren't complete, valid codes,
  and there's no reliable way to reconstruct the real one each is
  missing, so they're treated as missing data rather than left looking
  like citations they aren't.
- **`Article`**: fills missing values two ways, in order — first a
  Charge-based lookup (`Article` is the broader legal-code family a
  `Charge` belongs to, e.g. `"21-902(a1)"` falls under `"Transportation
  Article"`; `Charge` maps to exactly one `Article` in 799 of 800 cases
  where both are known), then a fallback to `Article`'s own dominant,
  repeating value (`"TRANSPORTATION ARTICLE"`, 96% of known values) for
  anything the lookup can't reach. Checked directly against the real
  data: the lookup finds **zero** matches on this specific file — every
  one of the 7,138 blank-Article rows also has one of the malformed
  Charge codes noted above, and those never co-occur with a known
  Article anywhere else. The lookup is still applied first regardless,
  since it's the technically correct general approach and would recover
  real gaps on a file where that overlap doesn't happen to be total.
- **`Search Outcome` / `Search Disposition` mix-up, corrected**: an
  earlier pass through the brief document swapped which description
  belongs to which column. Verified directly against the real data:
  `Search Outcome` holds Citation/Arrest/Warning/SERO (matching its own
  stated meaning), and `Search Disposition` holds Nothing/Contraband
  Only/Property Only/Contraband and Property (matching its own stated
  meaning) — there was never an actual inconsistency in the brief, only
  in an earlier reading of it. The code now correctly fills
  `Search Outcome` and `Search Type` with `"NOT APPLICABLE"`, and
  `Search Disposition` specifically with `"NA"` (the brief's distinct
  wording for that one column) — both only for rows where
  `Search Conducted` is `False`.
- **`Search Reason For Stop`, `Search Reason`, and `Search Arrest
  Reason`** all join the `"NOT APPLICABLE"` group too, even though the
  brief doesn't explicitly call for this treatment on any of the three
  (their tips just say "standardize codes"/"standardize legal code
  formatting"). Checked directly for each: `Search Reason` is blank
  only when no search happened — a completely clean pattern.
  `Search Reason For Stop` is blank either because no search happened
  or because the invalid-code cleanup above nulled a malformed code
  that existed during an actual search (193 rows). `Search Arrest
  Reason` is blank either because no search happened or because a
  search happened with no resulting arrest (4,466 rows). In every case
  the fill only touches the "no search happened" reason, correctly
  leaving the others as real missing data. `Search Reason` and `Search
  Arrest Reason` were added after checking whether leaving them
  unfilled caused any actual problem: neither is read anywhere in
  `eda_report.py` or `app.py`, so there was no functional risk, but
  their combined 375,870 blanks were inflating the EDA report's "Total
  missing cells" figure, making the data look messier than it really is.
- **`VehicleType` / `Arrest Type`**: both split into a Code column and a
  Category/Description column (`VehicleType Code`/`VehicleType
  Category`, `Arrest Type Code`/`Arrest Type Description`), per the
  brief's own suggestion for each. Checked first that this is actually
  safe: both real columns are 100% consistently formatted as `"CODE -
  Description"`, with no ambiguous double-dash values and no missing
  separators. The original combined columns are kept, not replaced, so
  nothing that already depended on them (like the dashboard's
  `VehicleType` filter) breaks.
- **`Violation Category`** (new column): groups `Description` into one
  of 10 keyword-based categories (Speeding, Registration, License,
  Alcohol/DUI, etc.) or `"OTHER"`, per the brief's own suggestion.
  Verified against the real data before implementing: covers 76% of all
  violations, with well under 1% miscategorized (checked the riskiest
  overlap by hand — `"LICENSE PLATE"` is checked before the plain
  `"LICENSE"` keyword, so a plate issue correctly routes to
  Registration, not License). Now feeds a new EDA chart
  (`violations_by_category`) and a new dashboard filter, so the column
  is actually used somewhere, not just computed and left idle.

## Possible extensions
- Add a `folium`/`pydeck` heatmap layer instead of the basic `st.map` point map
  for a denser visual of hotspots.
