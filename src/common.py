"""Shared paths and deterministic helpers for the Route2Zero pipeline."""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd

from adapters import MetroManilaGTFSAdapter


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "gtfs_master"
PROCESSED_DIR = ROOT / "data" / "processed"
DOCS_DIR = ROOT / "docs"
CONFIG_DIR = ROOT / "config"
VALIDATED_DIR = ROOT / "data" / "validated"
MODELS_DIR = ROOT / "models"

CLAIM_STATUSES = {
    "VERIFIED",
    "OBSERVED",
    "DERIVED",
    "ML_ESTIMATED",
    "PROXY",
    "SCENARIO",
    "NEUTRAL_PRIOR",
    "MISSING",
}


def validate_claim_status_columns(
    frame: pd.DataFrame,
    columns: Iterable[str] | None = None,
) -> list[str]:
    """Reject claim labels outside the shared measurement-status vocabulary."""
    selected = list(columns) if columns is not None else [
        column for column in frame.columns if column.endswith("claim_status")
    ]
    for column in selected:
        if column not in frame.columns:
            raise ValueError(f"Required claim-status column is missing: {column}")
        invalid = sorted(set(frame[column].dropna().astype(str)) - CLAIM_STATUSES)
        if invalid:
            raise ValueError(f"Invalid values in {column}: {invalid}")
    return selected

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
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATED_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)


def load_gtfs(name: str, **kwargs) -> pd.DataFrame:
    """Read one immutable GTFS file with identifiers preserved as strings."""
    return MetroManilaGTFSAdapter(ROOT).load_table(name, **kwargs)


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
    def json_safe(value: object) -> object:
        if isinstance(value, dict):
            return {key: json_safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [json_safe(item) for item in value]
        if isinstance(value, float) and not math.isfinite(value):
            return None
        return value

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(json_safe(payload), indent=2, ensure_ascii=False, allow_nan=False))


def normalize_text_newlines(path: Path) -> None:
    """Rewrite a generated text artifact with platform-independent LF endings."""
    data = path.read_bytes()
    normalized = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    if normalized != data:
        path.write_bytes(normalized)


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_hash(payload: object, length: int = 12) -> str:
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:length]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_corridor_name(value: object) -> str:
    """Return a stable corridor group key without inferring a current franchise."""
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode()
    text = re.sub(r"\b(via|route|loop|puj)\b.*$", "", text, flags=re.IGNORECASE)
    parts = [re.sub(r"[^a-z0-9]+", "-", part.lower()).strip("-") for part in text.split("-")]
    parts = sorted(part for part in parts if part)
    return "__".join(parts) or "unknown-corridor"


def parse_grade(value: object) -> int:
    return {"A": 4, "B": 3, "C": 2, "D": 1}.get(str(value).strip().upper(), 0)
