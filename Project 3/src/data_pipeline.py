from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np
import pandas as pd

from src.config import (
    BOOKINGS_FILE,
    CUSTOMERS_FILE,
    DRIVERS_FILE,
    LOCATION_DEMAND_FILE,
    PROCESSED_DATA_DIR,
    PROCESSED_FILE,
    TIME_FEATURES_FILE,
)


@dataclass
class RawDataBundle:
    bookings: pd.DataFrame
    customers: pd.DataFrame
    drivers: pd.DataFrame
    location_demand: pd.DataFrame
    time_features: pd.DataFrame


def _safe_divide(num: pd.Series, den: pd.Series) -> pd.Series:
    den = den.replace(0, np.nan)
    return (num / den).replace([np.inf, -np.inf], np.nan)


def load_raw_data() -> RawDataBundle:
    bookings = pd.read_csv(BOOKINGS_FILE)
    customers = pd.read_csv(CUSTOMERS_FILE)
    drivers = pd.read_csv(DRIVERS_FILE)
    location_demand = pd.read_csv(LOCATION_DEMAND_FILE)
    time_features = pd.read_csv(TIME_FEATURES_FILE)

    return RawDataBundle(
        bookings=bookings,
        customers=customers,
        drivers=drivers,
        location_demand=location_demand,
        time_features=time_features,
    )


def clean_and_merge_data(bundle: RawDataBundle) -> pd.DataFrame:
    bookings = bundle.bookings.copy()
    customers = bundle.customers.copy()
    drivers = bundle.drivers.copy()
    location_demand = bundle.location_demand.copy()
    time_features = bundle.time_features.copy()

    bookings["booking_datetime"] = pd.to_datetime(
        bookings["booking_date"].astype(str) + " " + bookings["booking_time"].astype(str),
        errors="coerce",
    )
    bookings["booking_hourly_ts"] = bookings["booking_datetime"].dt.floor("h")

    bookings["actual_ride_time_min"] = bookings["actual_ride_time_min"].fillna(
        bookings["estimated_ride_time_min"]
    )

    bookings["incomplete_ride_reason"] = bookings["incomplete_ride_reason"].fillna("None")

    time_features["datetime"] = pd.to_datetime(time_features["datetime"], errors="coerce")

    merged = bookings.merge(customers, on="customer_id", how="left")
    merged = merged.merge(drivers, on="driver_id", how="left", suffixes=("", "_driver"))
    merged = merged.merge(
        location_demand,
        on=["city", "pickup_location", "hour_of_day", "vehicle_type"],
        how="left",
        suffixes=("", "_demand"),
    )
    merged = merged.merge(
        time_features,
        left_on="booking_hourly_ts",
        right_on="datetime",
        how="left",
        suffixes=("", "_time"),
    )

    return merged


def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    engineered = df.copy()

    engineered["fare_per_km"] = _safe_divide(engineered["booking_value"], engineered["ride_distance_km"])
    engineered["fare_per_min"] = _safe_divide(
        engineered["booking_value"], engineered["actual_ride_time_min"]
    )

    engineered["rush_hour_flag"] = engineered["hour_of_day"].isin([8, 9, 10, 17, 18, 19, 20]).astype(int)

    distance_threshold = engineered["ride_distance_km"].quantile(0.75)
    engineered["long_distance_flag"] = (engineered["ride_distance_km"] >= distance_threshold).astype(int)

    engineered["city_pair"] = (
        engineered["pickup_location"].astype(str) + "__" + engineered["drop_location"].astype(str)
    )

    engineered["driver_reliability_score"] = (
        0.4 * engineered["acceptance_rate"].fillna(0)
        + 0.4 * (1 - engineered["delay_rate"].fillna(0))
        + 0.2 * (engineered["avg_driver_rating"].fillna(0) / 5)
    )

    engineered["customer_loyalty_score"] = (
        0.4 * (engineered["total_bookings"].fillna(0) / engineered["total_bookings"].fillna(0).max())
        + 0.4 * (1 - engineered["cancellation_rate"].fillna(0))
        + 0.2 * (engineered["avg_customer_rating"].fillna(0) / 5)
    )

    engineered["ride_outcome_target"] = engineered["booking_status"].astype(str)
    engineered["fare_target"] = engineered["booking_value"]
    engineered["customer_cancel_target"] = engineered["customer_cancel_flag"].fillna(0).astype(int)
    engineered["driver_delay_target"] = engineered["driver_delay_flag"].fillna(0).astype(int)

    return engineered


def prepare_dataset() -> pd.DataFrame:
    bundle = load_raw_data()
    merged = clean_and_merge_data(bundle)
    prepared = feature_engineering(merged)

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    prepared.to_csv(PROCESSED_FILE, index=False)
    return prepared


def train_ready_dataset() -> Tuple[pd.DataFrame, list[str], list[str]]:
    df = prepare_dataset()

    target_cols = [
        "ride_outcome_target",
        "fare_target",
        "customer_cancel_target",
        "driver_delay_target",
    ]

    drop_cols = [
        "booking_id",
        "booking_date",
        "booking_time",
        "booking_datetime",
        "booking_hourly_ts",
        "datetime",
    ]

    feature_df = df.drop(columns=[c for c in drop_cols if c in df.columns])
    return feature_df, target_cols, drop_cols


if __name__ == "__main__":
    output = prepare_dataset()
    print(f"Prepared dataset saved with shape: {output.shape}")
