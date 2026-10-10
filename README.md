# Priced by the Bell? Bitcoin overnight returns and Monday drift in crypto-exposed equities

Capstone project, Data Structures and Algorithms, Imperial College Business School — Mert Ayranci

Tests whether Bitcoin's return between the prior 16:00 New York equity close and 09:00 the next trading morning
predicts the open-to-close return of an equal-weight basket of MSTR, MARA and RIOT, and whether a simple
long-or-cash rule based on it beats buying the basket every Monday after costs. In-sample 2021–2023;
out-of-sample 2024–2025 (evaluated once, after a recorded design freeze).

## Contents

| Item | Description |
|---|---|
| `report.md` | The written report (standalone) |
| `notebook.ipynb` | Full pipeline: data acquisition → cleaning → strategy → backtest → analysis |
| `data/` | Downloaded snapshot, processed tables, results, figures and metadata (see `data/README.md`) |
| `requirements.txt` | Exact package versions used |

## How to run

Requires Python 3.12. From the project folder:

```bash
python3.12 -m venv .venv
source .venv/bin/activate       
pip install -r requirements.txt
jupyter notebook notebook.ipynb
```

Then **Kernel → Restart & Run All**. The notebook runs fully offline from the saved snapshot in `data/raw/`
(about 15 seconds). No API keys or credentials are needed. Set `REFRESH = True` in the first code cell only to
re-download the public sources; the code refuses to overwrite a saved file whose contents differ.

## Key design records

- `data/metadata/decision_log.md`: every design decision, every strategy variant tried, the design freeze
  and post-freeze analyses.
- `data/metadata/manifest.json`: source URLs, SHA-256 checksums, download times and library versions.