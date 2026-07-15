#!/usr/bin/env python3
"""Generate the Morning Asia Market Color block and copy it to the clipboard.

Usage:
  python market_color.py            # live Bloomberg fetch (Windows + Terminal)
  python market_color.py --dry-run  # use fixture; runs anywhere, no Terminal
"""
import argparse
import logging
import sys

import yaml

from src.bloomberg import load_fixture, fetch_live, BloombergError
from src.report import build_report
from clipboard import copy_to_clipboard

logging.basicConfig(
    filename="market_color.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("market_color")


def main() -> int:
    parser = argparse.ArgumentParser(description="Morning Asia Market Color generator")
    parser.add_argument("--dry-run", action="store_true", help="use fixture data, no Bloomberg")
    parser.add_argument("--config", default="config.yaml", help="path to config.yaml")
    parser.add_argument("--no-clip", action="store_true", help="do not copy to clipboard")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh)

    if args.dry_run:
        data = load_fixture()
    else:
        try:
            data = fetch_live(config)
        except BloombergError as exc:
            logger.error("Bloomberg connection failed: %s", exc)
            print(f"ERROR: could not reach Bloomberg: {exc}", file=sys.stderr)
            print("Is the Terminal running and logged in? Try --dry-run to test formatting.",
                  file=sys.stderr)
            return 2

    report = build_report(data, config, logger=logger)
    print(report, end="")

    if not args.no_clip:
        if copy_to_clipboard(report):
            print("\n[copied to clipboard]", file=sys.stderr)
        else:
            print("\n[clipboard unavailable — copy manually]", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
