# Project Timeline & Execution Milestones
## Mini Project: SympSort — Medical Cost & Lifestyle Factors (PCC CS 393)

This document details the structured 6-week laboratory schedule followed for the development, verification, and presentation of the IT Workshop Lab Mini Project.

---

### Comprehensive 6-Week Gantt & Milestone Breakdown

| Week | Phase | Key Tasks & Technical Activities | Tools & Techniques | Deliverables | Assigned Responsibility |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **Week 1** | **Problem Formulation & Literature Review** | • Review official lab assignment list.<br>• Examine Kaggle dataset source (`mirichoi0218/insurance`).<br>• Research domain variables (`age`, `bmi`, `smoker`, `charges`).<br>• Create project workspace directory structure. | • Kaggle dataset portal<br>• Markdown<br>• Git | • `data/` directory initialized<br>• Literature review notes<br>• Problem statement validation | Entire Team |
| **Week 2** | **Data Ingestion & Hygiene Architecture** | • Implement centralized constants in `config.py`.<br>• Develop defensive CSV loader in `data_loader.py`.<br>• Implement normalization (strip whitespace, lowercase).<br>• Coerce numeric charges and capture corrupted values. | • Python 3.13<br>• `pandas`<br>• `dataclasses`<br>• `pathlib` | • `config.py`<br>• `data_loader.py`<br>• `ValidationReport` dataclass | Student 1 & Student 3 |
| **Week 3** | **Core Pandas Grouping & Analysis** | • Implement `df.groupby("smoker")["charges"].mean()`.<br>• Compute arithmetic means, medians, and standard deviations.<br>• Implement absolute difference formula.<br>• Implement relative percentage difference with division-by-zero guard. | • `pandas`<br>• Floating-point arithmetic<br>• Dynamic text interpolation | • `analysis.py`<br>• `SmokerAnalysisResult` dataclass<br>• Preliminary numerical outputs | Student 1 & Student 4 |
| **Week 4** | **Statistical Graphics & Seaborn Styling** | • Build publication-grade barplot function in `visualization.py`.<br>• Configure Seaborn theme (`whitegrid`, restrained palette).<br>• Implement Matplotlib currency tick formatters.<br>• Annotate bar tops with exact dollar labels.<br>• Export high-res PNG at 300 DPI. | • `seaborn`<br>• `matplotlib.pyplot`<br>• `matplotlib.ticker` | • `visualization.py`<br>• `outputs/smoker_charges_comparison.png` | Student 2 |
| **Week 5** | **Interactive Streamlit Workspace** | • Create `app.py` for live classroom demonstration.<br>• Implement metric cards for group means and percentage differences.<br>• Embed interactive Seaborn figure.<br>• Build collapsible Dataset Explorer & Methodology inspection.<br>• Provide one-click chart (PNG) and summary (CSV) download buttons. | • `streamlit`<br>• Custom CSS<br>• `io.BytesIO` | • `app.py`<br>• Interactive web dashboard<br>• Export mechanisms | Student 2 & Student 3 |
| **Week 6** | **Automated Testing, Documentation & Viva Prep** | • Author 11 comprehensive automated tests under `pytest`.<br>• Execute test suite and verify 100% pass rate.<br>• Compile official academic synopsis following lab guidelines.<br>• Prepare 25+ viva voce questions and answers.<br>• Finalize beginner-friendly `README.md`. | • `pytest`<br>• IEEE reference formatting<br>• Markdown | • `tests/test_analysis.py`<br>• `tests/test_data_validation.py`<br>• `docs/synopsis.md`<br>• `docs/viva_questions.md`<br>• `README.md` | Entire Team |

---

### Key Milestone Review Points

1. **Milestone M1 (End of Week 2): Data Pipeline Sign-Off**
   - Verified that `data/insurance.csv` loads with 1,338 rows.
   - Confirmed zero missing values in primary columns (`smoker`, `charges`).

2. **Milestone M2 (End of Week 3): Mathematical Verification**
   - Verified exact values:
     - Smoker Mean: **\$32,050.23 USD**
     - Non-Smoker Mean: **\$8,434.27 USD**
     - Absolute Difference: **+\$23,615.96 USD**
     - Percentage Difference: **+280.00%**

3. **Milestone M3 (End of Week 4): Visualization Sign-Off**
   - Seaborn barplot rendered with clean typography, restrained colors, and exact overhead labels.
   - Saved 300 DPI image in `outputs/smoker_charges_comparison.png`.

4. **Milestone M4 (End of Week 5): User Interface Demonstration**
   - Streamlit app runs with instant data reloading, interactive filters, and responsive layout.

5. **Milestone M5 (End of Week 6): Academic Deliverable Completion**
   - 11/11 tests passing cleanly under `pytest`.
   - Comprehensive IEEE-compliant academic synopsis compiled for spiral-bound submission.
