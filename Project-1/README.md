# NCAA Football Analytics System

A centralized NCAA Football data pipeline and dashboard. It pulls live data from the
Sportradar NCAAFB API, stores it in a normalized SQLite database, and presents it
through an interactive Streamlit application for exploring teams, players, rankings,
schedules, and venues.

## Project Objective

Build a working analytics platform that connects rankings, teams, players, and game
data into a single, relationally linked database — supporting real questions like
"which teams stayed in the Top 5 across multiple seasons" or "which players appeared
for the same team across multiple seasons."

## Project Structure

```
config.py       - all settings (API key, limits, poll types) in one place
schema.sql      - the 11-table database schema, with real primary/foreign keys
get_data.py     - downloads data from the API and saves it into ncaafb.db
app.py          - the Streamlit dashboard that reads ncaafb.db
requirements.txt - Python packages needed
CODE_EXPLANATION.md - a full function-by-function, flow-by-flow walkthrough
```

## Setup

**1. Install dependencies:**
```
pip install -r requirements.txt
```

**2. Get a free Sportradar trial API key:**
Sign up at [console.sportradar.com](https://console.sportradar.com), create an
application, and add the NCAA Football trial to it. Copy the key it gives you.

**3. Add your key to `config.py`:**
```python
API_KEY = "your-real-key-here"
```
Never commit a real key to a public repository — keep `config.py` private, or use
an environment variable in place of the literal string if sharing this project.

**4. Download the data:**
```
python get_data.py
```
This creates `ncaafb.db` and fills it with real teams, players, rankings, schedules,
and more. Watch the console — it prints progress and any data-quality issues found
along the way (missing fields, teams outside the sampled set, etc.) rather than
failing silently.

**5. Launch the dashboard:**
```
streamlit run app.py
```

## What Gets Collected

| Setting (in `config.py`) | Meaning |
|---|---|
| `HOW_MANY_SEASONS = 50` | How many years back to look — set high so any real year Sportradar has is found |
| `HOW_MANY_TEAMS = 10` | How many teams to pull full rosters for (trial keys are rate-limited to 1 request/second) |
| `HOW_MANY_PLAYERS = 50` | How many players to pull season stats for |
| `RANKING_WEEKS = [1, 2, 3]` | Which weeks of each season's rankings to pull |
| `POLL_TYPES` | All 5 polls Sportradar supports: AP25, EU25, CFP25, FCS25, FCSC25 |

Raising `HOW_MANY_TEAMS`/`HOW_MANY_PLAYERS` collects more data but uses more of the
trial key's 1,000-call/30-day budget — see `CODE_EXPLANATION.md` for the exact math.

## Database Schema (11 tables)

`conferences`, `divisions`, `venues`, `seasons`, `teams`, `coaches`, `players`,
`player_statistics`, `rankings`, `season_schedule`, `raw_responses` — normalized,
indexed, and linked by real foreign keys enforced by SQLite itself
(`PRAGMA foreign_keys = ON` in `schema.sql`). `raw_responses` stores every API
response verbatim, so no field is ever truly lost even if a table doesn't use it.

## Dashboard Pages

Home · Teams Explorer · Players Explorer · Player Stats · Season & Schedule ·
Rankings · Venues · Coaches — each with real filters, search, and (on Rankings and
Players Explorer) aggregate analysis views like "teams ranked Top 5 across multiple
seasons" and "position distribution by team."

## Notes on Data Completeness

- `HOW_MANY_TEAMS`/`HOW_MANY_PLAYERS` sample a subset of real teams/players, not
  every one that exists — some rankings or stats may reference a team/player outside
  that sample. Those specific rows are safely skipped (with a console message), not
  silently corrupted or allowed to break the rest of the table.
- FCS-division polls (`FCS25`, `FCSC25`) will mostly produce no rows, since team
  discovery is scoped to the FBS schedule — this is expected, not a bug.
- If the Sportradar Seasons endpoint is ever unavailable, `get_data.py` falls back
  to a small guessed range of recent years so the rest of the pipeline can still run.

## Testing

`get_data.py` was tested against real Sportradar API examples for every endpoint,
plus deliberately broken/missing/empty responses at every level (a whole endpoint
failing, one field missing, wrong-type values, orphaned foreign keys) to confirm
nothing crashes and nothing silently corrupts the database. See
`CODE_EXPLANATION.md` for details on what each safeguard does and why.
