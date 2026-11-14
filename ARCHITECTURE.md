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
| **Statistical Engine**| Pandas | >=2.0.0 | `df.groupby('smoker')['charges'].mean()` |
| **Visualization** | Seaborn / Matplotlib | >=0.12.0 / >=3.7.0 | `sns.barplot` with 95% CI error bars and direct labels |
| **Backend Web Server**| Flask | >=3.0.0 | REST JSON APIs, relative-route asset serving, dynamic PNG streaming |
| **Frontend UI** | HTML5 / CSS3 / Vanilla JS | ES6+ | SPA with 5 client views, hash routing, zero CDN dependencies |
| **Automated Testing** | Pytest | >=7.0.0 | 30 unit & integration tests covering data loader, analysis, Flask routes |

---

## 3. Directory Layout & Module Roles
```text
SympSort/
├── config.py              # Central constants, file paths, palettes, chart DPI settings
├── data_loader.py         # CSV loading, validation, cleaning, and ValidationReport
├── analysis.py            # Pandas groupby computation, moments, SmokerAnalysisResult
├── visualization.py       # Seaborn barplot rendering (Light/Dark themes), PNG byte generation
├── app.py                 # Flask factory (create_app), REST endpoints, cache management
├── main.py                # Application entrypoint: CLI runner (--cli) and desktop server runner
├── requirements.txt       # Pinned dependencies
├── pytest.ini             # Test runner configuration
├── run.bat / run.ps1      # Native OS launchers
├── ARCHITECTURE.md        # Master architectural and implementation specification
├── PRD.md                 # Product requirements and verification matrix
├── SCHEMA.md              # Original lab schema specification
├── data/
│   ├── insurance.csv      # Real Kaggle dataset (1,338 rows)
│   └── insurance_sample.csv # 50-row fallback fixture
├── outputs/
│   ├── smoker_charges_comparison.png # 300 DPI high-resolution export
│   └── smoker_charges_summary.csv    # Summary aggregation export
├── templates/
│   └── index.html         # Single-page application shell (5 distinct views)
├── static/
│   ├── css/
│   │   └── desktop.css    # Calm editorial styling, design tokens, light/dark themes
│   ├── js/
│   │   └── app.js         # Client router, table renderer, accessible sorting, theme sync
│   └── img/
│       ├── logo.png       # Project emblem
│       └── favicon.ico    # Standard favicon
└── tests/
    ├── conftest.py        # Shared pytest fixtures (mock DataFrames, Flask test client)
    ├── test_analysis.py   # Unit tests for Pandas grouped mean calculations and math
    ├── test_data_validation.py # Unit tests for CSV ingestion, coercion, missing columns
    └── test_flask_app.py  # Integration tests for HTTP 200, JSON structure, PNG streaming
```

---

## 4. End-to-End Data Pipeline
```text
[data/insurance.csv]
       │
       ▼
[data_loader.py] ───► Coerces charges to float64, trims & validates smoker values
       │
       ├──► ValidationReport (valid_rows, excluded_rows, warnings)
       ▼
[analysis.py] ──────► df.groupby('smoker')['charges'].mean()
       │
       ├──► SmokerAnalysisResult (means, medians, std, min, max, multiplier)
       ▼
[visualization.py] ─► sns.barplot (95% CI error bars, exact dollar annotations)
       │
       ├──► Cached PNG bytes (Light theme #FAF8F4 / Dark theme #1E1F22)
       ▼
[app.py] ───────────► Serves JSON endpoints & relative-path assets to Client
       │
       ├── GET /api/summary  -> Full statistical JSON payload + live groupby text
       ├── GET /api/chart    -> Dynamic theme-matching PNG stream
       ├── GET /api/data     -> Filtered, sorted, paginated records (JSON numbers, no NaN)
       └── GET /api/health   -> Server status and row counts
```

---

## 5. Mathematical Formulations & Exact Formulas
1. **Arithmetic Mean:**
   $$\bar{X}_{\text{smoker}} = \frac{1}{n_s} \sum_{i \in \text{smoker}} X_i = \$32,050.23 \quad (n_s = 274)$$
   $$\bar{X}_{\text{non-smoker}} = \frac{1}{n_{ns}} \sum_{j \in \text{non-smoker}} X_j = \$8,434.27 \quad (n_{ns} = 1,064)$$

2. **Absolute Difference:**
   $$\Delta_{\text{abs}} = \bar{X}_{\text{smoker}} - \bar{X}_{\text{non-smoker}} = +\$23,615.96$$

3. **Percentage Increase:**
   $$\Delta_{\text{pct}} = \left( \frac{\bar{X}_{\text{smoker}} - \bar{X}_{\text{non-smoker}}}{\bar{X}_{\text{non-smoker}}} \right) \times 100 = +280.00\%$$

4. **Relative Multiplier:**
   $$\text{Multiplier} = \frac{\bar{X}_{\text{smoker}}}{\bar{X}_{\text{non-smoker}}} \approx 3.80\times$$

---

## 6. Frontend Design Tokens & Architecture
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

## 7. Viva Q&A Cheat Sheet (For Examiner Defense)
1. **Q: Why use `df.groupby('smoker')['charges'].mean()` instead of a loop?**
   *A:* Pandas vectorization executes in optimized C/Cython via contiguous memory arrays, running orders of magnitude faster and producing cleaner, declarative code.
2. **Q: Why are charges for smokers skewed?**
   *A:* Smoker charges have a higher variance ($\text{std} = \$11,541.59$ vs $\$5,993.78$) and a bimodal distribution driven by smoking interaction with high BMI ($\ge 30$).
3. **Q: Does correlation imply causation here?**
   *A:* No. This is observational actuarial data. While smoking correlates with 3.80× higher charges, confounding factors (age, underlying conditions) must be controlled before claiming direct clinical causality.
