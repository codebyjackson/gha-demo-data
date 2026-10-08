"""Turn data/coffee.csv into dist/stats.json for the site repo to publish."""
import csv
import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

SRC = Path("data/coffee.csv")
OUT = Path("dist/stats.json")
CUPS_COLUMN = "cups"


def main():
    by_team = defaultdict(int)
    by_day = defaultdict(int)
    rows = 0
    with SRC.open(newline="") as f:
        for row in csv.DictReader(f):
            cups = int(row[CUPS_COLUMN])
            by_team[row["team"]] += cups
            by_day[row["date"]] += cups
            rows += 1

    stats = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": {
            "repo": os.environ.get("GITHUB_REPOSITORY", "local"),
            "run_id": os.environ.get("GITHUB_RUN_ID", ""),
            "sha": os.environ.get("GITHUB_SHA", "local")[:7],
        },
        "rows": rows,
        "total_cups": sum(by_team.values()),
        "by_team": dict(sorted(by_team.items(), key=lambda kv: -kv[1])),
        "by_day": dict(sorted(by_day.items())),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(stats, indent=2))
    print(f"Wrote {OUT}: {rows} rows, {stats['total_cups']} cups")


if __name__ == "__main__":
    main()
