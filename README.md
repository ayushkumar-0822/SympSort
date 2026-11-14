# SympSort: Medical Cost & Lifestyle Factors
### Desktop-Style Web Analytics Application | IT Workshop Lab (PCC CS 393)

A premium, desktop-application-style web analytics platform built with **Python**, **Flask**, **Pandas**, **Seaborn**, and a custom **HTML5 / CSS3 / Vanilla JavaScript** desktop shell to compare health insurance charges between smokers and non-smokers.

---

## 1. Project Overview

In healthcare economics and insurance underwriting, individual lifestyle determinants—such as chronic tobacco usage—are associated with significant variations in medical expenditures. **SympSort** implements a verifiable, modular, and beginner-friendly Python data-analysis pipeline to ingest, clean, aggregate, and visualize empirical health insurance claims data.

Rather than using generic dashboard frameworks or Streamlit, this project provides a custom **desktop-style web interface** powered by a lightweight Python Flask backend and pure client-side vanilla JavaScript.

---

## 2. Exact Academic Question

This project directly implements **Problem #1** from the official **IT Workshop Lab (PCC CS 393)** mini-project curriculum:

> **"Find the average insurance charge for smokers vs. non-smokers using Pandas. Create a Seaborn barplot to visually compare the average costs between the two groups."**

---

## 3. Architecture & Premium UI/UX Design

```text
┌─────────────────────────────────────────────────────────────────┐
│                    DESKTOP WEB FRONTEND                         │
│   • Semantic HTML5 + Vanilla JS + High-Contrast Desktop CSS     │
│   • Views: Overview | Comparison | Explorer | Method | About    │
└───────────────────────────────▲─────────────────────────────────┘
                                │ JSON REST API & Image Streaming
┌───────────────────────────────▼─────────────────────────────────┐
│                    FLASK PYTHON BACKEND (app.py)                │
│   • /api/summary  • /api/chart  • /api/data  • /api/reload      │
└───────────────▲───────────────────────────────▲─────────────────┘
                │                               │
┌───────────────▼───────────────┐ ┌─────────────▼─────────────────┐
│     PANDAS ANALYSIS ENGINE    │ │   SEABORN / MATPLOTLIB PLOT   │
│  df.groupby("smoker").mean()  │ │  sns.barplot() -> 300 DPI PNG │
└───────────────▲───────────────┘ └───────────────────────────────┘
                │
┌───────────────▼───────────────┐
│  LOCAL CSV (data/insurance.csv│
│  1,338 records, 7 columns     │
└───────────────────────────────┘
```

### Visual Identity
- **Palette**: Warm off-white background (`#F8FAFC`), deep charcoal/navy text (`#0F172A`), muted teal accent (`#0D9488`), and terracotta (`#E76F51`).
- **Layout**: Native desktop shell with fixed left sidebar, top application bar with dataset status and reload controls, and smooth client-side view switching.
- **Components**: Metric cards, interactive data explorer with live multi-column search, categorical smoker filter, pagination, code viewer, and one-click chart/CSV exports.

---

## 4. Empirical Results at a Glance

Calculated from the authentic 1,338-record Kaggle dataset (`data/insurance.csv`):

| Cohort | Sample Size ($n$) | Cohort Share | Average Charge (Mean) | Median Charge | Standard Deviation |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Non-Smokers** (`smoker == "no"`) | 1,064 | 79.52% | **\$8,434.27 USD** | \$7,345.41 USD | \$5,993.78 USD |
| **Smokers** (`smoker == "yes"`) | 274 | 20.48% | **\$32,050.23 USD** | \$34,456.35 USD | \$11,541.55 USD |
| **Difference** | — | — | **+\$23,615.96 USD** | **+\$27,110.94 USD** | — |
| **Percentage Increase** | — | — | **+280.00%** | **+369.09%** | — |

> **Key Finding**: Average charges in the smoker group were **280.00% higher** than in the non-smoker group in this dataset. This represents an observed statistical correlation in the sample, not medical causation.

---

## 5. Application Views

1. **Overview**: Executive introduction to the research question, dynamic insight box, 4 primary metric cards, and dataset parameter breakdown.
2. **Cost Comparison**: Centerpiece view featuring the publication-grade Seaborn barplot (rendered at 300 DPI with currency ticks and overhead annotations) alongside group statistics and download options.
3. **Dataset Explorer**: Real-time searchable and paginated inspection table of all 1,338 rows with smoker category filtering (`All`, `Non-Smokers`, `Smokers`) and adjustable row count (15, 25, 50).
4. **Methodology**: Step-by-step analytical breakdown explaining Pandas grouping, validation, differences, and real code snippets.
5. **About Project**: Academic identification (PCC CS 393), technologies, Kaggle dataset attribution, and ethical scope.

---

## 6. Project Directory Structure

```text
SympSort/
├── main.py                     # Master launcher (Desktop App / CLI / Tests)
├── sympsort.py                 # Convenience alias for main.py
├── app.py                      # Flask application factory, routes & API endpoints
├── analysis.py                 # Core Pandas grouping and difference calculations
├── data_loader.py              # Defensive CSV loading and schema validation
├── visualization.py            # Seaborn barplot rendering and in-memory PNG generator
├── config.py                   # Centralized paths, column mappings, and styling
├── run.bat                     # 1-click Windows Command Prompt launcher
├── run_sympsort.bat            # CMD launcher alias
├── run.ps1                     # 1-click Windows PowerShell launcher
├── run_sympsort.ps1            # PowerShell launcher alias
├── pytest.ini                  # Pytest configuration
├── requirements.txt            # Python dependencies (Flask, Pandas, Seaborn, Matplotlib, Pytest)
├── .gitignore                  # Git exclusion rules
├── README.md                   # Setup guide and technical documentation
├── .vscode/
│   ├── launch.json             # VS Code F5 Run & Debug profiles
│   ├── settings.json           # VS Code Python environment settings
│   └── tasks.json              # VS Code preconfigured build/run tasks
├── templates/
│   └── index.html              # Custom Desktop Web App Shell template
├── static/
│   ├── css/
│   │   └── desktop.css         # Refined desktop styling system
│   └── js/
│       └── app.js              # Client-side routing, live search, pagination & API controller
├── data/
│   ├── .gitkeep
│   └── insurance.csv           # Official Kaggle dataset (1,338 records)
├── outputs/
│   ├── .gitkeep
│   └── smoker_charges_comparison.png  # High-res Seaborn barplot output (300 DPI)
├── tests/
│   ├── test_analysis.py        # Unit tests for calculations & plots
│   ├── test_data_validation.py # Unit tests for schema & dirty data
│   └── test_flask_app.py       # Integration tests for Flask endpoints & search
└── docs/
    ├── synopsis.md             # Formal academic synopsis for hardcopy submission
    ├── viva_questions.md       # 25+ viva voce questions with model answers
    └── project_timeline.md     # 6-week laboratory execution milestones
```

---

## 7. How to Run SympSort

You can run SympSort in any of three environments: **Windows PowerShell**, **Command Prompt (CMD)**, or **Visual Studio Code (VS Code)**.

### Method A: Running via Windows PowerShell

1. Open PowerShell and navigate to the project directory:
   ```powershell
   cd D:\Kumar\Sonykaka\SympSort
   ```
2. **Launch Desktop Web Application**:
   ```powershell
   .\run.ps1
   ```
   *(Or activate the virtual environment and run directly):*
   ```powershell
   .\.venv\Scripts\Activate.ps1
   python main.py
   ```
   *The application will open automatically in your browser at `http://127.0.0.1:5000`.*
3. **Run Terminal CLI Report (without browser)**:
   ```powershell
   .\run.ps1 -ArgsList "--cli"
   ```
4. **Run Automated Unit Tests**:
   ```powershell
   .\run.ps1 -ArgsList "--test"
   ```

> **Tip for PowerShell Script Execution**:  
> If PowerShell displays a script policy warning, run:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> ```

---

### Method B: Running via Windows Command Prompt (CMD)

1. Open Command Prompt (`cmd.exe`) and navigate to the project folder:
   ```cmd
   cd /d D:\Kumar\Sonykaka\SympSort
   ```
2. **Launch Desktop Web Application**:
   ```cmd
   run.bat
   ```
   *(You can also simply double-click `run.bat` in Windows File Explorer!)*
3. **Run Terminal CLI Report**:
   ```cmd
   run.bat --cli
   ```
4. **Run Automated Tests**:
   ```cmd
   run.bat --test
   ```

---

### Method C: Running via Visual Studio Code (VS Code)

1. Open the `SympSort` folder in VS Code (`File` ➔ `Open Folder...` ➔ select `D:\Kumar\Sonykaka\SympSort`).
2. VS Code automatically detects and selects the `.venv` Python interpreter.
3. **Run with F5 (Debug / Run)**:
   - Press **F5** or open the **Run & Debug** panel (<kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>D</kbd>).
   - Select **`SympSort: Run Desktop Web App (Flask)`** from the dropdown.
4. **Run with the Play Button**:
   - Open [main.py](file:///d:/Kumar/Sonykaka/SympSort/main.py) or [app.py](file:///d:/Kumar/Sonykaka/SympSort/app.py) and click the **▷ Run Python File** button in the top-right corner.
5. **Run via VS Code Tasks**:
   - Press <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>P</kbd>, type `Tasks: Run Task`, and select **`SympSort: Launch Desktop Web App (Flask)`**.

---

## 8. Dataset Verification

The project includes the verified Kaggle dataset:
- **Location**: `data/insurance.csv`
- **Rows**: 1,338 records (+1 header row)
- **Source**: [mirichoi0218/insurance on Kaggle](https://www.kaggle.com/datasets/mirichoi0218/insurance)

---

## 9. Automated Testing & Verification

To run the automated test suite:

```powershell
.\.venv\Scripts\pytest -v
```

### Verified Test Summary (18/18 Passing):
```text
============================= test session starts =============================
platform win32 -- Python 3.13.16, pytest-9.1.1, pluggy-1.7.0
rootdir: D:\Kumar\Sonykaka\SympSort
configfile: pytest.ini
testpaths: tests
collected 18 items

tests/test_analysis.py::test_standard_fixture_calculations PASSED        [  5%]
tests/test_analysis.py::test_zero_non_smoker_baseline PASSED             [ 11%]
tests/test_analysis.py::test_empty_dataframe_raises PASSED               [ 16%]
tests/test_analysis.py::test_missing_required_column_raises PASSED       [ 22%]
tests/test_analysis.py::test_seaborn_chart_generation PASSED             [ 27%]
tests/test_data_validation.py::test_missing_file_handling PASSED         [ 33%]
tests/test_data_validation.py::test_missing_required_columns PASSED      [ 38%]
tests/test_data_validation.py::test_non_numeric_and_null_charges PASSED  [ 44%]
tests/test_data_validation.py::test_whitespace_and_capitalization_normalization PASSED [ 50%]
tests/test_data_validation.py::test_unexpected_smoker_categories PASSED  [ 55%]
tests/test_data_validation.py::test_sample_dataset_generator PASSED      [ 61%]
tests/test_flask_app.py::test_index_page PASSED                          [ 66%]
tests/test_flask_app.py::test_api_summary_endpoint PASSED                [ 72%]
tests/test_flask_app.py::test_api_chart_endpoint PASSED                  [ 77%]
tests/test_flask_app.py::test_api_data_pagination PASSED                 [ 83%]
tests/test_flask_app.py::test_api_data_filtering_and_search PASSED       [ 88%]
tests/test_flask_app.py::test_api_reload_endpoint PASSED                 [ 94%]
tests/test_flask_app.py::test_api_downloads PASSED                       [100%]

============================= 18 passed in 9.08s ==============================
```

---

## 10. Academic Attribution & Links

- **Course**: Mini Project of IT Workshop Lab (`PCC CS 393`)
- **Academic Synopsis**: [docs/synopsis.md](file:///d:/Kumar/Sonykaka/SympSort/docs/synopsis.md)
- **Viva Voce Q&A**: [docs/viva_questions.md](file:///d:/Kumar/Sonykaka/SympSort/docs/viva_questions.md)
- **Project Timeline**: [docs/project_timeline.md](file:///d:/Kumar/Sonykaka/SympSort/docs/project_timeline.md)
- **Generated 300 DPI Chart**: [outputs/smoker_charges_comparison.png](file:///d:/Kumar/Sonykaka/SympSort/outputs/smoker_charges_comparison.png)
