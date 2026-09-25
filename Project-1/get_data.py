"""get_data.py - downloads NCAA Football data from the Sportradar API and
saves it into ncaafb.db. Run with: python get_data.py"""

import requests
import sqlite3
import pandas as pd
import time
import os
from datetime import datetime, timezone
import config

HEADERS = {"accept": "application/json", "x-api-key": config.API_KEY}
RAW_RESPONSES = []  # every successful response, saved verbatim (see raw_responses table)


def get_json(url):
    """GET one url; return parsed JSON, or None on failure/error status."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        time.sleep(1)  # trial keys: 1 request/second
        if response.status_code == 200:
            RAW_RESPONSES.append({
                "url": url,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "raw_json": response.text,
            })
            return response.json()
        print("Error", response.status_code, "for", url)
        return None
    except Exception as e:
        print("Request failed for", url, "-", e)
        return None


def safe_dict(value):
    """Return value if it's a dict, else {} - guards against a field
    existing but being the wrong type (list/string/None)."""
    return value if isinstance(value, dict) else {}


def make_tables(conn):
    """Create all tables (with real PK/FK constraints) from schema.sql."""
    with open("schema.sql") as f:
        conn.executescript(f.read())
    print("Tables created from schema.sql.\n")


def save_table(rows, table_name, conn, fk_checks=None, numeric_columns=None):
    """Save a list of dicts as rows in table_name.
    fk_checks: [(column, parent_table, parent_column), ...] - drops only
    the specific rows whose FK doesn't exist yet, instead of one bad row
    failing the whole table's insert.
    numeric_columns: columns that must hold real numbers - non-numeric
    values become NULL instead of being stored as-is."""
    if not rows:
        return
    try:
        df = pd.DataFrame(rows).drop_duplicates()  # exact-duplicate rows only

        for column in (numeric_columns or []):
            if column in df.columns:
                before = df[column].notna().sum()
                df[column] = pd.to_numeric(df[column], errors="coerce")
                bad = before - df[column].notna().sum()
                if bad:
                    print(f"'{table_name}'.{column}: {bad} non-numeric value(s) saved as NULL.")

        for column, parent_table, parent_column in (fk_checks or []):
            valid = pd.read_sql(f"SELECT {parent_column} FROM {parent_table}", conn)[parent_column]
            valid = set(valid.dropna())
            before = len(df)
            df = df[df[column].isna() | df[column].isin(valid)]
            dropped = before - len(df)
            if dropped:
                print(f"Dropped {dropped} row(s) from '{table_name}' - "
                      f"{column} has no matching {parent_table} row.")

        df.to_sql(table_name, conn, if_exists="append", index=False)
        print(f"Saved {len(df)} rows to '{table_name}'")
    except Exception as e:
        print(f"Could not save table '{table_name}':", e)


# STEP 1: schedule -> team ids (from home/away/bye_week) + every game
def get_schedule_data(season_years, season_id_by_year):
    team_ids = []
    games = []

    for year in season_years:
        data = get_json(f"{config.BASE_URL}/games/{year}/REG/schedule.json")
        if not data:
            print(f"Skipping schedule for {year} - no data returned.")
            continue

        season_id = season_id_by_year.get(year)  # looked up, not trusted from this response

        for week in data.get("weeks", []):
            week_num = week.get("sequence")
            for game in week.get("games", []):
                game_id = game.get("id")
                if not game_id:
                    print(f"Skipping a game in {year} week {week_num} - no game id.")
                    continue

                home = safe_dict(game.get("home"))
                away = safe_dict(game.get("away"))
                venue = safe_dict(game.get("venue"))

                games.append({
                    "game_id": game_id, "season_id": season_id, "week": week_num,
                    "scheduled": game.get("scheduled"), "status": game.get("status"),
                    "home_team_id": home.get("id"), "away_team_id": away.get("id"),
                    "venue_id": venue.get("id"),
                })

                for side in (home, away):  # every game has 2 teams
                    team_id = side.get("id")
                    if team_id and team_id not in team_ids:
                        team_ids.append(team_id)

            for bye in week.get("bye_week", []):  # teams not playing that week
                team_id = safe_dict(bye.get("team")).get("id")
                if not team_id:
                    print(f"Skipping a bye-week entry in {year} week {week_num} - no team id.")
                    continue
                if team_id not in team_ids:
                    team_ids.append(team_id)

        print("Got schedule for", year, "-", len(data.get("weeks", [])), "weeks")

    return team_ids[:config.HOW_MANY_TEAMS], games


# STEP 2: for each team, its full roster -> teams/venues/conferences/divisions/coaches/players
def collect_teams(team_ids):
    teams, venues, conferences, divisions, coaches, players = [], [], [], [], [], []
    player_ids = []

    for team_id in team_ids:
        t = get_json(f"{config.BASE_URL}/teams/{team_id}/full_roster.json")
        if not t or not t.get("id"):
            print(f"Skipping team {team_id} - roster response was empty or missing its own id.")
            continue

        venue = safe_dict(t.get("venue"))
        location = safe_dict(venue.get("location"))
        conf = safe_dict(t.get("conference"))
        div = safe_dict(t.get("division"))

        teams.append({
            "team_id": t.get("id"), "market": t.get("market"), "name": t.get("name"),
            "alias": t.get("alias"), "founded": t.get("founded"), "mascot": t.get("mascot"),
            "fight_song": t.get("fight_song"), "championships_won": t.get("championships_won"),
            "conference_id": conf.get("id"), "division_id": div.get("id"),
            "venue_id": venue.get("id"),
        })

        if venue.get("id"):
            venues.append({
                "venue_id": venue.get("id"), "name": venue.get("name"), "city": venue.get("city"),
                "state": venue.get("state"), "country": venue.get("country"),
                "zip": venue.get("zip"),
                "address": venue.get("address"), "capacity": venue.get("capacity"),
                "surface": venue.get("surface"), "roof_type": venue.get("roof_type"),
                "latitude": location.get("lat"), "longitude": location.get("lng"),
            })
        else:
            print(f"Note: {t.get('market')} {t.get('name')} - no venue info.")

        if conf.get("id"):
            conferences.append({
                "conference_id": conf.get("id"), "name": conf.get("name"),
                "alias": conf.get("alias"),
            })
        else:
            print(f"Note: {t.get('market')} {t.get('name')} - no conference info.")

        if div.get("id"):
            divisions.append({"division_id": div.get("id"), "name": div.get("name")})
        else:
            print(f"Note: {t.get('market')} {t.get('name')} - no division info.")

        for coach in t.get("coaches", []):
            if not coach.get("id"):
                print(f"Skipping a coach for {t.get('name')} - no coach id.")
                continue
            coaches.append({
                "coach_id": coach.get("id"), "full_name": coach.get("full_name"),
                "position": coach.get("position"), "team_id": t.get("id"),
            })

        for p in t.get("players", []):
            if not p.get("id"):
                print(f"Skipping a player for {t.get('name')} - no player id.")
                continue
            players.append({
                "player_id": p.get("id"), "first_name": p.get("first_name"),
                "last_name": p.get("last_name"), "abbr_name": p.get("abbr_name"),
                "birth_place": p.get("birth_place"), "position": p.get("position"),
                "height": p.get("height"), "weight": p.get("weight"), "status": p.get("status"),
                "eligibility": p.get("eligibility"), "team_id": t.get("id"),
            })
            player_ids.append(p.get("id"))

        print("Got roster for:", t.get("market"), t.get("name"))

    return teams, venues, conferences, divisions, coaches, players, player_ids


# STEP 3: for each player, their profile -> seasons (partial) + player_statistics
def collect_player_stats(player_ids):
    seasons, stats = [], []

    for player_id in player_ids[:config.HOW_MANY_PLAYERS]:
        p = get_json(f"{config.BASE_URL}/players/{player_id}/profile.json")
        if not p:
            print(f"Skipping player {player_id} - profile response was empty.")
            continue

        for season in p.get("seasons", []):  # every season this player has stats for
            season_id = season.get("id")
            if not season_id:
                print(f"Skipping a season for player {player_id} - no season id.")
                continue

            seasons.append({
                "season_id": season_id, "year": season.get("year"),
                "start_date": season.get("start_date"), "end_date": season.get("end_date"),
                "status": season.get("status"), "type_code": season.get("type"),
            })

            for team_season in season.get("teams", []):
                if not team_season.get("id"):
                    print(f"Skipping stats for {player_id}, season {season_id} - no team id.")
                    continue

                s = safe_dict(team_season.get("statistics"))
                rushing = safe_dict(s.get("rushing"))
                receiving = safe_dict(s.get("receiving"))
                kick = safe_dict(s.get("kick_returns"))
                fumbles = safe_dict(s.get("fumbles"))

                stats.append({
                    "player_id": player_id, "team_id": team_season.get("id"),
                    "season_id": season_id,
                    "games_played": s.get("games_played"), "games_started": s.get("games_started"),
                    "rushing_yards": rushing.get("yards"),
                    "rushing_touchdowns": rushing.get("touchdowns"),
                    "receiving_yards": receiving.get("yards"),
                    "receiving_touchdowns": receiving.get("touchdowns"),
                    "kick_return_yards": kick.get("yards"), "fumbles": fumbles.get("fumbles"),
                })
        print("Got stats for player:", p.get("first_name"), p.get("last_name"))

    return seasons, stats


# STEP 4: the full list of seasons Sportradar has - real ids, dates, status
def collect_seasons():
    seasons = []
    data = get_json(f"{config.BASE_URL}/league/seasons.json")
    if not data:
        print("Skipping seasons - no data returned.")
        return seasons

    for s in data.get("seasons", []):
        season_id = s.get("id")
        if not season_id:
            print("Skipping a season entry - no id.")
            continue
        seasons.append({
            "season_id": season_id, "year": s.get("year"), "start_date": s.get("start_date"),
            "end_date": s.get("end_date"), "status": s.get("status"),
            "type_code": safe_dict(s.get("type")).get("code"),  # nested, unlike Player Profile
        })
    print("Got", len(seasons), "seasons.\n")
    return seasons


# STEP 5: weekly rankings for every configured poll, year, and week
def collect_rankings(season_years, season_id_by_year):
    rankings = []

    for year in season_years:
        season_id = season_id_by_year.get(year)
        if season_id is None:
            print(f"Warning: no season found for year {year} - season_id will be blank.\n")

        for poll_type in config.POLL_TYPES:
            for week in config.RANKING_WEEKS:
                url = f"{config.BASE_URL}/polls/{poll_type}/{year}/{week}/rankings.json"
                data = get_json(url)
                if not data:
                    print(f"Skipping {poll_type} {year} week {week} rankings - no data returned.")
                    continue

                poll = safe_dict(data.get("poll"))
                entries = data.get("rankings", [])
                if not entries:  # poll not released yet for that week
                    print(f"No {poll_type} {year} wk{week} rankings - not released yet.")
                    continue

                for entry in entries:
                    team_id = entry.get("id")
                    if not team_id:
                        print(f"Skipping a {poll_type} entry ({year} wk{week}) - no team id.")
                        continue

                    rankings.append({
                        "poll_id": poll.get("id"), "poll_name": poll.get("name"),
                        "season_id": season_id, "week": week,
                        "effective_time": data.get("effective_time"), "team_id": team_id,
                        "rank": entry.get("rank"), "prev_rank": entry.get("prev_rank"),
                        "points": entry.get("points"), "fp_votes": entry.get("fp_votes"),
                        "wins": entry.get("wins"), "losses": entry.get("losses"),
                        "ties": entry.get("ties"),
                    })
                print(f"Got {len(entries)} {poll_type} rankings for {year} week {week}")

    return rankings


def main():
    if not config.API_KEY:
        raise RuntimeError(
            "SPORTRADAR_API_KEY is required to download data. "
            "Set it as an environment variable or add API-KEY.txt locally."
        )

    if os.path.exists(config.DB_FILE):
        os.remove(config.DB_FILE)  # fresh database on every run

    conn = sqlite3.connect(config.DB_FILE)
    make_tables(conn)

    # Seasons runs first - its real years drive both schedule and rankings below
    all_seasons = collect_seasons()
    known_years = sorted({s["year"] for s in all_seasons if s.get("year")}, reverse=True)
    season_years = known_years[:config.HOW_MANY_SEASONS]
    season_id_by_year = {s["year"]: s["season_id"] for s in all_seasons}

    if not season_years:
        # Seasons failed entirely - without a fallback, nothing downstream would
        # ever run (both loops below are "for year in season_years"). Guess a
        # small, safe range instead of producing an empty database.
        fallback_year = datetime.now(timezone.utc).year
        season_years = [fallback_year - i for i in range(3)]
        print(f"WARNING: Seasons endpoint returned no usable years - falling back to "
              f"{season_years}. season_id will be blank until this is fixed.\n")

    team_ids, games = get_schedule_data(season_years, season_id_by_year)
    print("Found", len(team_ids), "teams and", len(games), "scheduled games.\n")

    teams, venues, conferences, divisions, coaches, players, player_ids = collect_teams(team_ids)
    seasons_from_players, stats = collect_player_stats(player_ids)
    rankings = collect_rankings(season_years, season_id_by_year)

    # Merge seasons from both sources; prefer collect_seasons()'s version (has
    # real dates/status) whenever the same season_id came from both places.
    seasons_by_id = {s["season_id"]: s for s in seasons_from_players}
    seasons_by_id.update({s["season_id"]: s for s in all_seasons})
    seasons = list(seasons_by_id.values())

    # Save order matters: a table must save AFTER whatever it has a foreign key to.
    tables = [
        (conferences, "conferences", None, None),
        (divisions, "divisions", None, None),
        (venues, "venues", None, ["capacity", "latitude", "longitude"]),
        (seasons, "seasons", None, ["year"]),
        (teams, "teams", [
            ("conference_id", "conferences", "conference_id"),
            ("division_id", "divisions", "division_id"),
            ("venue_id", "venues", "venue_id"),
        ], ["founded", "championships_won"]),
        (coaches, "coaches", [("team_id", "teams", "team_id")], None),
        (players, "players", [("team_id", "teams", "team_id")], ["height", "weight"]),
        (stats, "player_statistics", [
            ("player_id", "players", "player_id"),
            ("team_id", "teams", "team_id"),
            ("season_id", "seasons", "season_id"),
        ], ["games_played", "games_started", "rushing_yards", "rushing_touchdowns",
            "receiving_yards", "receiving_touchdowns", "kick_return_yards", "fumbles"]),
        (rankings, "rankings", [
            ("season_id", "seasons", "season_id"),
            ("team_id", "teams", "team_id"),
        ], ["week", "rank", "prev_rank", "points", "fp_votes", "wins", "losses", "ties"]),
        (games, "season_schedule", [
            ("season_id", "seasons", "season_id"),
            ("home_team_id", "teams", "team_id"),
            ("away_team_id", "teams", "team_id"),
            ("venue_id", "venues", "venue_id"),
        ], ["week"]),
        (RAW_RESPONSES, "raw_responses", None, None),
    ]
    for rows, name, fk_checks, numeric_columns in tables:
        save_table(rows, name, conn, fk_checks, numeric_columns)

    conn.close()
    print("\nAll done! Data saved to", config.DB_FILE)


if __name__ == "__main__":  # only run main() when executed directly, not when imported
    main()
