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
- `GET /api/health`: JSON health check `{"status": "ok", "rows": 1338}`.
- `GET /api/summary`: JSON statistical metrics, validation counts, and live `groupby_text`.
- `GET /api/chart`: Dynamic PNG stream (150 DPI screen).
- `GET /api/data`: Filtered, sorted, and paginated records with JSON numbers.
- `POST /api/reload`: Invalidates cache, reloads CSV, returns `{"status": "success", "rows": N}`.
- `GET /api/download/chart`: Direct 300 DPI high-resolution attachment.
- `GET /api/download/summary`: CSV summary export.

---

## 3. Non-Functional Requirements (NFR)
1. **Zero External CDN Dependencies:** All fonts, scripts, and stylesheets work offline in an isolated laboratory environment.
2. **Accessibility (WCAG AA):** Visible 2px focus rings, `aria-current="page"`, `aria-sort="ascending|descending"`, semantic buttons.
3. **Motion Safety:** All animations respect `prefers-reduced-motion` and disable count-up and transition effects when set.
4. **Resilience & Fallback:** If `data/insurance.csv` is absent, the backend gracefully falls back to `data/insurance_sample.csv` with a visible indicator.

---

## 4. Verification & QA Checklist (7 Points)
| Checkpoint | Expected Behavior | Verification Status |
|---|---|---|
| **1. Sidebar Navigation** | Clicking any of the 5 views opens immediately with no page reload. | Passed |
| **2. History & Refresh** | URL hash updates; browser Back/Forward and page refresh preserve view. | Passed |
| **3. Table Alignment** | Explorer headers and columns match 1:1 with zero drift. | Passed |
| **4. Currency Formatting** | Charges format as `$12,345.67`; nulls show `—`; never shows `$NaN`. | Passed |
| **5. Expected Values** | Non-smoker: $8,434.27; Smoker: $32,050.23; Multiplier: 3.80×. | Passed (30/30 tests) |
| **6. Filtering & Sorting** | Search, smoker filter, region filter, and column sort work properly. | Passed |
| **7. Export Actions** | "Export Chart" downloads 300 DPI PNG; "Download CSV" downloads data. | Passed |
