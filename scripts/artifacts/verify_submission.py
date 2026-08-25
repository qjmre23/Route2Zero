from pathlib import Path
from pypdf import PdfReader
import json
import re

root = Path(__file__).resolve().parents[2]
base = root / "output" / "submission"
manifest = json.loads((root / "data" / "processed" / "build_manifest.json").read_text(encoding="utf-8"))
pdfs = [
    "Route2Zero_Concept.pdf",
    "Route2Zero_Prototype_Demonstration.pdf",
    "Route2Zero_Team_Larpers_Pilot_Plan.pdf",
]
team_names = [
    "John Marwin Ebona", "Isaac Marcus", "Andrei Dela Cruz", "Russel Mendez",
    "Joaquin Sarmiento", "Prince Marl Mirasol", "Carl Nueva",
    "JOSEPH CLARENCE PARAYAOAN",
]
expected_pages = {
    "Route2Zero_Concept.pdf": 20,
    "Route2Zero_Prototype_Demonstration.pdf": 18,
    "Route2Zero_Team_Larpers_Pilot_Plan.pdf": 5,
}
provenance_ids = (
    manifest["build_id"],
    manifest["default_scenario_id"],
    manifest["default_portfolio_scenario_id"],
)
out = {}
for fn in pdfs:
    reader = PdfReader(base / fn)
    page_text = [(page.extract_text() or "") for page in reader.pages]
    text = "\n".join(page_text)
    uris = []
    page_uris = []
    for page in reader.pages:
        current_page_uris = []
        for annot_ref in page.get("/Annots", []) or []:
            annot = annot_ref.get_object()
            action = annot.get("/A")
            if action and action.get("/URI"):
                uri = str(action.get("/URI"))
                uris.append(uri)
                current_page_uris.append(uri)
        page_uris.append(current_page_uris)
    compact_text = re.sub(r"\s+", "", text)
    compact_text_folded = compact_text.casefold()
    missing_names = [
        name for name in team_names
        if re.sub(r"\s+", "", name) not in compact_text
    ]
    case_mismatches = [
        name for name in team_names
        if re.sub(r"\s+", "", name).casefold() in compact_text_folded
        and re.sub(r"\s+", "", name) not in compact_text
    ]
    name_occurrences = {
        name: compact_text.count(re.sub(r"\s+", "", name))
        for name in team_names
    }
    out[fn] = {
        "pages": len(reader.pages),
        "expected_pages": expected_pages[fn],
        "page_count_ok": len(reader.pages) == expected_pages[fn],
        "links_visible_on_every_page": all(
            "github.com/qjmre23/Route2Zero" in page
            and "route2zero.netlify.app" in page
            for page in page_text
        ),
        "links_clickable_on_every_page": all(
            any("github.com/qjmre23/Route2Zero" in uri for uri in page)
            and any("route2zero.netlify.app" in uri for uri in page)
            for page in page_uris
        ),
        "provenance_ids_on_every_page": all(
            all(provenance_id in page for provenance_id in provenance_ids)
            for page in page_text
        ),
        "hyperlinks": sorted(set(uris)),
        "missing_names": missing_names,
        "case_mismatches": case_mismatches,
        "canonical_name_occurrences": name_occurrences,
        "canonical_roster_once": all(count == 1 for count in name_occurrences.values()),
        "canonical_roster_ok": not missing_names and not case_mismatches and all(
            count == 1 for count in name_occurrences.values()
        ),
        "team_larpers": "Team Larpers" in text,
        "build_ids_found": sorted(set(re.findall(r"r2z-[0-9a-f]+", text))),
        "single_canonical_build_id": set(re.findall(r"r2z-[0-9a-f]+", text)) == {manifest["build_id"]},
    }

surface_paths = {
    "README.md": root / "README.md",
    "docs/judging_matrix.md": root / "docs" / "judging_matrix.md",
}
surface_build_ids = {
    name: sorted(set(re.findall(r"r2z-[0-9a-f]+", path.read_text(encoding="utf-8"))))
    for name, path in surface_paths.items()
}
out["traceability_contract"] = {
    "manifest_build_id": manifest["build_id"],
    "manifest_scenario_id": manifest["default_scenario_id"],
    "manifest_portfolio_id": manifest["default_portfolio_scenario_id"],
    "surface_build_ids": surface_build_ids,
    "all_surfaces_use_canonical_build": all(
        set(build_ids) == {manifest["build_id"]}
        for build_ids in surface_build_ids.values()
    ),
    "all_pdfs_use_canonical_build": all(
        item["single_canonical_build_id"]
        for name, item in out.items()
        if name.endswith(".pdf")
    ),
}
print(json.dumps(out, indent=2))

pdf_checks_ok = all(
    item["page_count_ok"]
    and item["links_visible_on_every_page"]
    and item["links_clickable_on_every_page"]
    and item["provenance_ids_on_every_page"]
    and item["canonical_roster_ok"]
    and item["team_larpers"]
    and item["single_canonical_build_id"]
    for name, item in out.items()
    if name.endswith(".pdf")
)
if not pdf_checks_ok or not out["traceability_contract"]["all_surfaces_use_canonical_build"]:
    raise SystemExit(1)
