from pathlib import Path
from pypdf import PdfReader
import json
import re

base = Path("output/submission")
pdfs = [
    "Route2Zero_Concept.pdf",
    "Route2Zero_Prototype_Demonstration.pdf",
    "Route2Zero_Team_Larpers_Pilot_Plan.pdf",
]
team_names = [
    "John Marwin Ebona", "Isaac Marcus", "Andrei Dela Cruz", "Russel Mendez",
    "TRISTIAN JAMES CABALAR", "JOHN MICHAEL PALAGANAS", "Carl Nueva",
    "JOSEPH CLARENCE PARAYAOAN",
]
expected_pages = {
    "Route2Zero_Concept.pdf": 20,
    "Route2Zero_Prototype_Demonstration.pdf": 18,
    "Route2Zero_Team_Larpers_Pilot_Plan.pdf": 5,
}
provenance_ids = (
    "r2z-d4c8d4cc709a",
    "scn-e0f12f397e",
    "prt-fd6de9d793",
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
    }
print(json.dumps(out, indent=2))
