# Priced by the Bell?
## Bitcoin Weekend Returns and Monday Drift in Crypto-Exposed Equities

**Document:** Project introduction, research specification and implementation roadmap  
**Course:** Foundations of Financial Technology — Data Structures and Algorithms, Imperial College London  
**Created:** 7 October 2026  
**Planning horizon:** Deadline 20 October 2026 (confirmed by student)  
**Status:** Stages 0–6 implemented in-sample (7 Oct 2026); design freeze and OOS evaluation pending  
**Results status:** No data has been backtested for this roadmap. All numerical results remain pending.

> **Purpose:** Keep the student and any assisting AI agent aligned on the question, scope, sequence and submission requirements. This is a working specification, not a completed coursework report. Defaults below are methodological choices, not evidence that the strategy works. Never invent findings or replace the hypothesis merely because initial results are disappointing.

## How to use this file

Read Sections A–D before coding. Follow the implementation stages in Section E in order. Use Section F to structure the final coursework report. Update the progress board, decision log and results table as actual work is completed. If the official brief or Canvas instructions change, record the change and reconcile this roadmap before proceeding.

The student should be able to explain each stage in ordinary language. AI assistance is permitted by the brief, but understanding, interpretation and ownership remain with the student. The reflection must describe the student's actual experience.

## Contents

- [A. Project introduction and hypothesis](#a-project-introduction-and-hypothesis)
- [B. Scope and initial research specification](#b-scope-and-initial-research-specification)
- [C. Data, calendars and timestamp contract](#c-data-calendars-and-timestamp-contract)
- [D. Strategy, benchmarks and evaluation](#d-strategy-benchmarks-and-evaluation)
- [E. Implementation stages and completion checks](#e-implementation-stages-and-completion-checks)
- [F. Exact coursework report structure](#f-exact-coursework-report-structure)
- [G. Results register and possible conclusions](#g-results-register-and-possible-conclusions)
- [H. Two-week work schedule and scope control](#h-two-week-work-schedule-and-scope-control)
- [I. Instructions for an implementing AI agent](#i-instructions-for-an-implementing-ai-agent)
- [J. Progress board, decision log and final checklist](#j-progress-board-decision-log-and-final-checklist)
- [K. Sources and reference notes](#k-sources-and-reference-notes)

---

# A. Project introduction and hypothesis

## A1. The idea in ordinary language

Bitcoin trades continuously, including over the weekend. Crypto-exposed US equities have a regular trading session with an opening and closing bell. Bitcoin can move substantially between Friday's regular equity close and Monday's opening.

It is reasonable to expect those stocks to open at different prices after a Bitcoin move. The research question is whether the adjustment is already complete at Monday's opening, or whether a predictable movement remains during Monday's regular session.

**Main question:** Does Bitcoin's return between Friday's regular equity close and Monday's pre-open cutoff contain useful information about Monday open-to-close returns in a fixed basket of crypto-exposed equities?

**Trading question:** Can a rule based only on that pre-open information improve on buying the same basket every Monday, after execution costs and in an untouched test period?

The result need not be profitable to be valuable. A fair test showing that the opening absorbs the relationship is a legitimate outcome under the brief.

## A2. Distinguish information transfer from a tradable opportunity

There are two outcomes, and they must remain separate throughout the project:

| Outcome | Definition | Interpretation |
| --- | --- | --- |
| Opening gap | Friday equity close to Monday equity open | How the stock reprices before regular-session entry |
| Monday drift | Monday equity open to Monday equity close | The return potentially captured by the proposed trade |

Illustrative example, not a backtest result: a stock closes Friday at $100, opens Monday at $106 and closes Monday at $107. A Monday-open purchase earns about 0.94% before costs. It does not earn the 7% Friday-to-Monday-close move. If the stock closes Monday at $104, the Monday trade loses despite a positive opening gap.

**Never credit the strategy with the Friday-to-Monday opening gap.** Buying Friday in response to a weekend return would use future information.

## A3. Primary hypothesis

> Positive Bitcoin returns from Friday 4 p.m. to Monday 9 a.m. New York time predict more positive Monday open-to-close returns in a predefined basket of crypto-exposed equities. This would be consistent with incomplete incorporation of the intervening Bitcoin information at the regular-session opening.

This directional hypothesis is deliberately specific. The primary trading rule will use positive signals only. Negative signals remain in the explanatory analysis but do not require a short-selling strategy.

**Companion hypothesis:** Bitcoin's intervening return is positively associated with the equity opening gap.

**Null interpretation:** After the opening, the Bitcoin signal provides no useful incremental information or no economically useful return after costs. Do not equate a statistically insignificant estimate with proof of exactly zero effect.

## A4. Why the hypothesis might be true

Possible mechanisms include limited investor attention, heterogeneous expectations and gradual reassessment of how Bitcoin moves affect the companies. Those are proposed explanations, not demonstrated causes.

The difference in trading schedules explains a possible opening gap. It does not automatically explain drift after the opening. The additional claim of incomplete incorporation must be tested.

Avoid saying that all equities are completely untradeable until Monday 9:30 a.m. Premarket, after-hours and selected overnight venues exist. Describe the interval as being outside regular equity trading hours, and recognise that some information may already be incorporated before the regular opening. Changes in trading access can weaken the effect over time.

The interval also includes Friday after-hours and Monday premarket time. In the report, define this explicitly; “weekend return” is convenient shorthand, not a claim that every minute in the interval is Saturday or Sunday.

## A5. What would challenge or overturn the idea

- Bitcoin predicts the gap, but not subsequent open-to-close returns.
- The signal-conditioned strategy performs no better than the unconditional Monday basket.
- Apparent gains disappear under plausible execution-cost assumptions.
- The relationship fails in the frozen test period or reverses across years.
- A few exceptional weekends account for most of the apparent benefit.
- The sample is too small or uncertainty too wide to reach a confident conclusion.
- Equity drift mainly accompanies new Bitcoin movement during Monday, weakening the specific explanation of delayed response to weekend information.

Do not change these criteria after seeing results. Report uncertainty and competing explanations.

## A6. Working hypothesis pitch to personalise before coding

> I will investigate whether Bitcoin returns outside regular US equity trading hours are fully incorporated into crypto-exposed equities by Monday's opening bell. I hypothesise that positive Bitcoin returns from Friday's regular close to a fixed Monday pre-open cutoff predict positive Monday open-to-close returns in a predefined equity basket. The difference in trading schedules creates a clear information-transfer setting; limited attention or gradual reassessment may allow some response to continue after the opening. I will distinguish the opening gap from the return available to a trader who enters on Monday, implement a simple long-or-cash rule and compare it with an unconditional Monday strategy. The hypothesis will be challenged if the signal predicts only the gap, fails out of sample, depends on a few unusual weekends or loses its economic value after costs. Predictive results would be consistent with incomplete incorporation but would not establish its behavioural cause.

Rewrite this in the student's own terms. Do not claim a personal motivation, original discovery or literature novelty that has not been established.

---

> **Amendments 7 Oct 2026** (see `data/metadata/decision_log.md`): two periods (in-sample 2021–2023, OOS 2024–2025) replace the three-way split; weeknight events added as a secondary explanatory comparison; corporate actions handled via verified split-adjusted yfinance OHLC; simple bootstrap/HC3 statistics replace the block bootstrap.

# B. Scope and initial research specification

## B1. Decisions to register before examining returns

The following are proposed defaults for implementation. Validate coverage and historical exposure in Stage 1. Record any necessary amendment before performance analysis. Once the design is frozen, changes become explicitly exploratory or corrective.

| Item | Initial specification | Reason |
| --- | --- | --- |
| Core universe | MSTR, MARA, RIOT | Small thematic basket; manageable pipeline |
| Exposure checks | Verify each firm's crypto exposure was relevant at the proposed sample start | Current exposure must not be projected backwards without evidence |
| Bitcoin series | One continuous BTC/USDT spot series from Binance's public archive, subject to access and coverage | Historical intraday source; explicitly a dollar proxy |
| Bitcoin resolution | 30-minute candles | Supports fixed pre-open endpoints and a Monday-session diagnostic |
| Equity resolution | Daily regular-session OHLC plus adjustment and corporate-action fields | Enough for open-to-close backtesting |
| Planned sample | 1 January 2021–31 December 2025 | Complete historical years, including different market conditions |
| Acquisition buffer | Begin by 1 December 2020; request through 1 January 2026 where API end dates are exclusive | Prevent boundary truncation |
| Development | 2021–2022 | Debugging and exploratory analysis |
| Validation | 2023 | Limited checks before freezing the design |
| Final test | 2024–2025 | Two complete years reserved for evaluation |
| Signal start | Friday 16:00 America/New_York | Regular equity close on eligible full-session Fridays |
| Signal cutoff | Monday 09:00 America/New_York | Information available before planned 09:30 entry |
| Primary signal | Simple BTC return between those endpoints | Transparent, no fitted model required |
| Primary entry condition | BTC return > 0 | Prespecified sign rule; no threshold optimisation |
| Entry / exit | Monday regular-session open / close | Short, interpretable holding period |
| Allocation | One-third of capital allocated to each of the three names on trade days | Fixed weights, no optimisation |
| Leverage / shorts | None | Limits implementation and risk assumptions |
| Cash | Zero interest in the initial model | Explicit simplification; discuss opportunity cost |
| Base execution friction | Provisional 10 basis points per side | Scenario assumption, not a measured historical spread |
| Cost sensitivity | 0, 5, 10, 25 and 50 bps per side | Shows dependence on execution assumptions |
| Random seed | 42 for bootstrap or any stochastic diagnostic | Reproducibility |

The stock selection is a restricted case-study universe, not a point-in-time census of every crypto-exposed stock. Historical availability does not eliminate survivorship or selection bias. Document how the names were selected and limit generalisation accordingly.

## B2. Avoid parameter searching

The primary signal threshold is zero. Keep it even if a different threshold looks better. Validation checks may establish that the pipeline is correct or reveal a genuine methodological problem; they should not become unrestricted searches for profitable variants.

If time permits, predeclare at most two threshold sensitivities, +1% and +2%, using the same execution rules. Treat them as sensitivity analyses, not replacements selected from the final test. Record every strategy variation tried, including discarded ones.

Do not optimise asset weights, choose the best-performing stock, search dozens of entry times or select the best year.

## B3. Explicitly outside the core scope

- Coinbase or spot Bitcoin ETFs as additional universes.
- Short selling, margin, derivatives or hedged pairs.
- News scraping, sentiment models or machine learning.
- Stop-losses based on daily highs/lows, which cannot reveal the sequence of intraday prices.
- Entry rules conditioned on the observed opening gap while assuming execution at the same opening price.
- A dashboard, website, live trading bot or brokerage integration.
- Trading holiday weekends on Tuesday.
- A definitive causal claim about investor attention.

These are possible future extensions. Finish the core pipeline and report first.

---

# C. Data, calendars and timestamp contract

## C1. Sources and acquisition behaviour

**Equities:** Use `yfinance` or another documented provider. Set adjustment and corporate-action options explicitly instead of relying on library defaults. Preserve the downloaded raw daily prices, adjusted close and available dividend/split records. Verify that daily Open/Close refer to the intended regular session. Treat vendor data as imperfect.

**Bitcoin:** Use a historical spot candle archive with reproducible downloads. Binance's archive provides daily/monthly files, including 30-minute candles. Record the exchange, pair, interval, URLs, download time and checksums where available. BTC/USDT is not identical to BTC/USD; acknowledge stablecoin and venue-specific risk.

Binance documents a change to microsecond timestamps for spot archive data from January 2025. Earlier files use millisecond timestamps. Parse according to the documented file period, validate converted dates against the filename and fail on mismatches. Do not divide all timestamps by a single hard-coded factor.

Do not assume `yfinance` will supply the entire multi-year intraday Bitcoin sample. Intraday retention varies by interval; verify actual coverage. Historical archive access has not been tested in this roadmap.

**Calendar:** Use a documented exchange-calendar package supporting historical US equity sessions, such as `exchange_calendars` or `pandas_market_calendars`. Verify timezone-aware session opens/closes and representative holidays against official exchange schedules. Pin the actual version used.

## C2. Required raw-data and metadata records

| Dataset | Required contents |
| --- | --- |
| Equity snapshot | Ticker, session date, Open, High, Low, Close, adjusted close if supplied, volume and corporate actions |
| Bitcoin snapshot | Candle open and close timestamps, OHLC, pair and interval; preserve remaining vendor fields where practical |
| Source manifest | Provider, URL/request arguments, date range, download timestamp, file checksum, library versions |
| Calendar snapshot | Session date, regular open/close in UTC and New York time, full/short-session flag |
| Data-quality log | Missing rows, duplicates, action dates, suspicious values, exact exclusions and resolutions |
| Configuration | Universe, periods, cutoffs, weights, costs, seed and design-freeze date |

Use local snapshots by default when rerunning. A deliberate refresh mode may redownload; it must not silently replace the original research snapshot. Hashes help detect accidental changes. Never include private credentials.

## C3. Candle availability: the most important timing rule

A candle labelled by its start time becomes fully known only when it finishes. A 09:00–09:30 candle's Close is not a valid 09:00 input.

For each target timestamp, select the final candle that has completed by that timestamp:

- Friday 16:00: use the close of the 15:30–16:00 New York candle.
- Monday 09:00: use the close of the 08:30–09:00 New York candle.
- Optional Monday-session diagnostic: use completed endpoints at 09:30 and 16:00.

When vendor close times end just before the next boundary, accept the documented sub-second convention. Define an expected candle-end boundary separately if useful. Require the selected candle to end at the intended boundary, allowing no more than one second of timestamp-convention tolerance. If the expected candle is missing, mark the event invalid. Do not accept a stale candle from a previous half-hour and do not interpolate from future prices.

A backward `merge_asof` or binary search may locate candidates, but locating a previous row is not enough: enforce the endpoint tolerance and reject stale observations.

There is a 30-minute interval between the 09:00 cutoff and the 09:30 entry. Document the practical assumption that data delivery and order preparation fit inside this interval.

## C4. Timezone and session rules

Keep canonical timestamps in UTC and use `America/New_York` for session construction. Convert through timezone-aware operations; do not apply a constant four- or five-hour offset. US daylight saving must be handled independently of UK daylight saving.

For the core sample, an eligible event requires:

1. A full regular session on the calendar Friday immediately before the Monday.
2. A full regular session on that calendar Monday.
3. Correct Bitcoin endpoint candles.
4. No known pre-entry trading unavailability in the fixed basket. Return calculation subsequently requires reliable execution/valuation prices, but a future missing price cannot retroactively determine entry eligibility.

Exclude Friday market holidays, early-close Fridays, Monday holidays and unusual/non-full sessions. Do not rename Tuesday as Monday. Keep an exclusions table with reasons and counts by period.

Use equity session dates as dates, not as artificial UTC-midnight instants converted into New York time; that conversion can shift them to the previous date.

## C5. Missing prices and trade availability

Do not forward-fill equity prices over a missing session or silently reweight away from a missing ticker.

Before entry, a known suspension or unavailability of one basket member means no core basket trade; log it. If the only issue is a missing vendor row, attempt documented repair or cross-check it. A missing Monday Close must not be used to retroactively skip a trade that the strategy would have entered. An unresolved post-entry valuation failure blocks an authoritative performance result until a defensible valuation/execution rule is supplied.

Do not turn unknown returns into zero. Distinguish genuine no-trade days, known market closures and unresolved data failures.

## C6. Corporate actions and comparable prices

Preserve both raw fields and adjustment information. A split between Friday and Monday can produce a false gap if unmatched price scales are compared.

For the explanatory gap diagnostic, a transparent option is a consistently adjusted OHLC series. With raw Close and Adjusted Close, define the vendor adjustment factor for date d as `AdjClose[d] / Close[d]`, and apply it consistently to Open and Close for that date. Verify the provider's conventions and sample action dates. A dividend-adjusted gap is an adjusted return diagnostic, not necessarily the raw exchange-price jump; label it accordingly.

For the Monday open-to-close trade, the same-date adjustment factor cancels. Use raw prices for fill/quantity bookkeeping and reconcile the return with the consistently adjusted ratio. Investigate any intraday action or exceptional session instead of assuming cancellation always resolves it.

Never mix adjusted Close with unadjusted Open. Do not use absolute retrospectively adjusted stock-price levels as signal inputs. The primary signal is Bitcoin-based.

## C7. Processed event schema

Produce one row per candidate calendar Monday, retaining ineligible rows and their reasons. Populate outcomes for valid events, with basket-level outcomes and per-ticker details available for auditing:

| Field | Meaning |
| --- | --- |
| `event_id` | Unique Monday date |
| `friday_date`, `monday_date` | Calendar endpoints |
| `btc_start_target_utc`, `btc_cutoff_target_utc` | Intended boundaries |
| `btc_start_close_time`, `btc_cutoff_close_time` | Actual source candle timestamps |
| `btc_start_price`, `btc_cutoff_price` | Completed-candle prices |
| `btc_weekend_return` | Signal x |
| `split` | Development / validation / test |
| `eligible`, `exclusion_reason` | Eligibility audit |
| `signal_long` | True when eligible and x > 0 |
| Per-ticker Friday Close and Monday Open/Close | Raw execution values and consistent adjusted diagnostic values |
| `basket_gap_adjusted` | Equal-weight adjusted opening-gap diagnostic |
| `basket_intraday_gross` | Equal-weight Monday open-to-close return |
| `btc_monday_session_return` | Optional hindsight-only diagnostic |

Keep predictor columns separate from outcome columns. The signal-building function should receive only information available by the cutoff, never Monday equity prices or Monday-session Bitcoin returns.

---

# D. Strategy, benchmarks and evaluation

## D1. Return definitions

For weekend w and equity i:

```text
x[w] = BTC_completed_price(Monday 09:00 NY)
       / BTC_completed_price(Friday 16:00 NY) - 1

gap_adjusted[i,w] = adjusted_Open[i,Monday]
                   / adjusted_Close[i,Friday] - 1

drift[i,w] = raw_Close[i,Monday] / raw_Open[i,Monday] - 1

basket_drift[w] = mean(drift[MSTR,w], drift[MARA,w], drift[RIOT,w])

signal[w] = 1 if eligible[w] and x[w] > 0, otherwise 0
```

Use simple returns for portfolio arithmetic. Log returns can be optional analytical outputs but must not be substituted into wealth compounding without conversion.

## D2. Trading and execution contract

On a qualifying Monday, allocate one-third of beginning-of-day portfolio value to each asset's purchase, inclusive of entry friction. Buy at the recorded regular-session Open with adverse entry friction. Exit at the recorded Close with adverse exit friction. The exit decision is fixed before trading, not based on that day's observed outcome.

Daily vendor Open/Close are academic execution proxies; they may not exactly match achievable auction fills. State that limitation. No signal uses the actual Monday Open. No trade earns returns before the opening. Flat all other sessions; no overnight holdings. Ignore fractional-share restrictions in the initial capital-scalable model and disclose that choice.

Let `c_in` and `c_out` be fractional, all-in proportional execution frictions. For an asset allocation A:

```text
shares = A / (Open * (1 + c_in))
proceeds = shares * Close * (1 - c_out)
net_return_asset = (Close / Open) * (1 - c_out) / (1 + c_in) - 1

net_return_basket = sum(weight[i] * net_return_asset[i])
```

This models entry friction without borrowing to pay it. With equal costs across names it also equals `(1 + basket_drift) * (1 - c_out) / (1 + c_in) - 1`.

Do not charge costs on cash/no-trade days. Record gross and net results separately. The friction parameter combines spread/slippage/fees into an assumption; avoid double counting. A displayed quoted spread is not automatically a cost per side or the opening-auction execution cost. Support a realistic interpretation using credible execution evidence if obtainable; otherwise honestly report a range and the unresolved limitation.

## D3. Required benchmarks

| Benchmark | Implementation | Purpose |
| --- | --- | --- |
| Cash | Zero return under the initial cash convention | Absolute baseline |
| Unconditional Monday basket | Buy the same fixed basket every eligible Monday, with identical fills/costs | Determines whether the filter adds useful selection |
| Primary signal strategy | Buy only when x > 0 | Tests the proposed rule |

Report exposure and trade count alongside performance. Lower drawdown can arise from fewer trading days rather than better prediction. Compare the basket's average Monday drift when x > 0 with its drift when x <= 0, including uncertainty. This conditional comparison complements the full portfolio comparison.

A frequency-matched random Monday selector or buy-and-hold chart is optional context, not necessary for the core deliverable. Do not choose the best random seed or imply equal risk because all portfolios have the same tickers.

## D4. Full daily portfolio series

Create a return series indexed by every regular equity session within each evaluation period. Known cash days have zero return under the initial model. Trade Mondays have the relevant net return. Unresolved data errors remain errors, not cash.

Wealth starts at 1 at the beginning of each period. Compound via `wealth[t] = wealth[t-1] * (1 + return[t])`. Include the initial wealth point in drawdown calculations so an immediate loss is captured. Calculate development, validation and test metrics on their own period series; the test portfolio begins with wealth 1.

Required metrics:

```text
cumulative_return = final_wealth - 1
Sharpe_zero_rf = sqrt(252) * mean(daily_returns) / std(daily_returns, ddof=1)
drawdown[t] = wealth[t] / running_max_including_initial_wealth[t] - 1
maximum_drawdown = minimum(drawdown)
```

Label the zero-risk-free-rate Sharpe explicitly. The brief requires a Sharpe ratio, but a zero cash/risk-free convention simplifies reality, particularly when cash yields are material. A risk-free/cash-accrual sensitivity is a future improvement unless time permits a properly aligned source. Never annualise a Monday-only return series using sqrt(252). If variance is zero, Sharpe is undefined; output N/A with an explanation, not infinity or zero.

Also report eligible weekends, actual trade weekends, exposure fraction, average trade return, median trade return, win rate and turnover. Define gross one-way entry turnover as allocated purchase capital / portfolio value and round-trip turnover as entry plus exit traded notional / portfolio value. Fractional shares and proportional costs make capacity assumptions explicit.

## D5. Explanatory analysis and uncertainty

Use the equal-weight basket as the primary analytical unit, one observation per weekend. Plot:

1. Bitcoin interval return versus adjusted basket opening gap.
2. Bitcoin interval return versus basket Monday drift.
3. Full daily net wealth of the signal strategy and Monday benchmark.
4. Net drawdown and cost sensitivity.

Display period boundaries and sample counts. Do not expose test-return charts before design freeze.

Simple regressions are descriptive tools, not required trading models:

```text
gap[w] = a_gap + b_gap * x[w] + error[w]
drift[w] = a_drift + b_drift * x[w] + error[w]
```

Analyse all eligible weekend signals for these relationships, including negative ones. Report uncertainty rather than only slope signs or R-squared. Multiple equity rows from one weekend are correlated; do not count them as independent events.

For a feasible uncertainty check, bootstrap paired weekend rows with a fixed seed, preserving all ticker outcomes together. A moving-block bootstrap over contiguous eligible weekends can help account for serial dependence; for example, predeclare four-week blocks, 2,000 replications and a 95% interval, recording its limitations at this sample size. Apply identical sampled event blocks to strategy and benchmark comparisons. Do not pick block lengths based on the narrowest interval. If no-trade events appear, retain them rather than resample only profitable trades. Calendar-based metrics must still use the original full daily series.

At minimum, provide uncertainty for the conditional mean drift difference and the average strategy-minus-benchmark event return. If the sample is too thin, label the result inconclusive. A positive average or Sharpe alone does not establish a statistically robust edge.

## D6. Monday Bitcoin movement as a diagnostic

Using 30-minute candles, optionally calculate Bitcoin's return from Monday 09:30 to 16:00. Check whether observed equity drift accompanies continued Bitcoin movement during that session. An explanatory regression may include this hindsight-only variable to assess an alternative account.

It must never enter the pre-open trading signal. A relationship that disappears in this diagnostic is evidence against a simple catch-up story, not proof of a particular causal mechanism. Do not add extensive control-variable searches.

## D7. Frozen test protocol

Before opening any final-test outcomes, save the specification, code/configuration hashes where practical, data version and experiment log. The primary design must already be runnable on development/validation data.

Data-schema and coverage checks may include the test period without inspecting returns, strategy performance or signal-outcome relationships. Test outcomes are revealed only after freeze.

Run the complete frozen strategy on 2024–2025 once for evaluation. Reruns to reproduce identical results are fine. If a genuine bug is found, fix it, record the original issue and the corrected result, and disclose that the test was previously viewed. Do not present a post-test redesign as untouched validation. Analyse losing periods as honestly as winning periods.

---

# E. Implementation stages and completion checks

## Stage 0 — Orient and register the design

**Inputs:** This file and the four coursework PDFs.

**Actions:** Read the brief, confirm the Canvas deadline and current submission rules, personalise the pitch, record the defaults and initialise a decision/experiment log. Mark all performance results pending.

**Outputs:** Research specification and a clear scope statement, stored in the notebook's introductory/configuration cells and metadata.

**Done when:** The student can explain why the gap is different from a return earned after entry, why the 09:00 cutoff exists and what would falsify the hypothesis.

## Stage 1 — Check data feasibility before full development

**Actions:** Obtain a small historical Bitcoin sample from 2021 and another from 2025, plus small equity samples. Check archive access, candle schema, timestamp units, adjustment fields and historical crypto exposure of the proposed firms. Verify rough coverage for 2021–2025 without calculating final-test performance.

Manually inspect one ordinary weekend, one winter/summer timing pair, one daylight-saving transition and one holiday/early-close case. Demonstrate that every endpoint exists at the required resolution and is available before the cutoff.

**Outputs:** Feasibility note, source manifest and a few inspectable alignment rows.

**Done when:** There is a reproducible route to the planned history and timestamp alignment works. If coverage fails, try a documented alternative historical provider before shrinking the sample. Do not silently substitute UTC daily closes for New York intraday endpoints. Any changed endpoint/sample must be recorded before return analysis. If no defensible historical source is accessible, stop dependent backtesting and report the concrete blocker.

## Stage 2 — Acquire and preserve the full snapshots

**Actions:** Download the historical Bitcoin archives and equity data with bounded retries. Save raw bytes/data, request arguments, source identifiers and checksums. Store exact dependency versions. Implement cached and refresh modes.

**Outputs:** `data/raw/`, source manifest, calendar snapshot and reproducible acquisition code.

**Done when:** Raw inputs can be loaded locally without credentials and the acquisition code documents how to recreate them. Offline notebook execution must not require successful fresh API calls.

## Stage 3 — Clean data and build eligible events

**Actions:** Parse timestamps, sort, resolve duplicates explicitly, validate dates and OHLC relationships, check missing intervals/actions, construct the historical session calendar and pair normal Fridays/Mondays. Align completed Bitcoin candles with endpoint tolerance checks. Construct the event table and exclusion log.

**Outputs:** Processed prices, clean event inputs and quality/exclusion summaries.

**Done when:** Endpoints are correct, exclusions reconcile with the starting calendar and no unresolved post-entry valuation failures are hidden. Repeated source timestamps with conflicting values require investigation, not an arbitrary last-row choice.

## Stage 4 — Analyse development data and build the baselines

**Actions:** Calculate gap/drift outcomes for 2021–2022. Produce initial scatterplots and summary counts. Build cash and unconditional Monday portfolios with correct fills, costs and daily compounding.

**Outputs:** Development diagnostics and an auditable baseline trade ledger.

**Done when:** A manually calculated example matches the code and metrics reconcile with the ledger. Do not redesign the signal around favourable development outliers.

## Stage 5 — Implement the primary strategy

**Actions:** Build the x > 0 signal using only predictor fields. Apply the fixed basket weights, cost model and close exit. Save a ledger with event/ticker, signal timestamp, allocated capital, fill assumptions, shares, gross/net proceeds and cash/no-trade reasons.

**Outputs:** Strategy event returns, full daily portfolio series and comparative development metrics.

**Done when:** No trade captures the opening gap; weights and costs reconcile; Monday outcomes do not affect entry eligibility except genuine pre-entry known availability conditions.

## Stage 6 — Run meaningful correctness checks

Implement compact checks that catch financial/timing errors, not tests that merely reproduce implementation details:

- A 09:00-start candle's Close cannot be consumed at 09:00.
- Winter and summer weekends map to the correct UTC endpoints.
- A Monday holiday and shortened Friday do not produce trades.
- Missing expected endpoint candles are rejected, not replaced by stale ones.
- A synthetic $100 Friday close, $106 Monday open, $107 close earns $107/$106−1 before costs.
- A zero-friction flat intraday price earns zero; positive friction makes it negative.
- Known no-trade days incur no friction; a missing post-entry Close is an error.
- Correctly matched split-adjusted values avoid a false diagnostic gap.
- Truncating data after Monday 09:00 leaves the computed signal unchanged.
- Basket allocations do not require leverage, and trade ledgers reconcile to wealth.
- Initial losses appear in maximum drawdown; constant cash produces undefined Sharpe.

**Outputs:** Small deterministic checks, results and timing assertions in the notebook.

**Done when:** All critical checks pass and representative real alignment rows have been inspected.

## Stage 7 — Validate, justify and freeze

**Actions:** Run the unchanged strategy on 2023. Check counts, robustness, costs and sensitivity to exceptional weekends. Record every variant attempted. Investigate factual or implementation problems, not merely weak performance. Freeze design and code before the final test.

**Outputs:** Validation metrics, experiment register and design-freeze record.

**Done when:** The primary strategy is fixed and its major choices can be defended. A losing validation result does not automatically authorise a new hypothesis.

## Stage 8 — Evaluate the held-out test

**Actions:** Reveal 2024–2025 outcomes. Compute required metrics, annual breakdowns, uncertainty, cost sensitivity and paired benchmark comparisons. Inspect trade concentration and optional Monday-Bitcoin diagnostic. Record genuinely corrective reruns.

**Outputs:** Final result tables, full daily wealth/drawdown figures and an interpretation of what the evidence does and does not support.

**Done when:** Every reported number is traceable to saved output and the untouched/post-correction status is accurate. Do not add filters to improve test performance.

## Stage 9 — Profile the expensive step and explain risk

**Actions:** Measure representative runtime for acquisition separately from local parsing, sorting, alignment and backtesting. Identify the single most expensive computational stage actually observed. State input sizes and complexity. Explain the basket's correlated risk, execution risk and an adverse scenario.

**Outputs:** Brief timing/complexity table and risk discussion.

**Done when:** Complexity corresponds to the real implementation and risk analysis goes beyond Sharpe/drawdown. Do not invent profiling results.

## Stage 10 — Write the report and package reproducibly

**Actions:** Follow Section F exactly. Execute the notebook from a fresh kernel using saved snapshots. Verify results match the report; check all figures, required sections and data paths. Inspect the final package for secrets and broken dependencies. Follow the actual capstone upload instructions on Canvas.

**Outputs:** Separate report, `notebook.ipynb` and `data/` folder.

**Done when:** An independent reviewer can rerun the submitted pipeline and follow the student's explanation without this conversation.

---

# F. Exact coursework report structure

This roadmap uses its own navigation. The **submitted report** must instead begin with the student's name, submission date and one-line project title, without a separate title page, and use the following eight headings in this exact order.

## 1. Hypothesis Pitch

Approximately half a page: pattern, mechanism, distinction between gap and drift, falsification criteria and the student's own explanation. Avoid claiming the strategy's success before presenting evidence.

## 2. Data Pipeline

Identify sources, universe, sample, timestamp conventions, holiday rules, corporate actions, missing data, raw snapshots, cleaning and reproducibility. State BTC/USDT proxy limitations. Include a compact calendar-to-eligible-event reconciliation and period counts.

## 3. Strategy and Backtest

Explain the signal, weights, execution timing, costs, cash model, benchmarks and chronological split. Near the beginning of the results discussion, provide an explicit table of cumulative return, labelled Sharpe and maximum drawdown, covering development/validation/test and the main benchmark. Add trade counts, exposure and uncertainty. Include interpretable figures and gross/net comparison.

## 4. Methodology Defense

Justify the universe, period, split, pre-open cutoff, daily stock/intraday Bitcoin resolution, sign threshold, equal weights, long-only design, entry/exit, cost scenarios and benchmarks. Explain what would break if each key assumption were wrong. Be able to defend any AI-assisted component.

## 5. Pitfall Checklist

Use the following names as individual subheadings, each immediately followed by the actual checks and findings. These instructions are prompts, not completed answers.

### Look-ahead bias

Show completed-candle timing, the cutoff-before-entry relation, predictor/outcome separation and truncation checks. Do not use Monday's close, full Monday Bitcoin return or future opening information in the entry rule. Explain retrospective adjusted prices and why they are diagnostic/outcome data rather than the primary predictor.

### Survivorship bias

Describe the static three-stock case study and how it excludes other companies, including potentially failed/delisted firms. Historical exposure checks do not make it survivorship-free. State the resulting limit on generalisation. Do not assert “not applicable” because the sample uses famous stocks.

### Overfitting/data-snooping

State every variant tried, the fixed primary rule, sensitivity variants and the freeze date. Account for any post-test fixes or exploration. Do not present the best configuration found after reviewing the test as the original strategy.

### Transaction costs and slippage

State all-in per-side costs, their evidence or provisional nature, the adverse fill model and the gross/net/stress results. Discuss that daily-price proxies and scenario costs cannot establish actual historical fills or capacity.

### Out-of-sample validation

List precise development, validation and test dates; distinguish tuning from testing. Compare period results and show uncertainty/trade counts. State whether the test remained untouched until freeze.

## 6. Efficiency Touchpoint

Identify the single most expensive actual step. Possible candidates, to be measured rather than assumed:

| Operation | Indicative complexity | Conditions |
| --- | --- | --- |
| Parse Bitcoin files | O(B) | B candle rows, fixed-size row schema |
| Sort Bitcoin timestamps | O(B log B) | If sorting is required |
| Locate W endpoint pairs | O(W log B) | Binary search on sorted candles |
| Streaming temporal alignment | O(B + W) | Sorted data with a linear merge |
| Fixed-basket backtest | O(WN + D) | N equities, D daily sessions |

Reading all history can dominate a very small trading loop. Download latency is important operationally but is not adequately characterised by a sorting Big-O bound. Record wall time and distinguish network I/O from local computation. Explain why the measured workload is acceptable and why cached snapshots matter. Graph algorithms and custom classes are not mandatory; use course concepts where they genuinely solve a problem.

## 7. Risk Touchpoint

Explain no leverage, maximum allocation and lack of overnight holdings. Three stocks in one Bitcoin-linked theme provide limited economic diversification. A Monday Bitcoin reversal, company-specific announcement, halt, liquidity problem or adverse opening/closing execution can hurt all positions together. Weekend exchange/regulatory news can influence the signal and later price path, but a Monday-open entry does not hold equity risk over the preceding weekend. BTC/USDT data can also be distorted by a stablecoin/venue event. Discuss capacity separately from backtest returns.

An optional labelled scenario can apply a hypothetical −10% Monday basket return to full allocation, with costs. It is a stress illustration, not an observed event or a calibrated risk forecast.

## 8. Reflection

The student should answer from actual work: what was learned, which original assumptions were wrong and what became clear only after implementation. Possible prompts include timezone difficulty, the gap-versus-drift distinction, small independent sample size, survivorship limitations and cost sensitivity. Never invent an autobiographical reflection.

Discuss natural next steps: a point-in-time broader universe, historical executable intraday prices, improved cost estimates, a fresh future test, additional exposure types or more realistic cash/capital modelling. Explain what would need to change for each.

## References

Add a short References section after the eight sections for data documentation, exchange calendars and any external methodology actually used. Cite primary sources. Use documentation to understand data/API behaviour, not online completed solutions. The assessment says not to seek or post coursework solutions online.

## Notebook and package layout

The notebook must contain visible headings for Data Acquisition, Cleaning, Strategy and Backtest, in the order used in the report. Additional explanatory/result cells are useful, but the report must remain a single standalone document.

The final capstone package should have three clearly separated top-level items:

```text
report.md                    # or report.pdf
notebook.ipynb
data/
    raw/                     # downloaded equity and Bitcoin snapshots
    processed/               # reproducible cleaned data and event table
    metadata/                # manifest, configuration, calendar, exclusions, experiment log
    results/                 # metrics and trade ledger
    figures/                 # any images referenced by report.md
    README.md                # source and snapshot explanation
```

Keep the core functions in the notebook for the simplest self-contained submission. Conceptual function boundaries below do not require separate modules. The roadmap is a development guide; it does not replace the report or become an extra required top-level submission item.

The supplied `submission.pdf` describes weekly class-activity ZIPs and `python ok --score`. Do not assume that activity-specific launcher/tests apply to the capstone. The capstone brief specifies its own three-part structure; check the capstone Canvas assignment for the actual upload container and deadline. The syllabus/assessment also disagree on whether class activities require hand-ins; that does not change the capstone scope.

---

# G. Results register and possible conclusions

## G1. Results table — populate only from executed code

**Every value below is pending. No number should be inferred from expectations.** Store full numeric values in machine-readable output; use consistent rounded display values in the report.

| Period | Strategy | Eligible weekends | Trade weekends | Exposure | Gross cumulative return | Net cumulative return | Net Sharpe (daily, zero rf) | Net max drawdown |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Development 2021–2022 | Positive BTC signal | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| Development 2021–2022 | Unconditional Monday | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| Validation 2023 | Positive BTC signal | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| Validation 2023 | Unconditional Monday | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| Test 2024–2025 | Positive BTC signal | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| Test 2024–2025 | Unconditional Monday | Pending | Pending | Pending | Pending | Pending | Pending | Pending |

Additional outputs:

- Signal-to-gap and signal-to-drift relationships, with uncertainty and counts.
- Mean/median drift by positive and non-positive signal; their difference and interval.
- Strategy-minus-benchmark comparisons on paired events.
- Net performance across the registered per-side cost scenarios.
- Annual results and largest contributors to profit/loss.
- Optional Monday Bitcoin diagnostic, labelled hindsight-only.
- Data exclusions and known limitations.

## G2. Outcome interpretation guide

| Finding | Defensible interpretation | Avoid claiming |
| --- | --- | --- |
| Gap predictable; drift weak or absent | The opening appears to incorporate much of the relationship; little evidence of this open-to-close opportunity | Bitcoin has no effect on these stocks |
| Drift and net strategy stable out of sample | Evidence supports a predictive association and potential economic usefulness under stated assumptions | Guaranteed returns, proven causal underreaction or deployable arbitrage |
| Drift apparent; costs erase gains | Statistical predictability may be economically impractical at those costs | The strategy is profitable because gross returns are positive |
| Development strong; test weak | Possible overfitting, instability or regime dependence | Test results do not matter |
| Few weekends dominate | Fragile result with high concentration in events | Broadly reliable forecasting skill |
| Drift negative following positive BTC moves | Evidence contradicts the original directional hypothesis; overreaction/reversal is a possible explanation | A new reversal strategy was independently validated on the same test |
| Monday Bitcoin movement explains much of drift | Continued crypto movement is an alternative account; catch-up interpretation is weaker | A hindsight explanatory control is a tradable signal |
| Wide intervals / too few trades | Evidence is inconclusive at this sample size | Insignificance proves no effect |
| Data timing or valuation unresolved | Strategy validity has not been established | Missing or unreliable outcomes can be treated as zero |

Judge the hypothesis, incremental prediction and economic performance separately. A profitable long-only basket may reflect market exposure rather than signal skill. A non-profitable project can still satisfy the research brief when the test is meaningful and honest.

---

# H. Two-week work schedule and scope control

Use relative days from the actual project start; this is not a verified calendar deadline.

| Day | Target | Exit condition |
| --- | --- | --- |
| 1 | Register question and test historical source access | Specification and feasibility checks documented |
| 2 | Acquire snapshots and session calendar | Local data available with provenance |
| 3 | Clean timestamps/actions and build weekend events | Alignment rows and exclusion counts inspected |
| 4 | Development descriptive analysis | Gap/drift separated and sample counts known |
| 5 | Cash and unconditional Monday backtests | Ledger/manual examples reconcile |
| 6 | Primary signal strategy | Fixed rule executes correctly |
| 7 | Critical timing, cost and valuation checks | Meaningful checks pass |
| 8 | Validation and limited sensitivity work | Experiment log complete |
| 9 | Freeze design and evaluate final test | OOS outputs saved without redesign |
| 10 | Uncertainty, cost and concentration analysis | Claims match strength of evidence |
| 11 | Efficiency/risk analysis and report draft | Eight sections drafted |
| 12 | Complete report and student's reflection | Required tables and references present |
| 13 | Fresh-kernel offline rerun and package review | Report/notebook/results agree |
| 14 | Buffer for actual failures and final checks | Submission ready |

**If time is tight, reduce extensions first:** omit extra tickers, additional thresholds, control regressions and cosmetic figures. Preserve correct timestamps, real snapshots, the primary strategy, benchmark, OOS metrics, five pitfall answers, efficiency, risk and reflection. Do not save time by removing the held-out test or silently dropping messy data.

**Definition of success:** A reproducible, explainable, defensible test of the chosen hypothesis, with all mandatory deliverables. It does not require a positive Sharpe, a profitable strategy or a claim of global originality.

---

# I. Instructions for an implementing AI agent

## I1. Operating rules

1. Read this roadmap and the official brief before modifying the project. Reuse completed work; do not restart merely because a new session begins.
2. Work through Section E in order. Complete and verify each stage before relying on its outputs. Routine reversible implementation choices do not need repeated permission.
3. Explain major choices to the student in plain language and preserve their ability to defend the pipeline.
4. Treat the registered defaults as fixed until a factual data/implementation problem requires a documented amendment. Weak returns alone are not such a problem.
5. Never invent data, test results, sources, execution fills, historical spreads, personal reflections or an untouched-test claim.
6. Keep the original hypothesis visible even if contradicted. Do not search indefinitely for a profitable variant.
7. Inspect predictor availability explicitly. Never pass future outcome columns into signal construction.
8. Use snapshots and explicit dependencies. Preserve raw inputs; make cleaning traceable.
9. Keep unknown/missing outcomes distinct from cash days. Resolve actual valuation failures before claiming a complete backtest.
10. Do not add new assets, short selling, complex models or live execution as routine “improvements.” Record scope changes and their effect on validation.
11. Obtain primary data/API/methodology documentation when needed, not completed coursework solutions. Do not publish the work or share it with classmates.
12. Update the progress board, decision log and experiment log after meaningful changes. On interruption, leave a short handoff stating completed stages, unresolved issues and the exact next step.
13. Stop a dependent stage when source access or an essential assumption is genuinely unresolved. Report the specific obstacle; do not manufacture a convenient substitute.
14. At completion, deliver the separate report, notebook and snapshot folder with required checks. The current request creates this roadmap only; implementation remains future work.

## I2. Suggested function responsibilities

These are interfaces for clear thinking, not a mandate to build a large framework:

```text
load_config()
download_or_load_equities(config)
download_or_load_btc_archive(config)
build_session_calendar(config)
clean_equity_data(raw, action_records)
clean_btc_candles(raw, file_metadata)
build_weekend_endpoints(calendar, config)
align_completed_candles(candles, endpoints, tolerance)
build_signal_inputs(aligned_prices, pre_entry_availability)
build_outcome_table(equities, endpoints)
make_primary_signal(signal_inputs)
run_monday_portfolio(signal, outcomes, weights, costs, calendar)
compute_period_metrics(daily_returns)
run_registered_diagnostics(events, config)
export_results_and_figures()
```

Signal construction must be independently testable without outcomes. Use DataFrames for indexed time-series tables, dictionaries for configuration/source metadata and sets for unique/exclusion checks. An unnecessary class hierarchy or graph adds no research value here.

## I3. Suggested next-agent starting instruction

> Continue the Priced by the Bell project using this roadmap. Start with Stages 0 and 1: review the official brief, register the proposed configuration, verify historical Bitcoin candles and equity coverage, and demonstrate timezone-safe completed-candle alignment on representative weekends. Do not inspect final-test return relationships or run a strategy search. Preserve raw snapshots and document exclusions. Then progress sequentially through the baseline, primary strategy, meaningful checks, validation, design freeze and held-out evaluation. Keep the student informed and ensure they can explain each major choice. Record actual outputs and unresolved issues; do not invent results.

---

# J. Progress board, decision log and final checklist

## J1. Current progress

- [x] Choose the crypto weekend / Monday drift question.
- [x] Create an introductory roadmap mapped to the brief.
- [x] Confirm Canvas deadline (20 Oct 2026); upload instructions still to check.
- [ ] Personalise and register the hypothesis pitch.
- [x] Verify source access and history (exposure check from filings still to cite in report).
- [x] Acquire and preserve raw snapshots.
- [x] Clean and inspect time alignment / corporate actions.
- [x] Build the event table and exclusions log.
- [x] Build and reconcile the unconditional Monday benchmark (in-sample).
- [x] Build and reconcile the primary strategy (in-sample).
- [x] Pass meaningful timing and backtest checks (10 asserts).
- [ ] Complete validation and register all variants.
- [ ] Freeze design before examining the final test.
- [ ] Evaluate test and populate actual results.
- [ ] Complete uncertainty, costs, efficiency and risk.
- [ ] Write all eight report sections and references.
- [ ] Add the student's actual reflection.
- [ ] Run notebook from a fresh kernel using saved snapshots.
- [ ] Check final package and submit through Canvas.

## J2. Decision log template

| Date | Decision/change | Reason | Evidence consulted | Test already viewed? | Effect on claims |
| --- | --- | --- | --- | --- | --- |
| 2026-10-07 | Select weekend Bitcoin / Monday equity drift project | Clear mechanism and feasible intended two-week scope | Coursework brief and discussion; source documentation | No backtest performed | Hypothesis only; no performance claim |
| Pending | Validate or amend roadmap defaults | Pending data feasibility | Pending | No | Pending |

Maintain a separate experiment register with configuration, periods inspected, reason, outputs and whether primary/secondary/exploratory. Log abandoned variants too.

## J3. Final coursework compliance checklist

- [ ] Hypothesis pitch explains the pattern, economic/behavioural mechanism and falsification.
- [ ] Student can explain and defend every major design choice and AI-assisted component.
- [ ] Real data acquired with a documented pipeline and downloaded snapshot.
- [ ] Missing days, corporate actions and selection/survivorship addressed explicitly.
- [ ] Notebook runs data acquisition/loading → cleaning → strategy → backtest end to end.
- [ ] Separate standalone report; no report buried in notebook cells.
- [ ] Report begins with name, submission date and one-line title.
- [ ] Eight numbered report headings exactly match the brief, in order.
- [ ] All five named pitfall subheadings have actual checks and findings.
- [ ] Explicit labelled cumulative return, Sharpe and maximum drawdown table near the start of results.
- [ ] Out-of-sample evaluation and comparison with development/validation clearly identified.
- [ ] Costs, slippage, exposure and benchmarks are understandable and consistent with code.
- [ ] Single most expensive computational step and its complexity explained.
- [ ] Risk discusses sizing/leverage, concentration and a plausible bad scenario.
- [ ] Honest student reflection covers learning, changed assumptions and next steps.
- [ ] References identify the external sources actually used.
- [ ] Required top-level report / notebook / data items clearly separated.
- [ ] Saved data paths are relative and work outside the original machine.
- [ ] No credentials, fabricated results or unsupported profitability claims.
- [ ] Capstone-specific Canvas deadline/upload requirements checked.

---

# K. Sources and reference notes

## K1. Authoritative coursework documents

These four supplied PDFs were read to construct this roadmap:

1. **capstone-project.pdf** — authoritative project workflow, required eight sections, five pitfalls, OOS metrics, efficiency/risk/reflection, data snapshots and three-part submission format.
2. **assessment.pdf** — the capstone determines the module grade; assessment concerns methodology, correctness and critical reflection; individual-work and AI-ownership expectations. No numerical rubric weights were supplied.
3. **submission.pdf** — primarily weekly class-activity uploads; do not transfer its `python ok --score` procedure to the capstone without capstone-specific instructions.
4. **syllabus.pdf** — Python, algorithms, complexity, data structures and graph topics; use relevant computational ideas without artificially expanding the project.

Original source copies in this workspace:

- `info/capstone-project.pdf`
- `info/assessment.pdf`
- `info/submission.pdf`
- `info/syllabus.pdf`

These absolute paths identify the current source copies. Future implementation must not depend on them remaining available; keep the supplied briefs accessible alongside development work. Do not add unrelated coursework resources to the submitted data snapshot.

## K2. Primary external documentation

Documentation checked on 7 October 2026; source availability and schemas must still be verified during Stage 1.

- [Binance public historical-data documentation](https://github.com/binance/binance-public-data) — archive files, candle intervals/fields, timestamp-unit change and checksum support.
- [Binance public archive](https://data.binance.vision/) — proposed Bitcoin spot snapshot source.
- [yfinance historical download API](https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html) — explicit download/adjustment parameters and intraday coverage limitations.
- [yfinance price-history implementation](https://github.com/ranaroussi/yfinance/blob/main/yfinance/scrapers/history.py) — interval-specific history handling; do not assume unlimited intraday downloads.
- [Nasdaq market schedule](https://www.nasdaq.com/market-activity/stock-market-holiday-schedule) — regular/extended session definitions and holidays; use a historical calendar for the full sample.
- [Robinhood 24 Hour Market documentation](https://robinhood.com/us/en/support/articles/24hour-market/) — selected overnight access illustrates why “all stocks are closed until Monday's opening” is too absolute.

Use official issuer filings/publications to verify each company's historical crypto exposure and corporate actions in Stage 1. Those checks are pending, and no issuer facts have been fabricated here. Add official documentation for the calendar, statistical packages and execution assumptions actually selected during implementation.

**Next concrete action:** Complete Stage 0 and Stage 1. Verify the historical data and timing contract before calculating strategy performance.
