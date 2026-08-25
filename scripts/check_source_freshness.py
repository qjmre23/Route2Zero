import argparse
import json
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config" / "source_registry.json"
THRESHOLDS = {"current": 120, "mixed": 120, "rolling": 45}


def parse_args():
    parser = argparse.ArgumentParser(description="Fail when operational source snapshots or rolling evidence ledgers are stale.")
    parser.add_argument("--as-of", default=date.today().isoformat(), help="Date used for the freshness check (YYYY-MM-DD).")
    return parser.parse_args()


def main():
    args = parse_args()
    as_of = datetime.strptime(args.as_of, "%Y-%m-%d").date()
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    checked = []
    stale = []
    exempt = []

    for source in registry["sources"]:
        status = str(source.get("currentness", "")).lower()
        item = {
            "source_id": source["source_id"],
            "currentness": status,
            "retrieval_date": source.get("retrieval_date"),
        }
        if status not in THRESHOLDS:
            exempt.append(item)
            continue
        retrieved = datetime.strptime(source["retrieval_date"], "%Y-%m-%d").date()
        item["age_days"] = (as_of - retrieved).days
        item["maximum_age_days"] = THRESHOLDS[status]
        checked.append(item)
        if item["age_days"] > item["maximum_age_days"]:
            stale.append(item)

    result = {
        "as_of": as_of.isoformat(),
        "status": "FAIL" if stale else "PASS",
        "checked": checked,
        "historic_or_other_exempt": exempt,
        "stale": stale,
    }
    print(json.dumps(result, indent=2))
    raise SystemExit(1 if stale else 0)


if __name__ == "__main__":
    main()
