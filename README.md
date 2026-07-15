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
