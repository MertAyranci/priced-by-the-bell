# Decision and experiment log

Every design change and every strategy variant run is recorded here, with whether out-of-sample (OOS)
outcomes had been viewed at the time. Git commit history provides timestamps.

## Decisions

| Date | Decision / change | Reason | OOS viewed? | Effect on claims |
|---|---|---|---|---|
| 2026-10-07 | Select weekend Bitcoin → Monday open-to-close drift hypothesis (roadmap) | Clear mechanism; feasible scope | No | Hypothesis only |
| 2026-10-07 | Two periods instead of three: in-sample 2021-01-01–2023-12-31, OOS 2024-01-01–2025-12-31 | Primary rule `x > 0` has no fitted parameter, so a separate validation year has nothing to tune; in-sample used for pipeline debugging and descriptive analysis | No | OOS is the only performance claim |
| 2026-10-07 | Add weeknight events (prior 16:00 → 09:00 NY, Tue–Fri) as a secondary explanatory comparison | ~5× more observations; tests whether the longer weekend closure matters | No | Explanatory only; not a separate traded strategy |
| 2026-10-07 | Corporate actions: rely on yfinance split-adjusted OHLC (`auto_adjust=False`); verify Adj Close == Close and the MSTR 10:1 split | yfinance OHLC already split-adjusted; none of the three pays cash dividends (verified: 0 dividend rows, max \|AdjClose/Close−1\| = 0) | No | Gap/drift comparable across split |
| 2026-10-07 | Truncated Binance candles (close_time > 1 s before boundary; 5 found, all exchange outages) are flagged incomplete and never used as endpoints | Their close is not the price at the boundary; using it would be a stale price | No | 1 weeknight event (2023-03-24) rejected |
| 2026-10-07 | Statistics: HC3 OLS, Welch t-test, iid paired-event bootstrap (seed 42, 2,000 reps) instead of block bootstrap | Weak serial dependence of weekly events; simpler and defensible at n ≈ 90–130 | No | — |

## Experiment register

| Date | Variant | Periods run | Status | OOS viewed? |
|---|---|---|---|---|
| 2026-10-07 | Primary: long basket Monday open→close if BTC(Fri 16:00→Mon 09:00) > 0, 10 bps/side | In-sample | Primary (registered) | No |
| 2026-10-07 | Benchmark: long basket every eligible Monday, 10 bps/side | In-sample | Benchmark (registered) | No |
| 2026-10-07 | Threshold sensitivities +1%, +2% (signal counts only so far) | In-sample | Pre-declared sensitivity | No |




| 2026-10-07 | Cost scenarios 0/5/10/25/50 bps per side, primary + benchmark | In-sample | Pre-declared sensitivity | No |
| 2026-10-07 | Threshold +1% and +2% strategies run (in-sample: +3.2% and +14.2% net vs −18.8% primary) | In-sample | Pre-declared sensitivity; NOT adopted | No |
| 2026-10-07 | Bootstrap (paired events, seed 42, 2,000 reps): drift difference and strategy−benchmark excess | In-sample | Uncertainty analysis | No |
| 2026-10-07 | Per-year breakdown 2021/2022/2023 | In-sample | Robustness | No |
| 2026-10-07 | Monday 09:30–16:00 BTC hindsight diagnostic regression | In-sample | Explanatory only, never a signal | No |
| 2026-10-07 | Concentration: without best/worst 5 trading days | In-sample | Robustness | No |
| 2026-10-07 | Single out-of-sample run of the frozen design (main table, costs, thresholds, bootstrap, per-year, diagnostic, concentration) | Out-of-sample 2024–2025 | Final evaluation, run once after freeze commit fec2b54 | Yes (after freeze) |

Note (2026-10-07): first in-sample results were weak for the primary rule (net −18.8% vs benchmark −19.7%).
Per protocol this does **not** authorise any redesign; the rule stays as registered.

## Design freeze

**Frozen on 2026-10-07** in the commit titled "Design freeze before out-of-sample evaluation".

Frozen specification: universe MSTR/MARA/RIOT, equal weights; signal = BTCUSDT completed-candle return from prior 16:00 NY to 09:00 NY; primary rule long if > 0; entry Monday regular Open, exit same-day Close; 10 bps per side base cost; cost scenarios 0/5/10/25/50; sensitivities +1%/+2% reported but not adopted; in-sample 2021–2023, out-of-sample 2024-01-01–2025-12-31; seed 42, 2,000 bootstrap reps.

The +1%/+2% thresholds performed better in-sample; the primary rule was deliberately kept at > 0 as registered. Out-of-sample outcomes had not been computed or viewed at the time of freezing. The out-of-sample run is evaluated once; any later correction will be logged below with the original result.

## Post-freeze record

- 2026-10-07: Out-of-sample evaluation run once after the freeze commit (fec2b54). No code, parameters or data were changed between the freeze and this run. No corrections have been made since.