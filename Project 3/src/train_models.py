from __future__ import annotations

import json
import os
from typing import Dict, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    roc_auc_score,
)
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from src.config import MODELS_DIR, RANDOM_STATE, REPORTS_DIR, TARGETS, TEST_SIZE
from src.data_pipeline import prepare_dataset


def _tune(pipeline: Pipeline, param_grid: dict, X_train, y_train, scoring: str) -> Tuple[Pipeline, Dict]:
    search = GridSearchCV(pipeline, param_grid, cv=3, scoring=scoring, n_jobs=-1)
    search.fit(X_train, y_train)
    return search.best_estimator_, search.best_params_


def build_preprocessor(X: pd.DataFrame) -> ColumnTransformer:
    numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = X.select_dtypes(exclude=[np.number]).columns.tolist()

    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_cols),
            ("cat", categorical_transformer, categorical_cols),
        ]
    )


def _classification_metrics(y_true: pd.Series, y_pred: np.ndarray, y_proba: np.ndarray | None = None) -> Dict:
    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "f1_weighted": float(f1_score(y_true, y_pred, average="weighted")),
        "classification_report": classification_report(y_true, y_pred, output_dict=True),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }

    if y_proba is not None:
        try:
            if len(np.unique(y_true)) > 2:
                metrics["roc_auc_ovr_weighted"] = float(
                    roc_auc_score(y_true, y_proba, multi_class="ovr", average="weighted")
                )
            else:
                metrics["roc_auc"] = float(roc_auc_score(y_true, y_proba[:, 1]))
        except ValueError:
            metrics["roc_auc"] = None

    return metrics


def _regression_metrics(y_true: pd.Series, y_pred: np.ndarray) -> Dict:
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(mean_absolute_error(y_true, y_pred))
    r2 = float(r2_score(y_true, y_pred))

    return {"rmse": rmse, "mae": mae, "r2": r2}


def _split_features_target(df: pd.DataFrame, target_col: str) -> Tuple[pd.DataFrame, pd.Series]:
    forbidden = {
        TARGETS["ride_outcome"],
        TARGETS["fare"],
        TARGETS["customer_cancel"],
        TARGETS["driver_delay"],
    }
    # Drop the target-source columns (and fare-derived leaks) so models learn real
    # patterns instead of copying the answer.
    forbidden |= {
        "booking_status",
        "booking_value",
        "customer_cancel_flag",
        "driver_delay_flag",
        "fare_per_km",
        "fare_per_min",
    }
    X = df.drop(columns=[c for c in forbidden if c in df.columns])
    y = df[target_col]
    return X, y


def train_ride_outcome_model(df: pd.DataFrame) -> Dict:
    X, y = _split_features_target(df, TARGETS["ride_outcome"])
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor(X_train)),
            (
                "model",
                RandomForestClassifier(
                    random_state=RANDOM_STATE,
                    class_weight="balanced_subsample",
                    n_jobs=-1,
                ),
            ),
        ]
    )

    pipeline, best_params = _tune(
        pipeline,
        {"model__n_estimators": [3, 10, 40]},
        X_train,
        y_train,
        "f1_weighted",
    )
    preds = pipeline.predict(X_test)
    proba = pipeline.predict_proba(X_test)

    metrics = _classification_metrics(y_test, preds, proba)
    metrics["best_params"] = best_params
    joblib.dump(pipeline, MODELS_DIR / "ride_outcome_model.joblib")
    return metrics


def train_fare_model(df: pd.DataFrame) -> Dict:
    X, y = _split_features_target(df, TARGETS["fare"])
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor(X_train)),
            (
                "model",
                RandomForestRegressor(
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    pipeline, best_params = _tune(
        pipeline,
        {"model__n_estimators": [5, 60], "model__max_depth": [6, 12]},
        X_train,
        y_train,
        "r2",
    )
    preds = pipeline.predict(X_test)

    metrics = _regression_metrics(y_test, preds)
    metrics["best_params"] = best_params
    joblib.dump(pipeline, MODELS_DIR / "fare_model.joblib")
    return metrics


def train_customer_cancel_model(df: pd.DataFrame) -> Dict:
    X, y = _split_features_target(df, TARGETS["customer_cancel"])
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor(X_train)),
            (
                "model",
                RandomForestClassifier(
                    random_state=RANDOM_STATE,
                    class_weight="balanced_subsample",
                    n_jobs=-1,
                ),
            ),
        ]
    )

    pipeline, best_params = _tune(
        pipeline,
        {"model__n_estimators": [4, 9, 40]},
        X_train,
        y_train,
        "f1_weighted",
    )
    preds = pipeline.predict(X_test)
    proba = pipeline.predict_proba(X_test)

    metrics = _classification_metrics(y_test, preds, proba)
    metrics["best_params"] = best_params
    joblib.dump(pipeline, MODELS_DIR / "customer_cancel_model.joblib")
    return metrics


def train_driver_delay_model(df: pd.DataFrame) -> Dict:
    X, y = _split_features_target(df, TARGETS["driver_delay"])
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor(X_train)),
            (
                "model",
                RandomForestClassifier(
                    random_state=RANDOM_STATE,
                    class_weight="balanced_subsample",
                    n_jobs=1,
                ),
            ),
        ]
    )

    pipeline, best_params = _tune(
        pipeline,
        {"model__n_estimators": [6, 10, 40]},
        X_train,
        y_train,
        "f1_weighted",
    )
    preds = pipeline.predict(X_test)
    proba = pipeline.predict_proba(X_test)

    metrics = _classification_metrics(y_test, preds, proba)
    metrics["best_params"] = best_params
    joblib.dump(pipeline, MODELS_DIR / "driver_delay_model.joblib")
    return metrics


def run_training() -> Dict:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    df = prepare_dataset()

    max_rows = int(os.getenv("RAPIDO_MAX_ROWS", "30000"))
    if len(df) > max_rows:
        df = df.sample(n=max_rows, random_state=RANDOM_STATE).reset_index(drop=True)

    print(f"Training on rows: {len(df)}", flush=True)

    print("Training ride outcome model...", flush=True)
    metrics = {
        "ride_outcome": train_ride_outcome_model(df),
    }

    print("Training fare model...", flush=True)
    metrics["fare"] = train_fare_model(df)

    print("Training customer cancellation model...", flush=True)
    metrics["customer_cancel"] = train_customer_cancel_model(df)

    print("Training driver delay model...", flush=True)
    metrics["driver_delay"] = train_driver_delay_model(df)

    with open(REPORTS_DIR / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    return metrics


if __name__ == "__main__":
    all_metrics = run_training()
    print(json.dumps(all_metrics, indent=2))
