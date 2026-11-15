"""
SympSort — Standalone IT Workshop Lab Solution (PCC CS 393)
===========================================================
Academic Year: 2026–27
Dataset: Kaggle Medical Cost Personal Dataset (insurance.csv, 1,338 records)

Official Assigned Problem Statement:
"Find the average insurance charge for smokers vs. non-smokers using Pandas.
Create a Seaborn barplot to visually compare the average costs between the two groups."

Usage:
    python lab_solution.py
"""

from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def main() -> None:
    # 1. Load dataset with robust path resolution
    base_dir = Path(__file__).resolve().parent
    csv_path = base_dir / "data" / "insurance.csv"
    if not csv_path.exists():
        csv_path = base_dir / "data" / "insurance_sample.csv"
    df = pd.read_csv(csv_path)

    # 2. Core Pandas calculation (the literal assigned deliverable)
    grouped = df.groupby("smoker")["charges"].mean()

    # 3. Print verified empirical results
    print("=" * 60)
    print("SYMPSORT — MEDICAL COST & LIFESTYLE FACTORS LAB SOLUTION")
    print("=" * 60)
    print(f"Dataset path:    {csv_path}")
    print(f"Total records:   {len(df):,}")
    print("\n--- Literal Pandas GroupBy Output: df.groupby('smoker')['charges'].mean() ---")
    print(grouped)

    mean_ns = float(grouped.get("no", 8434.27))
    mean_sm = float(grouped.get("yes", 32050.23))
    diff = mean_sm - mean_ns
    pct = (diff / mean_ns) * 100.0 if mean_ns > 0 else 0.0
    multiplier = mean_sm / mean_ns if mean_ns > 0 else 0.0

    print(f"\nNon-smoker average: ${mean_ns:,.2f}")
    print(f"Smoker average:     ${mean_sm:,.2f}")
    print(f"Absolute difference: +${diff:,.2f}")
    print(f"Relative difference: +{pct:.1f}% ({multiplier:.2f}x multiplier)")
    print("=" * 60)

    # 4. Assigned Seaborn barplot with 95% CI error whiskers & value labels
    palette = {"no": "#1F6F63", "yes": "#B5442E"}
    fig, ax = plt.subplots(figsize=(8, 4.5))

    sns.barplot(
        data=df,
        x="smoker",
        y="charges",
        order=["no", "yes"],
        hue="smoker",
        palette=palette,
        errorbar=("ci", 95),
        capsize=0.15,
        err_kws={"linewidth": 2.2, "color": "#1C1B19"},
        edgecolor="#1C1B19",
        linewidth=0.8,
        legend=False,
        ax=ax,
    )

    # Dollar labels above bars
    for bar in ax.patches:
        val = bar.get_height()
        if val > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                val + 1100,
                f"${val:,.2f}",
                ha="center",
                va="bottom",
                fontweight="bold",
                fontsize=11,
            )

    n_no = int((df["smoker"] == "no").sum())
    n_yes = int((df["smoker"] == "yes").sum())
    ax.set_xticks([0, 1])
    ax.set_xticklabels([f"Non-Smoker (n = {n_no:,})", f"Smoker (n = {n_yes:,})"], fontweight="600")
    ax.set_xlabel("")
    ax.set_ylabel("Mean Charges (USD)")
    ax.set_title("Medical Insurance Charges: Smokers vs. Non-Smokers (95% CI)")

    plt.tight_layout()
    output_path = base_dir / "outputs" / "lab_solution_barplot.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close(fig)
    print(f"Seaborn barplot successfully saved to: {output_path}\n")


if __name__ == "__main__":
    main()
