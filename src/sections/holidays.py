from src.formatting import build_holiday


def render(data: dict, config: dict) -> str:
    return build_holiday(data.get("holidays", []), config["flags"])
