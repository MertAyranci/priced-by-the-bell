# Decision and experiment log

Every design change and every strategy variant run is recorded here, grouped by project stage and listed in the order they happened. The design freeze is git commit fec2b54.

## Stage 1: Design decisions (before any results were seen)

| Decision / change | Reason | Out-of-sample viewed? | Effect on claims |
|---|---|---|---|
| Select weekend Bitcoin → Monday open-to-close drift hypothesis | Clear mechanism; feasible scope | No | Hypothesis only |
| Two periods instead of three: in-sample 2021-01-01 to 2023-12-31, out-of-sample 2024-01-01 to 2025-12-31 | The rule `x > 0` has no fitted parameter, so a separate validation year has nothing to tune; in-sample used for pipeline debugging and descriptive analysis | No | Out-of-sample is the only performance claim |
| Add weeknight events (prior 16:00 → 09:00 NY, Tue–Fri) as a secondary explanatory comparison | About 5× more observations; tests whether the longer weekend closure matters | No | Explanatory only; not a traded strategy |
| Corporate actions: rely on yfinance split-adjusted OHLC (`auto_adjust=False`); verify Adj Close = Close and the MSTR 10:1 split | yfinance OHLC already split-adjusted; none of the three pays cash dividends (0 dividend rows, max \|AdjClose/Close − 1\| = 0) | No | Gap and drift comparable across the split |
| Truncated Binance candles (close time > 1 s before boundary; 5 found, all exchange outages) flagged incomplete and never used as endpoints | Their close is not the price at the boundary | No | 1 weeknight event (2023-03-24) rejected |
| Statistics: OLS with HC3 standard errors, Welch t-test, paired-event bootstrap (seed 42, 2,000 resamples) | Simple and defensible at n ≈ 90–130 | No | — |

## Stage 2: In-sample runs (2021–2023)

| Variant | Status |
|---|---|
| Primary: long basket Monday open → close if BTC (Fri 16:00 → Mon 09:00) > 0, 10 bps per side | Primary (registered before results) |
| Benchmark: long basket every eligible Monday, 10 bps per side | Benchmark (registered before results) |
| Cost scenarios 0 / 5 / 10 / 25 / 50 bps per side, primary and benchmark | Pre-declared sensitivity |
| Thresholds +1% and +2% (in-sample: +3.2% and +14.2% net vs −18.8% primary) | Pre-declared sensitivity; **not adopted** |
| Bootstrap: drift difference and strategy − benchmark excess return | Uncertainty analysis |
| Per-year breakdown 2021 / 2022 / 2023 | Robustness |
| Monday 09:30–16:00 BTC return regression | Hindsight diagnostic only, never a signal |
| Concentration: without best / worst 5 trading days | Robustness |

The first in-sample results were weak for the primary rule (net −18.8% vs benchmark −19.7%). Per protocol this did not authorise any redesign; the rule stayed as registered.

## Stage 3: Design freeze (commit fec2b54)

Frozen specification: universe MSTR / MARA / RIOT, equal weights; signal = BTCUSDT completed-candle return from prior 16:00 NY to 09:00 NY; primary rule long if > 0; entry at Monday regular Open, exit at same-day Close; 10 bps per side base cost; cost scenarios 0 / 5 / 10 / 25 / 50; sensitivities +1% / +2% reported but not adopted; in-sample 2021–2023, out-of-sample 2024-01-01 to 2025-12-31; seed 42, 2,000 bootstrap resamples.

The +1% / +2% thresholds performed better in-sample; the primary rule was deliberately kept at > 0 as registered.

## Stage 4: Out-of-sample evaluation (2024–2025)

| Variant | Status |
|---|---|
| Single run of the frozen design: main table, costs, thresholds, bootstrap, per-year, diagnostic, concentration | Final evaluation, run once after the freeze |

Between the freeze and this run, the only changes were setting `OUT_OF_SAMPLE_UNLOCKED = True` and adding the section 8 evaluation cells. No data, parameters, signal or backtest code was changed.

**Correction to the original freeze statement.** An earlier version of this log said that out-of-sample outcomes "had not been computed or viewed" at the freeze. That overstated the lock. The outcome table (gap and drift for every event, 2021–2025) is computed in the cleaning stage and was saved in `data/processed/outcomes.csv` from the first commit. Accurate statement: 2024–2025 outcomes were computed and stored, but not displayed, analysed or used in any metric, regression or strategy result before the freeze. The primary rule was registered before any results were seen.

## Stage 5: Post-freeze checks (after out-of-sample results were seen)

These are labelled post-freeze. They do not change the primary rule and are not untouched out-of-sample validation.

| Check | Result | Status |
|---|---|---|
| Look-ahead check reimplemented as bounded binary search (`TruncatedCandles`, `hi` argument, no slicing); now covers all 1,195 eligible events instead of 150 | Returns and signals identical; all result files unchanged; check time 8.28 s → 0.0013 s on the same 150 events | Verification / efficiency change; signal path unchanged |
| Random-selection benchmark: the signal's trade count drawn at random from eligible Mondays, 10,000 draws, seed 42 | In-sample 60/128 → 37th percentile; out-of-sample 53/91 → 76th percentile | Interpretation only |
| Independence check: lag-1 autocorrelation of basket drift vs ±2/√n band | All four series inside (0.005, −0.006, −0.036, −0.078); does not rule out longer-lag dependence | Interpretation only; formal tests left as next steps |
| Network download time measured once | About 1 s per monthly file, about 60 s for 61 files; measurement cell then switched off | Efficiency measurement only |
| Naive-scan timing re-measured with a sample spread across the whole period (first version used only the earliest dates) | About 15 s estimated for all lookups, instead of 1.9 s | Measurement correction |
| Equity cleaning and backtest made to stop on non-positive or inconsistent prices | No such rows exist; results unchanged | Safeguard only |