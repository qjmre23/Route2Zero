"""Validate the machine-readable source registry and write its resolved manifest."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from common import CONFIG_DIR, PROCESSED_DIR, ROOT, ensure_output_dirs, read_json, sha256_file, write_json


REQUIRED_FIELDS = {
    "source_id", "title", "organization", "source_url", "local_path", "retrieval_date",
    "reference_period", "geography", "spatial_resolution", "license", "source_type",
    "currentness", "notes", "required",
}


def checksum_path(path: Path) -> str:
    if path.is_file():
        return sha256_file(path)
    digest = hashlib.sha256()
    for child in sorted(item for item in path.rglob("*") if item.is_file()):
        digest.update(child.relative_to(path).as_posix().encode("utf-8"))
        digest.update(sha256_file(child).encode("ascii"))
    return digest.hexdigest()


def main() -> int:
    ensure_output_dirs()
    registry_path = CONFIG_DIR / "source_registry.json"
    registry = read_json(registry_path)
    sources = registry.get("sources", [])
    if not sources:
        raise ValueError("source_registry.json contains no sources")
    source_ids = [str(source.get("source_id", "")) for source in sources]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("source_registry.json contains duplicate source IDs")
    resolved = []
    for source in sources:
        missing_fields = REQUIRED_FIELDS - set(source)
        if missing_fields:
            raise ValueError(f"Source {source.get('source_id')} missing {sorted(missing_fields)}")
        local = ROOT / source["local_path"]
        required = bool(source["required"])
        if required and not local.exists():
            raise FileNotFoundError(f"Required source path is missing: {local}")
        entry = dict(source)
        entry["available"] = local.exists()
        entry["checksum_sha256"] = checksum_path(local) if local.exists() else None
        entry["availability_status"] = "AVAILABLE" if local.exists() else "MISSING_OPTIONAL"
        resolved.append(entry)
    payload = {
        "registry_version": registry["registry_version"],
        "registry_checksum_sha256": sha256_file(registry_path),
        "source_count": len(resolved),
        "sources": resolved,
    }
    write_json(PROCESSED_DIR / "source_manifest.json", payload)
    optional_missing = sum(not source["available"] for source in resolved)
    print(f"[PASS] source manifest: {len(resolved)} sources; optional missing={optional_missing}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
