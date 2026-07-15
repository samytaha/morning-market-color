from src.formatting import build_macro


def render(data: dict, config: dict) -> str:
    return build_macro(data.get("macro", []), config["flags"])
