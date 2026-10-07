"""Builds notebook.ipynb from ordered cells. Run with the project venv."""
import sys
import nbformat as nbf

OUT = sys.argv[1]
cells = []
md = lambda s: cells.append(nbf.v4.new_markdown_cell(s.strip("\n")))
code = lambda s: cells.append(nbf.v4.new_code_cell(s.strip("\n")))

md(r"""
# Priced by the Bell? Bitcoin overnight returns and Monday drift in crypto-exposed equities

**Question.** Does Bitcoin's return between Friday's 16:00 New York close and Monday 09:00 New York time
predict the Monday **open-to-close** return of an equal-weight basket of MSTR, MARA and RIOT?

**Two outcomes are kept separate throughout:**

| Outcome | Definition | Tradable by a Monday-open buyer? |
|---|---|---|
| Opening gap | Friday close → Monday open | No — it happens before entry |
| Monday drift | Monday open → Monday close | Yes — this is what the strategy earns |

**Primary rule (registered before looking at returns):** if the Bitcoin return from Friday 16:00 to Monday 09:00 (NY)
is > 0, buy the basket at Monday's open and sell at Monday's close; otherwise hold cash.
Benchmark: buy the same basket every eligible Monday.

**Secondary analysis:** the same Bitcoin → gap / drift relationship on ordinary weeknights (16:00 → 09:00 next day),
to see whether the longer weekend closure leaves more unabsorbed information than a single night.

The written report is a separate document; this notebook is the reproducible pipeline.
""")

md(r"""
## 0. Setup and registered configuration

Everything that defines the experiment lives in `CONFIG` and is saved to `data/metadata/config.json`.
`OUT_OF_SAMPLE_UNLOCKED` stays `False` until the design is frozen (see the decision log); while it is
`False`, no 2024–2025 return, signal–outcome relationship or strategy result is computed or displayed.
""")

code(r"""
import datetime as dt
import hashlib
import io
import json
import platform
import time
import zipfile
from bisect import bisect_right
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pandas_market_calendars as mcal
import requests
import scipy
import statsmodels
import statsmodels.api as sm
import yfinance as yf
from scipy import stats

pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 30)

NY = "America/New_York"
DATA = Path("data")
RAW_BTC = DATA / "raw" / "btc"
RAW_EQ = DATA / "raw" / "equity"
PROCESSED = DATA / "processed"
META = DATA / "metadata"
RESULTS = DATA / "results"
FIGURES = DATA / "figures"
for p in (RAW_BTC, RAW_EQ, PROCESSED, META, RESULTS, FIGURES):
    p.mkdir(parents=True, exist_ok=True)

# Set True only to deliberately re-download sources. Default runs entirely from the saved snapshot.
REFRESH = False

# Flipped to True only after the design-freeze entry in data/metadata/decision_log.md.
OUT_OF_SAMPLE_UNLOCKED = False
""")

code(r"""
CONFIG = {
    "universe": ["MSTR", "MARA", "RIOT"],
    "weights": {"MSTR": 1 / 3, "MARA": 1 / 3, "RIOT": 1 / 3},
    "btc_source": {
        "exchange": "Binance spot public archive (data.binance.vision)",
        "pair": "BTCUSDT",
        "interval": "30m",
        "base_url": "https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/30m/",
        "first_month": "2020-12",
        "last_month": "2025-12",
    },
    "equity_source": {
        "provider": "yfinance Ticker.history",
        "interval": "1d",
        "auto_adjust": False,
        "actions": True,
        "start": "2020-12-01",
        "end_exclusive": "2026-01-01",
    },
    "calendar": "NYSE via pandas_market_calendars (MSTR/MARA/RIOT are Nasdaq-listed; regular sessions coincide)",
    "sample": ["2021-01-01", "2025-12-31"],
    "periods": {
        "in_sample": ["2021-01-01", "2023-12-31"],
        "out_of_sample": ["2024-01-01", "2025-12-31"],
    },
    "signal_start": "16:00 NY on the prior full session (Friday for weekends)",
    "signal_cutoff_ny": "09:00",
    "entry_exit": "regular-session Open -> same-day regular-session Close",
    "threshold": 0.0,
    "sensitivity_thresholds": [0.01, 0.02],
    "base_cost_bps_per_side": 10,
    "cost_scenarios_bps": [0, 5, 10, 25, 50],
    "candle_close_tolerance_seconds": 1,
    "seed": 42,
    "bootstrap_reps": 2000,
    "cash_return": 0.0,
}
(META / "config.json").write_text(json.dumps(CONFIG, indent=2))

VERSIONS = {
    "python": platform.python_version(),
    "pandas": pd.__version__,
    "numpy": np.__version__,
    "yfinance": yf.__version__,
    "pandas_market_calendars": mcal.__version__,
    "statsmodels": statsmodels.__version__,
    "scipy": scipy.__version__,
    "matplotlib": matplotlib.__version__,
}
VERSIONS
""")

# --------------------------------------------------------------------------------------------
md(r"""
# 1. Data Acquisition

Three sources, each saved locally so the notebook reruns offline:

1. **Bitcoin** — Binance spot BTC/USDT 30-minute candles, one zip per month (Dec 2020 – Dec 2025).
   Each file is verified against Binance's published SHA-256 `.CHECKSUM` before it is accepted.
   BTC/USDT is a proxy for BTC/USD (stablecoin and single-venue risk acknowledged in the report).
2. **Equities** — yfinance daily OHLC for MSTR, MARA, RIOT with `auto_adjust=False, actions=True`,
   so splits/dividends are visible rather than silently applied.
3. **Session calendar** — NYSE regular sessions with exact open/close times (detects holidays and early closes).
""")

code(r"""
def sha256_bytes(content):
    return hashlib.sha256(content).hexdigest()


def fetch(url, retries=3, timeout=30):
    # Bounded retries with linear back-off; re-raises after the last attempt.
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response.content
        except requests.RequestException:
            if attempt == retries:
                raise
            time.sleep(2 * attempt)


def load_previous_manifest():
    path = META / "manifest.json"
    return json.loads(path.read_text()) if path.exists() else {}


def download_or_load_btc_archive(config, refresh=False):
    src = config["btc_source"]
    months = pd.period_range(src["first_month"], src["last_month"], freq="M")
    previous = {r["file"]: r for r in load_previous_manifest().get("btc_files", [])}
    records = []
    for month in months:
        name = f"{src['pair']}-{src['interval']}-{month}.zip"
        path, checksum_path = RAW_BTC / name, RAW_BTC / f"{name}.CHECKSUM"
        downloaded_at = previous.get(name, {}).get("downloaded_at_utc")
        if refresh or not path.exists():
            content = fetch(src["base_url"] + name)
            checksum_text = fetch(src["base_url"] + name + ".CHECKSUM").decode()
            if path.exists() and sha256_bytes(path.read_bytes()) != sha256_bytes(content):
                raise RuntimeError(f"{name}: refreshed file differs from saved snapshot; not overwriting")
            path.write_bytes(content)
            checksum_path.write_text(checksum_text)
            downloaded_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        expected = checksum_path.read_text().split()[0]
        actual = sha256_bytes(path.read_bytes())
        if actual != expected:
            raise ValueError(f"{name}: SHA-256 mismatch with Binance CHECKSUM")
        records.append({"file": name, "month": str(month), "url": src["base_url"] + name,
                        "sha256": actual, "checksum_verified": True,
                        "bytes": path.stat().st_size, "downloaded_at_utc": downloaded_at})
    return pd.DataFrame(records)


t0 = time.perf_counter()
btc_files = download_or_load_btc_archive(CONFIG, refresh=REFRESH)
timing = {"btc_acquire_or_verify_s": time.perf_counter() - t0}
print(f"{len(btc_files)} monthly files, {btc_files.bytes.sum() / 1e6:.1f} MB, all checksums verified:",
      btc_files.checksum_verified.all())
btc_files.head(3)
""")

code(r"""
def download_or_load_equities(config, refresh=False):
    src = config["equity_source"]
    previous = {r["ticker"]: r for r in load_previous_manifest().get("equity_files", [])}
    frames, records = {}, []
    for ticker in config["universe"]:
        path = RAW_EQ / f"{ticker}_daily.csv"
        downloaded_at = previous.get(ticker, {}).get("downloaded_at_utc")
        if refresh or not path.exists():
            hist = yf.Ticker(ticker).history(start=src["start"], end=src["end_exclusive"],
                                             interval=src["interval"], auto_adjust=src["auto_adjust"],
                                             actions=src["actions"])
            if hist.empty:
                raise RuntimeError(f"{ticker}: yfinance returned no rows")
            # The index is midnight New York time. Keep the *local* calendar date; converting the
            # instant to UTC first could shift a session onto the wrong date.
            hist.index = hist.index.tz_localize(None).normalize()
            hist.index.name = "date"
            hist.to_csv(path)
            downloaded_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        frames[ticker] = pd.read_csv(path, parse_dates=["date"]).set_index("date")
        records.append({"ticker": ticker, "file": str(path), "sha256": sha256_bytes(path.read_bytes()),
                        "rows": len(frames[ticker]), "request": src, "downloaded_at_utc": downloaded_at})
    return frames, pd.DataFrame(records)


t0 = time.perf_counter()
equity_raw, equity_files = download_or_load_equities(CONFIG, refresh=REFRESH)
timing["equity_acquire_or_load_s"] = time.perf_counter() - t0
equity_files[["ticker", "rows", "sha256", "downloaded_at_utc"]]
""")

code(r"""
def build_session_calendar(start, end):
    sched = mcal.get_calendar("NYSE").schedule(start_date=start, end_date=end)
    cal = pd.DataFrame({
        "session": pd.DatetimeIndex(sched.index).normalize(),
        "open_utc": sched["market_open"].to_numpy(),
        "close_utc": sched["market_close"].to_numpy(),
    })
    cal["open_utc"] = pd.to_datetime(cal["open_utc"], utc=True)
    cal["close_utc"] = pd.to_datetime(cal["close_utc"], utc=True)
    cal["open_ny"] = cal["open_utc"].dt.tz_convert(NY)
    cal["close_ny"] = cal["close_utc"].dt.tz_convert(NY)
    cal["full_session"] = (cal["open_ny"].dt.strftime("%H:%M") == "09:30") & (
        cal["close_ny"].dt.strftime("%H:%M") == "16:00")
    return cal


calendar = build_session_calendar(CONFIG["equity_source"]["start"], "2025-12-31")
calendar.to_csv(META / "calendar_snapshot.csv", index=False)
print(len(calendar), "NYSE sessions;", (~calendar.full_session).sum(), "short sessions:")
calendar.loc[~calendar.full_session, ["session", "open_ny", "close_ny"]]
""")

code(r"""
manifest = {
    "created_or_verified_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    "library_versions": VERSIONS,
    "btc_files": btc_files.to_dict("records"),
    "equity_files": equity_files.to_dict("records"),
    "calendar": {"provider": "pandas_market_calendars", "exchange": "NYSE",
                 "file": "data/metadata/calendar_snapshot.csv", "sessions": len(calendar)},
}
(META / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str))
print("manifest written:", META / "manifest.json")
""")

# --------------------------------------------------------------------------------------------
md(r"""
# 2. Cleaning

### 2.1 Bitcoin candles

* Binance switched spot archive timestamps from **milliseconds to microseconds from January 2025**.
  The unit is chosen per file from its month, and every parsed timestamp must fall inside the month
  named in the filename — otherwise the run fails.
* A candle labelled 08:30 is only *known* once it finishes at 09:00. Each candle therefore gets a
  `candle_end = open_time + 30 min`, and prices are always looked up by the time the candle **ended**.
* Binance's `close_time` is normally `candle_end − 1 ms/µs`. A candle whose `close_time` is more than 1 s
  before `candle_end` was **truncated by an exchange outage/maintenance** — its close is not the price at
  `candle_end`. Such candles are kept, flagged `complete = False`, logged, and never used as an endpoint.
* Duplicates: identical rows are dropped and logged; conflicting duplicates stop the run.
""")

code(r"""
KLINE_COLS = ["open_time", "open", "high", "low", "close", "volume", "close_time",
              "quote_volume", "n_trades", "taker_buy_base", "taker_buy_quote", "ignore"]
UNIT_SWITCH = pd.Period("2025-01", freq="M")


def parse_btc_file(path, month):
    with zipfile.ZipFile(path) as zf:
        raw = pd.read_csv(zf.open(zf.namelist()[0]), header=None, names=KLINE_COLS)
    if not pd.api.types.is_numeric_dtype(raw["open_time"]):  # tolerate a header row if one appears
        raw = raw[pd.to_numeric(raw["open_time"], errors="coerce").notna()].astype({"open_time": "int64"})
    unit = "us" if month >= UNIT_SWITCH else "ms"
    df = raw.copy()
    df["open_time"] = pd.to_datetime(df["open_time"].astype("int64"), unit=unit, utc=True)
    df["close_time"] = pd.to_datetime(df["close_time"].astype("int64"), unit=unit, utc=True)
    in_month = df["open_time"].dt.tz_convert(None).dt.to_period("M") == month
    if not in_month.all():
        raise ValueError(f"{path.name}: {(~in_month).sum()} timestamps outside {month} with unit={unit}")
    df["source_file"] = path.name
    return df


def clean_btc_candles(files, interval=pd.Timedelta("30min"), tolerance_s=1):
    issues = []
    frames = [parse_btc_file(RAW_BTC / f, pd.Period(m, freq="M")) for f, m in zip(files.file, files.month)]
    df = pd.concat(frames, ignore_index=True).sort_values("open_time", kind="mergesort")
    price_cols = ["open", "high", "low", "close"]

    dup_mask = df.duplicated("open_time", keep=False)
    if dup_mask.any():
        conflicting = df[dup_mask].groupby("open_time")[price_cols].nunique().gt(1).any(axis=1)
        if conflicting.any():
            raise ValueError(f"conflicting duplicate candles at {list(conflicting[conflicting].index)}")
        n_drop = int(df.duplicated("open_time").sum())
        issues.append({"dataset": "btc", "issue": "identical duplicate candles dropped", "count": n_drop})
        df = df.drop_duplicates("open_time")

    bad_ohlc = (df[price_cols] <= 0).any(axis=1) | (df["high"] < df[["open", "close"]].max(axis=1)) | (
        df["low"] > df[["open", "close"]].min(axis=1))
    if bad_ohlc.any():
        raise ValueError(f"{bad_ohlc.sum()} candles violate OHLC consistency")

    df["candle_end"] = df["open_time"] + interval
    close_gap = (df["candle_end"] - df["close_time"]).dt.total_seconds()
    if (close_gap < 0).any():
        raise ValueError("close_time after candle_end")
    df["complete"] = close_gap <= tolerance_s
    for _, r in df[~df["complete"]].iterrows():
        issues.append({"dataset": "btc", "issue": f"truncated candle {r.open_time:%Y-%m-%d %H:%M} UTC "
                       f"(close_time {r.close_time:%H:%M:%S}, volume {r.volume:g}) excluded from endpoints", "count": 1})

    grid = pd.date_range(df["open_time"].min(), df["open_time"].max(), freq=interval)
    missing = grid.difference(pd.DatetimeIndex(df["open_time"]))
    issues.append({"dataset": "btc", "issue": "missing 30m candles in archive (not filled)",
                   "count": len(missing)})
    return df.reset_index(drop=True), missing, issues


t0 = time.perf_counter()
btc, btc_missing, quality_log = clean_btc_candles(btc_files, tolerance_s=CONFIG["candle_close_tolerance_seconds"])
timing["btc_parse_clean_s"] = time.perf_counter() - t0
print(f"{len(btc):,} candles from {btc.open_time.min()} to {btc.open_time.max()}")
print(f"{len(btc_missing)} missing candle slots; grouped into outages:")
outages = pd.Series(btc_missing).groupby((pd.Series(btc_missing).diff() != pd.Timedelta("30min")).cumsum()).agg(["min", "max", "count"])
outages
""")

md(r"""
### 2.2 Equities and corporate actions

yfinance with `auto_adjust=False` returns Open/High/Low/Close that are **already split-adjusted** (not raw
exchange prints) plus a separate `Adj Close` that additionally adjusts for cash dividends.
We verify rather than assume: (i) each ticker has exactly one row per NYSE session, (ii) no cash dividends
(so `Adj Close == Close`), (iii) the MSTR 10-for-1 split (effective 8 Aug 2024) leaves no artificial jump,
(iv) OHLC values are internally consistent. Nothing is forward-filled.
""")

code(r"""
def clean_equity_data(frames, calendar, issues):
    sessions = pd.DatetimeIndex(calendar["session"])
    clean = {}
    for ticker, df in frames.items():
        df = df.sort_index()
        if df.index.duplicated().any():
            raise ValueError(f"{ticker}: duplicate dates")
        missing = sessions.difference(df.index)
        extra = df.index.difference(sessions)
        issues.append({"dataset": ticker, "issue": "sessions missing vs calendar", "count": len(missing)})
        issues.append({"dataset": ticker, "issue": "rows on non-session dates", "count": len(extra)})
        if len(extra):
            raise ValueError(f"{ticker}: rows on non-session dates {list(extra)[:5]}")
        bad = (df[["Open", "High", "Low", "Close"]] <= 0).any(axis=1) | (
            df["High"] < df[["Open", "Close"]].max(axis=1)) | (df["Low"] > df[["Open", "Close"]].min(axis=1))
        issues.append({"dataset": ticker, "issue": "OHLC inconsistent rows", "count": int(bad.sum())})
        n_div = int((df["Dividends"] != 0).sum())
        issues.append({"dataset": ticker, "issue": "cash dividend rows", "count": n_div})
        max_adj_gap = float((df["Adj Close"] / df["Close"] - 1).abs().max())
        issues.append({"dataset": ticker, "issue": "max |AdjClose/Close - 1|", "count": max_adj_gap})
        for d, ratio in df.loc[df["Stock Splits"] != 0, "Stock Splits"].items():
            issues.append({"dataset": ticker, "issue": f"stock split {ratio:g}:1 on {d.date()}", "count": 1})
        clean[ticker] = df[["Open", "High", "Low", "Close", "Adj Close", "Volume", "Dividends", "Stock Splits"]]
    return clean


equity = clean_equity_data(equity_raw, calendar, quality_log)
mstr = equity["MSTR"]
split_window = mstr.loc["2024-08-06":"2024-08-12", ["Open", "Close", "Stock Splits"]]
split_window["close_to_open_gap"] = split_window["Open"] / mstr["Close"].shift(1).loc[split_window.index] - 1
split_window
""")

code(r"""
quality = pd.DataFrame(quality_log)
quality.to_csv(META / "data_quality_log.csv", index=False)
quality
""")

md(r"""
### 2.3 Event table: pairing sessions and aligning completed Bitcoin candles

One row per **candidate** entry day in 2021–2025 (every calendar Monday for the weekend study, every
Tuesday–Friday for the weeknight study), including ineligible rows and the reason.

An event is eligible only if the entry day **and** the prior calendar trading day (Friday for Monday;
the previous day otherwise) are both **full** NYSE sessions, and both Bitcoin endpoint candles exist.
Tuesdays after a Monday holiday are *not* relabelled as Mondays.

**Endpoint lookup.** Candles are stored in a dictionary keyed by `candle_end`. The price at a target
time T is the close of the candle that ended **exactly** at T. If that candle is missing the event is
rejected — an older (stale) candle is never used and nothing is interpolated.
""")

code(r"""
def build_close_lookup(candles):
    # O(B) build; O(1) average lookup per endpoint. Truncated (incomplete) candles are never endpoints.
    if "complete" in candles:
        candles = candles[candles["complete"]]
    return dict(zip(candles["candle_end"], candles["close"]))


def completed_price(lookup, target_utc):
    return lookup.get(target_utc, np.nan)


def ny_to_utc(date, hhmm):
    return (pd.Timestamp(date) + pd.Timedelta(hours=int(hhmm[:2]), minutes=int(hhmm[3:]))).tz_localize(NY).tz_convert("UTC")


def build_event_skeleton(calendar, start, end, cutoff_ny="09:00"):
    sess = calendar.set_index("session")
    days = pd.date_range(start, end, freq="D")
    rows = []
    for d in days[days.dayofweek < 5]:
        prior = d - pd.Timedelta(days=3 if d.dayofweek == 0 else 1)
        reason = None
        if d not in sess.index:
            reason = "entry day market closed"
        elif prior not in sess.index:
            reason = "prior day market closed"
        elif not sess.at[d, "full_session"]:
            reason = "entry day short session"
        elif not sess.at[prior, "full_session"]:
            reason = "prior day short session"
        rows.append({
            "event_id": d,
            "event_type": "weekend" if d.dayofweek == 0 else "weeknight",
            "prior_date": prior,
            "entry_date": d,
            "btc_start_target_utc": ny_to_utc(prior, "16:00"),
            "btc_cutoff_target_utc": ny_to_utc(d, cutoff_ny),
            "calendar_eligible": reason is None,
            "exclusion_reason": reason,
        })
    return pd.DataFrame(rows)


def build_signal_inputs(skeleton, lookup):
    # Only Bitcoin prices that finished at or before the cutoff are touched here.
    ev = skeleton.copy()
    ev["btc_start_price"] = [completed_price(lookup, t) for t in ev["btc_start_target_utc"]]
    ev["btc_cutoff_price"] = [completed_price(lookup, t) for t in ev["btc_cutoff_target_utc"]]
    btc_missing = ev["calendar_eligible"] & (ev["btc_start_price"].isna() | ev["btc_cutoff_price"].isna())
    ev.loc[btc_missing, "exclusion_reason"] = "btc endpoint candle missing"
    ev["eligible"] = ev["calendar_eligible"] & ~btc_missing
    ev["btc_return"] = np.where(ev["eligible"], ev["btc_cutoff_price"] / ev["btc_start_price"] - 1, np.nan)
    return ev


def assign_period(dates, periods):
    out = pd.Series("outside", index=dates.index)
    for name, (a, b) in periods.items():
        out[(dates >= a) & (dates <= b)] = name
    return out


t0 = time.perf_counter()
lookup = build_close_lookup(btc)
skeleton = build_event_skeleton(calendar, *CONFIG["sample"], cutoff_ny=CONFIG["signal_cutoff_ny"])
signal_inputs = build_signal_inputs(skeleton, lookup)
signal_inputs["period"] = assign_period(signal_inputs["entry_date"], CONFIG["periods"])
timing["event_alignment_s"] = time.perf_counter() - t0

reconciliation = (signal_inputs.assign(exclusion_reason=signal_inputs.exclusion_reason.fillna("eligible"))
                  .pivot_table(index=["event_type", "exclusion_reason"], columns="period",
                               values="event_id", aggfunc="count", fill_value=0))
reconciliation["total"] = reconciliation.sum(axis=1)
reconciliation
""")

md(r"""
**Manual inspection of representative weekends.** Winter (EST, UTC−5), summer (EDT, UTC−4), the US
daylight-saving switch (14 Mar 2021) and holiday cases. The Friday 16:00 target must map to 21:00 UTC in
winter and 20:00 UTC in summer; Monday 09:00 to 14:00 / 13:00 UTC. Only the candidate rows and BTC
fields are shown (no equity outcomes).
""")

code(r"""
inspect_dates = ["2021-01-11", "2021-03-15", "2021-07-12", "2021-11-08", "2021-01-18",
                 "2021-11-29", "2022-04-18", "2022-06-20", "2023-07-03"]
show = signal_inputs.set_index("event_id").loc[pd.to_datetime(inspect_dates),
    ["prior_date", "btc_start_target_utc", "btc_cutoff_target_utc", "btc_start_price",
     "btc_cutoff_price", "btc_return", "eligible", "exclusion_reason"]]
show
""")

code(r"""
# Cross-check one weekend directly against the raw candle rows (the candle that *ends* at each target).
ev = signal_inputs.set_index("event_id").loc[pd.Timestamp("2021-03-15")]
raw_rows = btc[btc["candle_end"].isin([ev.btc_start_target_utc, ev.btc_cutoff_target_utc])]
raw_rows.assign(open_ny=raw_rows.open_time.dt.tz_convert(NY), end_ny=raw_rows.candle_end.dt.tz_convert(NY))[
    ["open_time", "candle_end", "open_ny", "end_ny", "close_time", "close", "source_file"]]
""")

md(r"""
### 2.4 Outcomes (kept in a separate table from the predictor)

Per ticker: prior close, entry-day open and close. `gap = Open/prior Close − 1` (diagnostic, not tradable),
`drift = Close/Open − 1` (what the trade earns). Basket values are equal-weight means.
The hindsight-only Bitcoin return from 09:30 to 16:00 on the entry day is stored here too — it is an
explanatory diagnostic and is never passed to the signal.
""")

code(r"""
def build_outcome_table(events, equity, lookup, universe):
    out = events[["event_id", "event_type", "period", "eligible", "prior_date", "entry_date"]].copy()
    for t in universe:
        px = equity[t]
        out[f"{t}_prior_close"] = out["prior_date"].map(px["Close"])
        out[f"{t}_open"] = out["entry_date"].map(px["Open"])
        out[f"{t}_close"] = out["entry_date"].map(px["Close"])
        out[f"{t}_gap"] = out[f"{t}_open"] / out[f"{t}_prior_close"] - 1
        out[f"{t}_drift"] = out[f"{t}_close"] / out[f"{t}_open"] - 1
    out["basket_gap"] = out[[f"{t}_gap" for t in universe]].mean(axis=1, skipna=False)
    out["basket_drift"] = out[[f"{t}_drift" for t in universe]].mean(axis=1, skipna=False)
    s930 = [completed_price(lookup, ny_to_utc(d, "09:30")) for d in out["entry_date"]]
    s1600 = [completed_price(lookup, ny_to_utc(d, "16:00")) for d in out["entry_date"]]
    out["btc_session_return_hindsight"] = np.array(s1600) / np.array(s930) - 1
    unresolved = out["eligible"] & out["basket_drift"].isna()
    out["unresolved_outcome"] = unresolved
    return out


outcomes = build_outcome_table(signal_inputs, equity, lookup, CONFIG["universe"])
print("eligible events with unresolved equity outcomes:", int(outcomes.unresolved_outcome.sum()))
assert not outcomes["unresolved_outcome"].any(), "unresolved post-entry valuation — fix before backtesting"

signal_inputs.to_csv(PROCESSED / "signal_inputs.csv", index=False)
outcomes.to_csv(PROCESSED / "outcomes.csv", index=False)
""")

# --------------------------------------------------------------------------------------------
md(r"""
# 3. Strategy

The signal function receives **only** predictor columns (event id, type, eligibility and the Bitcoin
return measured up to the 09:00 cutoff). It cannot see Monday prices. Registered rule: long the basket
on an eligible Monday when `btc_return > 0`. Sensitivities (+1%, +2%) are pre-declared and reported as
such, never substituted for the primary rule.
""")

code(r"""
PREDICTOR_COLS = ["event_id", "event_type", "period", "eligible", "btc_return"]


def make_signal(signal_inputs, threshold=0.0, name="signal"):
    extra = set(signal_inputs.columns) - set(PREDICTOR_COLS)
    if extra:
        raise ValueError(f"signal function received non-predictor columns: {extra}")
    return (signal_inputs["eligible"] & (signal_inputs["btc_return"] > threshold)).rename(name)


predictors = signal_inputs[PREDICTOR_COLS]
signals = pd.DataFrame({
    "event_id": predictors["event_id"],
    "always": predictors["eligible"],  # unconditional benchmark: every eligible event
    "signal_long": make_signal(predictors, CONFIG["threshold"]),
    "signal_1pct": make_signal(predictors, CONFIG["sensitivity_thresholds"][0]),
    "signal_2pct": make_signal(predictors, CONFIG["sensitivity_thresholds"][1]),
})
signals.to_csv(PROCESSED / "signals.csv", index=False)

weekend_sig = signals[predictors["event_type"] == "weekend"].join(predictors["period"])
weekend_sig.groupby("period")[["always", "signal_long", "signal_1pct", "signal_2pct"]].sum()
""")

# --------------------------------------------------------------------------------------------
md(r"""
# 4. Backtest

**Execution contract.** On a signal Monday, one-third of start-of-day wealth goes to each stock.
Each purchase pays an adverse proportional friction `c` at the Open, each sale pays `c` at the Close:

`net_return_i = (Close/Open)·(1 − c)/(1 + c) − 1`

No leverage, no shorts, no overnight holding; cash earns 0 and incurs no cost. Fractional shares
are allowed. The output is a **daily** return series over *every* NYSE session in the period
(zeros on cash days), compounded from wealth = 1, so Sharpe (√252, zero risk-free rate) and drawdown are
calendar-consistent. Gross (c = 0) and net results are both recorded.
""")

code(r"""
def asset_net_return(open_px, close_px, c):
    return (close_px / open_px) * (1 - c) / (1 + c) - 1


def run_portfolio(signal_col, period, cost_bps, event_type="weekend", config=CONFIG,
                  signals=signals, outcomes=outcomes, calendar=calendar):
    start, end = config["periods"][period] if isinstance(period, str) else period
    c = cost_bps / 1e4
    sessions = calendar.loc[calendar.session.between(start, end), "session"]
    merged = outcomes.merge(signals[["event_id", signal_col]], on="event_id")
    trades = merged[(merged.event_type == event_type) & merged[signal_col]
                    & merged.entry_date.between(start, end)].set_index("entry_date")
    daily = pd.Series(0.0, index=pd.DatetimeIndex(sessions, name="session"))
    ledger, wealth = [], 1.0
    for day in daily.index:
        if day not in trades.index:
            continue
        row, pnl_total = trades.loc[day], 0.0
        for t, w in config["weights"].items():
            o, cl = row[f"{t}_open"], row[f"{t}_close"]
            if not (np.isfinite(o) and np.isfinite(cl)):
                raise ValueError(f"{day.date()} {t}: missing execution price after entry decision")
            alloc = w * wealth
            shares = alloc / (o * (1 + c))
            proceeds = shares * cl * (1 - c)
            ledger.append({"date": day, "ticker": t, "wealth_before": wealth, "allocation": alloc,
                           "fill_open": o * (1 + c), "fill_close": cl * (1 - c), "shares": shares,
                           "proceeds": proceeds, "pnl": proceeds - alloc,
                           "gross_return": cl / o - 1, "net_return": proceeds / alloc - 1})
            pnl_total += proceeds - alloc
        daily[day] = pnl_total / wealth
        wealth += pnl_total
    return daily, pd.DataFrame(ledger)


def wealth_curve(daily):
    w = (1 + daily).cumprod()
    start = pd.Series([1.0], index=[w.index[0] - pd.Timedelta(days=1)])
    return pd.concat([start, w])  # includes initial wealth so an immediate loss shows in drawdown


def compute_metrics(daily, ledger):
    w = wealth_curve(daily)
    dd = w / w.cummax() - 1
    sd = daily.std(ddof=1)
    trade_days = ledger.groupby("date").apply(lambda g: g.pnl.sum() / g.wealth_before.iloc[0]) if len(ledger) else pd.Series(dtype=float)
    return {
        "sessions": len(daily),
        "trade_days": len(trade_days),
        "exposure": len(trade_days) / len(daily),
        "cumulative_return": w.iloc[-1] - 1,
        "sharpe_daily_zero_rf": np.sqrt(252) * daily.mean() / sd if sd > 0 else np.nan,
        "max_drawdown": dd.min(),
        "avg_trade_return": trade_days.mean() if len(trade_days) else np.nan,
        "median_trade_return": trade_days.median() if len(trade_days) else np.nan,
        "win_rate": (trade_days > 0).mean() if len(trade_days) else np.nan,
        "round_trip_turnover": (ledger.allocation.sum() + ledger.proceeds.sum()) / w.mean() if len(ledger) else 0.0,
    }
""")

code(r"""
def results_table(periods, strategies, cost_bps):
    rows, ledgers, dailies = [], {}, {}
    for period in periods:
        for label, col in strategies.items():
            gross_daily, _ = run_portfolio(col, period, 0)
            daily, ledger = run_portfolio(col, period, cost_bps)
            m = compute_metrics(daily, ledger)
            m_gross = compute_metrics(gross_daily, ledger)
            rows.append({"period": period, "strategy": label,
                         "gross_cumulative_return": m_gross["cumulative_return"], **m})
            ledgers[(period, label)], dailies[(period, label)] = ledger, daily
    return pd.DataFrame(rows), ledgers, dailies


STRATEGIES = {"Positive BTC signal": "signal_long", "Unconditional Monday": "always"}
fmt = {"exposure": "{:.1%}", "cumulative_return": "{:.1%}", "gross_cumulative_return": "{:.1%}",
       "sharpe_daily_zero_rf": "{:.2f}", "max_drawdown": "{:.1%}", "avg_trade_return": "{:.2%}",
       "median_trade_return": "{:.2%}", "win_rate": "{:.1%}", "round_trip_turnover": "{:.1f}"}

is_table, is_ledgers, is_dailies = results_table(["in_sample"], STRATEGIES, CONFIG["base_cost_bps_per_side"])
is_table.style.format(fmt)
""")

code(r"""
# Ledger reconciliation: wealth from compounding daily returns == wealth from summing ledger P&L.
for key, ledger in is_ledgers.items():
    daily = is_dailies[key]
    compounded = (1 + daily).prod()
    from_ledger = 1 + ledger.pnl.sum()
    assert np.isclose(compounded, from_ledger, rtol=1e-12), key
    assert (ledger.groupby("date").allocation.sum() <= ledger.groupby("date").wealth_before.first() + 1e-12).all()
print("ledgers reconcile to wealth; no day allocates more than 100% of wealth")
for key, ledger in is_ledgers.items():
    ledger.to_csv(RESULTS / f"ledger_{key[0]}_{'signal' if 'BTC' in key[1] else 'benchmark'}.csv", index=False)
is_ledgers[("in_sample", "Positive BTC signal")].head(6)
""")

# --------------------------------------------------------------------------------------------
md(r"""
## 5. Correctness checks

Small deterministic checks aimed at the errors that would actually invalidate the study
(timing, look-ahead, costs, valuation, metrics). Each is an `assert`; the notebook stops if one fails.
""")

code(r"""
checks = []

# 1. A candle that STARTS at 09:00 must not be used for a 09:00 cutoff.
day = pd.Timestamp("2021-01-11")
c0830 = ny_to_utc(day, "08:30"); c0900 = ny_to_utc(day, "09:00"); c0930 = ny_to_utc(day, "09:30")
synthetic = pd.DataFrame({"open_time": [c0830, c0900], "close": [100.0, 999.0]})
synthetic["candle_end"] = synthetic["open_time"] + pd.Timedelta("30min")
lk = build_close_lookup(synthetic)
assert completed_price(lk, c0900) == 100.0 and completed_price(lk, c0930) == 999.0
checks.append("09:00 cutoff uses the 08:30-09:00 candle, never the 09:00-09:30 candle")

# 2. Winter / summer / DST-switch weekends map to the right UTC instants.
si = signal_inputs.set_index("event_id")
for monday, fri_utc, mon_utc in [("2021-01-11", "2021-01-08 21:00", "2021-01-11 14:00"),
                                 ("2021-03-15", "2021-03-12 21:00", "2021-03-15 13:00"),
                                 ("2021-07-12", "2021-07-09 20:00", "2021-07-12 13:00")]:
    assert si.at[pd.Timestamp(monday), "btc_start_target_utc"] == pd.Timestamp(fri_utc, tz="UTC")
    assert si.at[pd.Timestamp(monday), "btc_cutoff_target_utc"] == pd.Timestamp(mon_utc, tz="UTC")
checks.append("EST/EDT and the March-2021 DST switch map to correct UTC endpoints")

# 3. Holiday Monday, Good Friday weekend, short Friday, Juneteenth and short Monday never trade.
for d in ["2021-01-18", "2022-04-18", "2021-11-29", "2022-06-20", "2023-07-03"]:
    assert not si.at[pd.Timestamp(d), "eligible"]
    assert not signals.set_index("event_id").at[pd.Timestamp(d), "signal_long"]
checks.append("holiday / short-session weekends are excluded and generate no trade")

# 4. A missing endpoint candle is rejected, not replaced by a stale one.
lk_missing = dict(lookup); target = si.at[pd.Timestamp("2021-01-11"), "btc_cutoff_target_utc"]
del lk_missing[target]
test = build_signal_inputs(skeleton[skeleton.event_id == pd.Timestamp("2021-01-11")], lk_missing)
assert not test.eligible.iloc[0] and test.exclusion_reason.iloc[0] == "btc endpoint candle missing"
checks.append("missing endpoint candle -> event rejected (no stale fallback)")

# 5. Gap is not credited: $100 Fri close, $106 Mon open, $107 Mon close earns 107/106 - 1 gross.
assert np.isclose(asset_net_return(106.0, 107.0, 0.0), 107 / 106 - 1)
checks.append("$100/$106/$107 example earns 0.94%, not 7%")

# 6. Costs: flat price with zero friction = 0; positive friction is negative; cash days cost nothing.
assert asset_net_return(50.0, 50.0, 0.0) == 0.0 and asset_net_return(50.0, 50.0, 0.001) < 0
d10, l10 = run_portfolio("signal_long", "in_sample", 10)
assert (d10[~d10.index.isin(l10.date)] == 0).all()
checks.append("zero-friction flat trade = 0; friction > 0 is negative; no-trade days incur no cost")

# 7. Look-ahead: rebuild the signal from candles truncated at each event's cutoff; it must not change.
cutoffs = signal_inputs.loc[signal_inputs.eligible, ["event_id", "btc_cutoff_target_utc", "btc_return"]]
ends = btc["candle_end"].tolist()
mismatches = 0
for _, r in cutoffs.sample(150, random_state=CONFIG["seed"]).iterrows():
    k = bisect_right(ends, r.btc_cutoff_target_utc)
    lk_trunc = build_close_lookup(btc.iloc[:k])
    rebuilt = build_signal_inputs(skeleton[skeleton.event_id == r.event_id], lk_trunc).btc_return.iloc[0]
    mismatches += not np.isclose(rebuilt, r.btc_return)
assert mismatches == 0
checks.append("signal unchanged when all data after the 09:00 cutoff is deleted (150 sampled events)")

# 8. Signal function refuses outcome columns.
try:
    make_signal(signal_inputs.merge(outcomes[["event_id", "basket_drift"]], on="event_id"))
    raise AssertionError("signal accepted outcome data")
except ValueError:
    checks.append("signal construction rejects any non-predictor (outcome) column")

# 9. Split: MSTR's 10:1 split day shows no artificial -90% gap.
assert abs(split_window.loc["2024-08-08", "close_to_open_gap"]) < 0.25
checks.append("MSTR 10:1 split (2024-08-08) produces no artificial gap in split-adjusted prices")

# 10. Metrics: an immediate loss shows in max drawdown; constant cash gives undefined Sharpe.
idx = pd.bdate_range("2021-01-04", periods=5)
m = compute_metrics(pd.Series([-0.1, 0, 0, 0, 0.0], index=idx), pd.DataFrame(columns=["date", "pnl", "wealth_before", "allocation", "proceeds"]))
assert np.isclose(m["max_drawdown"], -0.1)
m0 = compute_metrics(pd.Series(0.0, index=idx), pd.DataFrame(columns=["date", "pnl", "wealth_before", "allocation", "proceeds"]))
assert np.isnan(m0["sharpe_daily_zero_rf"])
checks.append("first-day loss appears in max drawdown; all-cash series gives Sharpe = N/A")

pd.Series(checks, name="passed check").to_frame()
""")

# --------------------------------------------------------------------------------------------
md(r"""
## 6. In-sample explanatory analysis (2021–2023)

One observation per event (the equal-weight basket), so correlated stocks on the same day are not
counted as independent. Regressions are descriptive with heteroskedasticity-robust (HC3) standard errors.
""")

code(r"""
def analysis_frame(period, event_type):
    df = predictors.merge(outcomes[["event_id", "basket_gap", "basket_drift", "btc_session_return_hindsight"]],
                          on="event_id")
    return df[(df.period == period) & (df.event_type == event_type) & df.eligible].dropna(subset=["basket_drift"])


def ols(df, y, xcols):
    X = sm.add_constant(df[xcols])
    fit = sm.OLS(df[y], X).fit(cov_type="HC3")
    out = pd.DataFrame({"coef": fit.params, "se_hc3": fit.bse, "p": fit.pvalues})
    out["n"], out["r2"] = int(fit.nobs), fit.rsquared
    return out


def conditional_drift(df, threshold=0.0):
    pos, neg = df.loc[df.btc_return > threshold, "basket_drift"], df.loc[df.btc_return <= threshold, "basket_drift"]
    t = stats.ttest_ind(pos, neg, equal_var=False)
    return pd.Series({"n_pos": len(pos), "mean_drift_pos": pos.mean(), "median_drift_pos": pos.median(),
                      "n_nonpos": len(neg), "mean_drift_nonpos": neg.mean(), "median_drift_nonpos": neg.median(),
                      "difference": pos.mean() - neg.mean(), "welch_t": t.statistic, "welch_p": t.pvalue})


is_wk = analysis_frame("in_sample", "weekend")
is_wn = analysis_frame("in_sample", "weeknight")
reg_is = pd.concat({
    ("weekend", "gap ~ btc"): ols(is_wk, "basket_gap", ["btc_return"]),
    ("weekend", "drift ~ btc"): ols(is_wk, "basket_drift", ["btc_return"]),
    ("weeknight", "gap ~ btc"): ols(is_wn, "basket_gap", ["btc_return"]),
    ("weeknight", "drift ~ btc"): ols(is_wn, "basket_drift", ["btc_return"]),
})
reg_is
""")

code(r"""
pd.DataFrame({"weekend": conditional_drift(is_wk), "weeknight": conditional_drift(is_wn)})
""")

code(r"""
def scatter_panel(df, title, path):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharex=True)
    for ax, y, label in [(axes[0], "basket_gap", "Opening gap (Fri close → Mon open)"),
                         (axes[1], "basket_drift", "Monday drift (open → close)")]:
        ax.scatter(df.btc_return * 100, df[y] * 100, s=14, alpha=0.6)
        b = np.polyfit(df.btc_return, df[y], 1)
        xs = np.linspace(df.btc_return.min(), df.btc_return.max(), 50)
        ax.plot(xs * 100, np.polyval(b, xs) * 100, color="crimson", lw=1.5, label=f"slope {b[0]:.2f}")
        ax.axhline(0, color="grey", lw=0.6); ax.axvline(0, color="grey", lw=0.6)
        ax.set_xlabel("BTC return, prior 16:00 → 09:00 NY (%)"); ax.set_ylabel(f"{label} (%)")
        ax.legend(loc="upper left")
    fig.suptitle(f"{title} (n = {len(df)})")
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.show()


scatter_panel(is_wk, "In-sample 2021–2023, weekends: equal-weight basket", FIGURES / "is_weekend_scatter.png")
""")

code(r"""
def wealth_drawdown_plot(dailies, title, path):
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 6), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
    for label, daily in dailies.items():
        w = wealth_curve(daily)
        a1.plot(w.index, w.values, label=label)
        a2.plot(w.index, (w / w.cummax() - 1).values * 100, label=label)
    a1.set_ylabel("Wealth (start = 1)"); a1.axhline(1, color="grey", lw=0.6); a1.legend()
    a2.set_ylabel("Drawdown (%)")
    fig.suptitle(title); fig.tight_layout(); fig.savefig(path, dpi=150); plt.show()


wealth_drawdown_plot({k[1]: v for k, v in is_dailies.items()},
                     f"In-sample net wealth and drawdown ({CONFIG['base_cost_bps_per_side']} bps per side)",
                     FIGURES / "is_wealth_drawdown.png")
""")

# --------------------------------------------------------------------------------------------
md(r"""
## 7. Efficiency touchpoint: endpoint lookup

The pipeline must find 2 endpoint prices for each of W events among B ≈ 88k candles. Three ways:

| Method | Complexity |
|---|---|
| Naive scan of every candle per endpoint | O(W·B) |
| Binary search on sorted `candle_end` (`bisect`) | O(B log B) sort once + O(W log B) |
| Hash map keyed by `candle_end` (used in the pipeline) | O(B) build + O(W) lookups |

Measured below together with the other pipeline stages (acquisition vs local computation separated).
""")

code(r"""
targets = list(signal_inputs["btc_start_target_utc"]) + list(signal_inputs["btc_cutoff_target_utc"])
complete = btc[btc["complete"]]
ends_list = list(complete["candle_end"]); closes_list = list(complete["close"])


def lookup_naive(t):
    for e, c in zip(ends_list, closes_list):
        if e == t:
            return c
    return np.nan


def lookup_bisect(t):
    i = bisect_right(ends_list, t) - 1
    return closes_list[i] if i >= 0 and ends_list[i] == t else np.nan  # exact-match guard rejects stale rows


def time_it(fn, reps=1):
    t0 = time.perf_counter()
    for _ in range(reps):
        res = fn()
    return (time.perf_counter() - t0) / reps, res

naive_sample = targets[:200]  # naive version is too slow to run on all targets; scale linearly
t_naive, r_naive = time_it(lambda: [lookup_naive(t) for t in naive_sample])
t_bisect, r_bisect = time_it(lambda: [lookup_bisect(t) for t in targets], reps=3)
t_build, lk = time_it(lambda: build_close_lookup(btc), reps=3)
t_hash, r_hash = time_it(lambda: [completed_price(lk, t) for t in targets], reps=3)
assert np.allclose(r_bisect, r_hash, equal_nan=True) and np.allclose(r_naive, r_hash[:200], equal_nan=True)

efficiency = pd.DataFrame([
    {"method": "naive scan", "complexity": "O(W·B)", "seconds_all_targets": t_naive * len(targets) / len(naive_sample), "note": "extrapolated from 200 targets"},
    {"method": "binary search", "complexity": "O(W log B)", "seconds_all_targets": t_bisect, "note": "candles already sorted"},
    {"method": "hash map (pipeline)", "complexity": "O(B) + O(W)", "seconds_all_targets": t_build + t_hash, "note": f"build {t_build:.3f}s + lookups {t_hash:.4f}s"},
])
print(f"B = {len(btc):,} candles, W·2 = {len(targets):,} endpoint lookups")
efficiency
""")

code(r"""
pd.Series(timing, name="seconds").to_frame().style.format("{:.3f}")
""")

# --------------------------------------------------------------------------------------------
md(r"""
## 8. Design freeze and out-of-sample evaluation (2024–2025)

Run only after the freeze entry is recorded in `data/metadata/decision_log.md`.
""")

code(r"""
if not OUT_OF_SAMPLE_UNLOCKED:
    print("Out-of-sample section locked: design not yet frozen.")
""")

nb = nbf.v4.new_notebook()
nb["cells"] = cells
nb["metadata"]["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nbf.write(nb, OUT)
print("wrote", OUT, len(cells), "cells")
