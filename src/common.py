"""Shared paths and deterministic helpers for the Route2Zero pipeline."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Iterable

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "gtfs_master"
PROCESSED_DIR = ROOT / "data" / "processed"
DOCS_DIR = ROOT / "docs"

GTFS_FILES = (
    "routes.txt",
    "trips.txt",
    "stops.txt",
    "stop_times.txt",
    "shapes.txt",
    "frequencies.txt",
    "calendar.txt",
    "agency.txt",
)


def ensure_output_dirs() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)


def load_gtfs(name: str, **kwargs) -> pd.DataFrame:
    """Read one immutable GTFS file with identifiers preserved as strings."""
    if name not in GTFS_FILES:
        raise ValueError(f"Unexpected GTFS file: {name}")
    return pd.read_csv(RAW_DIR / name, dtype=str, low_memory=False, **kwargs)


def minmax_score(values: pd.Series) -> pd.Series:
    """Return a 0-100 min-max score while preserving missing values."""
    numeric = pd.to_numeric(values, errors="coerce")
    valid = numeric.dropna()
    if valid.empty:
        return pd.Series(float("nan"), index=values.index, dtype=float)
    lo, hi = float(valid.min()), float(valid.max())
    if math.isclose(lo, hi):
        result = pd.Series(float("nan"), index=values.index, dtype=float)
        result.loc[numeric.notna()] = 50.0
        return result
    return ((numeric - lo) / (hi - lo) * 100.0).clip(0, 100)


def parse_gtfs_time(value: object) -> float:
    """Parse HH:MM:SS, including GTFS hours above 24, into seconds."""
    if value is None or pd.isna(value):
        return float("nan")
    parts = str(value).strip().split(":")
    if len(parts) != 3:
        return float("nan")
    try:
        hours, minutes, seconds = (int(float(part)) for part in parts)
    except ValueError:
        return float("nan")
    return float(hours * 3600 + minutes * 60 + seconds)


def merge_intervals(intervals: Iterable[tuple[float, float]]) -> float:
    """Return total seconds covered by the union of valid intervals."""
    clean = sorted(
        (float(start), float(end))
        for start, end in intervals
        if pd.notna(start) and pd.notna(end) and float(end) > float(start)
    )
    if not clean:
        return float("nan")
    total = 0.0
    current_start, current_end = clean[0]
    for start, end in clean[1:]:
        if start <= current_end:
            current_end = max(current_end, end)
        else:
            total += current_end - current_start
            current_start, current_end = start, end
    return total + current_end - current_start


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

