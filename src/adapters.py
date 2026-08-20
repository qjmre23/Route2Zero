"""Small, explicit city/source adapters used by the Route2Zero pipeline.

The analytical stages depend on these interfaces rather than assuming that every
future city uses Metro Manila file names or evidence schemas.  Adapters never
invent missing evidence: optional layers return ``None`` or an empty, schema-
correct frame.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd


GTFS_FILES = {
    "routes.txt",
    "trips.txt",
    "stops.txt",
    "stop_times.txt",
    "shapes.txt",
    "frequencies.txt",
    "calendar.txt",
    "agency.txt",
}

CHARGING_EVIDENCE_COLUMNS = [
    "route_id", "site_name", "evidence_date", "site_lat", "site_lon",
    "site_control_verified", "utility_capacity_verified", "available_capacity_kw",
    "source_reference", "verifier", "notes",
]

OPERATOR_EVIDENCE_COLUMNS = [
    "route_id", "operator_name", "evidence_date", "verified_fleet_size",
    "depot_control_score", "financing_score", "organizational_capacity_score",
    "maintenance_capability_score", "willingness_to_participate_score",
    "modernization_experience_score", "charging_site_access_score",
    "source_reference", "verifier", "notes",
]


class GTFSAdapter(ABC):
    """Interface for a city's immutable GTFS screening universe."""

    @abstractmethod
    def load_table(self, name: str, **kwargs: object) -> pd.DataFrame:
        """Load one supported GTFS table with identifiers preserved as strings."""


class PopulationLayerAdapter(ABC):
    """Interface for an optional population-exposure layer."""

    @property
    @abstractmethod
    def raster_path(self) -> Path:
        """Return the configured population raster path."""

    @property
    def available(self) -> bool:
        return self.raster_path.is_file()


class ChargingEvidenceAdapter(ABC):
    """Interface for optional mapped infrastructure and validated site evidence."""

    @abstractmethod
    def load_snapshot(self) -> dict | None:
        """Return a mapped-infrastructure snapshot, or ``None`` when absent."""

    @abstractmethod
    def load_site_evidence(self) -> pd.DataFrame:
        """Return the charging evidence ledger, possibly empty."""


class OperatorEvidenceAdapter(ABC):
    """Interface for consent-based operator evidence."""

    @abstractmethod
    def load_evidence(self) -> pd.DataFrame:
        """Return the operator evidence ledger, possibly empty."""


class CityBoundaryAdapter(ABC):
    """Interface for route-to-city attribution."""

    @abstractmethod
    def cities_for_route(self, description: object, route_name: object) -> list[str]:
        """Return ordered city labels without implying spatial verification."""

    @property
    @abstractmethod
    def method(self) -> str:
        """Return the attribution method label exposed in outputs."""

    @property
    @abstractmethod
    def boundary_source_id(self) -> str:
        """Return the registered boundary source ID, blank when unavailable."""


class MetroManilaGTFSAdapter(GTFSAdapter):
    def __init__(self, root: Path):
        self.directory = root / "data" / "raw" / "gtfs_master"

    def load_table(self, name: str, **kwargs: object) -> pd.DataFrame:
        if name not in GTFS_FILES:
            raise ValueError(f"Unexpected GTFS file: {name}")
        return pd.read_csv(self.directory / name, dtype=str, low_memory=False, **kwargs)


class MetroManilaPopulationAdapter(PopulationLayerAdapter):
    def __init__(self, root: Path):
        self._raster_path = root / "data" / "raw" / "reference" / "phl_ppp_2020_1km_Aggregated.tif"

    @property
    def raster_path(self) -> Path:
        return self._raster_path


class MetroManilaChargingAdapter(ChargingEvidenceAdapter):
    def __init__(self, root: Path):
        self.snapshot_path = root / "data" / "raw" / "osm_power" / "metro_manila_overpass.json"
        self.ledger_path = root / "data" / "validated" / "charging_site_evidence.csv"

    def load_snapshot(self) -> dict | None:
        if not self.snapshot_path.is_file():
            return None
        return json.loads(self.snapshot_path.read_text(encoding="utf-8"))

    def load_site_evidence(self) -> pd.DataFrame:
        if not self.ledger_path.is_file():
            return pd.DataFrame(columns=CHARGING_EVIDENCE_COLUMNS)
        frame = pd.read_csv(self.ledger_path, dtype={"route_id": str})
        missing = set(CHARGING_EVIDENCE_COLUMNS) - set(frame.columns)
        if missing:
            raise ValueError(f"Charging evidence ledger missing columns: {sorted(missing)}")
        return frame[CHARGING_EVIDENCE_COLUMNS].copy()


class MetroManilaOperatorEvidenceAdapter(OperatorEvidenceAdapter):
    def __init__(self, root: Path):
        self.ledger_path = root / "data" / "validated" / "operator_evidence.csv"

    def load_evidence(self) -> pd.DataFrame:
        if not self.ledger_path.is_file():
            return pd.DataFrame(columns=OPERATOR_EVIDENCE_COLUMNS)
        frame = pd.read_csv(self.ledger_path, dtype={"route_id": str})
        missing = set(OPERATOR_EVIDENCE_COLUMNS) - set(frame.columns)
        if missing:
            raise ValueError(f"Operator evidence ledger missing columns: {sorted(missing)}")
        return frame[OPERATOR_EVIDENCE_COLUMNS].copy()


METRO_MANILA_CITY_ALIASES = {
    "Quezon City": ["Quezon City"], "Caloocan": ["Caloocan City", "Caloocan"],
    "Las Pinas": ["Las Piñas City", "Las Pinas City", "Las Piñas", "Las Pinas"],
    "Makati": ["Makati City", "Makati"], "Malabon": ["Malabon City", "Malabon"],
    "Mandaluyong": ["Mandaluyong City", "Mandaluyong"], "Marikina": ["Marikina City", "Marikina"],
    "Muntinlupa": ["Muntinlupa City", "Muntinlupa"], "Navotas": ["Navotas City", "Navotas"],
    "Paranaque": ["Parañaque City", "Paranaque City", "Parañaque", "Paranaque"],
    "Pasay": ["Pasay City", "Pasay"], "Pasig": ["Pasig City", "Pasig"],
    "San Juan": ["San Juan City", "San Juan"], "Taguig": ["Taguig City", "Taguig"],
    "Valenzuela": ["Valenzuela City", "Valenzuela"], "Pateros": ["Pateros"],
    "Antipolo": ["Antipolo City", "Antipolo"], "Bacoor": ["Bacoor City", "Bacoor"],
    "Dasmarinas": ["Dasmariñas City", "Dasmarinas City", "Dasmariñas", "Dasmarinas"],
    "San Jose del Monte": ["San Jose del Monte City", "San Jose del Monte"],
    "Binan": ["Biñan City", "Binan City", "Biñan", "Binan"], "Carmona": ["Carmona City", "Carmona"],
    "General Mariano Alvarez": ["General Mariano Alvarez", "GMA, Cavite"],
}


class MetroManilaCityBoundaryAdapter(CityBoundaryAdapter):
    """Current text fallback; replace with a spatial boundary adapter when sourced."""

    @property
    def method(self) -> str:
        return "text_fallback"

    @property
    def boundary_source_id(self) -> str:
        return ""

    def cities_for_route(self, description: object, route_name: object) -> list[str]:
        text = f"{description or ''} | {route_name or ''}"
        hits: list[tuple[int, str]] = []
        cleaned = text
        for city, aliases in METRO_MANILA_CITY_ALIASES.items():
            positions = [cleaned.lower().find(alias.lower()) for alias in aliases]
            positions = [position for position in positions if position >= 0]
            if positions:
                hits.append((min(positions), city))
            for alias in aliases:
                cleaned = re.sub(re.escape(alias) + r"\s*,?\s*Manila", alias, cleaned, flags=re.I)
        positions = [match.start() for match in re.finditer(r"(?<!Metro )\bManila\b", cleaned, flags=re.I)]
        if positions:
            hits.append((min(positions), "Manila"))
        ordered: list[str] = []
        for _, city in sorted(hits):
            if city not in ordered:
                ordered.append(city)
        return ordered or ["Unspecified"]
