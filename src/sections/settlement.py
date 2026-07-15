from src.formatting import build_settlement


def render(data: dict, config: dict) -> str:
    return build_settlement(data.get("settlement", []), config["flags"])
