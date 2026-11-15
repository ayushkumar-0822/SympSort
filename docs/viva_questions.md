# Comprehensive Viva Voce Preparation Guide
## Mini Project: SympSort — Medical Cost & Lifestyle Factors
### Course: B.Tech IT Workshop Lab (PCC CS 393), Academic Year 2026–27

This guide contains **25 targeted, high-yield viva voce questions and model answers** designed for B.Tech engineering students facing internal and external examiners.

---

### Category 1: Problem Statement & Core Empirical Findings

#### Q1. What was the exact problem statement assigned to your group?
**Answer:**  
*"Find the average insurance charge for smokers vs. non-smokers using Pandas. Create a Seaborn barplot to visually compare the average costs between the two groups."*  
This is the official deliverable for IT Workshop Lab (PCC CS 393).

#### Q2. What dataset did you use, and how many records does it contain?
**Answer:**  
We used the **Medical Cost Personal Dataset** from Kaggle (originally compiled by Brett Lantz). It contains **1,338 records** across 7 attributes: `age`, `sex`, `bmi`, `children`, `smoker`, `region`, and `charges`.

#### Q3. What are the key empirical findings of your analysis?
**Answer:**  
From our 1,338 validated records:
- **Non-smokers ($n = 1,064$ / $79.52\%$):** Mean medical insurance charge is **\$8,434.27 USD** (median \$7,345.41 USD, $\text{std} = \$5,993.78$).
- **Smokers ($n = 274$ / $20.48\%$):** Mean medical insurance charge is **\$32,050.23 USD** (median \$34,456.35 USD, $\text{std} = \$11,541.55$).
- **Absolute difference:** **+\$23,615.96 USD** higher for smokers.
- **Relative percentage difference:** **+280.00%** higher compared to the non-smoker baseline.
- **Multiplier:** Smokers incur charges approximately **3.80×** the non-smoker average.

#### Q4. Does this analysis prove that smoking directly causes higher medical bills?
**Answer:**  
No. As responsible computer science and data engineering students, we distinguish **correlation from causation**. This is a cross-sectional observational dataset showing an overwhelming statistical association between smoking status and insurance charges. However, observational data alone cannot establish medical etiology or direct biological causation without clinical trials or controlling for longitudinal confounders.

---

### Category 2: Pandas Operations & Computational Methods

#### Q5. What is the central Pandas code used to compute the required averages?
**Answer:**  
```python
grouped_means = df.groupby('smoker')['charges'].mean()
```
This splits the DataFrame into cohorts based on the distinct values of the `'smoker'` column (`'no'` and `'yes'`), extracts the numeric `'charges'` Series for each cohort, and applies the vectorized `.mean()` aggregation.

#### Q6. What is the difference between `df.groupby('smoker')['charges'].mean()` and `df.groupby('smoker').mean()`?
**Answer:**  
- `df.groupby('smoker')['charges'].mean()` selects only the target `'charges'` column before aggregation, returning a clean 2-element Pandas Series.
- `df.groupby('smoker').mean()` attempts to calculate arithmetic means across *all* numeric columns (`age`, `bmi`, `children`, `charges`), causing redundant computations and potential type coercion warnings.

#### Q7. How does the Split-Apply-Combine paradigm work in Pandas?
**Answer:**  
It is the computational pattern introduced by Hadley Wickham:
1. **Split**: Partition the dataset into groups based on key values (e.g. `'no'` vs `'yes'`).
2. **Apply**: Compute summary statistics independently on each subset (`.mean()`, `.median()`, `.std()`, etc.).
3. **Combine**: Assemble individual scalar aggregates back into a unified Pandas Series or DataFrame indexed by the grouping keys.

#### Q8. Why did you use `pd.to_numeric(..., errors='coerce')` in your data loader?
**Answer:**  
In real-world data pipelines, columns can contain unparseable strings (e.g., `"N/A"`, `"-"`, whitespace). Using `errors='coerce'` turns non-numeric entries into `NaN` (Not a Number) instead of raising an unhandled `ValueError`. This allows our `ValidationReport` to flag, audit, and exclude corrupt records safely.

#### Q9. How did you normalize the `smoker` column?
**Answer:**  
We converted the column to string dtype, stripped leading/trailing whitespace with `.str.strip()`, and converted all characters to lowercase using `.str.lower()`. This ensures that messy real-world values like `" YES "` or `"No "` are cleanly normalized into standard `'yes'` and `'no'`.

---

### Category 3: Statistical Formulation & Inferential Rigor

#### Q10. What formula was used to calculate the percentage difference?
**Answer:**  
$$\text{Percentage Difference} = \left( \frac{\bar{X}_{\text{smoker}} - \bar{X}_{\text{non-smoker}}}{\bar{X}_{\text{non-smoker}}} \right) \times 100$$
$$\frac{32,050.23 - 8,434.27}{8,434.27} \times 100 = \frac{23,615.96}{8,434.27} \times 100 \approx +280.00\%$$

#### Q11. How are the 95% Confidence Interval error whiskers calculated?
**Answer:**  
The margin of error for a 95% confidence interval ($\alpha = 0.05$) is calculated using the Standard Error of the Mean:
$$SE = \frac{s}{\sqrt{n}}, \quad \text{Margin} = t_{0.975, df} \times SE$$
- **Non-smokers ($n = 1,064$, $s = \$5,993.78$):** $SE \approx 183.75$, Margin $\approx \pm \$360.15 \implies [\$8,074.12, \$8,794.42]$.
- **Smokers ($n = 274$, $s = \$11,541.55$):** $SE \approx 697.10$, Margin $\approx \pm \$1,366.61 \implies [\$30,683.62, \$33,416.84]$.
Notice that the smoker confidence interval is nearly $4\times$ wider due to both smaller sample size ($274$ vs $1,064$) and significantly higher sample variance ($\sigma = \$11,541.55$ vs $\$5,993.78$).

#### Q12. Why did you use Welch's t-test instead of Student's two-sample t-test?
**Answer:**  
Standard Student's t-test assumes **homoscedasticity** (equal population variances). In our dataset, the variance of smoker charges ($\sigma^2 \approx 1.33 \times 10^8$) is nearly **four times** the variance of non-smoker charges ($\sigma^2 \approx 3.59 \times 10^7$). Welch's t-test drops the equal variance assumption, calculating degrees of freedom via the Welch–Satterthwaite equation ($df \approx 311.85$), yielding an overwhelmingly significant test statistic:
$$t = \frac{\bar{X}_1 - \bar{X}_2}{\sqrt{\frac{s_1^2}{n_1} + \frac{s_2^2}{n_2}}} \approx 32.75, \quad p < 0.001$$

#### Q13. What is Cohen's d, and what does its value in your project mean?
**Answer:**  
Cohen's $d$ quantifies the standardized **effect size** (the difference between two group means divided by the pooled standard deviation):
$$d = \frac{\bar{X}_{\text{smoker}} - \bar{X}_{\text{non-smoker}}}{s_{\text{pooled}}} \approx 3.16$$
In statistical conventions, $d = 0.2$ is small, $d = 0.5$ is medium, and $d = 0.8$ is large. A Cohen's $d$ of **$3.16$** indicates an exceptionally massive separation between the two distributions.

#### Q14. Why is the median lower than the mean for non-smokers, but higher than the mean for smokers?
**Answer:**  
Non-smoker charges exhibit severe **positive (right) skewness**: most healthy non-smokers incur low baseline costs ($<\$5,000$), but a few high-cost cases pull the mean (\$8,434.27) above the median (\$7,345.41). Conversely, smoker charges display a **bimodal distribution**: a cluster near \$15,000–\$20,000 and another high-cost cluster above \$40,000 (especially smokers with $\text{BMI} \ge 30$).

---

### Category 4: Seaborn & Matplotlib Visualization Engineering

#### Q15. How did you ensure the barplot displays visible 95% CI error whiskers?
**Answer:**  
In `visualization.py`, we pass the complete 1,338-row DataFrame to Seaborn:
```python
sns.barplot(
    data=df,
    x="smoker",
    y="charges",
    order=["no", "yes"],
    palette={"no": "#1F6F63", "yes": "#B5442E"},
    errorbar=("ci", 95),
    capsize=0.15,
    err_kws={"linewidth": 2.2, "color": text_color},
    ax=ax,
)
```
Passing the raw DataFrame allows Seaborn to compute bootstrap/t-distribution confidence interval bounds from the actual row variances, rendering clearly visible error whiskers with caps.

#### Q16. How did you annotate exact dollar values above the bars?
**Answer:**  
We iterate through `ax.patches`, retrieve each bar's coordinate and height:
```python
for bar in ax.patches:
    val = bar.get_height()
    if val > 0:
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            val + 1100,
            f"${val:,.2f}",
            ha="center",
            va="bottom",
            fontweight="bold",
            fontsize=11.5,
        )
```

#### Q17. What secondary charts did you build to support deeper analytical inquiry?
**Answer:**  
We implemented 6 additional exploratory chart kinds:
1. **Distribution (KDE)** (`sns.kdeplot`): Visualizes the unimodal non-smoker density vs bimodal smoker density.
2. **Boxplot** (`sns.boxplot`): Displays median, IQR, whiskers, and extreme actuarial outliers.
3. **BMI vs Charges Scatter** (`sns.scatterplot`): Highlights the critical interaction at $\text{BMI} \ge 30$ (obesity threshold).
4. **Region × Smoker** (`sns.barplot`): Proves the smoker disparity persists across Northeast, Northwest, Southeast, Southwest.
5. **Sex × Smoker** (`sns.barplot`): Shows smoking cost inflation impacts female and male policyholders equally.
6. **Age Bands × Smoker** (`sns.barplot`): Bins age into 18–29, 30–44, 45–64 to show how smoking amplifies healthcare costs across the lifespan.

---

### Category 5: Architecture, Web Engineering & Concurrency

#### Q18. Why is the application architected as a Flask REST service with hash routing?
**Answer:**  
- **Instant navigation**: Switching views (`#overview`, `#comparison`, `#explorer`, `#methodology`, `#about`) happens instantaneously in the DOM without full page reloads.
- **Deep-linking & accessibility**: Hash routing updates the browser URL, preserving Back/Forward history and allowing direct bookmarks. Keyboard shortcuts 1–5 allow rapid grading inspection.
- **Decoupled API**: The backend exposes clean REST endpoints (`/api/summary`, `/api/chart`, `/api/data`, `/api/profile-match`, `/api/data-quality`) that output pure JSON and PNG binary streams.

#### Q19. How did you diagnose and solve the "Connection Error: could not connect to backend server" bug from earlier attempts?
**Answer:**  
1. All client-side fetch calls were converted to **relative paths** (`fetch('/api/summary')` instead of hardcoded `http://localhost:5000/api/summary`).
2. The frontend is served directly by Flask from `/` via `render_template("index.html")`, eliminating cross-origin and file protocol (`file://`) restrictions.
3. Added a `/api/health` polling check that drives a dynamic status pill ("Connected: 1,338 rows" vs "Reconnecting…").
4. Implemented absolute path resolution in `config.py` using `Path(__file__).resolve().parent`, guaranteeing that dataset loading succeeds regardless of the terminal working directory.

#### Q20. How is chart image streaming handled without writing temporary files to disk?
**Answer:**  
In `visualization.py`, Matplotlib saves the figure directly into an in-memory byte buffer:
```python
buf = io.BytesIO()
fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
buf.seek(0)
png_bytes = buf.read()
```
The bytes are cached in an in-memory dictionary (`_chart_cache`) and served via Flask's `send_file(io.BytesIO(png_bytes), mimetype="image/png")`. This eliminates disk I/O bottlenecks and avoids concurrent file write collisions.

---

### Category 6: Automated Testing & Verification

#### Q21. How many automated tests exist in your test suite, and what do they verify?
**Answer:**  
We have **40 automated tests** passing in `pytest`:
- **`tests/test_analysis.py`** (9 tests): Grouped means match exact ground-truth values (\$8,434.27 and \$32,050.23), multiplier is 3.80×, percentage difference is +280.00%, empty/corrupt DataFrames raise exceptions, JSON serialization succeeds.
- **`tests/test_data_validation.py`** (8 tests): Missing CSV fallback, missing required column validation, non-numeric charge coercion, whitespace trimming, empty file handling.
- **`tests/test_flask_app.py`** (23 tests): Endpoint health, index rendering, summary JSON schema, 95% confidence intervals, 7 multi-chart PNG types, profile matching and small sample warning ($n < 20$), data quality audit, CSV downloads, pagination, and sorting.

#### Q22. How do you run the test suite and CLI standalone mode?
**Answer:**  
- **Test suite**:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest -v
  ```
- **CLI analysis mode**:
  ```powershell
  .\.venv\Scripts\python.exe main.py --cli
  ```
- **Standalone 25-line lab solution**:
  ```powershell
  .\.venv\Scripts\python.exe lab_solution.py
  ```

#### Q23. What is the empirical Profile Matcher tool, and why was it implemented?
**Answer:**  
The Profile Matcher (`/api/profile-match`) is an interactive actuarial lookup tool that allows an examiner or student to specify a demographic cohort (e.g. Young Adult 18–29, Normal BMI $<25$, Non-Smoker vs Smoker) and instantly see empirical counts, mean charges, median charges, and range. If a selected subgroup has fewer than 20 records, it displays a statistical advisory warning regarding higher empirical sample variance.

#### Q24. Which Program Outcomes (POs) are demonstrated in this mini project?
**Answer:**  
- **PO1 (Engineering Knowledge):** Mathematical formulation of Welch's t-test, Cohen's d, standard errors, and confidence intervals.
- **PO2 (Problem Analysis):** Dissecting lifestyle and healthcare expenditure correlations.
- **PO3 (Design/Development):** Full-stack REST architecture with accessible typography and clean editorial design.
- **PO5 (Modern Tool Usage):** Python 3.13, Pandas 2.2, Seaborn 0.13, Matplotlib, Flask, Pytest, and modern browser APIs.
- **PO8 (Ethics):** Transparently documenting observational limitations, avoiding false causal claims, and ensuring empirical honesty.
- **PO10 (Communication):** Presenting academic findings with clear visual hierarchy, accessible data tables, and an executive summary.

#### Q25. What is the single most important academic conclusion of this work?
**Answer:**  
While average smoker insurance charges are **3.80× higher** (+\$23,615.96 USD) with overwhelming statistical significance ($t = 32.75, p < 0.001, d = 3.16$), visual decomposition reveals that smoking and obesity ($\text{BMI} \ge 30$) act together to create the highest tier of medical expenses (exceeding \$35,000), whereas normal-weight smokers experience lower (though still elevated) charges. Observational data reveals strong actuarial correlation, but holistic policy requires evaluating multiple lifestyle determinants.
