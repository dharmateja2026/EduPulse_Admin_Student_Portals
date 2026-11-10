"""Analyze exported feedback data using Pandas, NumPy and Matplotlib.

The demo application stores submissions in data/feedback.json. This script
reads that file and produces aggregated CSV and PNG charts. Comments and
submission-level rows are never included in the report.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "feedback.json"
OUT = ROOT / "reports"
OUT.mkdir(exist_ok=True)

def main():
    if not DATA.exists():
        print("No feedback yet. Submit a form in the website first.")
        return
    submissions = json.loads(DATA.read_text(encoding="utf-8"))
    if not submissions:
        print("No feedback yet.")
        return
    records = []
    for row in submissions:
        for idx, rating in enumerate(row["ratings"], start=1):
            records.append({"course_code": row["course_code"], "question": f"Q{idx}", "rating": int(rating)})
    df = pd.DataFrame(records)
    course_stats = df.groupby("course_code").agg(
        average_rating=("rating", "mean"),
        rating_count=("rating", "count"),
    ).reset_index()
    question_stats = df.groupby(["course_code", "question"])["rating"].mean().reset_index(name="average_rating")
    distribution = pd.crosstab(df["course_code"], df["rating"]).reindex(columns=[1,2,3,4,5], fill_value=0)
    # Suppress course-level aggregates with fewer than five submissions.
    response_counts = pd.Series({r["course_code"]: 1 for r in submissions}).groupby(level=0).sum()
    for idx, row in course_stats.iterrows():
        if response_counts.get(row["course_code"], 0) < 5:
            course_stats.loc[idx, "average_rating"] = np.nan
    course_stats.to_csv(OUT / "course_wise_feedback_report.csv", index=False)
    question_stats.to_csv(OUT / "question_average_report.csv", index=False)
    distribution.to_csv(OUT / "rating_distribution.csv")
    if course_stats["average_rating"].notna().any():
        fig, ax = plt.subplots(figsize=(9, 5))
        plot_data = course_stats.dropna()
        ax.bar(plot_data["course_code"], plot_data["average_rating"], color="#7357e8")
        ax.set_ylim(0, 5)
        ax.set_ylabel("Average rating (1–5)")
        ax.set_title("Average course ratings")
        ax.grid(axis="y", alpha=.2)
        fig.tight_layout()
        fig.savefig(OUT / "course_rating_comparison.png", dpi=160)
        plt.close(fig)
    fig, ax = plt.subplots(figsize=(9, 5))
    totals = df["rating"].value_counts().reindex([1,2,3,4,5], fill_value=0)
    ax.bar(totals.index.astype(str), totals.values, color=["#e56b91","#f3a449","#20b886","#4c83f2","#7357e8"])
    ax.set_xlabel("Rating")
    ax.set_ylabel("Number of answers")
    ax.set_title("Rating distribution")
    ax.grid(axis="y", alpha=.2)
    fig.tight_layout()
    fig.savefig(OUT / "rating_distribution.png", dpi=160)
    plt.close(fig)
    print(f"Reports created in: {OUT}")

if __name__ == "__main__":
    main()
