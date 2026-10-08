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
    team_days = defaultdict(set)
    first_line = {}
    table = defaultdict(dict)  # the CSV as a grid: table[date][team] = cups
    rows = 0
    with SRC.open(newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        for column in ("date", "team", CUPS_COLUMN):
            if column not in header:
                print(f"::error file={SRC.as_posix()},line=1::"
                      f"Column '{column}' not found. The header has: {', '.join(header)}")
                raise SystemExit(1)
        # Line 1 is the header, so the first data row is line 2.
        for line_no, row in enumerate(reader, start=2):
            raw = row[CUPS_COLUMN]
            try:
                cups = int(raw)
            except ValueError:
                # ::error lines become annotations that point at the exact line in the CSV
                print(f"::error file={SRC.as_posix()},line={line_no}::"
                      f"'{raw}' is not a whole number of cups ({row['date']}, {row['team']})")
                raise SystemExit(1)
            by_team[row["team"]] += cups
            by_day[row["date"]] += cups
            team_days[row["team"]].add(row["date"])
            first_line.setdefault(row["team"], line_no)
            table[row["date"]][row["team"]] = cups
            rows += 1

    # Every team should have a row for every day. A misspelled team name breaks this twice:
    # the new name appears on one day, and the real team is missing that day.
    days = set(by_day)
    gaps = sorted((len(seen), team) for team, seen in team_days.items() if seen != days)
    for count, team in gaps:
        missing = ", ".join(sorted(days - team_days[team]))
        print(f"::error file={SRC.as_posix()},line={first_line[team]}::"
              f"Team '{team}' has rows for {count} of {len(days)} days (missing {missing})")
    if gaps:
        raise SystemExit(1)

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
        "teams": sorted(first_line, key=first_line.get),  # in the order they appear in the CSV
        "table": dict(sorted(table.items())),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(stats, indent=2))
    print(f"Wrote {OUT}: {rows} rows, {stats['total_cups']} cups")


if __name__ == "__main__":
    main()
