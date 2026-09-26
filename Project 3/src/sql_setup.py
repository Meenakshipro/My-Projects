from __future__ import annotations

import sqlite3

import pandas as pd

from src.config import PROCESSED_FILE, SQLITE_FILE


def export_to_sqlite() -> None:
    df = pd.read_csv(PROCESSED_FILE)

    SQLITE_FILE.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(SQLITE_FILE) as conn:
        df.to_sql("rides", conn, if_exists="replace", index=False)

        conn.execute("CREATE INDEX IF NOT EXISTS idx_rides_city_hour ON rides(city, hour_of_day)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_rides_customer ON rides(customer_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_rides_driver ON rides(driver_id)")
        conn.commit()


if __name__ == "__main__":
    export_to_sqlite()
    print(f"SQLite DB created at: {SQLITE_FILE}")
