from pathlib import Path

import pypdfium2 as pdfium


ROOT = Path(__file__).resolve().parents[2]
SUBMISSION = ROOT / "output" / "submission"
QA = ROOT / "tmp" / "route2zero-submission" / "pdf-2.1-qa"


def render(pdf_path: Path) -> int:
    target = QA / pdf_path.stem
    target.mkdir(parents=True, exist_ok=True)
    document = pdfium.PdfDocument(pdf_path)
    for index in range(len(document)):
        page = document[index]
        bitmap = page.render(scale=1.7)
        bitmap.to_pil().save(target / f"page-{index + 1:02d}.png")
        page.close()
    document.close()
    return len(list(target.glob("page-*.png")))


counts = {
    name: render(SUBMISSION / name)
    for name in (
        "Route2Zero_Concept.pdf",
        "Route2Zero_Prototype_Demonstration.pdf",
        "Route2Zero_Team_Larpers_Pilot_Plan.pdf",
    )
}
print(counts)
