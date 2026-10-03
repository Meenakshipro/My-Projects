from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = ROOT_DIR / "Project-files"
PROCESSED_DATA_DIR = ROOT_DIR / "data" / "processed"
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
MODELS_DIR = ARTIFACTS_DIR / "models"
REPORTS_DIR = ARTIFACTS_DIR / "reports"
SQL_DIR = ROOT_DIR / "sql"

BOOKINGS_FILE = RAW_DATA_DIR / "bookings.csv"
CUSTOMERS_FILE = RAW_DATA_DIR / "customers.csv"
DRIVERS_FILE = RAW_DATA_DIR / "drivers.csv"
LOCATION_DEMAND_FILE = RAW_DATA_DIR / "location_demand.csv"
TIME_FEATURES_FILE = RAW_DATA_DIR / "time_features.csv"

PROCESSED_FILE = PROCESSED_DATA_DIR / "rapido_processed.csv"
SQLITE_FILE = SQL_DIR / "rapido.db"

RANDOM_STATE = 48
TEST_SIZE = 0.2

TARGETS = {
    "ride_outcome": "ride_outcome_target",
    "fare": "fare_target",
    "customer_cancel": "customer_cancel_target",
    "driver_delay": "driver_delay_target",
}
