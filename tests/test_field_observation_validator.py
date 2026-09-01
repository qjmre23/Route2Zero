import csv

from scripts.validate_field_observation import EXPECTED_COLUMNS, validate


def write_observations(path, rows, columns=EXPECTED_COLUMNS):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def test_field_observation_template_accepts_a_complete_row(tmp_path):
    row = {column: "" for column in EXPECTED_COLUMNS}
    row.update(
        {
            "route_id": "LTFRB_PUJ1353",
            "route_long_name": "Francisco Homes - Cubao",
            "validation_status": "field_checked",
            "active_status": "active",
            "validation_date": "2026-08-20",
            "validator": "Team Larpers field lead",
            "source_type": "field_log",
            "source_reference": "field-log-2026-08-20.pdf",
            "geometry_verified": "true",
            "evidence_quality": "field_observed",
            "observed_headway_min": "12",
            "observed_service_window_hrs": "15.5",
        }
    )
    path = tmp_path / "observations.csv"
    write_observations(path, [row])
    result = validate(path)
    assert result["valid"] is True
    assert result["rows_checked"] == 1


def test_field_observation_validator_rejects_unsupported_columns(tmp_path):
    path = tmp_path / "unsafe.csv"
    write_observations(path, [], EXPECTED_COLUMNS + ["rider_phone"])
    result = validate(path)
    assert result["valid"] is False
    assert any("possible personal data" in item["message"] for item in result["errors"])
