# Data snapshot

All inputs used by `notebook.ipynb` are saved here so the notebook runs offline (`REFRESH = False`).
Paths are relative to the project root.

## raw/
- `btc/BTCUSDT-30m-YYYY-MM.zip` (+ `.CHECKSUM`): Binance spot BTC/USDT 30-minute candles, December 2020 to December 2025,
  from `https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/30m/`. Each zip is verified against Binance's
  published SHA-256 checksum. The timestamps are in milliseconds up to December 2024 and in microseconds from January 2025.
- `equity/{MSTR,MARA,RIOT}_daily.csv`: yfinance `Ticker.history(start="2020-12-01", end="2026-01-01",
  interval="1d", auto_adjust=False, actions=True)`. Open, High, Low and Close are split-adjusted. `Adj Close` also adjusts for dividends.
  The date column is the New York session date.

## metadata/
- `config.json`: the experiment configuration (universe, periods, cutoffs, costs, seed).
- `manifest.json`: source URLs, SHA-256 hashes, download times and library versions.
- `calendar_snapshot.csv`: NYSE regular sessions with open and close times in UTC and New York time, plus a full-session flag.
- `data_quality_log.csv`: truncated or missing candles, coverage checks and corporate actions.
- `decision_log.md`: design decisions, the experiment register and the design-freeze record.
- `requirements.txt`: exact Python package versions used (Python 3.12).

## processed/
- `signal_inputs.csv`: one row per candidate entry day with its Bitcoin endpoints, eligibility and exclusion reason (predictors only).
- `outcomes.csv`: per-ticker and basket gap and drift outcomes, kept separate from the predictors.
- `signals.csv`: the registered signals and the benchmark flags.

## results/, figures/
Trade ledgers, metric tables and the figures referenced by the report.
