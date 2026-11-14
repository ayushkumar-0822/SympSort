# Comprehensive Viva Voce Preparation Guide
## Mini Project: SympSort — Medical Cost & Lifestyle Factors (PCC CS 393)

This guide contains **25 targeted viva voce questions and model answers** designed for B.Tech first-year engineering students facing internal and external examiners for the IT Workshop Lab.

---

### Category 1: Problem Statement & Core Findings

#### Q1. What was the exact problem statement assigned to your group?
**Answer:**  
*"Find the average insurance charge for smokers vs. non-smokers using Pandas. Create a Seaborn barplot to visually compare the average costs between the two groups."*  
It is Problem #1 from the official IT Workshop Lab (PCC CS 393) Mini Project list.

#### Q2. What dataset did you use, and how many records does it contain?
**Answer:**  
We used the **Medical Cost Personal Dataset** hosted by mirichoi0218 on Kaggle (originally compiled by Brett Lantz). The dataset contains **1,338 records** across 7 attributes: `age`, `sex`, `bmi`, `children`, `smoker`, `region`, and `charges`.

#### Q3. What are the key empirical findings of your analysis?
**Answer:**  
In our dataset of 1,338 individuals:
- **Non-smokers ($n = 1,064$ / $79.52\%$):** Average medical insurance charge was **\$8,434.27 USD**.
- **Smokers ($n = 274$ / $20.48\%$):** Average medical insurance charge was **\$32,050.23 USD**.
- **Absolute difference:** **+\$23,615.96 USD** higher for smokers.
- **Relative percentage difference:** **+280.00%** higher compared to the non-smoker average.

#### Q4. Does this analysis prove that smoking directly causes higher medical bills?
**Answer:**  
No. As good engineering researchers, we must distinguish **correlation from causation**. This is an observational, descriptive analysis showing a strong statistical association between self-reported smoking and billed medical charges. However, it does not prove smoking was the direct sole cause for an individual bill, as other factors like age, BMI, or specific underlying medical conditions also play a role.

---

### Category 2: Pandas Operations & Data Processing

#### Q5. What is the central Pandas code used to compute the required averages?
**Answer:**  
```python
average_charges = df.groupby("smoker")["charges"].mean()
```
This splits the DataFrame into subsets based on the distinct values of the `"smoker"` column, extracts the `"charges"` Series for each subset, and applies the vectorized `.mean()` aggregation.

#### Q6. What is the difference between `df.groupby('smoker')['charges'].mean()` and `df.groupby('smoker').mean()`?
**Answer:**  
- `df.groupby('smoker')['charges'].mean()` aggregates only the numeric `'charges'` column and returns a Pandas Series.
- `df.groupby('smoker').mean()` attempts to compute the arithmetic mean across *all* numeric columns in the DataFrame (e.g., `age`, `bmi`, `children`, `charges`), which performs redundant computation when only charges are needed.

#### Q7. How does the Split-Apply-Combine paradigm work in Pandas?
**Answer:**  
It is the three-stage pattern introduced by Hadley Wickham that `groupby()` implements:
1. **Split**: Break the dataset into distinct subsets based on the grouping keys (e.g., `"yes"` vs. `"no"`).
2. **Apply**: Execute an aggregation function (like `.mean()`, `.count()`, or `.median()`) independently on each subset.
3. **Combine**: Merge the individual results back into a unified Pandas Series or DataFrame indexed by the grouping keys.

#### Q8. Why did you use `pd.to_numeric(..., errors='coerce')` in your data loader?
**Answer:**  
In real-world CSV files, numerical columns can sometimes contain corrupted text (e.g., `"N/A"`, `"-"`, or typos). Using `errors='coerce'` converts valid numbers into floats while turning unparseable strings into `NaN` (Not a Number). This prevents the entire application from crashing, allowing us to cleanly identify and filter corrupted rows.

#### Q9. How did you normalize the `smoker` column?
**Answer:**  
We converted the column to strings, stripped any leading or trailing whitespace with `.str.strip()`, and converted all characters to lowercase using `.str.lower()`. This ensures that entries like `" YES "` or `"No "` are correctly categorized as `"yes"` or `"no"`.

---

### Category 3: Mathematical & Statistical Formulations

#### Q10. What formula was used to calculate the percentage difference?
**Answer:**  
$$\text{Percentage Difference} = \left( \frac{\bar{C}_{\text{smoker}} - \bar{C}_{\text{non-smoker}}}{\bar{C}_{\text{non-smoker}}} \right) \times 100$$
Relative to the non-smoker baseline:
$$\frac{32,050.23 - 8,434.27}{8,434.27} \times 100 \approx 280.00\%$$

#### Q11. How do you prevent a division-by-zero error if the non-smoker average is zero?
**Answer:**  
In `analysis.py`, we check `if non_smoker_mean > 0:`. If the baseline is zero or negative, we set `percentage_difference = None` and report an informative message such as `"N/A (Reference average is zero)"`, ensuring the program never throws an uncaught `ZeroDivisionError`.

#### Q12. Why do you store unrounded values during calculations and only round during display?
**Answer:**  
To prevent **cumulative rounding error** (floating-point loss of precision). Calculations (such as differences and percentages) should always use the full precision IEEE 754 floating-point representations. Rounding to 2 decimal places is strictly for human readability on charts and UI cards.

#### Q13. Why did you examine median and standard deviation in addition to the mean?
**Answer:**  
The arithmetic mean can be sensitive to extreme outliers. The median gives the 50th percentile (central tendency), and standard deviation ($\sigma$) measures data dispersion. For non-smokers, the median is \$7,345.41 USD ($\sigma = \$5,993.78$), while for smokers it is \$34,456.35 USD ($\sigma = \$11,541.55$), confirming that the smoker distribution is shifted substantially higher across all percentiles.

---

### Category 4: Seaborn & Matplotlib Visualizations

#### Q14. Why did you choose Seaborn instead of plain Matplotlib for this chart?
**Answer:**  
Seaborn is built on top of Matplotlib and is specifically designed for statistical data visualization. It integrates natively with Pandas DataFrames, provides high-level aesthetic presets (`sns.set_theme(style="whitegrid")`), and automatically maps categorical groupings to customized palettes with minimal boilerplate code.

#### Q15. How did you ensure the barplot represents the arithmetic mean rather than count or sum?
**Answer:**  
We pre-aggregated the DataFrame using Pandas `.mean()`:
```python
df_grouped = valid_df.groupby("smoker", as_index=False)["charges"].mean()
```
We then passed `y="mean_charges"` directly to `sns.barplot()`. This guarantees that the height of each bar corresponds strictly to the precomputed arithmetic mean.

#### Q16. How did you format the Y-axis tick labels to show currency symbols ($)?
**Answer:**  
We used Matplotlib's `ticker.FuncFormatter`:
```python
import matplotlib.ticker as ticker
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda val, pos: f"${val:,.0f}"))
```
This formats numbers like `10000` into `"$10,000"`.

#### Q17. How did you annotate the values on top of the bars?
**Answer:**  
We iterated through `ax.patches` (which represent the rectangular bars of the chart), retrieved the height using `patch.get_height()`, and called `ax.annotate(f"${height:,.2f}", ...)` centered above each rectangle.

---

### Category 5: Software Architecture & Modular Design

#### Q18. How is your project structured, and why didn't you write everything in one script?
**Answer:**  
We separated concerns into dedicated, single-responsibility modules:
- `config.py`: Centralized constants, paths, and palette settings.
- `data_loader.py`: Ingestion, schema validation, and data cleaning.
- `analysis.py`: Groupby aggregation and difference calculations.
- `visualization.py`: Seaborn plotting and in-memory PNG streaming.
- `app.py`: Flask backend providing REST endpoints and serving the web shell.
- `templates/` & `static/`: HTML5, desktop CSS3, and JavaScript frontend.
- `tests/`: Automated unit and API integration tests using `pytest`.

Writing everything in one monolithic file violates the Single Responsibility Principle, makes unit testing difficult, and makes code hard to maintain.

#### Q19. Why did you choose a custom Flask desktop-style web architecture over a generic framework?
**Answer:**  
A custom Flask backend coupled with semantic HTML5, CSS3, and Vanilla JavaScript creates a true **desktop-application feel** with zero bloat. It provides direct control over REST APIs (`/api/summary`, `/api/chart`, `/api/data`), allows seamless client-side view switching without full page refreshes, and enables live search and pagination without heavy frontend dependencies like React or Electron.

#### Q20. What happens if the `insurance.csv` file is missing when the app runs?
**Answer:**  
Instead of crashing with an unhandled exception, `data_loader.py` catches the missing file, returns a `ValidationReport` with `is_valid = False`, and the desktop UI displays an informative alert card explaining where to download the dataset and where to place it (`data/insurance.csv`), with a live "Reload Data" button once placed.

---

### Category 6: Automated Testing & Academic Standards

#### Q21. How did you test your calculations?
**Answer:**  
We wrote automated unit tests using `pytest` in `tests/test_analysis.py`. We tested against a known academic fixture:
```python
sample = pd.DataFrame({
    "smoker": ["yes", "yes", "no", "no"],
    "charges": [300.0, 500.0, 100.0, 200.0],
})
```
Expected: Smoker mean = 400.0, Non-smoker mean = 150.0, Difference = 250.0, Percentage difference = 166.67%. All tests pass.

#### Q22. How many automated tests exist in your test suite?
**Answer:**  
We have **11 automated tests** covering:
- Standard calculation fixture.
- Zero non-smoker baseline safety.
- Empty DataFrame handling.
- Missing required column detection.
- Seaborn chart generation.
- Missing file handling.
- Corrupted non-numeric charges filtering.
- Whitespace and case normalization.
- Unrecognized categorical values handling.
- Sample dataset generator structure.

#### Q23. What command is used to execute the test suite?
**Answer:**  
From the project root in Windows PowerShell:
```powershell
.\.venv\Scripts\pytest -v
```

#### Q24. Which Program Outcomes (POs) does this mini project address?
**Answer:**  
Primarily:
- **PO1 (Engineering Knowledge):** Applying mathematics and computational aggregation to empirical data.
- **PO2 (Problem Analysis):** Analyzing health expenditure disparities.
- **PO5 (Modern Tool Usage):** Mastering Python 3, Flask, Pandas, Seaborn, Matplotlib, HTML5/CSS3/JavaScript, and Pytest.
- **PO8 (Ethics):** Reporting authentic data without fabrication and avoiding false causal claims.
- **PO10 (Communication):** Presenting results via visual graphs, interactive UI, and an academic synopsis.

#### Q25. If given more time, what would you add as a future enhancement?
**Answer:**  
We would perform a **multivariate analysis** examining how Body Mass Index (BMI) interacts with smoking status (e.g., comparing obese smokers vs. normal-weight non-smokers), and run formal inferential statistical tests like a two-sample $t$-test to report exact $p$-values and 95% confidence intervals.
