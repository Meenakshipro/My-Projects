from __future__ import annotations

from src.sql_setup import export_to_sqlite
from src.train_models import run_training


if __name__ == "__main__":
    metrics = run_training()
    export_to_sqlite()
    print("Pipeline completed. Models, metrics, and SQLite database generated.")
    print(metrics)
