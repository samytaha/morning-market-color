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
