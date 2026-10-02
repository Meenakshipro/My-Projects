# Rapido: Intelligent Mobility Insights

End-to-end ML project for ride outcome prediction, fare forecasting, cancellation risk, and driver delay risk.

## Project Structure

- `Project-files/`: Raw source datasets
- `src/config.py`: Central paths and model target definitions
- `src/data_pipeline.py`: Loads and merges source tables, cleans data, and creates features and targets
- `src/eda.py`: Exploratory data analysis (before and after cleaning); saves statistics and plots to `artifacts/reports/eda/`
- `src/train_models.py`: Trains and evaluates the four model pipelines
- `src/sql_setup.py`: Exports the processed dataset to SQLite
- `src/run_pipeline.py`: Runs EDA, model training, and SQLite export
- `data/processed/`: Processed dataset outputs
- `artifacts/models/`: Trained model files (`.joblib`)
- `artifacts/reports/`: Evaluation metrics and reports
- `sql/`: SQLite database for analytics
- `assets/`: Dashboard assets, including its favicon
- `.streamlit/`: Streamlit theme configuration
- `app.py`: Streamlit dashboard

## Setup

Use Python 3.12+.

```powershell
pip install -r requirements.txt
```

## Run Full Pipeline

```powershell
python -m src.run_pipeline
```

This command does all of the following:
- Runs EDA (before and after cleaning) and saves statistics and plots to `artifacts/reports/eda/`
- Cleans and merges the input files
- Builds engineered features
- Trains 4 models
- Saves metrics to `artifacts/reports/metrics.json`
- Exports processed data to SQLite `sql/rapido.db`

## Run EDA Only

```powershell
python -m src.eda
```

This generates the exploratory data analysis on its own (without training), saving the statistical summaries and plots under `artifacts/reports/eda/` for the `before_cleaning` and `after_cleaning` stages.

## Run Streamlit App

```powershell
streamlit run app.py
```

The dashboard has three tabs:
- **Business KPIs**: model metrics, booking summaries, and cancellation and fare charts
- **Single Ride Prediction**: select an existing booking by ID and score it with all four models
- **Batch Prediction**: upload a CSV with the processed dataset's feature columns, then download the scored results

The dashboard reads `data/processed/rapido_processed.csv`, the four model files in `artifacts/models/`, and the metrics report. Run the full pipeline if any of these are missing.

## Models Included

1. Ride Outcome Prediction (Multi-class)
2. Fare Prediction (Regression)
3. Customer Cancellation Risk (Binary)
4. Driver Delay Risk (Binary)

## Important Note About Target Leakage

The current baseline intentionally prioritizes execution and project structure. Some columns in the current feature set can leak target information, leading to unrealistically high scores.

Before final submission, remove leakage-prone features and retrain. Suggested columns to exclude include direct or proxy target columns such as:
- `booking_value` when predicting fare
- post-booking operational outcome indicators tightly tied to targets

## Suggested Next Improvement Steps

1. Add strict anti-leakage feature lists per model.
2. Add train/validation split with hyperparameter tuning (Optuna/GridSearch).
3. Add SHAP/feature-importance analysis.
4. Add model and data monitoring over time, such as drift checks and refreshed performance metrics.
5. Add FastAPI endpoint for prediction (optional).
