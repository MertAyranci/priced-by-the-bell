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

Note (2026-10-07): first in-sample results were weak for the primary rule (net −18.8% vs benchmark −19.7%).
Per protocol this does **not** authorise any redesign; the rule stays as registered.

## Design freeze

_Pending._ Will be recorded here (with commit hash) before `OUT_OF_SAMPLE_UNLOCKED = True`.
