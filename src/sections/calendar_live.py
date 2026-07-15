"""Live Bloomberg calendar pulls (macro / holidays / settlement).

Field names here are entitlement-dependent and must be verified on the Terminal PC.
Every function degrades to [] on any failure so the report never crashes.
"""
import logging

logger = logging.getLogger("market_color")


def _blp():
    """Lazy-import xbbg.blp to avoid import cycles on Mac."""
    from xbbg import blp
    return blp


def fetch_macro(config: dict) -> list:
    """Return today's ECO-calendar events for config['macro']['countries'] as [{country, event}].

    STUB: the correct economic-calendar accessor/field is entitlement-dependent and must be
    verified on the Bloomberg Terminal PC (see README troubleshooting). Until then this degrades
    to [] so the report renders with an empty Macro section rather than crashing.
    """
    try:
        raise NotImplementedError("verify ECO calendar field on Terminal PC")
    except Exception as exc:
        logger.warning("macro calendar fetch failed, using empty: %s", exc)
        return []


def fetch_holidays(config: dict) -> list:
    """Return today's exchange holidays for config['holidays']['exchanges'] as [{country, name}].

    STUB: the correct holiday-calendar accessor/field is entitlement-dependent and must be
    verified on the Bloomberg Terminal PC (see README troubleshooting). Until then this degrades
    to [] so the report renders with an empty Holidays section rather than crashing.
    """
    try:
        raise NotImplementedError("verify holiday calendar field on Terminal PC")
    except Exception as exc:
        logger.warning("holiday fetch failed, using empty: %s", exc)
        return []


def fetch_settlement(config: dict) -> list:
    """Return non-standard settlement days as [{country, date}] in D/M format.

    STUB: the correct settlement-calendar accessor/field is entitlement-dependent and must be
    verified on the Bloomberg Terminal PC (see README troubleshooting). Until then this degrades
    to [] so the report renders with an empty Settlement section rather than crashing.
    """
    try:
        raise NotImplementedError("verify settlement calendar field on Terminal PC")
    except Exception as exc:
        logger.warning("settlement fetch failed, using empty: %s", exc)
        return []
