"""Sanity-check stats.json before anything gets published."""
import json
import sys
from pathlib import Path


def main(path):
    stats = json.loads(Path(path).read_text())
    problems = []
    if stats.get("rows", 0) == 0:
        problems.append("the CSV has no rows")
    if any(cups < 0 for cups in stats["by_team"].values()):
        problems.append("a team has a negative number of cups")
    if sum(stats["by_team"].values()) != stats["total_cups"]:
        problems.append("team totals don't add up to total_cups")
    if sum(stats["by_day"].values()) != stats["total_cups"]:
        problems.append("daily totals don't add up to total_cups")

    if problems:
        for problem in problems:
            # ::error:: lines show up as annotations on the run page
            print(f"::error file={path}::{problem}")
        sys.exit(1)
    print(f"OK: {stats['rows']} rows, {stats['total_cups']} cups across {len(stats['by_team'])} teams")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dist/stats.json")
