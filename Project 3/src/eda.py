from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.config import REPORTS_DIR
from src.data_pipeline import clean_and_merge_data, load_raw_data

EDA_DIR = REPORTS_DIR / "eda"

sns.set_theme(style="whitegrid")

# Columns explored in EDA; their distributions/relationships drove the feature
# choices in feature_engineering (features selected from EDA). See FEATURE_SOURCE_MAP.
NUMERIC_COLS = [
    "booking_value",              # -> fare_target, fare_per_km, fare_per_min
    "ride_distance_km",           # -> fare_per_km, long_distance_flag
    "actual_ride_time_min",       # -> fare_per_min
    "hour_of_day",                # -> rush_hour_flag
    "acceptance_rate",            # -> driver_reliability_score
    "delay_rate",                 # -> driver_reliability_score
    "avg_driver_rating",          # -> driver_reliability_score
    "total_bookings",             # -> customer_loyalty_score
    "cancellation_rate",          # -> customer_loyalty_score
    "avg_customer_rating",        # -> customer_loyalty_score
]

CATEGORICAL_COLS = [
    "pickup_location",            # -> city_pair
    "drop_location",              # -> city_pair
    "booking_status",             # -> ride_outcome_target
]

# Raw sources of the engineered targets (enables class balance pre-FE).
TARGET_COLS = [
    "customer_cancel_flag",       # -> customer_cancel_target
    "driver_delay_flag",          # -> driver_delay_target
]

# Each engineered column -> the EDA columns that justified it (features chosen from
# EDA). Reference only — not used at runtime.
FEATURE_SOURCE_MAP = {
    # engineered features
    "fare_per_km": ["booking_value", "ride_distance_km"],
    "fare_per_min": ["booking_value", "actual_ride_time_min"],
    "rush_hour_flag": ["hour_of_day"],
    "long_distance_flag": ["ride_distance_km"],
    "city_pair": ["pickup_location", "drop_location"],
    "driver_reliability_score": ["acceptance_rate", "delay_rate", "avg_driver_rating"],
    "customer_loyalty_score": ["total_bookings", "cancellation_rate", "avg_customer_rating"],
    # engineered targets
    "ride_outcome_target": ["booking_status"],
    "fare_target": ["booking_value"],
    "customer_cancel_target": ["customer_cancel_flag"],
    "driver_delay_target": ["driver_delay_flag"],
}


def _present(df: pd.DataFrame, cols: List[str]) -> List[str]:
    return [c for c in cols if c in df.columns]


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _save(fig: plt.Figure, out_dir: Path, name: str) -> None:
    fig.tight_layout()
    fig.savefig(out_dir / f"{name}.png", dpi=120, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Statistical summary (describe + nulls + skew + value counts + class balance)
# --------------------------------------------------------------------------- #
def generate_statistical_summary(df: pd.DataFrame, label: str) -> Dict:
    num_cols = _present(df, NUMERIC_COLS)
    cat_cols = _present(df, CATEGORICAL_COLS)
    target_cols = _present(df, TARGET_COLS)
    analysis_cols = num_cols + cat_cols + target_cols

    numeric = df[num_cols]
    null_counts = df[analysis_cols].isna().sum()
    summary: Dict = {
        "label": label,
        "shape": {"rows": int(df.shape[0]), "columns": int(df.shape[1])},
        "analyzed_columns": len(analysis_cols),
        "dtype_counts": {str(k): int(v) for k, v in df[analysis_cols].dtypes.value_counts().items()},
        "null_counts": {c: int(n) for c, n in null_counts.items() if n > 0},
        "null_percentage": {
            c: round(float(n) / len(df) * 100, 2)
            for c, n in null_counts.items()
            if n > 0
        },
        "describe_numeric": json.loads(numeric.describe().to_json()) if not numeric.empty else {},
        "mode_skewness": {},
        "categorical_value_counts": {},
        "class_balance": {},
    }

    # describe_numeric already covers mean/std/min/median(50%)/max; add only mode + skewness
    if not numeric.empty:
        modes = numeric.mode()
        skew = numeric.skew()
        for col in num_cols:
            col_mode = modes[col].dropna()
            summary["mode_skewness"][col] = {
                "mode": round(float(col_mode.iloc[0]), 4) if not col_mode.empty else None,
                "skewness": round(float(skew[col]), 4) if pd.notna(skew[col]) else None,
            }

    for col in cat_cols:
        vc = df[col].value_counts(normalize=True).head(15)
        summary["categorical_value_counts"][col] = {
            str(k): round(float(v), 4) for k, v in vc.items()
        }

    for col in target_cols:
        vc = df[col].value_counts(normalize=True)
        summary["class_balance"][col] = {str(k): round(float(v), 4) for k, v in vc.items()}

    return summary


# --------------------------------------------------------------------------- #
# Univariate plots
# --------------------------------------------------------------------------- #
def plot_univariate(df: pd.DataFrame, out_dir: Path) -> None:
    num_dir = _ensure_dir(out_dir / "univariate" / "numeric")
    cat_dir = _ensure_dir(out_dir / "univariate" / "categorical")

    for col in _present(df, NUMERIC_COLS):
        s = df[col].dropna()
        if s.empty:
            continue
        # histogram (with KDE) + box = distribution shape + outliers/IQR
        fig, axes = plt.subplots(1, 2, figsize=(11, 4))
        sns.histplot(s, kde=True, ax=axes[0], color="#4c72b0")
        axes[0].set_title(f"{col} — histogram (skew: {s.skew():.2f})")
        sns.boxplot(x=s, ax=axes[1], color="#dd8452")
        axes[1].set_title(f"{col} — box (outliers/IQR)")
        if col == "ride_distance_km":  # long_distance_flag cutoff
            q75 = s.quantile(0.75)
            axes[0].axvline(q75, color="crimson", ls="--", lw=1, label=f"75th pct = {q75:.1f}")
            axes[0].legend(fontsize=8)
        _save(fig, num_dir, col)

    for col in _present(df, CATEGORICAL_COLS + TARGET_COLS):
        vc = df[col].value_counts()
        if vc.empty:
            continue
        top = vc.head(15)
        low_card = vc.size <= 15
        fig, axes = plt.subplots(1, 2, figsize=(14, 4.5))
        sns.barplot(
            x=top.values, y=top.index.astype(str), hue=top.index.astype(str),
            ax=axes[0], palette="viridis", legend=False,
        )
        axes[0].set_title(f"{col} — bar" if low_card else f"{col} — bar (top {len(top)})")
        if low_card:
            axes[1].pie(top.values, labels=top.index.astype(str), autopct="%1.1f%%", startangle=90)
            axes[1].set_title(f"{col} — pie (percentage)")
        else:
            # pie is misleading for many categories; Pareto shows cumulative coverage
            cum = vc.cumsum() / vc.sum() * 100
            axes[1].plot(range(1, len(cum) + 1), cum.values, marker=".", color="#dd8452")
            axes[1].set_xlabel("category rank")
            axes[1].set_ylabel("cumulative %")
            axes[1].set_title(f"{col} — cumulative share (Pareto)")
        _save(fig, cat_dir, col)


# --------------------------------------------------------------------------- #
# Bivariate plots
# --------------------------------------------------------------------------- #
def plot_bivariate(df: pd.DataFrame, out_dir: Path) -> None:
    bi_dir = _ensure_dir(out_dir / "bivariate")

    # numeric vs numeric — scatter (relationship) + line (trend over hour)
    if {"ride_distance_km", "booking_value"}.issubset(df.columns):
        fig, axes = plt.subplots(1, 2, figsize=(13, 5))
        sample = df.sample(min(len(df), 5000), random_state=48)
        sns.regplot(
            data=sample, x="ride_distance_km", y="booking_value", ax=axes[0],
            scatter_kws={"alpha": 0.3}, line_kws={"color": "crimson"},
        )
        axes[0].set_title("distance vs fare — scatter + trend (supports fare_per_km)")
        if "hour_of_day" in df.columns:
            hourly = df.groupby("hour_of_day")["booking_value"].mean().reset_index()
            sns.lineplot(data=hourly, x="hour_of_day", y="booking_value", marker="o", ax=axes[1])
            for h in [8, 9, 10, 17, 18, 19, 20]:  # rush_hour_flag hours
                axes[1].axvspan(h - 0.5, h + 0.5, color="orange", alpha=0.12)
            axes[1].set_title("avg fare by hour — line (rush hours shaded)")
        _save(fig, bi_dir, "num_vs_num_distance_fare")

    # categorical vs numeric — box (distribution) + bar (avg comparison)
    if {"booking_status", "booking_value"}.issubset(df.columns):
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        sns.boxplot(
            data=df, x="booking_status", y="booking_value", hue="booking_status",
            ax=axes[0], palette="Set2", legend=False,
        )
        axes[0].set_title("fare by booking_status — box")
        axes[0].tick_params(axis="x", rotation=30)
        means = df.groupby("booking_status")["booking_value"].mean().reset_index()
        sns.barplot(
            data=means, x="booking_status", y="booking_value", hue="booking_status",
            ax=axes[1], palette="Set2", legend=False,
        )
        axes[1].set_title("avg fare by booking_status — bar")
        axes[1].tick_params(axis="x", rotation=30)
        _save(fig, bi_dir, "cat_vs_num_status_fare")

    # categorical vs categorical — stacked bar + crosstab heatmap
    if {"hour_of_day", "booking_status"}.issubset(df.columns):
        ct = pd.crosstab(df["hour_of_day"], df["booking_status"])
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        ct.plot(kind="bar", stacked=True, ax=axes[0], colormap="tab20")
        axes[0].set_title("hour_of_day vs booking_status — stacked bar")
        sns.heatmap(ct, annot=False, cmap="Blues", ax=axes[1])
        axes[1].set_title("hour_of_day vs booking_status — crosstab heatmap")
        _save(fig, bi_dir, "cat_vs_cat_hour_status")


# --------------------------------------------------------------------------- #
# Multivariate plots
# --------------------------------------------------------------------------- #
def plot_multivariate(df: pd.DataFrame, out_dir: Path) -> None:
    mv_dir = _ensure_dir(out_dir / "multivariate")

    core_numeric = _present(
        df,
        [
            "booking_value",
            "ride_distance_km",
            "actual_ride_time_min",
            "acceptance_rate",
            "delay_rate",
            "avg_driver_rating",
            "cancellation_rate",
            "avg_customer_rating",
        ],
    )

    # correlation heatmap
    if len(core_numeric) >= 2:
        corr = df[core_numeric].corr()
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax)
        ax.set_title("correlation matrix — heatmap")
        _save(fig, mv_dir, "correlation_heatmap")

    # pair plot on a compact core set (sampled to keep it light)
    pair_cols = _present(
        df, ["booking_value", "ride_distance_km", "actual_ride_time_min", "hour_of_day"]
    )
    if len(pair_cols) >= 2:
        sample = df[pair_cols].dropna().sample(
            min(len(df.dropna(subset=pair_cols)), 2000), random_state=48
        )
        grid = sns.pairplot(sample)
        grid.fig.suptitle("pair plot — core numerics", y=1.02)
        grid.fig.savefig(mv_dir / "pair_plot.png", dpi=110, bbox_inches="tight")
        plt.close(grid.fig)

    # grouped bar — avg fare by hour_of_day and booking_status
    if {"hour_of_day", "booking_status", "booking_value"}.issubset(df.columns):
        grouped = (
            df.groupby(["hour_of_day", "booking_status"])["booking_value"].mean().reset_index()
        )
        fig, ax = plt.subplots(figsize=(13, 6))
        sns.barplot(data=grouped, x="hour_of_day", y="booking_value", hue="booking_status", ax=ax)
        ax.set_title("avg fare by hour_of_day and booking_status — grouped bar")
        _save(fig, mv_dir, "grouped_bar_hour_status")


def _run_for_stage(df: pd.DataFrame, stage: str) -> Dict:
    stage_dir = _ensure_dir(EDA_DIR / stage)
    summary = generate_statistical_summary(df, stage)
    (stage_dir / "statistical_summary.json").write_text(json.dumps(summary, indent=2))
    plot_univariate(df, stage_dir)
    plot_bivariate(df, stage_dir)
    plot_multivariate(df, stage_dir)
    return summary


def run_eda() -> Dict[str, Dict]:
    _ensure_dir(EDA_DIR)

    # BEFORE cleaning — raw bookings only.
    raw = load_raw_data()
    before_summary = _run_for_stage(raw.bookings, "before_cleaning")

    # Raw-table overview (shape + nulls for each source file).
    raw_overview = {
        name: {
            "shape": {"rows": int(frame.shape[0]), "columns": int(frame.shape[1])},
            "null_counts": {c: int(n) for c, n in frame.isna().sum().items() if n > 0},
        }
        for name, frame in {
            "bookings": raw.bookings,
            "customers": raw.customers,
            "drivers": raw.drivers,
            "location_demand": raw.location_demand,
            "time_features": raw.time_features,
        }.items()
    }
    (EDA_DIR / "raw_tables_overview.json").write_text(json.dumps(raw_overview, indent=2))

    # AFTER cleaning, before feature engineering — cleaned + merged data.
    cleaned = clean_and_merge_data(raw)
    after_summary = _run_for_stage(cleaned, "after_cleaning")

    return {"before_cleaning": before_summary, "after_cleaning": after_summary}


if __name__ == "__main__":
    results = run_eda()
    print(f"EDA complete. Outputs saved under: {EDA_DIR}")
    for stage, summary in results.items():
        shape = summary["shape"]
        print(f"  {stage}: {shape['rows']} rows x {shape['columns']} cols")
