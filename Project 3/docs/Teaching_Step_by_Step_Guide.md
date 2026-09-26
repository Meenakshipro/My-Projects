# Rapido Project Teaching Guide (Beginner Friendly)

This guide is written for students who are completely new to machine learning projects.
Use this along with the PPT.

## 1) Start With The Big Picture

Tell students this story first:
- Rapido has many ride bookings every day.
- Some rides get cancelled.
- Some drivers are delayed.
- Fare estimation is not always accurate.
- We will use old ride data to predict these risks early.

Explain why prediction matters:
- If cancellation risk is high, operations can act early.
- If driver delay risk is high, assign backup driver.
- If demand is high, pricing and driver allocation can be adjusted.

## 2) Explain The 4 Use Cases In Simple Words

1. Ride outcome prediction:
Predict if ride will be Completed, Cancelled, or Incomplete.

2. Fare prediction:
Predict expected ride fare before confirmation.

3. Customer cancellation risk:
Predict if customer is likely to cancel.

4. Driver delay risk:
Predict if driver may cause delay/incomplete ride.

## 3) Show The Project Files

Explain each file one by one:
- bookings file: core ride transactions
- customers file: customer history and behavior
- drivers file: driver history and behavior
- location_demand file: location and time demand pattern
- time_features file: weekday, holiday, peak, season details

Tell students this important idea:
A model is only as good as the quality of data and features.

## 4) Open Project And Set Up Environment

Ask students to do exactly this:
1. Open VS Code.
2. Open project folder PROJECT3.
3. Open terminal inside VS Code.
4. Confirm they are inside project root folder.

Install dependencies:
- pip install -r requirements.txt

If students get error:
- Check they are in correct folder.
- Check Python is installed.
- Fix one error at a time (do not panic and change many things at once).

## 5) Run The Full Pipeline

Command:
- python -m src.run_pipeline

Explain what this single command does:
- Reads raw CSV files.
- Cleans missing values and date-time fields.
- Merges all tables.
- Creates new engineered features.
- Trains 4 models.
- Saves metrics report.
- Saves SQLite database.

## 6) Verify Outputs After Pipeline

Students must check these outputs exist:
- data/processed/rapido_processed.csv
- artifacts/models/ride_outcome_model.joblib
- artifacts/models/fare_model.joblib
- artifacts/models/customer_cancel_model.joblib
- artifacts/models/driver_delay_model.joblib
- artifacts/reports/metrics.json
- sql/rapido.db

If outputs are missing:
- Read terminal error lines from top to bottom.
- Fix dependency or path issue and run again.

## 7) Teach Data Cleaning Clearly

Explain these cleaning actions in plain language:
- booking_date and booking_time are combined into one timestamp.
- Missing actual ride time is replaced using estimated ride time.
- Missing reason fields are filled safely.
- Tables are merged using ids and time keys.

Teaching tip:
Ask students why missing values are dangerous. Let them answer first.

## 8) Teach Feature Engineering Clearly

Explain each feature and its business meaning:
- fare_per_km: how expensive each km is
- fare_per_min: fare intensity by time
- rush_hour_flag: whether trip is in peak time
- long_distance_flag: whether trip is long
- city_pair: pickup-drop route pattern
- driver_reliability_score: summary of driver behavior
- customer_loyalty_score: summary of customer behavior

Teaching tip:
Ask students to suggest one extra useful feature.

## 9) Teach Train/Test Split

Explain simply:
- Train data is for learning patterns.
- Test data is for honest checking.
- If we test on training data, results are misleading.

Current split:
- 80 percent training
- 20 percent test

## 10) Teach Metrics Without Math Fear

Classification metrics:
- Accuracy: overall correct answers
- F1 Score: balance of missing and wrong alerts
- AUC: quality of probability ranking
- Confusion Matrix: exact mistake types

Regression metrics:
- MAE: average absolute fare error
- RMSE: higher penalty for large fare mistakes
- R2: how much fare variation is explained

## 11) Teach Data Leakage Warning

Important for beginners:
- Leakage means model sees information too close to actual answer.
- Leakage creates unrealistic perfect metrics.
- Real project success requires realistic, trustworthy metrics.

Explain this sentence clearly:
Better realistic model than fake perfect model.

## 12) Run Streamlit Dashboard

Command:
- streamlit run app.py

Explain the tabs:
- Business KPIs tab: overall trend and snapshots
- Single Ride Prediction tab: select an existing booking by ID and run all four model predictions
- Batch Prediction tab: upload a CSV with the processed dataset's feature columns, review the scored rows, and download the results

Teaching tip:
While demoing, ask class what action they would take if risk is high.

## 13) Explain How Business Uses Predictions

Examples:
- High cancellation risk: send communication or incentive.
- High delay risk: assign standby driver.
- High demand hour: pre-position drivers, dynamic pricing.
- Low reliability route: monitor and optimize matching.

## 14) Student Practice Activity

Give this mini assignment:
1. Run full pipeline.
2. Open metrics report.
3. Identify strongest and weakest model.
4. Propose one business action per model.
5. Present in 3 minutes.

## 15) Common Errors And Quick Fixes

1. Module not found:
Install requirements in active environment.

2. File not found:
Run command from project root folder.

3. Very high unrealistic score:
Review leakage-prone features and retrain.

4. Streamlit not opening:
Check terminal for local URL and open in browser.

## 16) Suggested Classroom Flow (2 Hours)

- 0 to 20 min: project story and use cases
- 20 to 50 min: data files and cleaning concepts
- 50 to 90 min: pipeline run and metrics reading
- 90 to 120 min: Streamlit demo and student Q and A

## 17) Final Message To Students

At the end, students should be able to:
- Explain business problem in simple language
- Run full ML pipeline from terminal
- Read model metrics confidently
- Use dashboard for decisions
- Communicate results to non-technical people
