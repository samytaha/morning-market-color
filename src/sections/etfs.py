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
