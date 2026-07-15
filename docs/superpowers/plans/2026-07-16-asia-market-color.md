# Asia Morning Market Color Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a manually-run Python 3.11 script that pulls Asia market data from Bloomberg and emits a fixed-format "Morning Asia Market Color" text block to console + clipboard, with a Mac-runnable `--dry-run` mode.

**Architecture:** Pure formatting logic (`src/formatting.py`) is isolated from all Bloomberg/OS code so it is fully unit-testable on Mac. Section modules each own one block of output and degrade gracefully to `N/A` on fetch failure. `report.py` orchestrates; `market_color.py` is the entry point. `--dry-run` swaps the live Bloomberg fetch for a YAML fixture so the whole downstream pipeline runs without a Terminal.

**Tech Stack:** Python 3.11, `blpapi` + `xbbg` (Bloomberg), `PyYAML` (config/fixtures), `pytest` (tests). Windows runtime target; Mac authoring/dry-run.

## Global Constraints

- Python 3.11.
- Data source is Bloomberg only (`blpapi`/`xbbg`) — no free/public data sources, ever.
- Read-only: no trades, no orders, no writes to Bloomberg.
- No LLM calls; "Market Overview" is left blank for the user.
- Never commit credentials or entitlement/account identifiers. `.gitignore` must exclude `config.local.yaml`, `*.log`, `__pycache__/`, venvs.
- `--dry-run` output must equal the template **byte-for-byte**.
- bps convention: `bps = pct_change × 100`.
- Markets line + `1D Chg` line: round to 1 decimal, drop trailing `.0`; sign always shown; space before `bps`; fields joined by ` | `.
- ETF lines: integer bps; sign always shown; **no** space before `bps`; fields joined by single spaces.
- `formatting.py` must import nothing Bloomberg/OS-specific (keeps Mac tests clean).

## Reference: exact target output (template)

```
Good morning!
* Macro
{SK} KR: Employment Data
{JN} JP: Core Machine Orders
{CH} CH: GDP / Retail Sales / Industrial Prod
* Market Holiday: None
* Non-Standard Settlement Days: {SK} KR: 20/7
* Markets
{AU} AU: +9.7 bps | {JN} JP: +91 bps | {CH} CH: -202.4 bps | {HK} HK: +24.4 bps
1D Chg - Brent: +79.4 bps | Gold: -7.8 bps | Bitcoin: +48.5 bps
* ETFs Overnight
PREMIUM: KR +53bps JP +34bps ID +45bps MY +24bps PH +5bps
DISCOUNT: FXI CHINA -12bps EEM -1bps HK -41bps TW -27bps TH -6bps AU -9bps
* Market Overview

```

(The block ends after `* Market Overview` with one trailing empty line for the user to write into.)

## File Structure

- `config.yaml` — all tickers, flag codes, ETF list, calendar filters. No secrets.
- `fixtures/sample_data.yaml` — the fixture that reproduces the template exactly.
- `src/formatting.py` — pure functions: bps conversion/rounding, line builders, bucket split.
- `src/sections/macro.py`, `holidays.py`, `settlement.py`, `markets.py`, `etfs.py` — one output block each.
- `src/bloomberg.py` — thin `xbbg`/`blpapi` wrapper + fixture loader for dry-run.
- `src/report.py` — orchestrates sections, assembles final text, graceful degradation.
- `clipboard.py` — OS-isolated copy (Windows `clip`, Mac `pbcopy`).
- `market_color.py` — CLI entry point.
- `tests/test_formatting.py`, `tests/test_report.py` — Mac-runnable, no Terminal.
- `requirements.txt`, `README.md`, `.gitignore`.

Data-shape contract used across all section modules (established in Task 2, consumed everywhere):
each section function takes a `data: dict` (the fetched/fixture values) and the loaded `config: dict`,
and returns a `str` (one or more lines, no trailing newline). `report.py` joins section strings with `\n`.

---

### Task 1: Project scaffolding, config, fixture, .gitignore

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `config.yaml`
- Create: `fixtures/sample_data.yaml`
- Create: `src/__init__.py`
- Create: `src/sections/__init__.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `config.yaml` and `fixtures/sample_data.yaml` on disk with the exact keys below; every later task reads these.

- [ ] **Step 1: Create `requirements.txt`**

```
# Bloomberg data (Windows runtime only; installed separately on the PC — see README)
blpapi
xbbg
PyYAML>=6.0
pytest>=8.0
# Windows clipboard helper (no-op import guard on Mac)
pywin32; sys_platform == "win32"
```

- [ ] **Step 2: Create `.gitignore`**

```
__pycache__/
*.pyc
*.log
.venv/
venv/
env/
config.local.yaml
.pytest_cache/
.DS_Store
```

- [ ] **Step 3: Create `config.yaml`**

```yaml
flags:
  KR: "{SK}"
  JP: "{JN}"
  CH: "{CH}"
  AU: "{AU}"
  HK: "{HK}"
indices:
  AU: {ticker: "AS51 Index",   label: "AU"}
  JP: {ticker: "NKY Index",    label: "JP"}
  CH: {ticker: "SHCOMP Index", label: "CH"}
  HK: {ticker: "HSI Index",    label: "HK"}
commodities:
  Brent:   "CO1 Comdty"
  Gold:    "XAU Curncy"
  Bitcoin: "XBT Curncy"
etfs:
  - {label: "KR",        ticker: "EWY US Equity"}
  - {label: "JP",        ticker: "EWJ US Equity"}
  - {label: "ID",        ticker: "EIDO US Equity"}
  - {label: "MY",        ticker: "EWM US Equity"}
  - {label: "PH",        ticker: "EPHE US Equity"}
  - {label: "FXI CHINA", ticker: "FXI US Equity"}
  - {label: "EEM",       ticker: "EEM US Equity"}
  - {label: "HK",        ticker: "EWH US Equity"}
  - {label: "TW",        ticker: "EWT US Equity"}
  - {label: "TH",        ticker: "THD US Equity"}
  - {label: "AU",        ticker: "EWA US Equity"}
macro:
  countries: [KR, JP, CH]
holidays:
  exchanges: [KR, JP, CH, HK, AU]
```

- [ ] **Step 4: Create `fixtures/sample_data.yaml`**

This is the single source of truth for `--dry-run`. Values are chosen to reproduce the template exactly.
Note `indices`/`commodities` hold **percent** values (bps = pct×100). ETF values are already in **bps**
(computed premium/discount), so the fixture stores them as bps directly to keep the fixture readable;
`etfs.py` will branch on dry-run vs live (see Task 6).

```yaml
macro:
  - {country: "KR", event: "Employment Data"}
  - {country: "JP", event: "Core Machine Orders"}
  - {country: "CH", event: "GDP / Retail Sales / Industrial Prod"}
holidays: []            # empty -> "None"
settlement:
  - {country: "KR", date: "20/7"}
indices:                # percent change
  AU: 0.097
  JP: 0.91
  CH: -2.024
  HK: 0.244
commodities:            # percent change
  Brent: 0.794
  Gold: -0.078
  Bitcoin: 0.485
etfs_bps:               # premium/discount already in bps (dry-run shortcut)
  KR: 53
  JP: 34
  ID: 45
  MY: 24
  PH: 5
  FXI CHINA: -12
  EEM: -1
  HK: -41
  TW: -27
  TH: -6
  AU: -9
```

- [ ] **Step 5: Create empty `src/__init__.py` and `src/sections/__init__.py`**

Both files are empty.

- [ ] **Step 6: Verify YAML parses**

Run: `python -c "import yaml; yaml.safe_load(open('config.yaml')); yaml.safe_load(open('fixtures/sample_data.yaml')); print('ok')"`
Expected: `ok`

- [ ] **Step 7: Commit**

```bash
git add requirements.txt .gitignore config.yaml fixtures/sample_data.yaml src/__init__.py src/sections/__init__.py
git commit -m "chore: scaffold config, fixture, and gitignore"
```

---

### Task 2: Core formatting primitives (bps + rounding)

**Files:**
- Create: `src/formatting.py`
- Test: `tests/test_formatting.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `fmt_bps_1dp(pct: float) -> str` — pct→bps, 1 decimal, drop trailing `.0`, sign always shown. E.g. `0.91 -> "+91"`, `0.097 -> "+9.7"`, `-2.024 -> "-202.4"`.
  - `fmt_bps_int(bps: float) -> str` — round to int, sign always shown. E.g. `53 -> "+53"`, `-12 -> "-12"`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_formatting.py
from src.formatting import fmt_bps_1dp, fmt_bps_int

def test_fmt_bps_1dp_drops_trailing_zero():
    assert fmt_bps_1dp(0.91) == "+91"

def test_fmt_bps_1dp_keeps_decimal():
    assert fmt_bps_1dp(0.097) == "+9.7"

def test_fmt_bps_1dp_negative():
    assert fmt_bps_1dp(-2.024) == "-202.4"

def test_fmt_bps_1dp_zero_is_positive_sign():
    assert fmt_bps_1dp(0.0) == "+0"

def test_fmt_bps_int_positive():
    assert fmt_bps_int(53) == "+53"

def test_fmt_bps_int_negative():
    assert fmt_bps_int(-12) == "-12"

def test_fmt_bps_int_rounds():
    assert fmt_bps_int(4.6) == "+5"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_formatting.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.formatting'` (or ImportError).

- [ ] **Step 3: Write minimal implementation**

```python
# src/formatting.py
"""Pure formatting helpers. MUST NOT import blpapi/xbbg/OS-specific modules."""


def _drop_trailing_zero(value: float) -> str:
    """Round to 1 decimal, drop a trailing '.0'."""
    s = f"{value:.1f}"
    if s.endswith(".0"):
        s = s[:-2]
    return s


def fmt_bps_1dp(pct: float) -> str:
    """Percent change -> bps string, 1 decimal, trailing .0 dropped, sign always shown."""
    bps = pct * 100
    sign = "+" if bps >= 0 else "-"
    return f"{sign}{_drop_trailing_zero(abs(bps))}"


def fmt_bps_int(bps: float) -> str:
    """Bps value -> integer bps string, sign always shown."""
    rounded = round(bps)
    sign = "+" if rounded >= 0 else "-"
    return f"{sign}{abs(rounded)}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_formatting.py -v`
Expected: PASS (7 passed).

- [ ] **Step 5: Commit**

```bash
git add src/formatting.py tests/test_formatting.py
git commit -m "feat: add bps formatting primitives"
```

---

### Task 3: Line builders for each output block (pure)

**Files:**
- Modify: `src/formatting.py`
- Test: `tests/test_formatting.py`

**Interfaces:**
- Consumes: `fmt_bps_1dp`, `fmt_bps_int` from Task 2; `N_A = "N/A"` sentinel defined here.
- Produces (all pure, no Bloomberg):
  - `N_A: str = "N/A"`.
  - `build_macro(rows: list[dict], flags: dict) -> str` — each row `{country, event}` → `"{FLAG} CC: event"`, lines joined by `\n`. Missing flag → country code with no brace token.
  - `build_holiday(rows: list[dict], flags: dict) -> str` — `"* Market Holiday: None"` if empty, else `"* Market Holiday: {FLAG} CC: name"` joined by `; `.
  - `build_settlement(rows: list[dict], flags: dict) -> str` — `"* Non-Standard Settlement Days: None"` if empty else `"* Non-Standard Settlement Days: {FLAG} CC: D/M"` joined by `; `.
  - `build_markets(indices: dict, flags: dict, order: list[str]) -> str` — for each key in `order`, `"{FLAG} CC: <fmt_bps_1dp> bps"`; value `None`→`N_A`; joined by ` | `.
  - `build_commodities(comm: dict, order: list[str]) -> str` — `"1D Chg - Name: <fmt_bps_1dp> bps"` per name in `order`; value `None`→`N_A`; joined by ` | `.
  - `build_etfs(etf_bps: dict, order: list[str]) -> tuple[str, str]` — returns `(premium_line, discount_line)`; split by sign (`>= 0` premium), preserve `order`; `"PREMIUM: LABEL <fmt_bps_int>bps ..."` / `"DISCOUNT: ..."`; entries with `None` value are skipped.

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/test_formatting.py
from src.formatting import (
    build_macro, build_holiday, build_settlement,
    build_markets, build_commodities, build_etfs, N_A,
)

FLAGS = {"KR": "{SK}", "JP": "{JN}", "CH": "{CH}", "AU": "{AU}", "HK": "{HK}"}

def test_build_macro():
    rows = [
        {"country": "KR", "event": "Employment Data"},
        {"country": "JP", "event": "Core Machine Orders"},
        {"country": "CH", "event": "GDP / Retail Sales / Industrial Prod"},
    ]
    assert build_macro(rows, FLAGS) == (
        "{SK} KR: Employment Data\n"
        "{JN} JP: Core Machine Orders\n"
        "{CH} CH: GDP / Retail Sales / Industrial Prod"
    )

def test_build_holiday_none():
    assert build_holiday([], FLAGS) == "* Market Holiday: None"

def test_build_holiday_one():
    assert build_holiday([{"country": "HK", "name": "Some Day"}], FLAGS) == \
        "* Market Holiday: {HK} HK: Some Day"

def test_build_settlement_one():
    assert build_settlement([{"country": "KR", "date": "20/7"}], FLAGS) == \
        "* Non-Standard Settlement Days: {SK} KR: 20/7"

def test_build_settlement_none():
    assert build_settlement([], FLAGS) == "* Non-Standard Settlement Days: None"

def test_build_markets():
    indices = {"AU": 0.097, "JP": 0.91, "CH": -2.024, "HK": 0.244}
    assert build_markets(indices, FLAGS, ["AU", "JP", "CH", "HK"]) == \
        "{AU} AU: +9.7 bps | {JN} JP: +91 bps | {CH} CH: -202.4 bps | {HK} HK: +24.4 bps"

def test_build_markets_missing_value():
    indices = {"AU": None, "JP": 0.91, "CH": -2.024, "HK": 0.244}
    out = build_markets(indices, FLAGS, ["AU", "JP", "CH", "HK"])
    assert "{AU} AU: N/A" in out

def test_build_commodities():
    comm = {"Brent": 0.794, "Gold": -0.078, "Bitcoin": 0.485}
    assert build_commodities(comm, ["Brent", "Gold", "Bitcoin"]) == \
        "1D Chg - Brent: +79.4 bps | Gold: -7.8 bps | Bitcoin: +48.5 bps"

def test_build_etfs():
    order = ["KR", "JP", "ID", "MY", "PH", "FXI CHINA", "EEM", "HK", "TW", "TH", "AU"]
    etf_bps = {"KR": 53, "JP": 34, "ID": 45, "MY": 24, "PH": 5,
               "FXI CHINA": -12, "EEM": -1, "HK": -41, "TW": -27, "TH": -6, "AU": -9}
    prem, disc = build_etfs(etf_bps, order)
    assert prem == "PREMIUM: KR +53bps JP +34bps ID +45bps MY +24bps PH +5bps"
    assert disc == "DISCOUNT: FXI CHINA -12bps EEM -1bps HK -41bps TW -27bps TH -6bps AU -9bps"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_formatting.py -v`
Expected: FAIL — ImportError for the new `build_*` names.

- [ ] **Step 3: Write minimal implementation (append to `src/formatting.py`)**

```python
N_A = "N/A"


def _flag(cc: str, flags: dict) -> str:
    return flags.get(cc, "")


def _prefix(cc: str, flags: dict) -> str:
    """'{FLAG} CC' or just 'CC' when no flag configured."""
    f = _flag(cc, flags)
    return f"{f} {cc}" if f else cc


def build_macro(rows: list[dict], flags: dict) -> str:
    return "\n".join(f"{_prefix(r['country'], flags)}: {r['event']}" for r in rows)


def build_holiday(rows: list[dict], flags: dict) -> str:
    if not rows:
        return "* Market Holiday: None"
    body = "; ".join(f"{_prefix(r['country'], flags)}: {r['name']}" for r in rows)
    return f"* Market Holiday: {body}"


def build_settlement(rows: list[dict], flags: dict) -> str:
    if not rows:
        return "* Non-Standard Settlement Days: None"
    body = "; ".join(f"{_prefix(r['country'], flags)}: {r['date']}" for r in rows)
    return f"* Non-Standard Settlement Days: {body}"


def build_markets(indices: dict, flags: dict, order: list[str]) -> str:
    parts = []
    for cc in order:
        val = indices.get(cc)
        chg = N_A if val is None else f"{fmt_bps_1dp(val)} bps"
        parts.append(f"{_prefix(cc, flags)}: {chg}")
    return " | ".join(parts)


def build_commodities(comm: dict, order: list[str]) -> str:
    parts = []
    for name in order:
        val = comm.get(name)
        chg = N_A if val is None else f"{fmt_bps_1dp(val)} bps"
        parts.append(f"{name}: {chg}")
    return "1D Chg - " + " | ".join(parts)


def build_etfs(etf_bps: dict, order: list[str]) -> tuple[str, str]:
    prem, disc = [], []
    for label in order:
        val = etf_bps.get(label)
        if val is None:
            continue
        entry = f"{label} {fmt_bps_int(val)}bps"
        (prem if val >= 0 else disc).append(entry)
    return "PREMIUM: " + " ".join(prem), "DISCOUNT: " + " ".join(disc)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_formatting.py -v`
Expected: PASS (all formatting tests green).

- [ ] **Step 5: Commit**

```bash
git add src/formatting.py tests/test_formatting.py
git commit -m "feat: add pure line builders for each output block"
```

---

### Task 4: Bloomberg wrapper + fixture loader

**Files:**
- Create: `src/bloomberg.py`

**Interfaces:**
- Consumes: `fixtures/sample_data.yaml` (Task 1).
- Produces:
  - `load_fixture(path: str = "fixtures/sample_data.yaml") -> dict` — returns parsed fixture dict.
  - `fetch_live(config: dict) -> dict` — returns a dict with the SAME top-level shape the section
    modules expect: keys `macro` (list), `holidays` (list), `settlement` (list), `indices` (dict cc→pct),
    `commodities` (dict name→pct), and `etf_prices` (dict label→{"px": float, "nav": float}). Uses `xbbg`.
    Wrapped so an import failure or connection error raises `BloombergError`.
  - `class BloombergError(Exception)`.
- Note: `fetch_live` returns `etf_prices` (px+nav) while the fixture provides `etfs_bps`. Task 6 (`etfs.py`)
  reconciles both shapes.

- [ ] **Step 1: Write `src/bloomberg.py`**

```python
"""Bloomberg access layer. Live path uses xbbg; dry-run path loads a YAML fixture.

Only this module (and clipboard.py) touch platform/Terminal-specific code, so the rest
of the pipeline runs unchanged on Mac via load_fixture().
"""
import yaml


class BloombergError(Exception):
    pass


def load_fixture(path: str = "fixtures/sample_data.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _bdp(tickers, flds):
    """Import xbbg lazily so Mac/dry-run never needs blpapi installed."""
    try:
        from xbbg import blp
    except Exception as exc:  # ImportError or blpapi load failure
        raise BloombergError(f"xbbg/blpapi unavailable: {exc}") from exc
    try:
        return blp.bdp(tickers=tickers, flds=flds)
    except Exception as exc:
        raise BloombergError(f"Bloomberg query failed: {exc}") from exc


def fetch_live(config: dict) -> dict:
    """Fetch every field needed for the report. Field-level failures are handled by the
    section modules; this returns whatever came back and lets sections map to N/A."""
    idx_tickers = {v["ticker"]: cc for cc, v in config["indices"].items()}
    comm_tickers = {t: name for name, t in config["commodities"].items()}
    etf_tickers = {e["ticker"]: e["label"] for e in config["etfs"]}

    # CHG_PCT_1D returns percent (e.g. 0.91 == +0.91%).
    idx_df = _bdp(list(idx_tickers), ["CHG_PCT_1D"])
    comm_df = _bdp(list(comm_tickers), ["CHG_PCT_1D"])
    etf_df = _bdp(list(etf_tickers), ["PX_LAST", "FUND_NET_ASSET_VAL"])

    def _cell(df, ticker, field):
        try:
            return float(df.loc[ticker, field.lower()])
        except Exception:
            return None

    indices = {cc: _cell(idx_df, t, "CHG_PCT_1D") for t, cc in idx_tickers.items()}
    commodities = {name: _cell(comm_df, t, "CHG_PCT_1D") for t, name in comm_tickers.items()}
    etf_prices = {
        label: {"px": _cell(etf_df, t, "PX_LAST"), "nav": _cell(etf_df, t, "FUND_NET_ASSET_VAL")}
        for t, label in etf_tickers.items()
    }
    return {
        "macro": [],          # populated by macro.py via calendar query (Task 5)
        "holidays": [],       # populated by holidays.py (Task 5)
        "settlement": [],     # populated by settlement.py (Task 5)
        "indices": indices,
        "commodities": commodities,
        "etf_prices": etf_prices,
    }
```

- [ ] **Step 2: Verify fixture loads**

Run: `python -c "from src.bloomberg import load_fixture; d=load_fixture(); print(sorted(d.keys()))"`
Expected: prints a list including `commodities`, `etfs_bps`, `holidays`, `indices`, `macro`, `settlement`.

- [ ] **Step 3: Commit**

```bash
git add src/bloomberg.py
git commit -m "feat: add Bloomberg wrapper and fixture loader"
```

---

### Task 5: Section modules — macro, holidays, settlement, markets

**Files:**
- Create: `src/sections/macro.py`
- Create: `src/sections/holidays.py`
- Create: `src/sections/settlement.py`
- Create: `src/sections/markets.py`

**Interfaces:**
- Consumes: builders from `src/formatting.py` (Task 3); `data` dict + `config` dict.
- Produces (each pure-ish, no direct Bloomberg import — they read from the passed `data`):
  - `macro.render(data: dict, config: dict) -> str` → the three macro lines (no `* Macro` header; report.py adds it).
  - `holidays.render(data: dict, config: dict) -> str` → the `* Market Holiday: ...` line.
  - `settlement.render(data: dict, config: dict) -> str` → the `* Non-Standard Settlement Days: ...` line.
  - `markets.render(data: dict, config: dict) -> str` → the two Markets lines (index line + `1D Chg` line), joined by `\n` (no `* Markets` header).

- [ ] **Step 1: Create `src/sections/macro.py`**

```python
from src.formatting import build_macro


def render(data: dict, config: dict) -> str:
    return build_macro(data.get("macro", []), config["flags"])
```

- [ ] **Step 2: Create `src/sections/holidays.py`**

```python
from src.formatting import build_holiday


def render(data: dict, config: dict) -> str:
    return build_holiday(data.get("holidays", []), config["flags"])
```

- [ ] **Step 3: Create `src/sections/settlement.py`**

```python
from src.formatting import build_settlement


def render(data: dict, config: dict) -> str:
    return build_settlement(data.get("settlement", []), config["flags"])
```

- [ ] **Step 4: Create `src/sections/markets.py`**

```python
from src.formatting import build_markets, build_commodities


def render(data: dict, config: dict) -> str:
    order = list(config["indices"].keys())
    idx_line = build_markets(data.get("indices", {}), config["flags"], order)
    comm_order = list(config["commodities"].keys())
    comm_line = build_commodities(data.get("commodities", {}), comm_order)
    return f"{idx_line}\n{comm_line}"
```

- [ ] **Step 5: Smoke-test against the fixture**

Run:
```bash
python -c "
import yaml
from src.bloomberg import load_fixture
from src.sections import macro, holidays, settlement, markets
cfg = yaml.safe_load(open('config.yaml')); d = load_fixture()
print(macro.render(d, cfg))
print(holidays.render(d, cfg))
print(settlement.render(d, cfg))
print(markets.render(d, cfg))
"
```
Expected (exactly):
```
{SK} KR: Employment Data
{JN} JP: Core Machine Orders
{CH} CH: GDP / Retail Sales / Industrial Prod
* Market Holiday: None
* Non-Standard Settlement Days: {SK} KR: 20/7
{AU} AU: +9.7 bps | {JN} JP: +91 bps | {CH} CH: -202.4 bps | {HK} HK: +24.4 bps
1D Chg - Brent: +79.4 bps | Gold: -7.8 bps | Bitcoin: +48.5 bps
```

- [ ] **Step 6: Commit**

```bash
git add src/sections/macro.py src/sections/holidays.py src/sections/settlement.py src/sections/markets.py
git commit -m "feat: add macro, holidays, settlement, and markets sections"
```

---

### Task 6: ETF section (handles both fixture-bps and live px/nav shapes)

**Files:**
- Create: `src/sections/etfs.py`
- Test: `tests/test_formatting.py` (add ETF-compute test) — or a new `tests/test_etfs.py`

**Interfaces:**
- Consumes: `build_etfs` from Task 3; `data` dict; `config` dict.
- Produces:
  - `compute_bps(px: float, nav: float) -> float | None` — `(px/nav - 1) * 10000`; returns `None` if
    either input is `None` or `nav` is `0`.
  - `render(data: dict, config: dict) -> str` — returns premium line + discount line joined by `\n`
    (no `* ETFs Overnight` header). If `data` has `etfs_bps` (fixture), use it directly; else compute
    from `data["etf_prices"]` (live).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_etfs.py
import yaml
from src.bloomberg import load_fixture
from src.sections.etfs import compute_bps, render

def test_compute_bps():
    # px 10.53 on nav 10.00 -> +530 ... use a clean case
    assert round(compute_bps(101.0, 100.0), 1) == 100.0
    assert compute_bps(None, 100.0) is None
    assert compute_bps(100.0, 0) is None

def test_render_from_fixture():
    cfg = yaml.safe_load(open("config.yaml"))
    d = load_fixture()
    out = render(d, cfg)
    assert out == (
        "PREMIUM: KR +53bps JP +34bps ID +45bps MY +24bps PH +5bps\n"
        "DISCOUNT: FXI CHINA -12bps EEM -1bps HK -41bps TW -27bps TH -6bps AU -9bps"
    )

def test_render_from_live_shape():
    cfg = yaml.safe_load(open("config.yaml"))
    # minimal live-shaped data: one premium, one discount
    cfg = {"flags": cfg["flags"], "etfs": [
        {"label": "KR", "ticker": "EWY US Equity"},
        {"label": "HK", "ticker": "EWH US Equity"},
    ]}
    d = {"etf_prices": {
        "KR": {"px": 100.53, "nav": 100.0},   # +53 bps
        "HK": {"px": 99.59, "nav": 100.0},     # -41 bps
    }}
    out = render(d, cfg)
    assert out == "PREMIUM: KR +53bps\nDISCOUNT: HK -41bps"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_etfs.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.sections.etfs'`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/sections/etfs.py
from src.formatting import build_etfs


def compute_bps(px, nav):
    if px is None or nav is None or nav == 0:
        return None
    return (px / nav - 1) * 10000


def render(data: dict, config: dict) -> str:
    order = [e["label"] for e in config["etfs"]]
    if "etfs_bps" in data:                       # fixture / dry-run shortcut
        etf_bps = data["etfs_bps"]
    else:                                        # live px/nav
        prices = data.get("etf_prices", {})
        etf_bps = {
            label: compute_bps(prices.get(label, {}).get("px"),
                               prices.get(label, {}).get("nav"))
            for label in order
        }
    prem, disc = build_etfs(etf_bps, order)
    return f"{prem}\n{disc}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_etfs.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add src/sections/etfs.py tests/test_etfs.py
git commit -m "feat: add ETF premium/discount section"
```

---

### Task 7: Report assembler with graceful degradation

**Files:**
- Create: `src/report.py`
- Test: `tests/test_report.py`

**Interfaces:**
- Consumes: all five section modules; `data` dict; `config` dict.
- Produces:
  - `build_report(data: dict, config: dict, logger=None) -> str` — assembles the full block with headers,
    matching the template byte-for-byte. Each section is wrapped in try/except: on exception it substitutes
    a per-section `N/A` placeholder line and logs via `logger` (if provided), never raising.
  - Section-to-header mapping is fixed (see implementation). Final output ends with `* Market Overview\n`
    (header + trailing newline for the user's prose).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_report.py
import yaml
from src.bloomberg import load_fixture
from src.report import build_report

EXPECTED = (
    "Good morning!\n"
    "* Macro\n"
    "{SK} KR: Employment Data\n"
    "{JN} JP: Core Machine Orders\n"
    "{CH} CH: GDP / Retail Sales / Industrial Prod\n"
    "* Market Holiday: None\n"
    "* Non-Standard Settlement Days: {SK} KR: 20/7\n"
    "* Markets\n"
    "{AU} AU: +9.7 bps | {JN} JP: +91 bps | {CH} CH: -202.4 bps | {HK} HK: +24.4 bps\n"
    "1D Chg - Brent: +79.4 bps | Gold: -7.8 bps | Bitcoin: +48.5 bps\n"
    "* ETFs Overnight\n"
    "PREMIUM: KR +53bps JP +34bps ID +45bps MY +24bps PH +5bps\n"
    "DISCOUNT: FXI CHINA -12bps EEM -1bps HK -41bps TW -27bps TH -6bps AU -9bps\n"
    "* Market Overview\n"
)

def test_dry_run_matches_template_byte_for_byte():
    cfg = yaml.safe_load(open("config.yaml"))
    data = load_fixture()
    assert build_report(data, cfg) == EXPECTED

def test_section_failure_degrades_to_placeholder():
    cfg = yaml.safe_load(open("config.yaml"))
    data = load_fixture()
    del data["indices"]          # markets.render will still run (uses .get) -> N/A values, not crash
    data["commodities"] = None   # force a real exception inside the markets section
    out = build_report(data, cfg)
    assert "* Markets\nN/A" in out   # placeholder substituted, report still whole
    assert out.endswith("* Market Overview\n")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_report.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.report'`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/report.py
from src.sections import macro, holidays, settlement, markets, etfs

# (header_line_or_None, render_fn, n_placeholder_lines)
_SECTIONS = [
    ("* Macro", macro.render, 1),
    (None, holidays.render, 1),          # holidays.render already emits its own '* ...' line
    (None, settlement.render, 1),
    ("* Markets", markets.render, 1),
    ("* ETFs Overnight", etfs.render, 1),
]


def _safe(render_fn, data, config, placeholder_lines, logger):
    try:
        return render_fn(data, config)
    except Exception as exc:
        if logger:
            logger.warning("section %s failed: %s", render_fn.__module__, exc)
        return "\n".join(["N/A"] * placeholder_lines)


def build_report(data: dict, config: dict, logger=None) -> str:
    lines = ["Good morning!"]
    for header, fn, n_ph in _SECTIONS:
        if header:
            lines.append(header)
        lines.append(_safe(fn, data, config, n_ph, logger))
    lines.append("* Market Overview")
    return "\n".join(lines) + "\n"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_report.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Run the full suite**

Run: `python -m pytest -v`
Expected: all tests pass (formatting + etfs + report).

- [ ] **Step 6: Commit**

```bash
git add src/report.py tests/test_report.py
git commit -m "feat: add report assembler with graceful degradation"
```

---

### Task 8: Clipboard helper (OS-isolated)

**Files:**
- Create: `clipboard.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `copy_to_clipboard(text: str) -> bool` — copies via `clip` on Windows, `pbcopy` on Mac;
  returns `True` on success, `False` (never raises) if no clipboard mechanism is available.

- [ ] **Step 1: Write `clipboard.py`**

```python
"""OS-isolated clipboard copy. Never raises — returns False if unavailable."""
import subprocess
import sys


def copy_to_clipboard(text: str) -> bool:
    try:
        if sys.platform == "win32":
            proc = subprocess.Popen(["clip"], stdin=subprocess.PIPE)
            proc.communicate(input=text.encode("utf-16-le"))
            return proc.returncode == 0
        if sys.platform == "darwin":
            proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            proc.communicate(input=text.encode("utf-8"))
            return proc.returncode == 0
    except Exception:
        return False
    return False
```

- [ ] **Step 2: Smoke test on Mac**

Run: `python -c "from clipboard import copy_to_clipboard; print(copy_to_clipboard('test123'))"; pbpaste`
Expected: prints `True` then `test123`.

- [ ] **Step 3: Commit**

```bash
git add clipboard.py
git commit -m "feat: add OS-isolated clipboard helper"
```

---

### Task 9: CLI entry point

**Files:**
- Create: `market_color.py`

**Interfaces:**
- Consumes: `load_fixture`/`fetch_live` (Task 4), `build_report` (Task 7), `copy_to_clipboard` (Task 8).
- Produces: `python market_color.py [--dry-run] [--config PATH] [--no-clip]` — prints the report,
  copies to clipboard (unless `--no-clip`), logs failures to `market_color.log`.

- [ ] **Step 1: Write `market_color.py`**

```python
#!/usr/bin/env python3
"""Generate the Morning Asia Market Color block and copy it to the clipboard.

Usage:
  python market_color.py            # live Bloomberg fetch (Windows + Terminal)
  python market_color.py --dry-run  # use fixture; runs anywhere, no Terminal
"""
import argparse
import logging
import sys

import yaml

from src.bloomberg import load_fixture, fetch_live, BloombergError
from src.report import build_report
from clipboard import copy_to_clipboard

logging.basicConfig(
    filename="market_color.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("market_color")


def main() -> int:
    parser = argparse.ArgumentParser(description="Morning Asia Market Color generator")
    parser.add_argument("--dry-run", action="store_true", help="use fixture data, no Bloomberg")
    parser.add_argument("--config", default="config.yaml", help="path to config.yaml")
    parser.add_argument("--no-clip", action="store_true", help="do not copy to clipboard")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh)

    if args.dry_run:
        data = load_fixture()
    else:
        try:
            data = fetch_live(config)
        except BloombergError as exc:
            logger.error("Bloomberg connection failed: %s", exc)
            print(f"ERROR: could not reach Bloomberg: {exc}", file=sys.stderr)
            print("Is the Terminal running and logged in? Try --dry-run to test formatting.",
                  file=sys.stderr)
            return 2

    report = build_report(data, config, logger=logger)
    print(report, end="")

    if not args.no_clip:
        if copy_to_clipboard(report):
            print("\n[copied to clipboard]", file=sys.stderr)
        else:
            print("\n[clipboard unavailable — copy manually]", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run dry-run end-to-end**

Run: `python market_color.py --dry-run --no-clip`
Expected: prints the exact template block (matching `EXPECTED` from Task 7).

- [ ] **Step 3: Verify dry-run output equals template via diff**

Run:
```bash
python market_color.py --dry-run --no-clip > /tmp/out.txt
printf 'Good morning!\n* Macro\n{SK} KR: Employment Data\n{JN} JP: Core Machine Orders\n{CH} CH: GDP / Retail Sales / Industrial Prod\n* Market Holiday: None\n* Non-Standard Settlement Days: {SK} KR: 20/7\n* Markets\n{AU} AU: +9.7 bps | {JN} JP: +91 bps | {CH} CH: -202.4 bps | {HK} HK: +24.4 bps\n1D Chg - Brent: +79.4 bps | Gold: -7.8 bps | Bitcoin: +48.5 bps\n* ETFs Overnight\nPREMIUM: KR +53bps JP +34bps ID +45bps MY +24bps PH +5bps\nDISCOUNT: FXI CHINA -12bps EEM -1bps HK -41bps TW -27bps TH -6bps AU -9bps\n* Market Overview\n' > /tmp/expected.txt
diff /tmp/out.txt /tmp/expected.txt && echo "BYTE-FOR-BYTE MATCH"
```
Expected: `BYTE-FOR-BYTE MATCH` with no diff output.

- [ ] **Step 4: Commit**

```bash
git add market_color.py
git commit -m "feat: add CLI entry point with --dry-run"
```

---

### Task 10: Live-data section stubs — macro / holidays / settlement calendar pulls

**Files:**
- Modify: `src/bloomberg.py`
- Create: `src/sections/calendar_live.py`

**Interfaces:**
- Consumes: `config` dict; `xbbg`/`blpapi`.
- Produces:
  - `calendar_live.fetch_macro(config) -> list[dict]` — ECO calendar events for `config["macro"]["countries"]`
    for today, each `{country, event}`. Returns `[]` and logs on failure.
  - `calendar_live.fetch_holidays(config) -> list[dict]` — today's exchange holidays for
    `config["holidays"]["exchanges"]`, each `{country, name}`. Returns `[]` on failure.
  - `calendar_live.fetch_settlement(config) -> list[dict]` — non-standard settlement days, each
    `{country, date}` in `D/M`. Returns `[]` on failure (per approved fallback).
  - `bloomberg.fetch_live` updated to call these three and populate `macro`/`holidays`/`settlement`.

Note: exact Bloomberg calendar field names are entitlement-dependent and cannot be validated on Mac.
Each function is written defensively (broad try/except → `[]`) so an unavailable/renamed field degrades to
an empty section rather than crashing. The user verifies/adjusts field names on the Windows PC (README covers this).

- [ ] **Step 1: Create `src/sections/calendar_live.py`**

```python
"""Live Bloomberg calendar pulls (macro / holidays / settlement).

Field names here are entitlement-dependent and must be verified on the Terminal PC.
Every function degrades to [] on any failure so the report never crashes.
"""
import logging

logger = logging.getLogger("market_color")


def _blp():
    from xbbg import blp
    return blp


def fetch_macro(config: dict) -> list:
    countries = config.get("macro", {}).get("countries", [])
    try:
        blp = _blp()
        # NOTE: verify the correct economic-calendar accessor/field for your entitlement.
        # Placeholder structure; adjust on the Terminal PC per README troubleshooting.
        events = blp.earning  # sentinel attribute access is replaced during PC verification
        raise NotImplementedError("verify ECO calendar field on Terminal PC")
    except Exception as exc:
        logger.warning("macro calendar fetch failed, using empty: %s", exc)
        return []


def fetch_holidays(config: dict) -> list:
    exchanges = config.get("holidays", {}).get("exchanges", [])
    try:
        blp = _blp()
        raise NotImplementedError("verify holiday calendar field on Terminal PC")
    except Exception as exc:
        logger.warning("holiday fetch failed, using empty: %s", exc)
        return []


def fetch_settlement(config: dict) -> list:
    try:
        blp = _blp()
        raise NotImplementedError("verify settlement calendar field on Terminal PC")
    except Exception as exc:
        logger.warning("settlement fetch failed, using empty: %s", exc)
        return []
```

- [ ] **Step 2: Wire into `fetch_live` (modify `src/bloomberg.py`)**

Replace the three placeholder lines in the returned dict:

```python
    from src.sections import calendar_live
    return {
        "macro": calendar_live.fetch_macro(config),
        "holidays": calendar_live.fetch_holidays(config),
        "settlement": calendar_live.fetch_settlement(config),
        "indices": indices,
        "commodities": commodities,
        "etf_prices": etf_prices,
    }
```

- [ ] **Step 3: Verify dry-run still passes (no live calls on Mac)**

Run: `python -m pytest -v && python market_color.py --dry-run --no-clip | head -1`
Expected: all tests pass; first line `Good morning!`.

- [ ] **Step 4: Commit**

```bash
git add src/bloomberg.py src/sections/calendar_live.py
git commit -m "feat: add live calendar-pull stubs with graceful fallback"
```

---

### Task 11: README + final repo polish

**Files:**
- Create: `README.md`

**Interfaces:**
- Consumes: nothing.
- Produces: setup + run + troubleshooting docs.

- [ ] **Step 1: Write `README.md`**

````markdown
# Asia Morning Market Color

Generates a "Morning Asia Market Color" text block from Bloomberg data and copies it to the
clipboard, formatted for pasting into Bloomberg chat.

## Prerequisites (Windows runtime PC)

- Bloomberg Terminal installed, **running, and logged in**.
- Python 3.11.
- `blpapi` installed (Bloomberg-hosted wheel):
  ```
  python -m pip install --index-url=https://blpapi.bloomberg.com/repository/releases/python/simple/ blpapi
  ```
- Remaining deps: `python -m pip install -r requirements.txt`

## Setup

```
git clone <your-repo-url>
cd asia-market-color
python -m pip install -r requirements.txt
```

## Run

```
python market_color.py            # live Bloomberg fetch (Windows + Terminal)
python market_color.py --dry-run  # fixture data; runs on Mac, no Terminal
python market_color.py --no-clip  # print only, don't touch clipboard
```

The block prints to the console and is copied to the clipboard. The `* Market Overview`
section is left blank for you to write.

## Editing config

All tickers, flag codes, the ETF list, and calendar filters live in `config.yaml` — edit there,
never in code. Copy to `config.local.yaml` (gitignored) if you need machine-specific overrides.

## Formatting conventions

- `bps = pct_change × 100`.
- Markets / `1D Chg` lines: 1 decimal, trailing `.0` dropped, sign always shown.
- ETF lines: integer bps, no space before `bps`.
- ETFs split into PREMIUM (≥0) / DISCOUNT (<0) by sign; order follows `config.yaml`.

## Testing (works on Mac, no Terminal)

```
python -m pytest -v
python market_color.py --dry-run --no-clip
```

## Troubleshooting Bloomberg connection

- **`could not reach Bloomberg` / BloombergError:** Terminal not running or not logged in. Open the
  Terminal, log in, then retry. Use `--dry-run` to confirm formatting independently.
- **Empty Macro / Holiday / Settlement sections:** the calendar field names in
  `src/sections/calendar_live.py` are entitlement-dependent and must be verified on your Terminal.
  Check `market_color.log` for the logged field error and adjust the accessor.
- **ETF PREMIUM/DISCOUNT all `N/A`:** `FUND_NET_ASSET_VAL` may be unavailable for a ticker/entitlement;
  confirm the field in the Terminal (FLDS) and update `config.yaml`.
- **Bitcoin wrong/blank:** swap `XBT Curncy` for `XBTUSD Curncy` in `config.yaml` per your entitlement.
- All field-level failures are logged to `market_color.log` and render as `N/A` — the report never crashes.

## Security

Never commit credentials or entitlement/account identifiers. `.gitignore` excludes `config.local.yaml`
and `*.log`.
````

- [ ] **Step 2: Final full-suite + dry-run check**

Run: `python -m pytest -v && python market_color.py --dry-run --no-clip | diff - /tmp/expected.txt && echo OK`
Expected: tests pass, `OK`.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add README with setup, run, and Bloomberg troubleshooting"
```

---

## Self-Review Notes

**Spec coverage:** Bloomberg-only source (Task 4/10), plain-text + clipboard (Task 8/9), manual run + `--dry-run` (Task 9), blank Market Overview / no LLM (Task 7), no trades (read-only fetch only), config-file for all mappings (Task 1), one-function-per-section modularity (Task 5/6), graceful `N/A` degradation + logging (Task 7/10), fixture reproducing template (Task 1), formatting tests (Task 2/3), Windows/Mac isolation (Task 4/8), README + requirements + .gitignore + no-secrets (Task 1/11), bps convention + rounding (Task 2/3). All covered.

**Placeholder scan:** The only intentional stubs are the three live calendar pulls (Task 10), which are documented as entitlement-dependent and must be verified on the Terminal PC — they degrade to `[]` and are covered by README troubleshooting. This is a real-world constraint (fields can't be validated on Mac), not a plan gap.

**Type consistency:** `data` dict keys (`macro`, `holidays`, `settlement`, `indices`, `commodities`, `etf_prices`/`etfs_bps`) are consistent across `bloomberg.py`, section modules, and `report.py`. Builder signatures match between `formatting.py` definitions and section-module call sites.
