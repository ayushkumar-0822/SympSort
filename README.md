# SympSort: Medical Cost & Lifestyle Factors
### Desktop-Style Web Analytics Application | IT Workshop Lab (PCC CS 393)

A premium, desktop-application-style web analytics platform built with **Python**, **Flask**, **Pandas**, **Seaborn**, and a custom **HTML5 / CSS3 / Vanilla JavaScript** editorial shell to compare health insurance charges between smokers and non-smokers.

---

## 1. Project Overview

In healthcare economics and insurance underwriting, individual lifestyle determinants—such as chronic tobacco usage—are associated with significant variations in medical expenditures. **SympSort** implements an empirically grounded, modular, and beginner-friendly Python data-analysis pipeline to ingest, clean, aggregate, and visualize empirical health insurance claims data.

Rather than relying on generic dashboard frameworks or Streamlit, this project provides a custom **desktop-style web interface** powered by a lightweight Python Flask backend and pure client-side vanilla JavaScript.

---

## 2. Exact Academic Question

This project directly implements **Problem #1** from the official **IT Workshop Lab (PCC CS 393)** mini-project curriculum:

> **"Find the average insurance charge for smokers vs. non-smokers using Pandas. Create a Seaborn barplot to visually compare the average costs between the two groups."**

---

## 3. Architecture & Editorial UI/UX Design

```text
┌─────────────────────────────────────────────────────────────────┐
│                    DESKTOP WEB FRONTEND                         │
│   • Semantic HTML5 + Vanilla JS + High-Contrast Editorial CSS   │
│   • Views: Overview | Comparison | Explorer | Method | About |  │
│            Scenario Comparison                                  │
└───────────────────────────────▲─────────────────────────────────┘
                                │ JSON REST API & Image Streaming
┌───────────────────────────────▼─────────────────────────────────┐
│                    FLASK PYTHON BACKEND (app.py)                │
│   • /api/summary  • /api/chart  • /api/data  • /api/reload      │
│   • /api/scenario-compare       • /api/report/pdf               │
└───────────────▲───────────────────────────────▲─────────────────┘
                │                               │
┌───────────────▼───────────────┐ ┌─────────────▼─────────────────┐
│     PANDAS ANALYSIS ENGINE    │ │   SEABORN / MATPLOTLIB PLOT   │
│  df.groupby("smoker").mean()  │ │  sns.barplot() -> 300 DPI PNG │
│  Welch t-test, Mann-Whitney U │ │  7 publication chart kinds    │
└───────────────▲───────────────┘ └───────────────────────────────┘
                │
┌───────────────▼───────────────┐
│  LOCAL CSV (data/insurance.csv│
│  1,338 records, 7 columns     │
└───────────────────────────────┘
```

### Visual Identity
- **Palette**: Calm editorial paper background (`#F6F3EC`), crisp hairline card borders (`#E2DCCF`), deep green navigation (`#17302B`), teal accent (`#1F6F63` for non-smoker / primary actions), and brick-red (`#B5442E` for smoker / comparison emphasis).
- **Typography**: Self-hosted **Source Serif 4** (`static/fonts/`) with lining, tabular figures (`font-variant-numeric: lining-nums tabular-nums`) so numbers never shift or drop below baseline. Clean system UI sans-serif for interface controls.
- **Layout**: Fixed deep green sidebar, sticky header with dynamic action controls, and responsive collapse under 1000px and 700px.

---

## 4. Empirical Results at a Glance

Calculated from the authentic 1,338-record Kaggle dataset (`data/insurance.csv`):

| Cohort | Sample Size ($n$) | Cohort Share | Average Charge (Mean) | 95% Confidence Interval | Median Charge | Standard Deviation |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Non-Smokers** (`smoker == "no"`) | 1,064 | 79.52% | **\$8,434.27 USD** | \$8,434.27 ± \$359.88 | \$7,345.41 USD | \$5,993.78 USD |
| **Smokers** (`smoker == "yes"`) | 274 | 20.48% | **\$32,050.23 USD** | \$32,050.23 ± \$1,368.53 | \$34,456.35 USD | \$11,541.55 USD |
| **Difference** | — | — | **+\$23,615.96 USD** | — | **+\$27,110.94 USD** | — |
| **Percentage Increase** | — | — | **+280.00%** | — | **+369.09%** | — |

> **Key Finding**: Average charges in the smoker group were **280.00% higher** (3.80× multiplier) than in the non-smoker group ($t = 32.75, p < 0.001, \text{Cohen's } d = 3.16$).

---

## 5. Application Views

1. **Overview** (<kbd>1</kbd>): Assigned problem deliverable, dynamic headline finding, primary KPI metrics, secondary strip (*Multiplier 3.80×*, *Non-smokers n = 1,064*, *Smokers n = 274*, *Valid records 1,338*), 16:9 Seaborn chart with 95% CI error whiskers, and sample records table.
2. **Cost Comparison** (<kbd>2</kbd>): Detailed statistical table with 95% CIs, **Beyond the Average** multi-chart explorer (7 chart kinds: *Barplot*, *KDE Distribution*, *Boxplot*, *BMI vs Charges*, *Region*, *Sex*, *Age Bands*), **Is the Difference Real?** statistical significance card, and empirical subgroup matcher.
3. **Dataset Explorer** (<kbd>3</kbd>): Paginated inspection table with multi-criteria filters (*Search*, *Smoker*, *Sex*, *Region*, *Children*, *Age Min/Max*, *BMI Min/Max*), live **Selection Summary Strip** (matched count, mean charges, median charges, mean BMI calculated over the full filtered set), sticky headers, and filter reset.
4. **Methodology** (<kbd>4</kbd>): Analytical pipeline explanation, dark code block with Copy button, live `df.groupby('smoker')['charges'].mean()` terminal output, and **Data Quality & Ingestion Audit Card** (`df.describe()`, `df.head()`, `df.info()`).
5. **About Project** (<kbd>5</kbd>): Academic identification (**B.Tech IT Workshop Lab PCC CS 393, Academic Year 2026–27**), student submission placeholders, verbatim problem statement quote block, technology stack, and methodological limitations.
6. **Scenario Comparison** (<kbd>6</kbd>): Dedicated two-group empirical comparison engine allowing examiners to define custom cohorts across 6 criteria (smoker, sex, region, age, BMI, children), calculate differences in empirical means, and view automatic small-sample variance advisories.

---

## 6. Complete API Reference

| Endpoint | Method | Description | Parameters / Payload |
| :--- | :---: | :--- | :--- |
| `/` | `GET` | Serves desktop single-page application shell | None |
| `/report/printable` | `GET` | Clean presentation report for browser printing / Save PDF | None |
| `/export-csv` | `GET` | Legacy alias for summary CSV export | None |
| `/api` | `GET` | API directory index and endpoint documentation | None |
| `/api/health` | `GET` | Health check & data validation status | None |
| `/api/summary` | `GET` | Primary groupby statistics, Welch t-test, Mann-Whitney U, Cohen's d, 95% CIs | None |
| `/api/sample-data` | `GET` | Top 5 representative dataset audit records | None |
| `/api/data-quality` | `GET` | Validation report, column dtypes, null counts, summary statistics | None |
| `/api/chart` | `GET` | Dynamic PNG chart stream (150 DPI) | `kind=bar\|dist\|box\|scatter\|region\|sex\|age`, `theme=light\|dark` |
| `/api/data` | `GET` | Filtered, sorted, paginated records | `search`, `smoker`, `sex`, `region`, `children`, `age_min`, `age_max`, `bmi_min`, `bmi_max`, `sort`, `order`, `page`, `page_size` |
| `/api/profile-match` | `GET` | Interactive demographic cohort matcher | `age`, `bmi`, `sex`, `region`, `smoker` |
| `/api/scenario-compare` | `GET`, `POST` | Authoritative two-cohort empirical comparison with Student's t CIs & Welch's t-test | POST JSON: `{"scenario_a": {...}, "scenario_b": {...}}` or GET query params |
| `/api/report/pdf` | `GET`, `POST` | Download executive PDF report (in-memory `io.BytesIO`) | Optional JSON / query params for Scenario A/B filters |
| `/api/download/chart` | `GET` | Direct 300 DPI high-resolution PNG download | None |
| `/api/download/summary` | `GET` | Download summary metrics CSV with exact statistics | None |
| `/api/download/filtered`| `GET` | Download active filtered records CSV | Inherits active explorer filter query params |
| `/api/reload` | `POST` | Cache invalidation & CSV reload | None |

---

## 7. Project Directory Structure

```text
SympSort/
├── lab_solution.py             # Minimal ~35-line standalone lab submission script
├── main.py                     # Master launcher (Desktop App / CLI / Tests)
├── sympsort.py                 # Convenience alias for main.py
├── app.py                      # Flask application factory, REST APIs & asset versioning
├── analysis.py                 # Core Pandas grouping, Welch's t-test, Mann-Whitney U, Cohen's d
├── scenario_analysis.py        # Two-group empirical cohort comparison engine with validation
├── reporting.py                # In-memory ReportLab executive PDF generator (zero disk writes)
├── data_loader.py              # Defensive CSV loading and schema validation
├── visualization.py            # 7-kind Seaborn/Matplotlib chart engine with 95% CI whiskers
├── config.py                   # Centralized paths, column mappings, 16:9 sizing & styling
├── run.bat                     # 1-click Windows Command Prompt launcher
├── run.ps1                     # 1-click Windows PowerShell launcher
├── pytest.ini                  # Pytest configuration
├── requirements.txt            # Python dependencies (Flask, Pandas, Seaborn, ReportLab, etc.)
├── vercel.json                 # Vercel serverless build and rewrite configuration
├── .vercelignore               # Serverless deployment exclusions
├── api/
│   └── index.py                # Vercel serverless WSGI entrypoint with path middleware
├── templates/
│   ├── index.html              # Single-page shell with versioned assets (?v={{ asset_version }})
│   └── report_printable.html   # Presentation-grade printable executive report for PDF export
├── static/
│   ├── css/
│   │   └── desktop.css         # Refined editorial styling system (paper bg, deep green sidebar)
│   ├── js/
│   │   └── app.js              # Client-side router, table renderer, scenario engine
│   ├── img/
│   │   ├── logo.png            # Application logo
│   │   └── favicon.png         # High-resolution PNG favicon
│   └── fonts/
│       ├── source-serif-4-roman.woff2   # Self-hosted Source Serif 4 Roman
│       └── source-serif-4-italic.woff2  # Self-hosted Source Serif 4 Italic
├── archive/
│   └── app_streamlit_legacy.py # Archived legacy prototype
├── data/
│   ├── insurance.csv           # Official Kaggle dataset (1,338 records)
│   └── insurance_sample.csv    # Fallback sample dataset
├── outputs/
│   ├── smoker_charges_chart.png         # Pre-saved 300 DPI barplot
│   ├── lab_solution_barplot.png         # Output of lab_solution.py
│   └── .gitkeep                         # Preserves directory in Git
├── tests/
│   ├── conftest.py             # Shared pytest fixtures
│   ├── test_analysis.py        # Unit tests for calculations, 95% CIs & metrics
│   ├── test_data_validation.py # Unit tests for schema validation & corrupted data
│   ├── test_flask_app.py       # Integration tests for endpoints, multi-charts & filters
│   ├── test_scenarios.py       # Validation and calculation tests for Scenario Comparison
│   ├── test_scenario.py        # Additional cohort filter tests
│   ├── test_explorer.py        # Unit tests for multi-criteria Explorer filters & pagination
│   └── test_reporting.py       # Unit tests for in-memory PDF generation & CSV exports
└── docs/
    ├── synopsis.md             # Formal academic synopsis for hardcopy submission
    ├── viva_questions.md       # 33 high-yield viva voce questions with model answers
    ├── implementation_log.md   # Audit record of all implementation blocks & checks
    └── project_timeline.md     # 6-week laboratory execution milestones
```

---

## 8. Architectural Rationale: Why a No-Database Design?

SympSort deliberately omits a relational database (SQLite, PostgreSQL) and ORMs (SQLAlchemy):
1. **Dataset Nature**: The dataset is an immutable, read-only 1,338-record observational CSV (Brett Lantz / Kaggle, ~54 KB). Ingesting it into an external database table creates needless I/O friction and SQLite file locking.
2. **Computational Velocity**: In-memory Pandas operations on 1,338 records execute in under 2 milliseconds. Vectorized operations (`df.groupby()`, quantiles, medians, Student's t confidence intervals, Welch's t-test) run at native Cython speed in memory.
3. **Stateless Serverless Scalability**: Zero database connections means zero connection pool exhaustion and zero cold-start database latency. The application deploys effortlessly as an immutable serverless microservice on platforms like Vercel with no database hosting costs or downtime.
4. **Maintenance & Hygiene**: Eliminates database migrations, connection strings, credential leaks, and concurrent file-lock contention.

---

## 9. How to Run SympSort Locally

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

1. Open the `SympSort` folder in VS Code (`File` ➔ `Open Folder...`).
2. VS Code automatically detects and selects the `.venv` Python interpreter.
3. **Run with F5**: Select **`SympSort: Run Desktop Web App (Flask)`** from the Run & Debug dropdown.
4. **Run with Play Button**: Open `main.py` and click **▷ Run Python File**.

---

## 9. Vercel Deployment Instructions

SympSort is fully preconfigured for zero-configuration deployment to **Vercel**:
1. Install the Vercel CLI or link via GitHub:
   ```bash
   npm i -g vercel
   vercel
   ```
2. Configuration details in `vercel.json`:
   - Serverless WSGI function located at `api/index.py`.
   - Asset and API rewrites route `/api/*`, `/static/*`, and `/*` through `api/index.py`.
   - Dataset files (`data/**`), templates (`templates/**`), and assets (`static/**`) are packaged via `includeFiles`.
   - Environment variable `MPLCONFIGDIR=/tmp` ensures writable Matplotlib font caching.
3. Deploy to production:
   ```bash
   vercel --prod
   ```

---

## 10. Automated Testing & Verification

To run the complete automated test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

### Verified Test Summary (81/81 Passing — 100% Pass Rate):
- **`tests/test_analysis.py`** (12 tests): Grouped means exact match (\$8,434.27 and \$32,050.23), multiplier 3.80×, +280.0% difference, JSON serialization, pure-Python Student's t 95% CIs, Welch's t-test, Mann-Whitney U, Cohen's d ($d \approx 3.16$).
- **`tests/test_data_validation.py`** (11 tests): Missing CSV fallback, schema validation, non-numeric charge coercion, negative charge rejection, separate null auditing, demographic validation.
- **`tests/test_flask_app.py`** (26 tests): Endpoint health, index rendering, summary JSON schema, 7-kind Seaborn chart generation, profile matching with $n < 20$ warning, data quality audit, paginated explorer, CSV downloads, no-cache headers.
- **`tests/test_scenarios.py` & `tests/test_scenario.py`** (15 tests): Two-group empirical scenario comparison backend, multi-parameter filtering, strict HTTP 400 validation, edge cases (empty groups, small sample size warnings).
- **`tests/test_explorer.py`** (10 tests): Multi-criteria filtering (sex, children, age min/max, BMI min/max), search debouncing, allowlisted sorting, stable pagination, and full selection summary.
- **`tests/test_reporting.py`** (6 tests): In-memory PDF report generation via ReportLab, CSV downloads (`/api/download/summary`, `/api/download/filtered`), and high-DPI chart downloads.

```text
======================= 81 passed, 2 warnings in 26.47s =======================
```

---

## 11. Academic Attribution & Links

- **Course**: B.Tech IT Workshop Lab (`PCC CS 393`), Academic Year 2026–27
- **Standalone Lab Solution**: [lab_solution.py](file:///d:/Kumar/Sonykaka/SympSort/lab_solution.py)
- **Academic Synopsis**: [docs/synopsis.md](file:///d:/Kumar/Sonykaka/SympSort/docs/synopsis.md)
- **Viva Voce Q&A**: [docs/viva_questions.md](file:///d:/Kumar/Sonykaka/SympSort/docs/viva_questions.md)
- **Implementation Audit Log**: [docs/implementation_log.md](file:///d:/Kumar/Sonykaka/SympSort/docs/implementation_log.md)
- **Architecture Specification**: [ARCHITECTURE.md](file:///d:/Kumar/Sonykaka/SympSort/ARCHITECTURE.md)
- **Product Requirements Document**: [PRD.md](file:///d:/Kumar/Sonykaka/SympSort/PRD.md)
- **Generated 300 DPI Chart**: [outputs/smoker_charges_comparison.png](file:///d:/Kumar/Sonykaka/SympSort/outputs/smoker_charges_comparison.png)
