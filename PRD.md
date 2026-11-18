# PRD.md — Product Requirements Document: SympSort

## 1. Project Identity & Objective
- **Product Name:** SympSort: Medical Cost & Lifestyle Factors
- **Context:** B.Tech IT Workshop Lab (PCC CS 393, 2026–2027)
- **Problem Statement:**
  > *"Find the average insurance charge for smokers vs. non-smokers using Pandas. Create a Seaborn barplot to visually compare the average costs between the two groups."*
- **Primary Goal:** Provide an unambiguous, academic, publication-grade desktop web analytics application that solves the assignment, demonstrates rigorous data engineering with Pandas and Seaborn, and delivers an accessible, editorial UI.

---

## 2. Core Functional Requirements (FR)

### FR-1: Assigned Analytical Core
- **Pandas Computation:** Must execute `df.groupby('smoker')['charges'].mean()`.
- **Expected Mathematical Outputs:**
  - Non-Smoker Mean: **$8,434.27** ($n = 1,064$)
  - Smoker Mean: **$32,050.23** ($n = 274$)
  - Absolute Difference: **+$23,615.96**
  - Relative Percentage: **+280.00%**
  - Cohort Multiplier: **3.80×**
- **Data Grounding:** 100% derived from `data/insurance.csv`. Zero hardcoded results.

### FR-2: Client Navigation & Routing
- Single-page application served by Flask at `/`.
- Five primary views accessible without page reload:
  1. **Overview:** Headline finding, large KPI serif figures, hero barplot, 5-row sample.
  2. **Cost Comparison:** Multi-moment statistical breakdown table (count, mean, median, std, min, max) and large chart stage.
  3. **Dataset Explorer:** Search bar, smoker filter (All, Non-smokers, Smokers), region filter, sortable columns, pagination (15/25/50).
  4. **Methodology:** 5-step numbered pipeline, syntax-highlighted Python code block with Copy button, live backend DataFrame groupby output.
  5. **About:** Academic submission metadata, Kaggle dataset attribution, and epistemological limitations.
- **Hash-based Routing:** Changes `#overview`, `#comparison`, `#explorer`, `#methodology`, `#about` so back/forward and bookmarks function seamlessly.
- **Keyboard Shortcuts:** Digits `1` through `5` instantly switch active views.

### FR-3: Data Integrity & Table Rendering (Bug Prevention)
- **Single Source of Truth:** Table headers and cells generated from a single JavaScript column definition array `COLUMNS = [{ key, label, align, sortable, format }]`.
- **Zero Shift Guarantee:** No detached `#` or drift between `<th>` and `<td>`.
- **No `$NaN`:** Missing/invalid numbers render as `—`. All currency formatted via `Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })` with `font-variant-numeric: tabular-nums`.

### FR-4: Theme & Chart Synchronization
- **Light Theme (Default):** Warm ivory `#FAF8F4`, white card `#FFFFFF`, near-black `#1C1B19`, non-smoker teal `#1F6F63`, smoker red `#B5442E`.
- **Dark Theme:** Neutral charcoal `#16171A`, dark card `#1E1F22`, light text `#E8E6E1`.
- **Dynamic Chart Generation:** Requests `/api/chart?theme=light` or `/api/chart?theme=dark`. Seaborn generates matching palette with 95% CI error bars and explicit currency annotations on bars.

### FR-5: Backend API Endpoints
- `GET /`: Serves desktop SPA.
- `GET /report/printable`: Presentation-grade printable executive report for browser printing / Save as PDF.
- `GET /api`: JSON API index and endpoint documentation.
- `GET /api/health`: JSON health check `{"status": "ok", "rows": 1338}`.
- `GET /api/summary`: JSON statistical metrics, Welch's t-test, Mann-Whitney U, Cohen's d, validation counts, and live `groupby_text`.
- `GET /api/chart`: Dynamic PNG stream (150 DPI screen) supporting 7 analytical views.
- `GET /api/data`: Filtered, sorted, and paginated records with JSON numbers and full selection summary.
- `GET /api/sample-data`: Top 5 representative sample records for instant audit.
- `GET /api/data-quality`: Data validation audit, dtypes, null counts, and describe statistics.
- `GET /api/profile-match`: Interactive demographic profile matcher.
- `GET, POST /api/scenario-compare`: Authoritative two-group empirical cohort comparison with Student's t CIs and Welch's t-test.
- `GET, POST /api/report/pdf`: Direct in-memory executive PDF download (io.BytesIO) with optional Scenario A/B parameter support.
- `GET /api/download/chart`: Direct 300 DPI high-resolution attachment.
- `GET /api/download/summary` (`/export-csv`): Dynamic summary metrics CSV export.
- `GET /api/download/filtered`: Active filtered records CSV export.
- `POST /api/reload`: Invalidates cache, reloads CSV, returns `{"status": "success", "rows": N}`.

### FR-6: Scenario Comparison Engine (View 6)
- Allows two customized empirical cohorts (Scenario A vs Scenario B) across 6 filter dimensions (smoker, sex, region, age min/max, BMI min/max, children).
- Computes genuine subgroup statistics: matched record count ($n$), mean charges, median charges, min–max range, and standard deviation ($s$).
- Calculates absolute difference in means, relative percentage shift, and higher cohort badge.
- Enforces strict input validation (HTTP 400 on inverted bounds or unknown categories).
- Displays statistical advisory warnings whenever either cohort matches fewer than 20 records ($n < 20$) or matches 0 records.
- Embeds prominent academic disclaimer establishing results as observational historical subgroup statistics, not individual quotes or causal health predictions.

### FR-7: Dataset Explorer Multi-Criteria Filtering
- Multi-dimensional filtering across text search, smoker status, sex, region, children count, numeric age min/max, and numeric BMI min/max.
- Selection summary strip computed over the entire filtered dataset (not just the current page), displaying matched count, average charges, median charges, and average BMI.
- Allowlisted column sorting (age, sex, bmi, children, smoker, region, charges) and stable pagination bounds ($1 \le \text{page\_size} \le 200$).

### FR-8: In-Memory PDF & CSV Reporting
- Generates executive PDF report dynamically in memory using ReportLab (`io.BytesIO`) without temporary disk files.
- Includes academic title, Kaggle dataset metadata, data cleaning audit, Pandas groupby methodology, summary comparison table with 95% CIs, high-resolution embedded Seaborn chart, statistical significance metrics (Welch's t-test, Mann-Whitney U, Cohen's d), and observational limitations.
- Preserves direct CSV downloads for summary metrics and filtered subsets.

---

## 3. Non-Functional Requirements (NFR)
1. **Zero External CDN Dependencies:** All fonts, scripts, and stylesheets work offline in an isolated laboratory environment.
2. **Accessibility (WCAG AA):** Visible 2px focus rings, `aria-current="page"`, `aria-sort="ascending|descending"`, semantic buttons, keyboard navigation (shortcuts `1`–`6`).
3. **Motion Safety:** All animations respect `prefers-reduced-motion` and disable count-up and transition effects when set.
4. **Resilience & Fallback:** If `data/insurance.csv` is absent, the backend gracefully falls back to `data/insurance_sample.csv` with a visible indicator.
5. **No Persistent Disk Pollution:** Temporary chart and report artifacts are compiled in-memory or in system temporary paths; serverless execution on Vercel is completely stateless.

---

## 4. Verification & QA Checklist (10 Points)
| Checkpoint | Expected Behavior | Verification Status |
|---|---|---|
| **1. Sidebar Navigation** | Clicking any of the 6 views opens immediately with no page reload. | Passed |
| **2. History & Refresh** | URL hash updates; browser Back/Forward and page refresh preserve view. | Passed |
| **3. Table Alignment** | Explorer headers and columns match 1:1 with zero drift. | Passed |
| **4. Currency Formatting** | Charges format as `$12,345.67`; nulls show `—`; never shows `$NaN`. | Passed |
| **5. Expected Values** | Non-smoker: $8,434.27; Smoker: $32,050.23; Multiplier: 3.80×. | Passed (81/81 tests) |
| **6. Advanced Filtering & Sorting** | Search, smoker, sex, region, children, age, and BMI filters work with full-dataset summary. | Passed |
| **7. Scenario Comparison** | Side-by-side empirical cohort comparison with diffs, warnings, and disclaimer. | Passed |
| **8. Export Actions** | "Download PDF" streams in-memory PDF; "Download CSV" streams clean CSVs. | Passed |
| **9. Error Sanitization** | Production error handler suppresses filesystem paths, tracebacks, and internal details. | Passed |
| **10. Serverless Readiness** | Vercel gateway middleware normalizes paths with zero diagnostic header pollution. | Passed |
