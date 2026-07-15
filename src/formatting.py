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
    formatted_magnitude = _drop_trailing_zero(abs(bps))
    sign = "-" if bps < 0 and formatted_magnitude != "0" else "+"
    return f"{sign}{formatted_magnitude}"


def fmt_bps_int(bps: float) -> str:
    """Bps value -> integer bps string, sign always shown."""
    rounded = round(bps)
    sign = "+" if rounded >= 0 else "-"
    return f"{sign}{abs(rounded)}"


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
        r = round(val)
        entry = f"{label} {fmt_bps_int(val)}bps"
        (prem if r >= 0 else disc).append(entry)
    prem_line = ("PREMIUM: " + " ".join(prem)) if prem else "PREMIUM:"
    disc_line = ("DISCOUNT: " + " ".join(disc)) if disc else "DISCOUNT:"
    return prem_line, disc_line
