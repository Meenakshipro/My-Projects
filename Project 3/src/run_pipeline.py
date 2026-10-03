from __future__ import annotations

from src.eda import run_eda
from src.sql_setup import export_to_sqlite
from src.train_models import run_training


if __name__ == "__main__":
    run_eda()  # EDA on cleaned data, before feature engineering
    metrics = run_training()
    export_to_sqlite()
    print("Pipeline completed. Models, metrics, and SQLite database generated.")
    print(metrics)
