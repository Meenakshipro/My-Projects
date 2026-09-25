-- schema.sql
-- These are the tables we store our NCAA Football data in.
-- "PRIMARY KEY" = the unique id for each row.
-- "FOREIGN KEY" = a link to another table's id, enforced by SQLite itself.

PRAGMA foreign_keys = ON;

-- 1. Conferences
CREATE TABLE IF NOT EXISTS conferences (
    conference_id TEXT PRIMARY KEY,
    name          TEXT,
    alias         TEXT
);

-- 2. Divisions
CREATE TABLE IF NOT EXISTS divisions (
    division_id TEXT PRIMARY KEY,
    name        TEXT
);

-- 3. Venues (the stadiums)
CREATE TABLE IF NOT EXISTS venues (
    venue_id  TEXT PRIMARY KEY,
    name      TEXT,
    city      TEXT,
    state     TEXT,
    country   TEXT,
    zip       TEXT,
    address   TEXT,
    capacity  INTEGER,
    surface   TEXT,
    roof_type TEXT,
    latitude  DECIMAL,
    longitude DECIMAL
);

-- 4. Seasons
CREATE TABLE IF NOT EXISTS seasons (
    season_id  TEXT PRIMARY KEY,
    year       INTEGER,
    start_date DATE,
    end_date   DATE,
    status     TEXT,
    type_code  TEXT
);

-- 5. Teams
CREATE TABLE IF NOT EXISTS teams (
    team_id           TEXT PRIMARY KEY,
    market            TEXT,
    name              TEXT,
    alias             TEXT,
    founded           INTEGER,
    mascot            TEXT,
    fight_song        TEXT,
    championships_won INTEGER,
    conference_id     TEXT,
    division_id       TEXT,
    venue_id          TEXT,
    FOREIGN KEY (conference_id) REFERENCES conferences(conference_id),
    FOREIGN KEY (division_id)   REFERENCES divisions(division_id),
    FOREIGN KEY (venue_id)      REFERENCES venues(venue_id)
);

-- 6. Coaches
CREATE TABLE IF NOT EXISTS coaches (
    coach_id  TEXT PRIMARY KEY,
    full_name TEXT,
    position  TEXT,
    team_id   TEXT,
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

-- 7. Players
CREATE TABLE IF NOT EXISTS players (
    player_id   TEXT PRIMARY KEY,
    first_name  TEXT,
    last_name   TEXT,
    abbr_name   TEXT,
    birth_place TEXT,
    position    TEXT,
    height      INTEGER,
    weight      INTEGER,
    status      TEXT,
    eligibility TEXT,
    team_id     TEXT,
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

-- 8. Player_Statistics (one row per player per season)
CREATE TABLE IF NOT EXISTS player_statistics (
    stat_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id            TEXT,
    team_id              TEXT,
    season_id            TEXT,
    games_played         INTEGER,
    games_started        INTEGER,
    rushing_yards        INTEGER,
    rushing_touchdowns   INTEGER,
    receiving_yards      INTEGER,
    receiving_touchdowns INTEGER,
    kick_return_yards    INTEGER,
    fumbles              INTEGER,
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (team_id)   REFERENCES teams(team_id),
    FOREIGN KEY (season_id) REFERENCES seasons(season_id)
);

-- 9. Rankings (weekly poll, e.g. AP Top 25)
CREATE TABLE IF NOT EXISTS rankings (
    ranking_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id        TEXT,
    poll_name      TEXT,
    season_id      TEXT,
    week           INTEGER,
    effective_time TIMESTAMP,
    team_id        TEXT,
    rank           INTEGER,
    prev_rank      INTEGER,
    points         INTEGER,
    fp_votes       INTEGER,
    wins           INTEGER,
    losses         INTEGER,
    ties           INTEGER,
    FOREIGN KEY (season_id) REFERENCES seasons(season_id),
    FOREIGN KEY (team_id)   REFERENCES teams(team_id)
);

-- 10. Season_Schedule (every scheduled game for the season)
CREATE TABLE IF NOT EXISTS season_schedule (
    game_id       TEXT PRIMARY KEY,
    season_id     TEXT,
    week          INTEGER,
    scheduled     TIMESTAMP,
    status        TEXT,
    home_team_id  TEXT,
    away_team_id  TEXT,
    venue_id      TEXT,
    FOREIGN KEY (season_id)    REFERENCES seasons(season_id),
    FOREIGN KEY (home_team_id) REFERENCES teams(team_id),
    FOREIGN KEY (away_team_id) REFERENCES teams(team_id),
    FOREIGN KEY (venue_id)     REFERENCES venues(venue_id)
);

-- 11. Raw_Responses (full body of every API call - captures fields no other table uses)
CREATE TABLE IF NOT EXISTS raw_responses (
    response_id INTEGER PRIMARY KEY AUTOINCREMENT,
    url         TEXT,
    fetched_at  TIMESTAMP,
    raw_json    TEXT
);

-- Indexes to make the dashboard's filters and joins faster
-- (required by the project's SQL best-practice guidelines).
CREATE INDEX IF NOT EXISTS idx_players_team        ON players(team_id);
CREATE INDEX IF NOT EXISTS idx_players_position    ON players(position);
CREATE INDEX IF NOT EXISTS idx_teams_conference    ON teams(conference_id);
CREATE INDEX IF NOT EXISTS idx_teams_division      ON teams(division_id);
CREATE INDEX IF NOT EXISTS idx_teams_venue         ON teams(venue_id);
CREATE INDEX IF NOT EXISTS idx_rankings_team       ON rankings(team_id);
CREATE INDEX IF NOT EXISTS idx_rankings_season     ON rankings(season_id);
CREATE INDEX IF NOT EXISTS idx_stats_player        ON player_statistics(player_id);
CREATE INDEX IF NOT EXISTS idx_stats_season        ON player_statistics(season_id);
CREATE INDEX IF NOT EXISTS idx_coaches_team        ON coaches(team_id);
CREATE INDEX IF NOT EXISTS idx_schedule_season     ON season_schedule(season_id);
CREATE INDEX IF NOT EXISTS idx_schedule_home       ON season_schedule(home_team_id);
CREATE INDEX IF NOT EXISTS idx_schedule_away       ON season_schedule(away_team_id);
CREATE INDEX IF NOT EXISTS idx_schedule_venue      ON season_schedule(venue_id);
