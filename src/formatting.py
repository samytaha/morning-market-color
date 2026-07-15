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
