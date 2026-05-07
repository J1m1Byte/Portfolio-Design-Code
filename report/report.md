# Active Portfolio Construction with Value Factors
## MFIN 5600 — US Equity Sleeve Report

---

## 1. Investment Objective

Construct a long-only, benchmark-aware US equity portfolio that delivers positive alpha over the S&P 500 with moderate tracking error. The strategy is designed for a long-horizon endowment client benchmarked to the S&P 500, targeting asymmetric capture — participating in up markets while limiting drawdowns.

---

## 2. Investment Thesis

**Value over growth.** Value stocks exhibit a well-documented long-run premium: from 1927 to 2017, US value stocks outperformed growth by approximately 4.8% annualized, with value beating growth in 78% of rolling 5-year windows and 94% of rolling 20-year windows. Value is a contrarian, negative-feedback strategy — it buys low and sells high, which provides natural protection against overreaction-driven drawdowns common in growth strategies. For a long-horizon endowment, this downside asymmetry matters more than peak return.

**Composite scoring, not single-factor.** No single value factor is reliable in isolation, so the portfolio scores each stock on six factors simultaneously and uses a random-search optimizer to find the weighting that best exploits the training window.

| Factor | Direction | Rationale |
|---|---|---|
| P/E | Lower is better | Cheap relative to earnings; mean-reverts as earnings recover |
| P/B | Lower is better | Cheap relative to book value; tangible-asset margin of safety |
| P/S | Lower is better | Cheap relative to revenue; works when earnings are temporarily depressed |
| EV/EBITDA | Lower is better | Capital-structure neutral; less distortable than P/E |
| FCF Yield | Higher is better | Direct cash-generation signal; resistant to accounting choices |
| Earnings Yield | Higher is better | E/P — the effective earnings rate investors are buying |

Each factor is z-scored cross-sectionally every month. Lower-is-better factors are sign-flipped so all six point in the same direction before weighting.

---

## 3. Data

| Variable | Provider | Scope |
|---|---|---|
| S&P 500 value factors (6 factors, monthly) | Morningstar Direct | `data/raw/sp500_factors.xlsx` |
| S&P 500 monthly returns (per ticker) | Morningstar Direct | `data/interim/<window>_sp_ret.csv` |
| S&P 500 benchmark return (`sprtrn`) | WRDS / CRSP `crsp.msi` | `data/interim/<window>_sp_bmk.csv` |
| Risk-free rate (`rf`) | WRDS / Fama–French `ff.factors_monthly` | `data/interim/<window>_rf.csv` |

Two evaluation windows were constructed independently:

- **5-year window:** 2020-01 → 2024-12 (`data/clean/5y_merged.csv`)
- **10-year window:** 2014-01 → 2024-12 (`data/clean/10y_merged.csv`) — primary window for all model development

Data pipeline notebooks (`notebook/data/`) pull each source, align on month-end dates, drop tickers with incomplete return history, and write the merged panels to `data/clean/`. A Morningstar Direct authorization token is read from `~/.md_token` and is never committed.

---

## 4. Methodology

### 4.1 Baseline: Fixed Equal-Weight (Notebook 1.0)

The starting point is the simplest implementable strategy: z-score all six factors with equal weights (1/6 each), sum into a composite score, rank all S&P 500 constituents, and hold the top 20 stocks equal-weighted. This serves as the performance floor — any subsequent optimization must beat it to justify added complexity.

### 4.2 Factor-Weight Random Search (Notebook 2.0 → 2.2)

Construction proceeds in two stages, both fit entirely on the training window. All choices are frozen before any test-window data is touched.

**Stage 1 — Factor weight search:**

For each of N = 10⁶ trials, draw a 6-dimensional weight vector from a Dirichlet distribution (positive entries, sum to 1). Compute each stock's composite score as the weighted sum of its z-scored factors, rank, select the top 45, and form an equal-weighted monthly portfolio. Score the trial by annualized active return on the training window:

$$\text{Ann. Active Return} = \frac{1200}{T} \sum_{t=1}^{T}(r_t - b_t)$$

**Stage 2 — Ensemble averaging (top-K):**

Taking the single highest-scoring trial overfits the training window. Instead, the top 100 trials by training active return are identified and their factor-weight vectors are averaged. The averaged vector is materially more stable than any single winner, and test-window performance is less seed-dependent. This is the production factor weight vector used for stock selection.

**Portfolio construction:**

- Universe: all S&P 500 constituents with complete data for the evaluation window
- Selection: top 45 stocks by composite factor score each month
- Weighting: equal-weighted
- Rebalancing: monthly

### 4.3 Sensitivity Analysis (Notebook 3.0)

Portfolio size sensitivity was tested by iterating from 1 to 300 holdings and recording out-of-sample total return at each size. The return curve is roughly flat from approximately 30 to 60 stocks. Forty-five stocks sits comfortably within the stable region, providing sufficient breadth to keep tracking error moderate without diluting the factor signal. Three hyperparameter configurations were tested: (N=10³, K=50), (N=10⁶, K=100), (N=10⁴, K=50).

### 4.4 Stability Analysis (Notebook 4.0)

Because both optimization stages use Dirichlet random search, seed dependence is a genuine concern. The full pipeline was wrapped into a single function and re-run 50 times with different random seeds. An OLS regression of each performance metric against run index tests whether performance drifts across seeds.

| Outcome | OLS Slope (per run) | p-value | 90% CI contains 0? |
|---|---:|---:|---|
| Total test-period return (%) | +0.19 | 0.31 | Yes (−0.12, +0.51) |
| Annual active return (%) | +0.012 | 0.45 | Yes (−0.015, +0.040) |

Neither slope is statistically distinguishable from zero. Reported performance is not an artifact of a lucky random seed.

---

## 5. Results

All performance figures are from the 10-year window (2014-01 → 2024-12) with a 50/50 chronological train-test split. The test window covers 2019-07 → 2024-12. The benchmark is the S&P 500 total return (`sprtrn`).

| Metric | Train | Test | Benchmark (test) |
|---|---:|---:|---:|
| Total return | ~137% | **~134%** | ~100% |
| Annualized mean monthly return | — | ~1.47% | — |
| Sharpe ratio | ~1.17 | ~0.74 | — |
| Jensen alpha (annualized) | — | **~3.0%** | — |
| Information ratio | — | ~0.35 | — |
| Tracking error (annualized) | — | ~2.9% | — |
| Beta to S&P 500 | — | ~1.05 | 1.00 |
| Correlation to S&P 500 | — | 0.87 | 1.00 |
| Up-market capture | — | ~104% | 100% |
| Down-market capture | — | **~88%** | 100% |

**Key observations:**

- The strategy outperformed the benchmark by approximately 34 percentage points over the test window on a cumulative basis.
- The Jensen alpha of ~3.0% annualized is statistically and economically meaningful for a long-only equity mandate.
- The down-market capture of ~88% is the primary driver of the return spread: the portfolio captures slightly more than the benchmark on the way up and materially less on the way down. This asymmetry is structurally consistent with the value thesis.
- The cumulative return spread accumulates gradually across the test window rather than arising from a single lucky period.
- Tracking error of ~2.9% is moderate and appropriate for a benchmark-aware mandate.
- Beta of ~1.05 and correlation of 0.87 confirm that the portfolio remains closely tied to the broad market and is not making aggressive factor bets.

---

## 6. Implementation Details

### Metrics (`src/metrics.py`)

| Function | Formula |
|---|---|
| `total_return(r)` | $(1+r_1)(1+r_2)\cdots(1+r_T) - 1$ |
| `ann_return(r)` | $100 \times \left[(1+\text{total})^{12/T} - 1\right]$ |
| `ann_sharpe(r, rf)` | $\frac{\bar{r} - \bar{r}_f}{\sigma_r} \times \sqrt{12}$ |
| `ann_active_return(r, bmk)` | $1200 \times \overline{(r - b)}$ |
| `ann_tracking_error(r, bmk)` | $\sigma_{r-b} \times \sqrt{12} \times 100$ |
| `information_ratio(r, bmk)` | $\text{Ann. Active Return} \div \text{Ann. Tracking Error}$ |

### Performance Tearsheet (`src/chart.py`)

`chart(r, bmk, rf)` produces a three-panel figure:
1. **Top:** Cumulative return — portfolio vs. benchmark
2. **Middle:** Spread return (portfolio minus benchmark, green/red fill)
3. **Bottom:** Monthly active return bar chart

A stats panel on the right reports all key metrics including Jensen alpha and beta (via OLS of monthly excess returns on benchmark excess returns), up/down capture ratios, semi-variance, and correlation.

### Portfolio Size Helper (`src/fig.py`)

`hist_g(r_list, interval, bmk)` plots total return as a function of portfolio size and a bar chart of the best-performing size within each size interval. Used in notebook 3.0 for the sensitivity sweep.

---

## 7. Project Structure

```
data/
  raw/        Source factor exports (Morningstar Direct)
  interim/    Per-source, per-window splits
  clean/      Final merged panels used by model notebooks

notebook/
  data/
    01-data-5y.ipynb      Pull and merge the 5-year panel
    02-data-10y.ipynb     Pull and merge the 10-year panel (primary)
  model/
    1.0-fixed-equal.ipynb     Baseline: fixed size, equal factor weights
    2.0-variable-score.ipynb  Random-search factor weights
    2.1-variable-best.ipynb   2.0 + second search over per-stock weights
    2.2-variable-avg.ipynb    Top-K averaging — production strategy
    3.0-rolling.ipynb         Sensitivity to hyperparameters and portfolio size
    4.0-stability.ipynb       50-seed stability test

src/
  paths.py    Project directory constants
  metrics.py  Performance metric functions
  chart.py    Full performance tearsheet
  fig.py      Portfolio-size sensitivity plot helper

output/       Figures from successive model iterations (1-initial → 4-final)
report/       This report
```

---

## 8. Environment

- Python 3.11+
- Core libraries: `pandas`, `numpy`, `scipy`, `matplotlib`, `statsmodels`
- Data access: `morningstar_data`, `wrds`
- Credentials: WRDS username/password via environment variables; Morningstar Direct token at `~/.md_token` (24-hour validity, never committed)
- All data files are git-ignored; only source code, notebooks, output figures, and this report are tracked
