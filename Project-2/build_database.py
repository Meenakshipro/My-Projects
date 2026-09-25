"""Load the cleaned CSV into a normalized, indexed SQLite database (run data_cleaning.py first)."""
import sqlite3

import pandas as pd

# Columns each dimension table deduplicates out of the fact table.
DIMENSION_TABLES = {
    "agencies": ["Agency", "SubAgency"],
    "vehicles": [
        "Make", "Model", "Color", "Year", "VehicleType",
        "VehicleType Code", "VehicleType Category",
    ],
    "demographics": [
        "Race", "Gender", "Driver City", "Driver State", "DL State",
    ],
    "search_details": [
        "Search Conducted", "Search Disposition", "Search Outcome",
        "Search Reason", "Search Reason For Stop", "Search Type",
        "Search Arrest Reason", "Arrest Type", "Arrest Type Code",
        "Arrest Type Description",
    ],
}
# Foreign-key column name for each dimension table.
FOREIGN_KEY_NAMES = {
    "agencies": "agency_id",
    "vehicles": "vehicle_id",
    "demographics": "demographic_id",
    "search_details": "search_id",
}
# Per-stop columns that stay in the main fact table.
VIOLATION_COLUMNS = [
    "SeqID", "Date Of Stop", "Time Of Stop", "Description", "Location",
    "Location Road 1", "Location Road 2", "Latitude", "Longitude",
    "State", "Charge", "Article", "Violation Type", "Violation Category",
    "Accident", "Belts", "Personal Injury", "Property Damage", "Fatal",
    "Commercial License", "HAZMAT", "Commercial Vehicle", "Alcohol",
    "Work Zone", "Contributed To Accident", "Accident Severity Score",
    "Time Of Day", "Day Of Week", "Month",
]

# Compound column names split before the general snake_case rule.
COMPOUND_NAME_FIXES = {
    "SeqID": "Seq Id",
    "SubAgency": "Sub Agency",
    "VehicleType": "Vehicle Type",
}

# Explicit CREATE TABLE statements with real FOREIGN KEY constraints; violation_id is a surrogate key (seq_id repeats across charges).
SCHEMA_STATEMENTS = [
    "PRAGMA foreign_keys = ON",
    """CREATE TABLE IF NOT EXISTS agencies (
        agency_id INTEGER PRIMARY KEY,
        agency TEXT,
        sub_agency TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS vehicles (
        vehicle_id INTEGER PRIMARY KEY,
        make TEXT,
        model TEXT,
        color TEXT,
        year REAL,
        vehicle_type TEXT,
        vehicle_type_code TEXT,
        vehicle_type_category TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS demographics (
        demographic_id INTEGER PRIMARY KEY,
        race TEXT,
        gender TEXT,
        driver_city TEXT,
        driver_state TEXT,
        dl_state TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS search_details (
        search_id INTEGER PRIMARY KEY,
        search_conducted INTEGER,
        search_disposition TEXT,
        search_outcome TEXT,
        search_reason TEXT,
        search_reason_for_stop TEXT,
        search_type TEXT,
        search_arrest_reason TEXT,
        arrest_type TEXT,
        arrest_type_code TEXT,
        arrest_type_description TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS violations (
        violation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        seq_id TEXT,
        date_of_stop TEXT,
        time_of_stop TEXT,
        description TEXT,
        location TEXT,
        location_road_1 TEXT,
        location_road_2 TEXT,
        latitude REAL,
        longitude REAL,
        state TEXT,
        charge TEXT,
        article TEXT,
        violation_type TEXT,
        violation_category TEXT,
        accident INTEGER,
        belts INTEGER,
        personal_injury INTEGER,
        property_damage INTEGER,
        fatal INTEGER,
        commercial_license INTEGER,
        hazmat INTEGER,
        commercial_vehicle INTEGER,
        alcohol INTEGER,
        work_zone INTEGER,
        contributed_to_accident INTEGER,
        accident_severity_score INTEGER,
        time_of_day TEXT,
        day_of_week TEXT,
        month TEXT,
        agency_id INTEGER,
        vehicle_id INTEGER,
        demographic_id INTEGER,
        search_id INTEGER,
        FOREIGN KEY (agency_id) REFERENCES agencies(agency_id),
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id),
        FOREIGN KEY (demographic_id)
            REFERENCES demographics(demographic_id),
        FOREIGN KEY (search_id) REFERENCES search_details(search_id)
    )""",
]


def _snake_case(name):
    """Lowercase a column name and turn spaces into underscores for SQL."""
    for compound, fixed in COMPOUND_NAME_FIXES.items():
        name = name.replace(compound, fixed)
    return name.lower().replace(" ", "_")


def load_clean_data(path):
    """Read the cleaned CSV, parsing dates back from text."""
    try:
        return pd.read_csv(
            path, low_memory=False, parse_dates=["Date Of Stop"]
        )
    except FileNotFoundError:
        print(f"ERROR: '{path}' not found. Run data_cleaning.py first.")
        raise


def build_dimension_table(df, columns):
    """Deduplicate a set of columns into a dimension table with a surrogate key."""
    dim = df[columns].drop_duplicates().reset_index(drop=True)
    dim.insert(0, "id", dim.index + 1)
    return dim


def merge_foreign_key(df, dim, columns, id_column):
    """Replace the repeating columns in the fact table with a foreign-key reference."""
    merged = df.merge(dim, on=columns, how="left")
    merged = merged.rename(columns={"id": id_column})
    return merged.drop(columns=columns)


def rename_for_sql(df):
    """Apply the snake_case naming convention to every column."""
    return df.rename(columns={c: _snake_case(c) for c in df.columns})


def create_schema(conn):
    """Create every table and enable foreign-key enforcement (per-connection pragma)."""
    for statement in SCHEMA_STATEMENTS:
        conn.execute(statement)
    conn.commit()


def create_indexes(conn):
    """Index the foreign keys and the columns most often filtered or grouped on."""
    statements = [
        "CREATE INDEX IF NOT EXISTS idx_violations_date "
        "ON violations(date_of_stop)",
        "CREATE INDEX IF NOT EXISTS idx_violations_category "
        "ON violations(violation_category)",
        "CREATE INDEX IF NOT EXISTS idx_violations_agency "
        "ON violations(agency_id)",
        "CREATE INDEX IF NOT EXISTS idx_violations_vehicle "
        "ON violations(vehicle_id)",
        "CREATE INDEX IF NOT EXISTS idx_violations_demographic "
        "ON violations(demographic_id)",
        "CREATE INDEX IF NOT EXISTS idx_violations_search "
        "ON violations(search_id)",
        "CREATE INDEX IF NOT EXISTS idx_vehicles_make ON vehicles(make)",
        "CREATE INDEX IF NOT EXISTS idx_demographics_city "
        "ON demographics(driver_city)",
    ]
    for statement in statements:
        conn.execute(statement)
    conn.commit()


def build_database(csv_path, db_path):
    """Build the full normalized, indexed SQLite database from the cleaned CSV."""
    df = load_clean_data(csv_path)

    dimension_frames = {}
    for table_name, columns in DIMENSION_TABLES.items():
        dim = build_dimension_table(df, columns)
        id_column = FOREIGN_KEY_NAMES[table_name]
        df = merge_foreign_key(df, dim, columns, id_column)
        dimension_frames[table_name] = rename_for_sql(dim).rename(
            columns={"id": id_column}
        )

    violations = df[VIOLATION_COLUMNS + list(FOREIGN_KEY_NAMES.values())]
    violations = rename_for_sql(violations)

    conn = sqlite3.connect(db_path)
    create_schema(conn)
    for table_name, frame in dimension_frames.items():
        frame.to_sql(table_name, conn, if_exists="append", index=False)
    violations.to_sql(
        "violations", conn, if_exists="append", index=False
    )
    create_indexes(conn)
    conn.close()
    return dimension_frames, violations


if __name__ == "__main__":
    build_database(
        "traffic_violations_clean.csv", "traffic_violations.db"
    )
