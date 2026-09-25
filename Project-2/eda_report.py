"""Runs the full EDA on the cleaned CSV; writes EDA_Report.md + charts."""
import os
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

OUTPUT_FOLDER = "eda_outputs"
NUMERIC_COLUMNS = ["Year", "Accident Severity Score"]
CATEGORY_FOR_NUMERIC_COMPARISON = "Gender"


def load_clean_data(path):
    """Read the cleaned CSV, parsing dates back from text."""
    try:
        return pd.read_csv(
            path, low_memory=False, parse_dates=["Date Of Stop"]
        )
    except FileNotFoundError:
        print(f"ERROR: '{path}' not found. Run data_cleaning.py first.")
        raise


def save_bar_chart(
    series, title, filename, xlabel, ylabel="Number of Violations"
):
    """Draw + save one bar chart, reused by every chart below."""
    plt.figure(figsize=(9, 5))
    series.plot(kind="bar", color="steelblue")
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=45, ha="right")
    plt.savefig(os.path.join(OUTPUT_FOLDER, filename), bbox_inches="tight")
    plt.close()


def data_understanding_summary(df):
    """Shape, duplicate, and missing-value snapshot of the dataset."""
    missing = df.isna().sum()
    return {
        "Rows": len(df),
        "Columns": df.shape[1],
        "Duplicate rows": int(df.duplicated().sum()),
        "Columns with missing values": int((missing > 0).sum()),
        "Total missing cells": int(missing.sum()),
    }


def most_common_violations(df, n=10):
    """Question: what are the most common violations?"""
    return df["Description"].value_counts().head(n)


def top_hotspots(df, n=10):
    """Question: which locations see the most violations?"""
    return df["Location"].value_counts().head(n)


def violations_by_time_bucket(df):
    """Question: how does frequency vary by time of day?"""
    return df["Time Of Day"].value_counts()


def top_vehicle_makes(df, n=10):
    """Question: which vehicle makes are most involved?"""
    return df["Make"].value_counts().head(n)


def top_vehicle_types(df, n=10):
    """Question: what types of vehicles are most involved?"""
    return df["VehicleType"].value_counts().head(n)


def violations_by_category(df):
    """Question: which broad violation categories are most common?"""
    return df["Violation Category"].value_counts()


def violations_by_month(df):
    """Violation counts per month, in calendar order."""
    order = [
        "January", "February", "March", "April", "May", "June", "July",
        "August", "September", "October", "November", "December",
    ]
    return df["Month"].value_counts().reindex(order).dropna()


def violations_by_weekday(df):
    """Question: how does frequency vary by weekday and weekend?"""
    order = [
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
        "Saturday", "Sunday",
    ]
    return df["Day Of Week"].value_counts().reindex(order).dropna()


def violation_type_breakdown(df):
    """Percentage share of each Violation Type."""
    counts = df["Violation Type"].value_counts(normalize=True)
    return (counts * 100).round(2)


def numeric_quick_stats(df, columns):
    """Mean/median/mode/skewness for each numeric column, by name."""
    stats = {}
    for col in columns:
        mode = df[col].mode()
        stats[col] = {
            "mean": round(df[col].mean(), 2),
            "median": df[col].median(),
            "mode": mode.iloc[0] if not mode.empty else None,
            "skewness": round(df[col].skew(), 3),
        }
    return stats


def numeric_univariate_stats(df, columns):
    """Full describe() summary (count/mean/std/min/quartiles/max)."""
    return df[columns].describe()


def save_distribution_plot(df, column):
    """Histogram + box plot for one numeric column's shape/outliers."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    sns.histplot(df[column].dropna(), ax=axes[0])
    axes[0].set_title(f"{column}: Distribution")
    sns.boxplot(x=df[column].dropna(), ax=axes[1])
    axes[1].set_title(f"{column}: Outliers")
    filename = column.lower().replace(" ", "_") + "_distribution.png"
    path = os.path.join(OUTPUT_FOLDER, filename)
    plt.savefig(path, bbox_inches="tight")
    plt.close()


def detect_outliers_iqr(df, column):
    """Count values outside 1.5x the inter-quartile range (IQR)."""
    q1 = df[column].quantile(0.25)
    q3 = df[column].quantile(0.75)
    iqr = q3 - q1
    below = df[column] < q1 - 1.5 * iqr
    above = df[column] > q3 + 1.5 * iqr
    return int((below | above).sum())


def numeric_correlation(df, columns):
    """Correlation matrix between the numeric columns."""
    return df[columns].corr()


def save_scatter_plot(df, col_x, col_y):
    """Scatter plot - the visual version of numeric_correlation()."""
    plt.figure(figsize=(7, 5))
    sns.scatterplot(data=df, x=col_x, y=col_y, alpha=0.3)
    plt.title(f"{col_x} vs {col_y}")
    filename = f"{col_x}_vs_{col_y}_scatter.png".lower()
    filename = filename.replace(" ", "_")
    path = os.path.join(OUTPUT_FOLDER, filename)
    plt.savefig(path, bbox_inches="tight")
    plt.close()


def average_by_category(df, numeric_col, category_col):
    """Average of a numeric column, grouped by a category."""
    grouped = df.groupby(category_col)[numeric_col].mean()
    return grouped.round(2).sort_values(ascending=False)


def save_boxplot_by_category(df, numeric_col, category_col):
    """Box plot of a numeric column's spread across each category."""
    plt.figure(figsize=(9, 5))
    sns.boxplot(data=df, x=category_col, y=numeric_col)
    plt.title(f"{numeric_col} by {category_col}")
    plt.xticks(rotation=45, ha="right")
    filename = f"{numeric_col}_by_{category_col}_boxplot.png".lower()
    filename = filename.replace(" ", "_")
    path = os.path.join(OUTPUT_FOLDER, filename)
    plt.savefig(path, bbox_inches="tight")
    plt.close()


def demographics_vs_violation(df):
    """Cross-tab of Race vs Violation Type."""
    return pd.crosstab(df["Race"], df["Violation Type"])


def save_demographics_heatmap(df):
    """Heatmap version of demographics_vs_violation()."""
    plt.figure(figsize=(10, 6))
    crosstab = demographics_vs_violation(df)
    sns.heatmap(crosstab, annot=True, fmt="d", cmap="Blues")
    plt.title("Race vs Violation Type")
    path = os.path.join(OUTPUT_FOLDER, "race_vs_violation_heatmap.png")
    plt.savefig(path, bbox_inches="tight")
    plt.close()


def accident_involvement_stats(df):
    """Count and % of stops involving accident/injury/damage/fatal."""
    total = len(df)
    stats = {"Total Violations": total}
    flags = ["Accident", "Personal Injury", "Property Damage", "Fatal"]
    for col in flags:
        if col in df.columns:
            count = int(df[col].sum())
            percent = round(100 * count / total, 2) if total else 0
            stats[col] = f"{count:,} ({percent}%)"
    return stats


def generate_insights(df, violations, hotspots, monthly):
    """Turn key numbers into short, interpreted sentences."""
    share = round(100 * violations.iloc[0] / len(df), 1)
    return [
        f"'{violations.index[0]}' is the most common violation "
        f"(~{share}% of all stops).",
        f"'{hotspots.index[0]}' is the busiest recorded location.",
        f"Violations peak in {monthly.idxmax()}.",
    ]


def write_conclusion(df):
    """Dataset condition, key patterns, and readiness - a summary."""
    missing = int(df.isna().sum().sum())
    return [
        f"{len(df):,} clean rows with {missing:,} missing cells "
        f"remaining (mostly optional fields).",
        "Violation type, location, and time of day are the "
        "strongest patterns found.",
        "Data is structured and ready for the dashboard and "
        "further reporting.",
    ]


def write_markdown_report(sections, insights, conclusion):
    """Combine every finding + Insights + Conclusion into a report."""
    lines = ["# Traffic Violations - EDA Report", ""]
    for title, content in sections:
        lines += [f"## {title}", "```", str(content), "```", ""]
    lines += ["## Insights"] + [f"- {p}" for p in insights] + [""]
    lines += ["## Conclusion"] + [f"- {p}" for p in conclusion]
    with open("EDA_Report.md", "w") as f:
        f.write("\n".join(lines))


CHART_QUESTIONS = [
    ("Most Common Violations", "top_violations.png",
     "Violation", most_common_violations),
    ("Top Hotspots", "top_hotspots.png", "Location", top_hotspots),
    ("Violations by Time of Day", "time_of_day.png",
     "Time Bucket", violations_by_time_bucket),
    ("Violations by Weekday", "by_weekday.png",
     "Weekday", violations_by_weekday),
    ("Violations by Month", "by_month.png", "Month", violations_by_month),
    ("Top Vehicle Makes", "top_makes.png", "Make", top_vehicle_makes),
    ("Top Vehicle Types", "top_vehicle_types.png",
     "Vehicle Type", top_vehicle_types),
    ("Violations by Category", "by_category.png",
     "Category", violations_by_category),
]


def run_full_eda(clean_csv_path):
    """Run every EDA step in order and write the final report."""
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    df = load_clean_data(clean_csv_path)
    sections = [("Data Understanding", data_understanding_summary(df))]

    for title, filename, xlabel, fn in CHART_QUESTIONS:
        result = fn(df)
        save_bar_chart(result, title, filename, xlabel)
        sections.append((title, result))

    numeric_cols = [c for c in NUMERIC_COLUMNS if c in df.columns]
    if numeric_cols:
        stats = numeric_quick_stats(df, numeric_cols)
        sections.append(("Numeric Quick Stats", stats))
        summary = numeric_univariate_stats(df, numeric_cols)
        sections.append(("Numeric Variable Summary", summary))
        outliers = {}
        for col in numeric_cols:
            save_distribution_plot(df, col)
            outliers[col] = detect_outliers_iqr(df, col)
        sections.append(("Outlier Counts (IQR)", outliers))

    if "Violation Type" in df.columns:
        breakdown = violation_type_breakdown(df)
        sections.append(("Violation Type Breakdown (%)", breakdown))

    if len(numeric_cols) >= 2:
        corr = numeric_correlation(df, numeric_cols)
        sections.append(("Correlation Between Numeric Variables", corr))
        save_scatter_plot(df, numeric_cols[0], numeric_cols[1])

    category = CATEGORY_FOR_NUMERIC_COMPARISON
    if "Accident Severity Score" in df.columns and category in df.columns:
        averages = average_by_category(
            df, "Accident Severity Score", category
        )
        save_bar_chart(
            averages, f"Average Severity by {category}",
            "severity_by_category_bar.png", category,
            ylabel="Average Accident Severity Score",
        )
        save_boxplot_by_category(df, "Accident Severity Score", category)
        sections.append((f"Average Severity by {category}", averages))

    save_demographics_heatmap(df)
    demo = demographics_vs_violation(df)
    sections.append(("Demographics vs Violation Type", demo))
    sections.append(("Accident Involvement", accident_involvement_stats(df)))

    violations = most_common_violations(df)
    hotspots = top_hotspots(df)
    monthly = violations_by_month(df)
    insights = generate_insights(df, violations, hotspots, monthly)
    write_markdown_report(sections, insights, write_conclusion(df))


if __name__ == "__main__":
    run_full_eda("traffic_violations_clean.csv")
