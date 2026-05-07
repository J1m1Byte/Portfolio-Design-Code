# Active Portfolio Construction with Value Factors

A long-only, benchmark-aware S&P 500 strategy that builds a 45-stock value portfolio by random-searching factor weights against the index. Designed to deliver positive alpha with moderate tracking error rather than aggressive concentrated bets — appropriate for a long-horizon endowment client benchmarked to the S&P 500.

Built as part of MFIN 5600 (Schulich School of Business), originally framed as the US-equity sleeve of the Blue Heaven Endowment Fund case study.

## Headline Results

Two-stage Dirichlet-weighted factor model, 45-stock portfolio, 50/50 chronological train/test split over the 10-year window (2014-01 → 2024-12).

| Metric | Train | Test | Benchmark (test) |
|---|---:|---:|---:|
| Total return | ~137% | **~134%** | ~100% |
| Annualized mean monthly return | — | ~1.47% | — |
| Sharpe ratio | ~1.17 | ~0.74 | — |
| Jensen alpha (annualized) | — | **~3.0%** | — |
| Information ratio | — | ~0.35 | — |
| Tracking error | — | ~2.9% | — |
| Beta to S&P 500 | — | ~1.05 | 1.00 |
| Correlation to S&P 500 | — | 0.87 | 1.00 |
| Up-market capture | — | ~104% | 100% |
| Down-market capture | — | **~88%** | 100% |

The strategy outperforms by capturing slightly more on the way up and noticeably less on the way down. The cumulative-return spread accumulates gradually across the test window rather than coming from a single lucky month.

### Stability across random seeds

Both stages of the model rely on Dirichlet random search, so seed dependence is a real concern. Wrapping the entire pipeline into one function and re-running it 50 times with different seeds:

| Outcome | OLS slope (per run) | p-value | 90% CI contains 0? |
|---|---:|---:|---|
| Total test-period return (%) | +0.19 | 0.31 | yes ([−0.12, +0.51]) |
| Annual active return (%)     | +0.012 | 0.45 | yes ([−0.015, +0.040]) |

Reported performance is not seed-dependent.

---

## Investment Thesis

**Value over growth.** From 1927 to 2017, US value stocks outperformed growth by ~4.8% annualized, and value beat growth in 78% of rolling 5-year windows and 94% of rolling 20-year windows (Brain, 2017). Value is a contrarian, negative-feedback strategy: it buys low and sells high, which provides protection against the kind of overreaction-driven drawdowns that punish momentum-style growth strategies. For a long-horizon endowment client, that asymmetry matters more than peak return.

**Value composite, not single-factor.** No single value factor is reliable on its own, so the portfolio scores stocks on six factors simultaneously and lets the optimizer find the mix.

| Factor | Direction | Rationale |
|---|---|---|
| P/E | lower is better | Cheap relative to earnings; mean-reverts as earnings recover |
| P/B | lower is better | Cheap relative to book value; tangible-asset margin of safety |
| P/S | lower is better | Cheap relative to revenue; works when earnings are temporarily depressed |
| EV/EBITDA | lower is better | Capital-structure neutral; less distortable than P/E |
| FCF Yield | higher is better | Direct cash-generation signal; resistant to accounting choices |
| Earnings Yield | higher is better | E/P; the "earnings rate" investors are buying |

Each factor is z-scored across the cross-section every month; lower-is-better factors are sign-flipped so all six contribute in the same direction.

---

## Methodology

The construction has two stages and is fit entirely on the training window — all modeling choices are then frozen for the test window.

### Stage 1: Factor-weight search

For each of N trials, draw a 6-vector from a Dirichlet distribution (positive, sums to 1). Multiply each factor's z-scores by its weight, sum across factors to get a composite score per stock, rank, take the top 45, and form an equal-weighted monthly portfolio. Score the trial by annualized active return on the training window:

$$
\mathrm{ann\text{-}active\text{-}return}(r, b) = \frac{1200}{T} \sum_{t=1}^{T}(r_t - b_t)
$$

### Stage 2: Stability via top-K averaging

Picking the single best-scoring trial overfits the training window. Instead, take the top K trials by training active return and average their factor-weight vectors. The averaged vector is more stable than any single winner, and out-of-sample performance is materially less seed-dependent.

### Why long-only and 45 stocks

The portfolio is long-only and equal-weighted across its 45 holdings, by design. Constraining to long-only keeps the strategy implementable at endowment scale and eliminates short-funding risk. The portfolio-size sweep (see `notebook/model/3.0-rolling`) shows that out-of-sample total return is roughly flat from ~30 to ~60 holdings; 45 sits comfortably in the stable region while preserving enough breadth to keep tracking error moderate.

---

## Data

| Variable | Provider | Path |
|---|---|---|
| S&P 500 value factors | Morningstar Direct | `data/raw/sp500_factors.xlsx` |
| S&P 500 monthly returns (per ticker) | Morningstar Direct | `data/interim/<window>_sp_ret.csv` |
| S&P 500 benchmark return (`sprtrn`) | WRDS / CRSP `crsp.msi` | `data/interim/<window>_sp_bmk.csv` |
| Risk-free rate (`rf`) | WRDS / Fama–French `ff.factors_monthly` | `data/interim/<window>_rf.csv` |

Two evaluation windows are pulled and merged independently:

- **5-year:** 2020-01 → 2024-12 (`5y_*.csv`)
- **10-year:** 2014-01 → 2024-12 (`10y_*.csv`) — primary window for all model notebooks

After the per-source pulls are merged on month-end and any tickers with missing return history are dropped, the surviving panel is written to `data/clean/<window>_merged.csv` plus a filtered `data/interim/<window>_factors.csv`.

A Morningstar Direct authorization token is read from `~/.md_token` (24-hour validity, refreshed from the Analytics Lab UI). It is never committed.

---

## Notebook Map

```
notebook/data/
  01-data-5y.ipynb           Pull + merge the 5-year panel
  02-data-10y.ipynb          Pull + merge the 10-year panel (primary)

notebook/model/
  1.0-fixed-equal.ipynb      Fixed size, equal factor weights — static baseline
  2.0-variable-score.ipynb   Random-search factor weights, score-weighted z-scores
  2.1-variable-best.ipynb    2.0 + a second random search over per-stock weights
  2.2-variable-avg.ipynb     Average top-K factor models — the production strategy
  3.0-rolling.ipynb          Sensitivity to (trials_train, top_k) and portfolio size
  4.0-stability.ipynb        50-seed re-run of the full pipeline; OLS slope test
```

Each model notebook is self-contained and runs end-to-end on the 10-year window; opening any one requires no prior notebook to have been executed.

---

## Project Structure

```
data/
  raw/        Source pulls (Morningstar factor exports)
  interim/    Per-source per-window splits + factor-clean snapshot
  clean/      Final merged panels used by the model notebooks

notebook/
  data/       Data pipeline notebooks
  model/      Experiment notebooks

src/
  paths.py    Project directory constants
  metrics.py  total / annualized / Sharpe / active / tracking-error / IR
  chart.py    chart() — full performance tearsheet (cumulative, spread, active, stats)
  fig.py      hist_g() — portfolio-size scan helper

output/       Figures from successive iterations of the model (1-initial → 4-final)
report/       Final case-study slides
```

---

## Environment

- Python 3.11+
- `pandas`, `numpy`, `scipy`, `matplotlib`, `statsmodels`, `morningstar_data`, `wrds`
- WRDS credentials in `WRDS_USERNAME` / `WRDS_PASSWORD` (or `.env`)
- Morningstar Direct auth token at `~/.md_token`
- Data files are git-ignored; only source code, notebooks, output figures, and the report are tracked
