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
- **Palette**: Calm editorial paper background (`#F6F3EC`), crisp hairline card borders (`#E2DCCF`), deep green sidebar (`#17302B`), teal accent (`#1F6F63` for non-smoker / primary actions), and brick-red (`#B5442E` for smoker / emphasis).
- **Typography**: Self-hosted **Source Serif 4** (`static/fonts/`) with lining, tabular figures (`font-variant-numeric: lining-nums tabular-nums`) so numbers never drop below baseline. System UI sans-serif for interface controls.
- **Layout**: Fixed deep green sidebar, sticky header with dynamic action controls, and responsive collapse under 1000px and 700px.

---

## 4. Empirical Results at a Glance

Calculated from the authentic 1,338-record Kaggle dataset (`data/insurance.csv`):

| Cohort | Sample Size ($n$) | Cohort Share | Average Charge (Mean) | 95% Confidence Interval | Median Charge | Standard Deviation |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Non-Smokers** (`smoker == "no"`) | 1,064 | 79.52% | **\$8,434.27 USD** | \$8,434.27 ± \$360.15 | \$7,345.41 USD | \$5,993.78 USD |
| **Smokers** (`smoker == "yes"`) | 274 | 20.48% | **\$32,050.23 USD** | \$32,050.23 ± \$1,366.61 | \$34,456.35 USD | \$11,541.55 USD |
| **Difference** | — | — | **+\$23,615.96 USD** | — | **+\$27,110.94 USD** | — |
| **Percentage Increase** | — | — | **+280.00%** | — | **+369.09%** | — |

> **Key Finding**: Average charges in the smoker group were **280.00% higher** (3.80× multiplier) than in the non-smoker group ($t = 32.75, p < 0.001, \text{Cohen's } d = 3.16$).

---

## 5. Application Views

1. **Overview**: Assigned problem deliverable, dynamic headline finding, primary KPI metrics, secondary strip (*Multiplier 3.80×*, *Non-smokers n = 1,064*, *Smokers n = 274*, *Valid records 1,338*), 16:9 Seaborn chart with 95% CI error whiskers, and sample records table.
2. **Cost Comparison**: Detailed statistical table with 95% CIs, **Beyond the Average** multi-chart explorer (7 chart kinds: *Barplot*, *KDE Distribution*, *Boxplot*, *BMI vs Charges*, *Region*, *Sex*, *Age Bands*), **Is the Difference Real?** statistical significance card, and the **Compare a Profile** empirical subgroup lookup tool.
3. **Dataset Explorer**: Paginated inspection table with smoker pills (`All 1,338`, `Non-smokers 1,064`, `Smokers 274`), live **Selection Summary Strip** (matched count, mean, median, mean BMI), sticky headers, and filter reset.
4. **Methodology**: Analytical pipeline explanation, dark `#1F2523` code block with Copy button, live `df.groupby('smoker')['charges'].mean()` terminal output, and **Data Quality & Ingestion Audit Card** (`df.describe()`, `df.head()`, `df.info()`).
5. **About Project**: Academic identification (**B.Tech IT Workshop Lab PCC CS 393, Academic Year 2026–27**), student submission placeholders, verbatim problem statement quote block, technology stack, and methodological limitations.

---

## 6. Project Directory Structure

```text
SympSort/
├── lab_solution.py             # Minimal ~35-line standalone lab submission script
├── main.py                     # Master launcher (Desktop App / CLI / Tests)
├── sympsort.py                 # Convenience alias for main.py
├── app.py                      # Flask application factory, REST APIs & asset versioning
├── analysis.py                 # Core Pandas grouping, 95% CIs, Welch's t-test, Cohen's d
├── data_loader.py              # Defensive CSV loading and schema validation
├── visualization.py            # 7-kind Seaborn/Matplotlib chart engine with 95% CI whiskers
├── config.py                   # Centralized paths, column mappings, 16:9 sizing & styling
├── run.bat                     # 1-click Windows Command Prompt launcher
├── run.ps1                     # 1-click Windows PowerShell launcher
├── pytest.ini                  # Pytest configuration
├── requirements.txt            # Python dependencies
├── templates/
│   └── index.html              # Single-page shell with versioned assets (?v={{ asset_version }})
├── static/
│   ├── css/
│   │   └── desktop.css         # Refined editorial styling system (paper bg, deep green sidebar)
│   ├── js/
│   │   └── app.js              # Client-side routing, multi-chart explorer, profile matcher
│   └── fonts/
│       ├── source-serif-4-roman.woff2   # Self-hosted Source Serif 4 Roman
│       └── source-serif-4-italic.woff2  # Self-hosted Source Serif 4 Italic
├── data/
│   ├── insurance.csv           # Official Kaggle dataset (1,338 records)
│   └── insurance_sample.csv    # Fallback sample dataset
├── outputs/
│   ├── smoker_charges_chart.png         # Pre-saved 300 DPI barplot
│   ├── smoker_charges_comparison.png    # Pre-saved 300 DPI comparison chart
│   └── lab_solution_barplot.png         # Output of lab_solution.py
├── tests/
│   ├── test_analysis.py        # Unit tests for calculations, 95% CIs & metrics
│   ├── test_data_validation.py # Unit tests for schema validation & corrupted data
│   └── test_flask_app.py       # Integration tests for 40 endpoints, multi-charts & tools
└── docs/
    ├── synopsis.md             # Formal academic synopsis for hardcopy submission
    ├── viva_questions.md       # 25 high-yield viva voce questions with model answers
    └── project_timeline.md     # 6-week laboratory execution milestones
```

---

## 7. How to Run SympSort

### 1. Run the Standalone Lab Solution Script (Instant Problem Statement Answer)
```powershell
python lab_solution.py
```
Outputs the literal Pandas `df.groupby('smoker')['charges'].mean()`, verified numbers, and saves `outputs/lab_solution_barplot.png` at 300 DPI.

### 2. Launch the Desktop Web Application
```powershell
python main.py
```
Open **`http://127.0.0.1:5000`** in your browser and press **`Ctrl+Shift+R`** to view the full application.

### 3. Run the Automated Test Suite (40/40 Passing)
```powershell
pytest -v
```
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

To run the full automated test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

### Verified Test Summary (40/40 Passing):
- **`tests/test_analysis.py`** (9 tests): Grouped means exact match ($8,434.27 and $32,050.23), multiplier 3.80×, +280.0% difference, JSON serialization, exception handling for empty/corrupted DataFrames.
- **`tests/test_data_validation.py`** (8 tests): File missing fallback, schema validation, non-numeric charge coercion, whitespace trimming, empty file checks.
- **`tests/test_flask_app.py`** (23 tests): Endpoint health, summary schema, 95% confidence intervals, 7-kind chart generation, profile matching with $n < 20$ warning, data quality audit, paginated explorer, CSV downloads, and no-cache headers.

```text
======================= 40 passed in 11.87s =======================
```

---

## 10. Academic Attribution & Links

- **Course**: B.Tech IT Workshop Lab (`PCC CS 393`), Academic Year 2026–27
- **Standalone Lab Solution**: [lab_solution.py](file:///d:/Kumar/Sonykaka/SympSort/lab_solution.py)
- **Academic Synopsis**: [docs/synopsis.md](file:///d:/Kumar/Sonykaka/SympSort/docs/synopsis.md)
- **Viva Voce Q&A**: [docs/viva_questions.md](file:///d:/Kumar/Sonykaka/SympSort/docs/viva_questions.md)
- **Project Timeline**: [docs/project_timeline.md](file:///d:/Kumar/Sonykaka/SympSort/docs/project_timeline.md)
- **Generated 300 DPI Chart**: [outputs/smoker_charges_comparison.png](file:///d:/Kumar/Sonykaka/SympSort/outputs/smoker_charges_comparison.png)
# SympSort
A mini project on medical factors and lifestyle.
