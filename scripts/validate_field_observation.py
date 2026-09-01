"""Validate a Route2Zero field-observation CSV before controlled ingestion."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import date
from pathlib import Path


EXPECTED_COLUMNS = [
    "route_id",
    "route_long_name",
    "validation_status",
    "active_status",
    "validation_date",
    "validator",
    "source_type",
    "source_reference",
    "notes",
    "observed_origin",
    "observed_destination",
    "observed_headway_min",
    "observed_service_window_hrs",
    "geometry_verified",
    "operator_name_if_verified",
    "evidence_quality",
]
VALIDATION_STATUSES = {
    "historic_only",
    "current",
    "desk_checked",
    "operator_confirmed",
    "lgu_confirmed",
    "field_checked",
    "conflicting_evidence",
}
ACTIVE_STATUSES = {"active", "inactive", "uncertain"}
EVIDENCE_QUALITIES = {
    "historic_only",
    "osm_desk_observed",
    "field_observed",
    "operator_confirmed",
    "lgu_confirmed",
    "conflicting",
}
ROUTE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]+$")


def add_error(errors: list[dict[str, object]], row_number: int, field: str, message: str) -> None:
    errors.append({"row": row_number, "field": field, "message": message})


def parse_optional_number(value: str, row_number: int, field: str, minimum: float, maximum: float, errors: list[dict[str, object]]) -> None:
    if not value.strip():
        return
    try:
        number = float(value)
    except ValueError:
        add_error(errors, row_number, field, "must be a number or blank")
        return
    if number < minimum or number > maximum:
        add_error(errors, row_number, field, f"must be between {minimum:g} and {maximum:g}")


def validate(path: Path) -> dict[str, object]:
    errors: list[dict[str, object]] = []
    warnings: list[dict[str, object]] = []
    rows_checked = 0
    route_ids: set[str] = set()
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            columns = reader.fieldnames or []
            if len(columns) != len(set(columns)):
                duplicates = sorted({column for column in columns if columns.count(column) > 1})
                add_error(errors, 1, "header", f"duplicate column(s): {', '.join(duplicates)}")
            if columns != EXPECTED_COLUMNS:
                missing = [column for column in EXPECTED_COLUMNS if column not in columns]
                extra = [column for column in columns if column not in EXPECTED_COLUMNS]
                if missing:
                    add_error(errors, 1, "header", f"missing column(s): {', '.join(missing)}")
                if extra:
                    add_error(errors, 1, "header", f"unsupported column(s); possible personal data: {', '.join(extra)}")
                if not missing and not extra and columns != EXPECTED_COLUMNS:
                    add_error(errors, 1, "header", "columns are in the wrong order; use the published template")
            for row_number, row in enumerate(reader, start=2):
                rows_checked += 1
                route_id = (row.get("route_id") or "").strip()
                if not route_id:
                    add_error(errors, row_number, "route_id", "is required")
                elif not ROUTE_ID_PATTERN.fullmatch(route_id):
                    add_error(errors, row_number, "route_id", "may contain only letters, numbers, underscore, dot, colon, or hyphen")
                if route_id in route_ids:
                    warnings.append({"row": row_number, "field": "route_id", "message": "route has more than one observation; retain the date and source for audit"})
                route_ids.add(route_id)
                for field in ("route_long_name", "validation_status", "active_status", "validation_date", "validator", "source_type", "source_reference", "geometry_verified", "evidence_quality"):
                    if not (row.get(field) or "").strip():
                        add_error(errors, row_number, field, "is required")
                if (row.get("validation_status") or "").strip() not in VALIDATION_STATUSES:
                    add_error(errors, row_number, "validation_status", f"must be one of: {', '.join(sorted(VALIDATION_STATUSES))}")
                if (row.get("active_status") or "").strip() not in ACTIVE_STATUSES:
                    add_error(errors, row_number, "active_status", f"must be one of: {', '.join(sorted(ACTIVE_STATUSES))}")
                observed_date = (row.get("validation_date") or "").strip()
                if observed_date:
                    try:
                        parsed_date = date.fromisoformat(observed_date)
                        if parsed_date > date.today():
                            add_error(errors, row_number, "validation_date", "cannot be in the future")
                    except ValueError:
                        add_error(errors, row_number, "validation_date", "must use ISO format YYYY-MM-DD")
                geometry = (row.get("geometry_verified") or "").strip().lower()
                if geometry not in {"true", "false", "1", "0"}:
                    add_error(errors, row_number, "geometry_verified", "must be true, false, 1, or 0")
                quality = (row.get("evidence_quality") or "").strip()
                if quality not in EVIDENCE_QUALITIES:
                    add_error(errors, row_number, "evidence_quality", f"must be one of: {', '.join(sorted(EVIDENCE_QUALITIES))}")
                parse_optional_number(row.get("observed_headway_min") or "", row_number, "observed_headway_min", 0, 1440, errors)
                parse_optional_number(row.get("observed_service_window_hrs") or "", row_number, "observed_service_window_hrs", 0, 24, errors)
    except FileNotFoundError:
        add_error(errors, 0, "input", f"file not found: {path}")
    except UnicodeDecodeError:
        add_error(errors, 0, "input", "file must be UTF-8 encoded")
    except csv.Error as error:
        add_error(errors, 0, "input", f"invalid CSV: {error}")
    return {
        "valid": not errors,
        "input": str(path),
        "rows_checked": rows_checked,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Route2Zero field-observation CSV")
    parser.add_argument("--input", required=True, type=Path, help="CSV file to validate")
    args = parser.parse_args()
    result = validate(args.input)
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
