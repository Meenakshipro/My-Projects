# Code Explanation

This document explains what every function does, in the order the program actually
calls them, followed by a step-by-step walkthrough of `main()` itself.

## The Big Picture

Two programs, connected only through the `ncaafb.db` file:

```
get_data.py  --(writes)-->  ncaafb.db  --(reads)-->  app.py
   (run once, from a terminal)                (run continuously, as a dashboard)
```

`get_data.py` never touches the dashboard. `app.py` never calls the API. Once
`ncaafb.db` exists, `app.py` could run forever with no internet connection at all.

## get_data.py — Function by Function, in Call Order

### 1. `get_json(url)`
The one function every API call goes through. Sends the request, waits 1 second
(trial keys are rate-limited to 1 request/second), and returns the parsed JSON —
or `None` if the request failed or the server returned an error. Also saves the
complete raw response text into `RAW_RESPONSES`, a list that becomes the
`raw_responses` table at the end — this means even fields no other part of the
code reads are still preserved somewhere.

**Called by:** every other function that needs live data — `get_schedule_data`,
`collect_teams`, `collect_player_stats`, `collect_seasons`, `collect_rankings`.

### 2. `safe_dict(value)`
A one-line safety helper: returns `value` if it's genuinely a dictionary, otherwise
returns an empty dict. Real API responses can have a field that's supposed to be a
nested object but occasionally isn't (missing, `null`, or even the wrong type) —
calling `.get()` on anything that isn't a dict crashes the program. Every nested
lookup in this file goes through `safe_dict()` first specifically to prevent that.

**Called by:** everywhere a nested object (venue, conference, division, statistics,
poll, home/away teams) is read from a response.

### 3. `make_tables(conn)`
Runs `schema.sql` once, at the very start, to create all 11 tables with their real
primary and foreign keys — before any data collection begins.

**Called by:** `main()`, first thing after opening the database connection.

### 4. `save_table(rows, table_name, conn, fk_checks=None, numeric_columns=None)`
The one function every table is saved through. Three layers of protection here,
each solving a different real problem:
- **Exact-duplicate removal** — drops rows that are byte-for-byte identical (e.g.
  the same season appearing from two different API calls).
- **`numeric_columns`** — for columns that should hold real numbers, converts the
  column with `pd.to_numeric(errors="coerce")`. SQLite doesn't actually enforce
  column types, so without this, a stray non-numeric value would silently sit in
  an `INTEGER` column forever. Non-numeric values become `NULL` instead, with a
  printed count of how many were caught.
- **`fk_checks`** — a list of `(column, parent_table, parent_column)` tuples. Before
  inserting, checks that every foreign key value actually exists in its parent
  table already. Without this, **one** bad row (e.g. a ranking for a team outside
  the sampled set) would fail SQLite's foreign key constraint and take the
  **entire table's insert** down with it — including every valid row alongside it.
  This drops only the specific bad rows, with a message naming exactly which
  column and which table it failed against.

**Called by:** `main()`, once per table, at the very end.

### 5. `get_schedule_data(season_years, season_id_by_year)`
**STEP 1 of data collection.** For each year, downloads that season's schedule and
extracts two things from the same response: every game (→ `season_schedule` table)
and every team id it can find — from `home`/`away` on each game, **and** from
`bye_week` entries (teams with no game that week, which would otherwise never be
discovered). Team ids are capped at `config.HOW_MANY_TEAMS`.

**Called by:** `main()`, right after `collect_seasons()` — needs `season_years`
(which years to check) and `season_id_by_year` (to link each game to a real season).

### 6. `collect_teams(team_ids)`
**STEP 2.** For each team id, downloads that team's full roster — one API call
returns the team's own info, its venue, conference, division, coaches, and full
player list all nested together. This function unpacks that single response into
6 separate lists (one per table), since the database is normalized. Also returns
`player_ids`, needed for the next step.

**Called by:** `main()`, using the `team_ids` from step 1.

### 7. `collect_player_stats(player_ids)`
**STEP 3.** For each player id (capped at `config.HOW_MANY_PLAYERS`), downloads
their profile — which contains their full season-by-season stat history in one
call. Flattens the nested `seasons → teams → statistics → rushing/receiving/...`
structure into two lists: `seasons` (partial info) and `player_statistics`.

**Called by:** `main()`, using the `player_ids` from step 2.

### 8. `collect_seasons()`
**STEP 4, but runs first in `main()`.** Downloads the complete list of every real
season Sportradar has, in one call — this is what tells the rest of the pipeline
which years actually exist, instead of guessing or hardcoding them.

**Called by:** `main()`, before anything else — its output (`season_years`) is
required input for both `get_schedule_data()` and `collect_rankings()`.

### 9. `collect_rankings(season_years, season_id_by_year)`
**STEP 5.** For every year, every configured poll type (AP25, EU25, CFP25, FCS25,
FCSC25), and every configured week, downloads that specific ranking. Each response
gives a poll object and a list of ranked teams; both get flattened into the
`rankings` table.

**Called by:** `main()`, using `season_years` from step 4.

## `main()` — Step by Step

1. Delete any old `ncaafb.db` so every run starts clean.
2. Open the database connection, call `make_tables()`.
3. Call `collect_seasons()` first — its result decides which years everything
   else will use.
4. Derive `season_years`: take the real years found, sorted newest-first, capped
   at `config.HOW_MANY_SEASONS`.
5. **Fallback check:** if `season_years` ends up empty (the Seasons endpoint
   failed entirely), guess a small range around the current year instead of
   letting the rest of the pipeline silently produce nothing — both
   `get_schedule_data()` and `collect_rankings()` loop over `season_years`, so an
   empty list here would otherwise cascade into zero teams, zero players, zero
   rankings.
6. Call `get_schedule_data()` with those years — gives `team_ids` and `games`.
7. Call `collect_teams(team_ids)` — gives 6 lists plus `player_ids`.
8. Call `collect_player_stats(player_ids)` — gives partial seasons and stats.
9. Call `collect_rankings()` with the same years — gives `rankings`.
10. **Merge seasons from both sources** — `collect_seasons()`'s version wins if
    the same `season_id` appears in both, since it has real dates/status that
    player profiles don't include.
11. Save every table, **in dependency order** — a table only saves after
    everything it has a foreign key to has already been saved (conferences →
    teams → players → player_statistics, etc.).
12. Close the connection, print a final summary.

## app.py — Function by Function

### `run_sql(query, params=())`
Every single query on every page goes through this. Opens a connection, runs the
query, closes the connection, returns the result as a table. Wrapped in
try/except so a bad query shows a friendly on-screen error instead of crashing
the whole dashboard.

### `options(column, table)`
Fills a dropdown filter with the real distinct values already in that column —
so a filter never shows a choice that doesn't actually exist in the data.

### The page structure
Streamlit reruns the entire file top-to-bottom every time the user interacts with
a widget. An `if page == "...": ... elif page == "...":` chain means only the
block matching the currently-selected sidebar page actually does anything visible.
Every page follows the same basic recipe: `options()` to build filter dropdowns →
read what the user picked → build a SQL string starting from a base query →
`run_sql()` → `st.dataframe()`.

## Key Safety Mechanisms — Why Each One Exists

| Mechanism | Problem it solves |
|---|---|
| `safe_dict()` | A nested field being the wrong type (list/string/null) instead of an object |
| skip-and-log guards (missing `id`) | An item with no real identifier — nothing to key it by |
| `fk_checks` in `save_table()` | One orphaned foreign key failing an entire table's insert |
| `numeric_columns` in `save_table()` | SQLite silently storing non-numeric garbage in a numeric column |
| Seasons fallback in `main()` | One failed endpoint cascading into an empty database |
| `raw_responses` table | Any field no structured table extracts still being preserved |
