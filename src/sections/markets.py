from src.formatting import build_markets, build_commodities


def render(data: dict, config: dict) -> str:
    order = list(config["indices"].keys())
    idx_line = build_markets(data.get("indices", {}), config["flags"], order)
    comm_order = list(config["commodities"].keys())
    comm_line = build_commodities(data.get("commodities", {}), comm_order)
    return f"{idx_line}\n{comm_line}"
