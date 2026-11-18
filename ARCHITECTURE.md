# ARCHITECTURE.md — SympSort Architecture Specification

## 1. Executive Summary
- **Project Name:** SympSort: Medical Cost & Lifestyle Factors
- **Lab Course:** B.Tech IT Workshop Lab (PCC CS 393, 2026–2027)
- **Primary Assignment:**
  > *"Find the average insurance charge for smokers vs. non-smokers using Pandas. Create a Seaborn barplot to visually compare the average costs between the two groups."*
- **Empirical Ground Truth (1,338 records):**
  - Non-Smoker Mean ($\bar{X}_{\text{no}}$): **$8,434.27** ($n = 1,064$)
  - Smoker Mean ($\bar{X}_{\text{yes}}$): **$32,050.23** ($n = 274$)
  - Absolute Difference ($\Delta$): **+$23,615.96**
  - Percentage Increase: **+280.00%**
  - Relative Multiplier: **3.80×**

---

## 2. Technology Stack & Dependencies
| Layer | Component | Version | Purpose |
|---|---|---|---|
| **Data Ingestion** | Python / Pandas | 3.13 / >=2.0.0 | CSV parsing, error coercion, column normalization |
| **Statistical Engine**| Pandas / SciPy | >=2.0.0 / >=1.10.0 | `df.groupby('smoker')['charges'].mean()`, Welch's t-test, Mann-Whitney U, Cohen's d |
| **Scenario Engine**| Python / Pandas | >=2.0.0 | Two-group empirical cohort comparison with strict range validation |
| **Reporting Engine**| ReportLab | >=4.0.0 | In-memory publication-grade PDF generation (`io.BytesIO`) |
| **Visualization** | Seaborn / Matplotlib | >=0.12.0 / >=3.7.0 | `sns.barplot` (and 6 additional chart views) with 95% CI error bars |
| **Backend Web Server**| Flask | >=3.0.0 | REST JSON APIs, relative-route asset serving, dynamic PNG streaming |
| **Frontend UI** | HTML5 / CSS3 / Vanilla JS | ES6+ | SPA with 6 client views, hash routing, zero CDN dependencies |
| **Automated Testing** | Pytest | >=7.0.0 | 96 unit & integration tests covering loader, analysis, scenarios, explorer, reporting |

---

## 3. Directory Layout & Module Roles
```text
SympSort/
├── config.py              # Central constants, file paths, palettes, chart DPI settings
├── data_loader.py         # CSV loading, validation, cleaning, and ValidationReport
├── analysis.py            # Pandas groupby computation, moments, SmokerAnalysisResult, Welch t, Cohen's d
├── scenario_analysis.py   # Authoritative empirical cohort comparison engine with strict validation
├── reporting.py           # In-memory ReportLab executive PDF generator (zero disk writes)
├── visualization.py       # 7-kind Seaborn/Matplotlib chart engine (Light/Dark themes), PNG byte generation
├── app.py                 # Flask factory (create_app), REST endpoints, production error handling
├── main.py                # Application entrypoint: CLI runner (--cli) and desktop server runner
├── sympsort.py            # CLI and runner alias for `python sympsort.py`
├── api/
│   └── index.py           # Vercel serverless WSGI entrypoint with path-rewriting middleware
├── requirements.txt       # Pinned production runtime dependencies
├── pytest.ini             # Test runner configuration
├── run.bat / run.ps1      # Native OS launchers
├── ARCHITECTURE.md        # Master architectural and implementation specification
├── PRD.md                 # Product requirements and verification matrix
├── SCHEMA.md              # JSON and dataset schema specifications
├── data/
│   ├── insurance.csv      # Real Kaggle dataset (1,338 rows)
│   ├── insurance_sample.csv # 50-row fallback fixture
│   └── .gitkeep           # Directory placeholder
├── outputs/
│   ├── smoker_charges_chart.png # 300 DPI high-resolution export
│   ├── lab_solution_barplot.png # 25-line lab solution plot export
│   └── .gitkeep           # Preserves directory structure in Git
├── templates/
│   ├── index.html         # Single-page application shell (6 distinct views)
│   └── report_printable.html # Presentation-grade printable executive report for PDF export
├── static/
│   ├── css/
│   │   └── desktop.css    # Calm editorial styling, design tokens, light/dark themes
│   ├── js/
│   │   └── app.js         # Client router, table renderer, scenario comparison engine
│   ├── fonts/             # Self-hosted Source Serif 4 (Roman and Italic WOFF2)
│   └── img/
│       ├── logo.png       # Authoritative project emblem
│       ├── favicon.png    # High-res favicon PNG
│       └── favicon.ico    # Favicon ICO
└── tests/
    ├── conftest.py        # Shared pytest fixtures (mock DataFrames, Flask test client)
    ├── test_analysis.py   # Unit tests for Pandas grouped mean calculations and statistics
    ├── test_data_validation.py # Unit tests for CSV ingestion, coercion, missing columns
    ├── test_flask_app.py  # Integration tests for HTTP 200, JSON structure, PNG streaming
    ├── test_scenario.py   # Unit tests for multi-parameter scenario comparison engine
    ├── test_scenarios.py  # Strict HTTP 400 validation and JSON safety tests
    ├── test_explorer.py   # Unit tests for multi-criteria Explorer filters & pagination
    └── test_reporting.py  # Unit tests for in-memory PDF generation & CSV exports
```

---

## 4. End-to-End Data Pipeline
```text
[data/insurance.csv]
       │
       ▼
[data_loader.py] ──────► Coerces charges to float64, trims & validates smoker values
       │
       ├──► ValidationReport (valid_rows, excluded_rows, demographic report)
       ▼
[analysis.py] ─────────► df.groupby('smoker')['charges'].mean()
       │               Pure-Python Welch's t-test, Mann-Whitney U, Cohen's d (3.16)
       │               Student's t 95% Confidence Intervals
       ├──► SmokerAnalysisResult
       ▼
[scenario_analysis.py] ─► Validates Scenario A & B inputs (age, bmi, sex, region, smoker, children)
       │               Computes subgroup empirical count, mean, median, min, max, std
       │               Computes delta mean, relative shift, higher badge, small-sample warnings
       ▼
[reporting.py] ────────► Compiles executive PDF in memory via ReportLab (io.BytesIO)
       │               Embeds Seaborn barplot, methodology, comparison table, limitations
       ▼
[visualization.py] ────► Seaborn 7-view charts (bar, dist, box, scatter, region, sex, age)
       │               Cached PNG bytes (Light theme #F6F3EC / Dark theme #16171A)
       ▼
[app.py] ──────────────► Serves JSON endpoints, static assets, and streaming responses
       │
       ├── GET /api/summary          -> Full statistical JSON payload + live groupby text
       ├── GET /api/chart            -> Dynamic theme-matching PNG stream (7 kinds)
       ├── GET /api/data             -> Filtered, sorted, paginated records with selection summary
       ├── POST /api/scenario-compare-> Two-group empirical cohort comparison
       ├── GET /api/report/pdf       -> Streamed in-memory executive PDF report
       └── GET /api/health           -> Server status and row counts
```

---

## 5. Architectural Decision: Why No Database (No SQLite / Postgres / ORM)?
A deliberate architectural choice in SympSort is the **complete absence of a relational database or ORM**:
1. **Data Scope & Nature**: The input is an immutable, read-only 1,338-row academic observational CSV (~54 KB). Ingesting it into a persistent relational database (SQLite/Postgres) introduces disk locks, connection pooling overhead, and migration friction without any architectural benefit.
2. **Computational Velocity**: In-memory Pandas operations on 1,338 records take < 2 milliseconds. Vectorized column operations (`df.groupby()`, quantile/median calculations, Student's t confidence intervals) run at native Cython/C speed directly from memory cache.
3. **True Statelessness for Serverless Deployment**: Because the application maintains zero local database state or open disk handles, it deploys seamlessly to serverless environments (such as Vercel AWS Lambda functions) with zero cold-start database latency, zero connection pooling exhaustion, and no risk of SQLite database file locking across concurrent lambdas.
4. **Epistemological Integrity**: Medical cost factors in this curriculum represent an observational benchmark dataset; treating it as a dynamic transactional entity requiring CRUD operations would obscure the assignment's data engineering and exploratory focus.

---

## 6. Mathematical Formulations & Exact Inferential Formulas
1. **Arithmetic Mean:**
   $$\bar{X}_{\text{smoker}} = \frac{1}{n_s} \sum_{i \in \text{smoker}} X_i = \$32,050.23 \quad (n_s = 274)$$
   $$\bar{X}_{\text{non-smoker}} = \frac{1}{n_{ns}} \sum_{j \in \text{non-smoker}} X_j = \$8,434.27 \quad (n_{ns} = 1,064)$$

2. **Absolute Difference:**
   $$\Delta_{\text{abs}} = \bar{X}_{\text{smoker}} - \bar{X}_{\text{non-smoker}} = +\$23,615.96$$

3. **Percentage Increase:**
   $$\Delta_{\text{pct}} = \left( \frac{\bar{X}_{\text{smoker}} - \bar{X}_{\text{non-smoker}}}{\bar{X}_{\text{non-smoker}}} \right) \times 100 = +280.00\%$$

4. **Relative Multiplier:**
   $$\text{Multiplier} = \frac{\bar{X}_{\text{smoker}}}{\bar{X}_{\text{non-smoker}}} \approx 3.80\times$$

5. **Welch's Independent-Samples t-test (Equal Variance Not Assumed):**
   $$t = \frac{\bar{X}_{\text{smoker}} - \bar{X}_{\text{non-smoker}}}{\sqrt{\frac{s_1^2}{n_1} + \frac{s_2^2}{n_2}}} \approx 32.75, \quad p < 0.001$$
   $$\text{df}_{\text{Welch}} = \frac{\left( \frac{s_1^2}{n_1} + \frac{s_2^2}{n_2} \right)^2}{\frac{(s_1^2 / n_1)^2}{n_1 - 1} + \frac{(s_2^2 / n_2)^2}{n_2 - 1}} \approx 311.85$$

6. **Cohen's d (Standardized Effect Size):**
   $$s_p = \sqrt{\frac{(n_1 - 1)s_1^2 + (n_2 - 1)s_2^2}{n_1 + n_2 - 2}}, \quad d = \frac{\bar{X}_{\text{smoker}} - \bar{X}_{\text{non-smoker}}}{s_p} \approx 3.16$$

7. **Student's t Confidence Intervals (df = n - 1):**
   $$\text{CI}_{95\%} = \bar{X} \pm t_{0.975, \, n-1} \cdot \left( \frac{s}{\sqrt{n}} \right)$$

---

## 7. In-Memory ReportLab PDF Generation Architecture
In serverless environments (e.g., Vercel AWS Lambda functions), writing permanent files to disk introduces concurrency collision risks and ephemeral storage exhaustion. `reporting.py` utilizes `io.BytesIO`:
1. Compiles ReportLab flowable elements (Project title, Kaggle dataset source, data validation metrics, Pandas groupby methodology, summary comparison table with exact Student's t 95% CIs, embedded 300 DPI Seaborn chart, and observational limitations).
2. Supports dynamic Scenario Comparison inclusion when optional Scenario A/B filter parameters are submitted.
3. Streams bytes directly to the HTTP response with `mimetype="application/pdf"` and `Content-Disposition: attachment`. Zero files are written or retained on the server.

---

## 8. Frontend Design Tokens & Architecture
- **Editorial Aesthetic:** Calm, restrained, paper-like report styling. Avoids glassmorphism, background blur, and neon gradients.
- **Light Theme (Default):**
  - Page Background: `#FAF8F4` (warm ivory)
  - Card Surface: `#FFFFFF` with 1px border `#E4DFD6`
  - Text: `#1C1B19` (near-black)
  - Non-Smoker Accent: `#1F6F63` (muted teal)
  - Smoker Signal: `#B5442E` (brick red)
- **Dark Theme:**
  - Page Background: `#16171A` (neutral charcoal)
  - Card Surface: `#1E1F22` with border `#2A2B2F`
  - Text: `#E8E6E1`
- **Typography:**
  - Headings & Big Figures: `'Iowan Old Style', 'Source Serif 4', Georgia, serif`
  - Body & UI Controls: `system-ui, -apple-system, 'Segoe UI', Inter, sans-serif`
  - Numbers & Currency: `font-variant-numeric: tabular-nums`
- **Zero Drift Table Architecture:**
  - Both `<th>` and `<td>` are generated dynamically from a single JavaScript array:
    `const COLUMNS = [{ key, label, align, sortable, format }]`
  - Guaranteed alignment: no extra index columns, no header shift, no `$NaN`.

---

## 9. Viva Q&A Cheat Sheet (For Examiner Defense)
1. **Q: Why use `df.groupby('smoker')['charges'].mean()` instead of a loop?**
   *A:* Pandas vectorization executes in optimized C/Cython via contiguous memory arrays, running orders of magnitude faster and producing cleaner, declarative code.
2. **Q: Why are charges for smokers skewed?**
   *A:* Smoker charges have a higher variance ($\text{std} = \$11,541.59$ vs $\$5,993.78$) and a bimodal distribution driven by smoking interaction with high BMI ($\ge 30$).
3. **Q: Does correlation imply causation here?**
   *A:* No. This is observational actuarial data. While smoking correlates with 3.80× higher charges, confounding factors (age, underlying conditions) must be controlled before claiming direct clinical causality.
