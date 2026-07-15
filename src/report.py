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
