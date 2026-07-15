# Asia Morning Market Color Generator — Design

**Date:** 2026-07-16
**Status:** Approved (design phase)

## Purpose

A manually-run Python script that generates a "Morning Asia Market Color" plain-text
block for pasting into Bloomberg chat. All market data is pulled programmatically from
the Bloomberg API (`blpapi` + `xbbg`) on a licensed Bloomberg Terminal. Output is printed
to the console and copied to the clipboard, formatted to match a fixed template exactly.

The narrative "Market Overview" paragraph is authored by the user, not generated. No LLM
is called. This is read-only market data — no trades, no orders.

## Deployment context

- **Authoring/review:** MacBook.
- **Runtime:** Windows PC at the user's company with Bloomberg Terminal running and logged in.
- **Delivery:** GitHub — clean repo pushed from Mac, `git clone` / `git pull` on the Windows PC.
- OS-specific code (clipboard, blpapi connection) is isolated so `--dry-run` runs fully on Mac.
- **No credentials or entitlement/account identifiers are ever committed.**

## Confirmed decisions

1. **ETF premium/discount = Option A:** compute `(PX_LAST / FUND_NET_ASSET_VAL − 1)`, expressed in bps.
2. **Flag codes** (`{XX}`) are literal Bloomberg-chat flag tokens, stored per-market in config.
3. **bps convention:** `bps = pct_change × 100` (e.g. +0.91% → `91 bps`; +0.097% → `9.7 bps`).
4. **Rounding:** 1 decimal but drop a trailing `.0` on the Markets and `1D Chg` lines
   (`91.0` → `91`, `9.7` → `9.7`, `202.4` → `202.4`); ETF lines render as **integer** bps.
5. **Macro calendar:** Bloomberg ECO/economic calendar, filtered to countries `[KR, JP, CH]`.
6. **Holidays & non-standard settlement days = Option A:** pulled from Bloomberg exchange
   calendar fields, with graceful fallback to `N/A` (logged) if a field proves unreliable.
7. **Environment:** Python 3.11; `blpapi` already installed on the Windows PC; Terminal access present.

## Output template (must match byte-for-byte in `--dry-run`)

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
<leave blank for me to write>
```

Notes on template mechanics:
- Markets/commodities line: sign always shown (`+`/`-`), space before `bps`, joined by ` | `.
- ETF lines: sign always shown, **no space** before `bps`, joined by single spaces; the bucket
  keyword (`PREMIUM:` / `DISCOUNT:`) prefixes each line.
- "Market Holiday: None" when no holiday; otherwise `{FLAG} XX: <name>`.
- Settlement day date format is `D/M` (e.g. `20/7`).

## Architecture

```
asia-market-color/
├── market_color.py          # entry point: arg parsing (--dry-run), orchestration, print + clipboard
├── config.yaml              # ALL tickers, flag codes, ETF list, calendar filters — no secrets
├── src/
│   ├── __init__.py
│   ├── bloomberg.py         # thin blpapi/xbbg wrapper: fetch(tickers, fields) -> dict; connection handling
│   ├── sections/
│   │   ├── macro.py         # ECO calendar -> "* Macro" lines
│   │   ├── holidays.py      # exchange holiday calendar -> "* Market Holiday"
│   │   ├── settlement.py    # non-standard settlement days -> "* Non-Standard Settlement Days"
│   │   ├── markets.py       # index CHG_PCT_1D + commodities/crypto -> "* Markets" + "1D Chg"
│   │   └── etfs.py          # PX_LAST / FUND_NET_ASSET_VAL -> premium/discount buckets
│   ├── formatting.py        # PURE functions: bps conversion, rounding, line assembly (no Bloomberg import)
│   └── report.py            # calls each section, assembles final text, applies graceful degradation
├── fixtures/
│   └── sample_data.yaml     # fixture dataset so --dry-run reproduces the template exactly
├── tests/
│   ├── test_formatting.py   # bps math, rounding, bucket sorting
│   └── test_report.py       # dry-run output == template, byte-for-byte
├── clipboard.py             # OS-isolated: Windows clip (pywin32/subprocess), Mac pbcopy fallback
├── requirements.txt
├── README.md
└── .gitignore
```

### Isolation rationale

- `formatting.py` is pure and imports nothing OS/Bloomberg-specific → unit-testable on Mac.
- `bloomberg.py` and `clipboard.py` are the only Terminal/OS-dependent modules.
- `--dry-run` substitutes the fixture loader for `bloomberg.py`, so the entire pipeline downstream
  of data fetch is exercised identically on Mac and Windows.

## Config shape (`config.yaml`)

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
etfs:                     # display order preserved within each bucket
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

### ETF bucketing behavior

Config order is preserved *within* each bucket. At runtime each ETF is placed in PREMIUM
(value ≥ 0) or DISCOUNT (value < 0) by the sign of its computed premium/discount. If a ticker
flips sign on a given morning, it simply moves buckets; the relative config order is retained.

## bps / rounding rules

- `bps = pct_change × 100`.
- **Markets line + `1D Chg` line:** round to 1 decimal, then drop a trailing `.0`. Sign always shown.
  Space before `bps`. Fields joined by ` | `.
- **ETF lines:** round to integer bps. Sign always shown. No space before `bps`. Fields joined by single spaces.
- ETF premium/discount from Option A: `(PX_LAST / FUND_NET_ASSET_VAL − 1) × 10000` bps.

## Data flow & error handling

`report.py` orchestrates: it calls each section function independently. Every section wraps its
Bloomberg fetch in try/except. On failure, the **specific field** renders as `N/A`
(e.g. `Gold: N/A`), the failure is logged to `market_color.log`, and the report continues —
a single failed field never crashes the whole report (graceful degradation).

`--dry-run` loads `fixtures/sample_data.yaml` instead of connecting to Bloomberg; the downstream
assembly path is identical, and its output must equal the template byte-for-byte.

## Testing

- `tests/test_formatting.py` — pure math: bps conversion, "drop trailing .0" rounding, ETF integer
  rounding, premium/discount bucket split and ordering. No Bloomberg connection.
- `tests/test_report.py` — full `--dry-run` assembly must equal the template byte-for-byte.
- Both run on Mac with no Terminal.

## Known risks / open items

- **Non-standard settlement days (Option A)** is the hardest pull — there is no single clean field for
  "T+n is non-standard today." `settlement.py` queries the exchange settlement calendar and compares
  against the standard cycle; if the field proves unreliable it falls back to `N/A` with a logged
  warning rather than blocking the report. (User-approved fallback.)
- **`XBT Curncy`** for Bitcoin may differ by entitlement (`XBTUSD Curncy` on some terminals). It is
  config-driven so it can be swapped on the Windows PC without code changes.

## Non-goals (YAGNI)

- No scheduler/service — manual `python market_color.py` only.
- No LLM / generated narrative — "Market Overview" is left blank for the user.
- No trading, orders, or writes to Bloomberg.
- No free/public data fallback — Bloomberg is the sole data source.
