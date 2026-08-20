"""Create a deterministic reliability assessment for every screening geometry."""

from __future__ import annotations

import math
import sys

import geopandas as gpd
import pandas as pd
from pyproj import Geod

from common import PROCESSED_DIR, ROOT, ensure_output_dirs


GEOD = Geod(ellps="WGS84")


def distance_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    _, _, metres = GEOD.inv(a[0], a[1], b[0], b[1])
    return abs(float(metres)) / 1000.0


def grade(score: float) -> str:
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 50:
        return "C"
    return "D"


def score_geometry(row: pd.Series, field_verified: bool = False) -> dict[str, object]:
    geometry = row.geometry
    coords = list(geometry.coords) if geometry is not None and not geometry.is_empty else []
    valid = bool(geometry is not None and not geometry.is_empty and geometry.is_valid and len(coords) >= 2)
    endpoint = distance_km(coords[0], coords[-1]) if valid else math.nan
    length = float(row.get("length_km", math.nan))
    detour = length / endpoint if valid and endpoint > 0.05 else math.nan
    duplicate_fraction = 1.0 - len(set(coords)) / len(coords) if coords else 1.0
    gaps = [distance_km(coords[index - 1], coords[index]) for index in range(1, len(coords))]
    max_gap = max(gaps) if gaps else math.nan
    score = 88.0 if row.get("geometry_source") == "shape" else 52.0
    reasons: list[str] = [
        "GTFS shape source" if row.get("geometry_source") == "shape" else "ordered-stop planning approximation"
    ]
    if int(row.get("stop_count", 0) or 0) >= 12:
        score += 4
    else:
        score -= 8
        reasons.append("few representative stops")
    if pd.notna(detour) and detour > 4:
        score -= 15
        reasons.append("extreme detour ratio")
    elif pd.notna(detour) and detour > 2.5:
        score -= 7
        reasons.append("high detour ratio")
    if pd.notna(max_gap) and max_gap > 8:
        score -= 14
        reasons.append("large consecutive-stop gap")
    elif pd.notna(max_gap) and max_gap > 4:
        score -= 6
        reasons.append("moderate consecutive-stop gap")
    if duplicate_fraction > 0.1:
        score -= 6
        reasons.append("duplicate coordinates")
    if valid and not geometry.is_simple:
        score -= 8
        reasons.append("self-intersection detected")
    if not valid:
        score = 0
        reasons.append("invalid or disconnected geometry")
    if field_verified:
        score = max(score, 92)
        reasons.append("field geometry verified")
    score = round(max(0.0, min(100.0, score)), 2)
    return {
        "endpoint_distance_km": round(endpoint, 3) if pd.notna(endpoint) else math.nan,
        "geometry_detour_ratio": round(detour, 3) if pd.notna(detour) else math.nan,
        "duplicate_stop_fraction": round(duplicate_fraction, 4),
        "max_consecutive_stop_gap_km": round(max_gap, 3) if pd.notna(max_gap) else math.nan,
        "geometry_valid": valid,
        "self_intersection_flag": bool(valid and not geometry.is_simple),
        "geometry_reliability_score": score,
        "geometry_reliability_grade": grade(score),
        "geometry_reliability_reasons": " | ".join(reasons),
        "geometry_validation_required": not field_verified and score < 85,
        "geometry_claim_status": "VERIFIED" if field_verified else "DERIVED",
    }


def main() -> int:
    ensure_output_dirs()
    routes = gpd.read_file(PROCESSED_DIR / "jeepney_routes.geojson")
    ledger_path = ROOT / "data" / "validated" / "route_validation.csv"
    ledger = pd.read_csv(ledger_path, dtype={"route_id": str})
    verified = set(
        ledger.loc[ledger.get("geometry_verified", pd.Series(dtype=object)).astype(str).str.lower().eq("true"), "route_id"]
    ) if not ledger.empty else set()
    rows = []
    for _, route in routes.iterrows():
        rows.append({"route_id": route["route_id"], "geometry_source": route["geometry_source"], **score_geometry(route, route["route_id"] in verified)})
    output = pd.DataFrame(rows)
    output.to_csv(PROCESSED_DIR / "geometry_reliability.csv", index=False)
    print(f"[PASS] geometry reliability: {len(output):,} routes; verified={len(verified)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
