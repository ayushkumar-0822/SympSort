"""Streamlit Application for Medical Cost & Lifestyle Factors.

Course: IT Workshop Lab (PCC CS 393) - Mini Project
Official Problem Statement:
"Find the average insurance charge for smokers vs. non-smokers using Pandas.
Create a Seaborn barplot to visually compare the average costs between the two groups."
"""

from __future__ import annotations

import io
from pathlib import Path
import streamlit as st

import config
from data_loader import load_dataset, create_sample_dataset
from analysis import calculate_smoker_charges
from visualization import create_smoker_barplot


# -----------------------------------------------------------------------------
# Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title=f"{config.PROJECT_NAME} | {config.COURSE_CODE}",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Custom Styling: Warm Neutral, Editorial, Academic Feel
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Main container styling */
    .main {
        background-color: #FAF9F6;
        color: #1E293B;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Academic Badge */
    .lab-badge {
        display: inline-block;
        padding: 4px 10px;
        background-color: #E2E8F0;
        color: #334155;
        font-size: 0.8rem;
        font-weight: 600;
        border-radius: 4px;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }

    /* Metric cards */
    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 18px 20px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        margin-bottom: 12px;
        transition: transform 0.15s ease-in-out;
    }
    .metric-card:hover {
        border-color: #CBD5E1;
    }
    .metric-label {
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: #64748B;
        font-weight: 600;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.65rem;
        font-weight: 700;
        color: #0F172A;
        line-height: 1.2;
    }
    .metric-sub {
        font-size: 0.8rem;
        color: #64748B;
        margin-top: 6px;
    }

    /* Status indicators */
    .status-pill {
        display: inline-flex;
        align-items: center;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.82rem;
        font-weight: 600;
    }
    .status-loaded {
        background-color: #DCFCE7;
        color: #166534;
        border: 1px solid #BBF7D0;
    }
    .status-missing {
        background-color: #FEE2E2;
        color: #991B1B;
        border: 1px solid #FECACA;
    }

    /* Section card container */
    .content-box {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 22px 24px;
        margin-bottom: 24px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    }

    /* Footer */
    .custom-footer {
        border-top: 1px solid #E2E8F0;
        padding-top: 20px;
        margin-top: 40px;
        font-size: 0.85rem;
        color: #64748B;
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Sidebar Configuration & Controls
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="lab-badge">ACADEMIC SUBMISSION</div>', unsafe_allow_html=True)
    st.title("Project Controls")
    st.caption(f"{config.COURSE_NAME} ({config.COURSE_CODE})")

    st.markdown("---")
    st.subheader("Dataset Configuration")

    dataset_path_input = st.text_input(
        "CSV File Path",
        value=str(config.DEFAULT_DATA_PATH),
        help="Path to the insurance.csv file.",
    )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        reload_clicked = st.button("🔄 Reload Data", use_container_width=True)
    with col_btn2:
        use_sample = st.button("🧪 Load Sample", use_container_width=True, help="Load 8-row demonstration data")

    st.markdown("---")
    st.subheader("Official Resources")
    st.markdown(
        f"- [Kaggle Dataset Page]({config.DATASET_SOURCE_URL})\n"
        "- [Pandas Documentation](https://pandas.pydata.org/docs/)\n"
        "- [Seaborn Documentation](https://seaborn.pydata.org/)\n"
        "- [Project Docs / Synopsis](docs/synopsis.md)"
    )

    st.markdown("---")
    st.caption("IT Workshop Lab Mini Project\nAcademic Year 2026-2027")


# -----------------------------------------------------------------------------
# Data Loading & Processing
# -----------------------------------------------------------------------------
target_path = Path(dataset_path_input)

if use_sample:
    df_raw = create_sample_dataset()
    df_valid, _, report = load_dataset_from_df(df_raw) if 'load_dataset_from_df' in globals() else (None, None, None)
    # If loading sample directly
    from config import EXPECTED_SMOKER_VALUES, LABEL_NON_SMOKER, LABEL_SMOKER, SMOKER_NO, SMOKER_YES
    df_clean = df_raw.copy()
    df_clean["smoker_clean"] = df_clean["smoker"].astype(str).str.strip().str.lower()
    df_clean["charges"] = pd.to_numeric(df_clean["charges"], errors="coerce")
    df_valid = df_clean[df_clean["charges"].notna() & df_clean["smoker_clean"].isin(EXPECTED_SMOKER_VALUES)].copy()
    label_map = {SMOKER_NO: LABEL_NON_SMOKER, SMOKER_YES: LABEL_SMOKER}
    df_valid["smoker_label"] = df_valid["smoker_clean"].map(label_map)
    is_sample_mode = True
    status_label = "Sample Demonstration Data Loaded"
    status_class = "status-loaded"
else:
    is_sample_mode = False
    df_valid, df_raw, report = load_dataset(target_path)
    if report.is_valid:
        status_label = f"Dataset Loaded: {target_path.name} ({report.total_raw_rows} rows)"
        status_class = "status-loaded"
    else:
        status_label = "Dataset Missing or Invalid"
        status_class = "status-missing"


# -----------------------------------------------------------------------------
# A. Header Section
# -----------------------------------------------------------------------------
st.markdown(f'<div class="lab-badge">{config.COURSE_NAME} | {config.COURSE_CODE}</div>', unsafe_allow_html=True)
st.title(f"🚀 {config.PROJECT_NAME}")
st.markdown(f"**Medical Cost & Lifestyle Factors** — *{config.PROJECT_SUBTITLE}*")

col_head_info, col_head_status = st.columns([3, 2])
with col_head_info:
    st.markdown(
        f"**Official Source:** [{config.DATASET_SOURCE_NAME}]({config.DATASET_SOURCE_URL}) "
        f"| Target Assignment: Problem #1"
    )
with col_head_status:
    st.markdown(
        f'<div style="text-align: right;"><span class="status-pill {status_class}">● {status_label}</span></div>',
        unsafe_allow_html=True,
    )

st.markdown("---")


# -----------------------------------------------------------------------------
# Handle Missing or Invalid Dataset
# -----------------------------------------------------------------------------
if not is_sample_mode and (df_valid is None or not report.is_valid):
    st.error(f"**Dataset Issue Encountered:**\n\n{report.error_message}")
    
    st.info(
        "### How to provide the required dataset:\n\n"
        "1. Download `insurance.csv` from the official Kaggle dataset page: \n"
        f"   [{config.DATASET_SOURCE_URL}]({config.DATASET_SOURCE_URL})\n"
        "2. Save or copy the file into the project directory at:\n"
        f"   `{config.DEFAULT_DATA_PATH.resolve()}`\n"
        "3. Click **🔄 Reload Data** in the left sidebar.\n\n"
        "*Alternatively, click **🧪 Load Sample** in the sidebar to inspect the application with demonstration data.*"
    )
    st.stop()


# -----------------------------------------------------------------------------
# Perform Core Analysis
# -----------------------------------------------------------------------------
try:
    results = calculate_smoker_charges(df_valid)
except Exception as exc:
    st.error(f"An error occurred while calculating group statistics: {exc}")
    st.stop()


# -----------------------------------------------------------------------------
# B. Overview & "Analysis at a Glance"
# -----------------------------------------------------------------------------
st.markdown("### Overview")
st.markdown(
    f"This project addresses the official IT Workshop Lab problem:  \n"
    f"> *\"{config.PROBLEM_STATEMENT}\"*  \n\n"
    "Using genuine Pandas aggregation, insurance charges are partitioned by smoking status. "
    "A Seaborn barplot visualizes the arithmetic mean of charges for each cohort to evaluate "
    "the observed empirical difference."
)

if is_sample_mode:
    st.warning("⚠️ **Notice:** You are currently viewing small demonstration data. Real project results require `data/insurance.csv`.")

# Analysis at a Glance Row
col_g1, col_g2, col_g3, col_g4 = st.columns(4)
with col_g1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Total Records</div>
            <div class="metric-value">{len(df_raw):,}</div>
            <div class="metric-sub">Raw rows in CSV</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_g2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Valid Records</div>
            <div class="metric-value">{results.total_valid_records:,}</div>
            <div class="metric-sub">Processed in analysis</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_g3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Non-Smoker Records</div>
            <div class="metric-value">{results.non_smoker_count:,}</div>
            <div class="metric-sub">{results.non_smoker_count / results.total_valid_records * 100:.1f}% of analyzed cohort</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_g4:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Smoker Records</div>
            <div class="metric-value">{results.smoker_count:,}</div>
            <div class="metric-sub">{results.smoker_count / results.total_valid_records * 100:.1f}% of analyzed cohort</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# C. Main Comparison & Metric Cards
# -----------------------------------------------------------------------------
st.markdown("### Core Comparison: Average Insurance Charges")

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.markdown(
        f"""
        <div class="metric-card" style="border-left: 4px solid {config.COLOR_NON_SMOKER};">
            <div class="metric-label">Non-Smoker Mean</div>
            <div class="metric-value">{results.format_non_smoker_mean()}</div>
            <div class="metric-sub">Sample size: n = {results.non_smoker_count:,}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_m2:
    st.markdown(
        f"""
        <div class="metric-card" style="border-left: 4px solid {config.COLOR_SMOKER};">
            <div class="metric-label">Smoker Mean</div>
            <div class="metric-value">{results.format_smoker_mean()}</div>
            <div class="metric-sub">Sample size: n = {results.smoker_count:,}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_m3:
    st.markdown(
        f"""
        <div class="metric-card" style="border-left: 4px solid #6366F1;">
            <div class="metric-label">Absolute Difference</div>
            <div class="metric-value">{results.format_absolute_difference()}</div>
            <div class="metric-sub">Smoker Mean - Non-Smoker Mean</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_m4:
    st.markdown(
        f"""
        <div class="metric-card" style="border-left: 4px solid #8B5CF6;">
            <div class="metric-label">Percentage Difference</div>
            <div class="metric-value">{results.format_percentage_difference()}</div>
            <div class="metric-sub">Relative to Non-Smoker Mean</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# D. Required Seaborn Visualization
# -----------------------------------------------------------------------------
st.markdown("### Seaborn Barplot Visualization")

fig = create_smoker_barplot(results.df_grouped, save_path=config.SAVED_CHART_PATH)
st.pyplot(fig, use_container_width=True)

# Dynamic interpretation & Academic disclaimer
st.markdown(
    f"""
    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 14px 18px; margin-top: 10px;">
        <p style="margin: 0 0 6px 0; font-size: 0.95rem; font-weight: 600; color: #1E293B;">
            📈 Result Interpretation: {results.dynamic_statement}
        </p>
        <p style="margin: 0; font-size: 0.85rem; color: #64748B;">
            {results.academic_disclaimer}
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Export / Download Actions
st.markdown("<br>", unsafe_allow_html=True)
col_dl1, col_dl2, col_dl3 = st.columns([2, 2, 4])

with col_dl1:
    # Save figure to in-memory buffer for instant download
    img_buf = io.BytesIO()
    fig.savefig(img_buf, format="png", dpi=300, bbox_inches="tight")
    st.download_button(
        label="📥 Download Chart (PNG)",
        data=img_buf.getvalue(),
        file_name="smoker_vs_nonsmoker_charges.png",
        mime="image/png",
        use_container_width=True,
    )

with col_dl2:
    csv_buf = results.df_grouped.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Group Summary (CSV)",
        data=csv_buf,
        file_name="smoker_charges_summary.csv",
        mime="text/csv",
        use_container_width=True,
    )


# -----------------------------------------------------------------------------
# E. Dataset Explorer (Collapsible)
# -----------------------------------------------------------------------------
st.markdown("---")
with st.expander("🔍 Dataset Explorer & Quality Report", expanded=False):
    st.markdown("#### Sample Records Preview")
    rows_to_show = st.slider("Number of preview rows", min_value=5, max_value=50, value=10, step=5)
    st.dataframe(df_raw.head(rows_to_show), use_container_width=True)

    st.markdown("#### Column Structure & Schema")
    col_summary = []
    for col in df_raw.columns:
        col_summary.append({
            "Column Name": col,
            "Data Type": str(df_raw[col].dtype),
            "Non-Null Count": int(df_raw[col].notna().sum()),
            "Null Count": int(df_raw[col].isna().sum()),
            "Unique Values": int(df_raw[col].nunique()),
            "Sample Value": str(df_raw[col].iloc[0]) if len(df_raw) > 0 else "N/A",
        })
    st.table(pd.DataFrame(col_summary))

    st.markdown("#### Column Definitions")
    st.markdown(
        """
        | Column | Type | Description | Role in Analysis |
        | :--- | :--- | :--- | :--- |
        | **`age`** | Integer | Age of primary beneficiary | Contextual demographic |
        | **`sex`** | Categorical | Insurance contractor gender (`female`, `male`) | Contextual demographic |
        | **`bmi`** | Float | Body mass index (weight in kg / height in m²) | Lifestyle / physiological indicator |
        | **`children`** | Integer | Number of children / dependents covered | Demographic |
        | **`smoker`** | Categorical | Smoking status (`yes`, `no`) | **Primary Independent Variable** |
        | **`region`** | Categorical | Beneficiary's residential area in US | Contextual geographic |
        | **`charges`** | Float | Individual medical costs billed by health insurance (USD) | **Primary Dependent Variable** |
        """
    )


# -----------------------------------------------------------------------------
# F. Methodology & Real Python Logic
# -----------------------------------------------------------------------------
with st.expander("🔬 Methodology & Python Implementation", expanded=False):
    st.markdown(
        """
        #### Analytical Pipeline Steps
        1. **Dataset Loading**: Read CSV from disk using `pandas.read_csv()`.
        2. **Validation & Normalization**: Verify required columns (`smoker`, `charges`), strip whitespace, lowercase categories, and coerce charges to numeric float.
        3. **Grouping**: Group valid records by `smoker` using `df.groupby("smoker")`.
        4. **Aggregation**: Compute the arithmetic mean of `charges` for each group using `.mean()`.
        5. **Metric Calculation**: Calculate absolute difference and percentage difference relative to the non-smoker baseline.
        6. **Visualization**: Plot group means using Seaborn `sns.barplot()`.
        """
    )
    
    st.markdown("#### Python Code Executed by Application")
    st.code(
        """
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# 1. Load data
df = pd.read_csv("data/insurance.csv")

# 2. Clean & normalize
df["smoker"] = df["smoker"].str.strip().str.lower()
df["charges"] = pd.to_numeric(df["charges"], errors="coerce")
valid_df = df.dropna(subset=["smoker", "charges"])

# 3. Core Syllabus Groupby Mean
average_charges = valid_df.groupby("smoker")["charges"].mean()

smoker_avg = average_charges["yes"]
non_smoker_avg = average_charges["no"]
diff = smoker_avg - non_smoker_avg
pct_diff = (diff / non_smoker_avg) * 100

print(f"Non-Smoker Average: ${non_smoker_avg:,.2f}")
print(f"Smoker Average:     ${smoker_avg:,.2f}")
print(f"Percentage Diff:    {pct_diff:.2f}%")

# 4. Seaborn Barplot
plot_df = valid_df.groupby("smoker", as_index=False)["charges"].mean()
plot_df["smoker_label"] = plot_df["smoker"].map({"no": "Non-Smoker", "yes": "Smoker"})

sns.barplot(data=plot_df, x="smoker_label", y="charges", palette={"Non-Smoker": "#2A9D8F", "Smoker": "#E76F51"})
plt.title("Average Medical Insurance Charges: Smokers vs. Non-Smokers")
plt.ylabel("Average Charges (USD)")
plt.xlabel("Smoking Status")
plt.show()
        """,
        language="python",
    )


# -----------------------------------------------------------------------------
# G. Academic Limitations & Ethics
# -----------------------------------------------------------------------------
with st.expander("⚖️ Academic Scope, Limitations & Ethical Notes", expanded=False):
    st.markdown(
        """
        - **Descriptive, Not Causal**: This analysis demonstrates an empirical correlation between self-reported smoking status and annual insurance charges. It does not establish that smoking was the sole or direct causal driver for any individual's bills.
        - **Potential Confounding Variables**: Other covariates (e.g., beneficiary age, BMI, preexisting health conditions, geographic region, and insurance plan tier) likely interact with health outcomes and billing rates.
        - **Dataset Specificity**: The findings reflect the 1,338 individuals sampled in the mirichoi0218 Kaggle dataset (originating from Brett Lantz's healthcare research data) and should not be generalized uncritically to other healthcare systems or national populations.
        """
    )


# -----------------------------------------------------------------------------
# H. Academic Footer
# -----------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="custom-footer">
        <p><strong>{config.PROJECT_NAME}</strong> — {config.PROJECT_TITLE} | Mini Project of {config.COURSE_NAME} ({config.COURSE_CODE})</p>
        <p>Data Source: <a href="{config.DATASET_SOURCE_URL}" target="_blank">Kaggle Medical Cost Personal Datasets</a></p>
        <p>Prepared for academic evaluation and classroom demonstration.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Direct Python Execution Entrypoint
# Allows running with: python app.py directly from CMD / PowerShell / VS Code
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    if not st.runtime.exists():
        import sys
        from streamlit.web import cli as stcli
        sys.argv = ["streamlit", "run", __file__]
        sys.exit(stcli.main())
