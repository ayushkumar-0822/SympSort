# Implementation Log — SympSort Upgrade & Verification

**Project**: SympSort: Medical Cost & Lifestyle Factors  
**Curriculum**: B.Tech IT Workshop Lab (PCC CS 393, 2026–27)  
**Assigned Deliverable**: `df.groupby('smoker')['charges'].mean()` and Seaborn barplot comparison  
**Dataset**: Kaggle Medical Cost Personal Dataset (`data/insurance.csv`, 1,338 rows)  

---

## Block-by-Block Execution Record

### BLOCK 0 — Preflight, Backup, and Baseline
- **Date**: 2026-11-16
- **Objective**: Inspect repository, verify Python virtual environment, baseline existing test suite.
- **Actions**:
  - Validated local virtual environment (`.venv\Scripts\python.exe`, Python 3.13.16).
  - Confirmed 1,338 records in `data/insurance.csv` with 0 missing required cells.
  - Baselined working tests.

---

### BLOCK 1 — Safe Repository Cleanup & Deployment Hygiene
- **Date**: 2026-11-16
- **Objective**: Deduplicate packaged assets, safely isolate legacy prototypes, and fix Git/Vercel ignore rules.
- **Actions**:
  - Removed redundant `public/` directory after verifying byte-for-byte SHA-256 equivalence with `static/`.
  - Archived `app_streamlit_legacy.py` to `archive/app_streamlit_legacy.py`.
  - Updated `.gitignore` and `.vercelignore` to cleanly ignore `.venv/`, `.pytest_cache/`, `archive/`, `outputs/`, and temporary build files.
  - Removed broad `*.png` rule in `.vercelignore` so that `logo.png` and `favicon.png` deploy.

---

### BLOCK 2 — Correctness of Analysis and Data Validation
- **Date**: 2026-11-16 / 2026-11-17
- **Objective**: Ensure every statistical metric is genuinely calculated from data without hardcoding.
- **Actions**:
  - Replaced hardcoded p-values with genuine calculations: Welch's independent-samples t-test (`equal_var=False`), two-sided Mann–Whitney U test, and Student's t 95% confidence intervals.
  - Calculated Cohen's d ($d = 3.16$) using documented pooled standard deviation formula.
  - Implemented strict numeric validation in `data_loader.py`: negative charges rejected, separate auditing of null vs non-numeric entries, demographic boundary validation.
  - Added JSON-safe serialization (`to_dict()`) converting all NumPy and float infinities to safe JSON values.

---

### BLOCK 3 — Scenario Comparison Backend
- **Date**: 2026-11-17
- **Objective**: Implement two-group empirical scenario comparison backend module.
- **Actions**:
  - Created `scenario_analysis.py` with strict input validation for `smoker`, `sex`, `region`, `age_min`, `age_max`, `bmi_min`, `bmi_max`, and `children`.
  - Added `POST /api/scenario-compare` returning matched counts, mean, median, min, max, std, diff in means, percentage diff, higher cohort badge, and small-sample warnings ($n < 20$).
  - Added `tests/test_scenarios.py` (10 tests) covering valid comparisons, empty subgroups, inverted bounds (HTTP 400), and JSON safety.

---

### BLOCK 4 — Dataset Explorer Improvements
- **Date**: 2026-11-17
- **Objective**: Enhance Dataset Explorer filtering and selection summary.
- **Actions**:
  - Extended `_apply_filters()` in `app.py` to support `sex`, `children`, `age_min`, `age_max`, `bmi_min`, `bmi_max` alongside `smoker` and `region`.
  - Added whole-dataset `selection_summary` (matched record count, average charges, median charges, average BMI).
  - Enforced allowlisted column sorting and pagination bounds ($1 \le \text{page\_size} \le 200$).
  - Added `tests/test_explorer.py` (10 tests) covering single, combined, boundary, and sort operations.

---

### BLOCK 5 — PDF and CSV Reporting
- **Date**: 2026-11-17
- **Objective**: Provide in-memory executive report generation without temporary file pollution.
- **Actions**:
  - Created `reporting.py` using ReportLab to build executive PDF in memory via `io.BytesIO`.
  - Added `GET /api/report/pdf` with `Content-Disposition: attachment`.
  - Preserved `/api/download/summary`, `/api/download/filtered`, and `/api/download/chart`.
  - Added `reportlab>=4.0.0` to `requirements.txt`.
  - Added `tests/test_reporting.py` (6 tests) verifying byte headers, empty dataset handling, and CSV formatting.

---

### BLOCK 6 — Editorial UI and Frontend Integration
- **Date**: 2026-11-17
- **Objective**: Implement View 6 (Scenario Comparison) in the single-page editorial shell.
- **Actions**:
  - Upgraded `templates/index.html` with sidebar nav item (shortcut `6`) and full View 6 panel.
  - Added CSS grid layout in `static/css/desktop.css` supporting side-by-side desktop panels and stacked mobile cards.
  - Updated `static/js/app.js`: mapped `scenario: "Scenario Comparison"`, cached scenario DOM elements, wired up `runScenarioComparison()` with button state management and safe `textContent` rendering.

---

### BLOCK 7 — Deployment, Regression, Documentation & Handover
- **Date**: 2026-11-17
- **Objective**: Harden production error handling, remove diagnostic headers, execute full regression, and finalize documentation.
- **Actions**:
  - Hardened `api/index.py`: removed diagnostic `X-Environ-*` headers and sanitized 500 error responses.
  - Hardened `app.py`: replaced traceback exposure with a production-safe generic 500 response (JSON & HTML) and detailed server logging; removed redundant `VercelPathMiddleware` definition.
  - Ran comprehensive regression suite covering all 8 categories (all passing).
  - Updated `README.md`, `PRD.md`, `ARCHITECTURE.md`, `SCHEMA.md`, `docs/viva_questions.md`, and created `docs/implementation_log.md`.

---

## Test Verification Audit

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

| Test Suite File | Test Count | Status | Focus Area |
| :--- | :---: | :---: | :--- |
| `tests/test_analysis.py` | 12 | **PASSED** | Groupby means, Welch t-test, Mann-Whitney U, Cohen's d, Student's t CI |
| `tests/test_data_validation.py` | 11 | **PASSED** | Schema verification, negative charges rejection, null audits |
| `tests/test_flask_app.py` | 26 | **PASSED** | Flask routes, 7 chart kinds, profile matcher, no-cache headers |
| `tests/test_scenarios.py` | 10 | **PASSED** | Scenario compare POST, HTTP 400 validation, edge cases |
| `tests/test_scenario.py` | 5 | **PASSED** | Cohort filtering functions & empty subgroups |
| `tests/test_explorer.py` | 10 | **PASSED** | Multi-criteria Explorer filters & full selection summary |
| `tests/test_reporting.py` | 6 | **PASSED** | In-memory ReportLab PDF generation & CSV downloads |
| **Total Passed** | **81** | **100% Pass** | Zero failures across entire application |
