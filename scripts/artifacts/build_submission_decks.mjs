import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  Presentation,
  PresentationFile,
} from "file:///C:/Users/LENOVO/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "..", "..");
const OUT = path.join(ROOT, "output", "submission");
const QA = path.join(ROOT, "tmp", "route2zero-submission", "deck-2.1-qa");
const SHOTS = path.join(ROOT, "output", "submission", "assets", "2.1");
const BUILD_MANIFEST = JSON.parse(await fs.readFile(path.join(ROOT, "data", "processed", "build_manifest.json"), "utf8"));

const GITHUB = "https://github.com/qjmre23/Route2Zero";
const LIVE = "https://route2zero.netlify.app/";
const BUILD = BUILD_MANIFEST.build_id;
const SCENARIO = BUILD_MANIFEST.default_scenario_id;
const PORTFOLIO = BUILD_MANIFEST.default_portfolio_scenario_id;
const SERVICE_MODEL = BUILD_MANIFEST.model_versions.service_intensity;
const TYPOLOGY_MODEL = BUILD_MANIFEST.model_versions.corridor_typology;
const GENERATED = new Intl.DateTimeFormat("en-GB", {
  day: "2-digit",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
  timeZone: "UTC",
}).format(new Date(BUILD_MANIFEST.build_timestamp_utc)).replace(",", " ·") + " UTC";
const TEAM = [
  "John Marwin Ebona",
  "Isaac Marcus",
  "Andrei Dela Cruz",
  "Russel Mendez",
  "TRISTIAN JAMES CABALAR",
  "JOHN MICHAEL PALAGANAS",
  "Carl Nueva",
  "JOSEPH CLARENCE PARAYAOAN",
];
const TEAM_ROWS = [TEAM.slice(0, 4), TEAM.slice(4)];

const C = {
  navy: "#07162B",
  navy2: "#0B2548",
  ink: "#101828",
  slate: "#475467",
  muted: "#667085",
  line: "#D0D5DD",
  soft: "#F3F6FA",
  white: "#FFFFFF",
  green: "#00A87E",
  mint: "#CFF9ED",
  blue: "#4B6BFB",
  cyan: "#11B8D6",
  coral: "#F45B69",
  amber: "#F2A900",
  lavender: "#E4E8FF",
};

const SLIDE = { width: 1280, height: 720 };
const FRAME = { left: 66, top: 58, width: 1148, height: 604 };
const NO_LINE = { style: "solid", fill: "none", width: 0 };

function shape(slide, geometry, x, y, w, h, fill = "none", line = NO_LINE, name) {
  return slide.shapes.add({
    geometry,
    name,
    position: { left: x, top: y, width: w, height: h },
    fill,
    line,
  });
}

function rect(slide, x, y, w, h, fill, radius = 0, line = NO_LINE, name) {
  const s = shape(slide, radius ? "roundRect" : "rect", x, y, w, h, fill, line, name);
  if (radius) s.borderRadius = radius;
  return s;
}

function text(slide, value, x, y, w, h, opts = {}) {
  const s = shape(slide, "textbox", x, y, w, h, opts.fill ?? "none", opts.line ?? NO_LINE, opts.name);
  s.text = value;
  s.text.style = {
    typeface: opts.typeface ?? "Arial",
    fontSize: opts.fontSize ?? 22,
    bold: opts.bold ?? false,
    italic: opts.italic ?? false,
    color: opts.color ?? C.ink,
    alignment: opts.align ?? "left",
    verticalAlignment: opts.valign ?? "top",
    autoFit: opts.autoFit ?? "shrinkText",
    insets: opts.insets ?? { left: 0, right: 0, top: 0, bottom: 0 },
    lineSpacing: opts.lineSpacing ?? 1.0,
  };
  return s;
}

function rich(slide, paragraphs, x, y, w, h, opts = {}) {
  const s = shape(slide, "textbox", x, y, w, h, opts.fill ?? "none", opts.line ?? NO_LINE, opts.name);
  s.text.set(paragraphs);
  s.text.style = {
    typeface: opts.typeface ?? "Arial",
    fontSize: opts.fontSize ?? 22,
    color: opts.color ?? C.ink,
    alignment: opts.align ?? "left",
    verticalAlignment: opts.valign ?? "top",
    autoFit: opts.autoFit ?? "shrinkText",
    insets: opts.insets ?? { left: 0, right: 0, top: 0, bottom: 0 },
    lineSpacing: opts.lineSpacing ?? 1.0,
  };
  return s;
}

function line(slide, x, y, w, color = C.line, weight = 1) {
  return rect(slide, x, y, w, weight, color);
}

function dot(slide, x, y, diameter, fill) {
  return shape(slide, "ellipse", x, y, diameter, diameter, fill);
}

function metric(slide, value, label, x, y, color = C.green, width = 250) {
  text(slide, value, x, y, width, 58, { fontSize: 48, bold: true, color });
  text(slide, label, x, y + 57, width, 46, { fontSize: 17, color: C.slate, lineSpacing: 0.95 });
}

function label(slide, value, x, y, fill = C.lavender, color = C.navy2, width = 155) {
  rect(slide, x, y, width, 28, fill, 14);
  text(slide, value.toUpperCase(), x + 10, y + 4, width - 20, 20, {
    fontSize: 12,
    bold: true,
    color,
    align: "center",
  });
}

function addTopLinks(slide, dark = false) {
  const color = dark ? "#C9D4E8" : C.muted;
  const linkColor = dark ? "#7DE6D1" : C.blue;
  rich(
    slide,
    [[
      { run: "GitHub: ", textStyle: { color } },
      {
        run: GITHUB,
        textStyle: { color: linkColor, underline: "sng" },
        link: { uri: GITHUB, isExternal: true },
      },
    ]],
    66,
    14,
    410,
    22,
    { fontSize: 13, color }
  );
  rich(
    slide,
    [[
      { run: "Live: ", textStyle: { color } },
      {
        run: LIVE,
        textStyle: { color: linkColor, underline: "sng" },
        link: { uri: LIVE, isExternal: true },
      },
    ]],
    490,
    14,
    420,
    22,
    { fontSize: 13, color }
  );
}

function addFooter(slide, pageNo, dark = false, meta = `${BUILD} · ${SCENARIO} · ${PORTFOLIO}`) {
  line(slide, 66, 680, 1148, dark ? "#243B5F" : C.line, 1);
  text(slide, meta, 66, 686, 880, 18, { fontSize: 11, color: dark ? "#8FA7C8" : C.muted });
  text(slide, String(pageNo).padStart(2, "0"), 1155, 684, 58, 20, {
    fontSize: 12,
    bold: true,
    color: dark ? "#8FA7C8" : C.muted,
    align: "right",
  });
}

function addTitle(slide, titleValue, kicker, dark = false, size = 43) {
  if (kicker) text(slide, kicker.toUpperCase(), 66, 48, 560, 22, { fontSize: 13, bold: true, color: dark ? "#7DE6D1" : C.green });
  text(slide, titleValue, 66, 74, 1130, 94, { fontSize: size, bold: true, color: dark ? C.white : C.ink, lineSpacing: 0.92 });
}

function addSourceLine(slide, value, dark = false) {
  text(slide, value, 66, 655, 1140, 19, { fontSize: 10.5, color: dark ? "#8FA7C8" : C.muted });
}

function notes(slide, body, sources = []) {
  const all = [body];
  if (sources.length) all.push("[Sources]", ...sources);
  slide.speakerNotes.textFrame.setText(all.join("\n"));
}

async function addImage(slide, fileName, x, y, w, h, alt, opts = {}) {
  const file = path.join(SHOTS, fileName);
  try {
    const bytes = await fs.readFile(file);
    slide.images.add({
      blob: bytes,
      contentType: "image/png",
      alt,
      fit: opts.fit ?? "cover",
      crop: opts.crop,
      geometry: opts.geometry ?? "roundRect",
      borderRadius: opts.radius ?? 16,
      position: { left: x, top: y, width: w, height: h },
    });
    if (opts.border !== false) rect(slide, x, y, w, h, "none", 16, { style: "solid", fill: opts.borderColor ?? C.line, width: 1.2 });
    return true;
  } catch {
    rect(slide, x, y, w, h, C.soft, 16, { style: "solid", fill: C.line, width: 1 });
    text(slide, `Screenshot pending: ${fileName}`, x + 24, y + h / 2 - 16, w - 48, 34, { fontSize: 17, bold: true, color: C.muted, align: "center" });
    return false;
  }
}

function bulletList(slide, items, x, y, w, h, opts = {}) {
  const paragraphs = items.map((item) => ({
    bulletCharacter: "•",
    marginLeft: 22,
    indent: -12,
    spaceAfter: opts.spaceAfter ?? 12,
    runs: typeof item === "string" ? [item] : item,
  }));
  return rich(slide, paragraphs, x, y, w, h, {
    fontSize: opts.fontSize ?? 21,
    color: opts.color ?? C.ink,
    lineSpacing: opts.lineSpacing ?? 1.05,
  });
}

function processNode(slide, num, heading, sub, x, y, width = 164, accent = C.green) {
  text(slide, String(num).padStart(2, "0"), x, y, 44, 34, { fontSize: 24, bold: true, color: accent });
  line(slide, x, y + 39, width, C.line, 1);
  text(slide, heading, x, y + 52, width, 52, { fontSize: 20, bold: true, color: C.ink });
  text(slide, sub, x, y + 108, width, 74, { fontSize: 15.5, color: C.slate, lineSpacing: 1.0 });
}

function annotation(slide, number, x, y, caption, dx = 36, dy = -4, width = 270) {
  dot(slide, x, y, 30, C.coral);
  text(slide, String(number), x, y + 4, 30, 20, { fontSize: 14, bold: true, color: C.white, align: "center" });
  rect(slide, x + dx - 8, y + dy - 5, width, 35, C.white, 8, { style: "solid", fill: C.line, width: 1 });
  text(slide, caption, x + dx, y + dy + 3, width - 16, 22, { fontSize: 13.5, bold: true, color: C.ink });
}

async function buildConcept() {
  const p = Presentation.create({ slideSize: SLIDE });

  // 1. Cover.
  {
    const s = p.slides.add();
    s.background.fill = C.navy;
    await addImage(s, "overview.png", 705, 60, 575, 660, "Route2Zero overview dashboard", { radius: 0, border: false, crop: { left: 0.14, top: 0, right: 0, bottom: 0 } });
    rect(s, 650, 0, 630, 720, { type: "gradient", gradientKind: "linear", angleDeg: 0, stops: [{ offset: 0, color: "#07162B" }, { offset: 72000, color: "#07162B66" }, { offset: 100000, color: "#07162B00" }] });
    addTopLinks(s, true);
    text(s, "ROUTE2ZERO", 66, 73, 540, 28, { fontSize: 15, bold: true, color: "#7DE6D1" });
    text(s, "AI/ML-assisted planning for a just e-jeepney transition.", 66, 122, 620, 190, { fontSize: 56, bold: true, color: C.white, lineSpacing: 0.92 });
    text(s, "Which Metro Manila corridors should be validated and prioritized first — and how robust is that decision?", 66, 333, 560, 112, { fontSize: 24, color: "#D6E0EF", lineSpacing: 1.05 });
    metric(s, "1,522", "route-direction records screened", 66, 492, "#7DE6D1", 205);
    metric(s, "9", "robust-priority corridors", 300, 492, "#7DE6D1", 190);
    metric(s, "20", "dated OSM validations", 515, 492, "#7DE6D1", 170);
    text(s, "Team Larpers · Metro Manila · AI x City Climate Action Hackathon 2026", 66, 625, 620, 26, { fontSize: 16, color: "#B5C5DC" });
    addFooter(s, 1, true);
    notes(s, "Open with the city decision: this is a transportation planning system, not vehicle hardware and not a generic chatbot.", [GITHUB, LIVE]);
  }

  // 2. Problem context.
  {
    const s = p.slides.add(); s.background.fill = C.white; addTopLinks(s); addTitle(s, "Transport electrification is a climate opportunity — prioritization is the bottleneck.", "Why this matters", false, 40);
    text(s, "34%", 70, 187, 280, 95, { fontSize: 84, bold: true, color: C.coral });
    text(s, "of Philippine GHG emissions came from transport in 2015", 72, 286, 320, 93, { fontSize: 23, bold: true, color: C.ink });
    text(s, "80%", 430, 187, 260, 95, { fontSize: 84, bold: true, color: C.blue });
    text(s, "of transport emissions were attributed to road transport", 432, 286, 310, 93, { fontSize: 23, bold: true, color: C.ink });
    line(s, 796, 176, 1, C.line, 360);
    label(s, "National direction", 835, 184, C.mint, C.green, 178);
    text(s, "50% EV adoption by 2040", 835, 230, 340, 62, { fontSize: 31, bold: true, color: C.navy2 });
    text(s, "A roadmap target — not an achieved value and not route-level proof.", 835, 300, 338, 64, { fontSize: 18, color: C.slate });
    text(s, "Cities still must decide where limited validation, planning, charging, and transition support create the strongest public value first.", 72, 438, 1095, 92, { fontSize: 29, bold: true, color: C.ink, lineSpacing: 1.0 });
    rect(s, 72, 558, 1095, 58, C.soft, 12);
    text(s, "2025 DOE direction: distribution utilities integrate EV charging demand into development planning.", 92, 576, 1055, 28, { fontSize: 19, color: C.navy2 });
    addSourceLine(s, "Sources: DOE CREVI (2023); DOE DC2025-08-0012 and official 2025 releases."); addFooter(s, 2);
    notes(s, "Establish the national climate and grid-planning context, then return to the city corridor decision.", ["https://doe.gov.ph/site/eumb/articles/group/roadmaps?category=Energy+Efficiency+and+Conservation&display_type=Card", "https://doe.gov.ph/site/eumb/articles/group/laws-and-issuances-eumb?display_type=Department+Circular&maincat=Issuances&subcategory=Department+Circular"]);
  }

  // 3. Fragmented evidence.
  {
    const s = p.slides.add(); s.background.fill = C.soft; addTopLinks(s); addTitle(s, "The evidence for one corridor decision lives in different systems.", "The planning gap");
    const items = [
      ["Route + service", "historic schedules, current status"], ["Climate + energy", "vehicle, grid, and operating assumptions"], ["Equity + access", "population and validated area evidence"], ["Charging", "mapped proximity versus verified capacity"], ["Operators", "fleet, depot, finance, governance"], ["Uncertainty", "data quality and policy sensitivity"],
    ];
    items.forEach((it, i) => {
      const col = i % 3, row = Math.floor(i / 3); const x = 72 + col * 252, y = 190 + row * 174;
      text(s, it[0], x, y, 218, 34, { fontSize: 22, bold: true, color: [C.blue, C.green, C.coral][col] });
      text(s, it[1], x, y + 42, 218, 74, { fontSize: 17, color: C.slate });
      line(s, x, y + 128, 218, C.line, 1);
    });
    rect(s, 856, 174, 340, 350, C.navy, 22);
    text(s, "Evidence does not agree by default.", 892, 215, 274, 74, { fontSize: 31, bold: true, color: C.white });
    bulletList(s, ["High activity can still mean weak charging evidence.", "High equity can rest on outdated service records.", "A top score can move when policy priorities change."], 892, 320, 268, 178, { fontSize: 18, color: "#D8E4F2", spaceAfter: 14 });
    text(s, "Route2Zero integrates the evidence — it does not erase disagreement.", 72, 566, 1090, 55, { fontSize: 27, bold: true, color: C.ink });
    addFooter(s, 3); notes(s, "Show why another map or another static ranking is not enough.");
  }

  // 4. Decision question.
  {
    const s = p.slides.add(); s.background.fill = C.navy; addTopLinks(s, true); addTitle(s, "Route2Zero answers one city decision.", "Decision frame", true);
    text(s, "Which corridors should Metro Manila validate and prioritize for e-jeepney transition — and how robust is that recommendation?", 72, 176, 1110, 132, { fontSize: 42, bold: true, color: C.white, lineSpacing: 0.98 });
    const qs = ["Where is the climate value?", "Who benefits — and what evidence supports that?", "Can charging and operators support the transition?", "Does the recommendation survive changing assumptions?"];
    qs.forEach((q, i) => { const x = 72 + (i % 2) * 555, y = 355 + Math.floor(i / 2) * 104; dot(s, x, y + 4, 18, i < 2 ? "#7DE6D1" : "#8197FF"); text(s, q, x + 32, y, 490, 58, { fontSize: 21, color: "#DDE6F3", bold: true }); });
    text(s, "Users: LGUs · DOTr/LTFRB · operators · energy partners · finance · riders and communities", 72, 584, 1098, 26, { fontSize: 18, bold: true, color: "#7DE6D1" });
    text(s, "Output: priority · evidence · climate range · stability · portfolio status · next validation action", 72, 614, 1098, 26, { fontSize: 17, color: "#9FB4CE" });
    addFooter(s, 4, true); notes(s, "The system does not authorize funding. It produces an auditable validation and prioritization decision.");
  }

  // 5. Product promise.
  {
    const s = p.slides.add(); s.background.fill = C.soft; addTopLinks(s); addTitle(s, "From a leaderboard to a city electrification decision laboratory.", "Product promise", false, 41);
    const flow = [
      ["Screen", "1,522 route directions"], ["Estimate", "one missing service input"], ["Quantify", "climate + energy scenarios"], ["Test", "equity, charging, operators"], ["Stress-test", "rank stability + evidence"], ["Assemble", "constrained Phase-1 portfolio"],
    ];
    flow.forEach((it, i) => processNode(s, i + 1, it[0], it[1], 70 + i * 188, 202, 160, i % 2 ? C.blue : C.green));
    line(s, 72, 430, 1092, C.line, 1);
    text(s, "Planning & Evidence Assistant", 72, 464, 355, 40, { fontSize: 27, bold: true, color: C.navy2 });
    text(s, "Explains precomputed evidence, compares scenarios, and turns missing evidence into a fieldwork queue.", 72, 510, 530, 78, { fontSize: 20, color: C.slate });
    text(s, "Humans decide", 845, 470, 305, 46, { fontSize: 36, bold: true, color: C.green, align: "right" });
    text(s, "Policy weights, constraints, evidence acceptance, and implementation remain explicit city choices.", 760, 522, 390, 64, { fontSize: 18, color: C.slate, align: "right" });
    addFooter(s, 5); notes(s, "This is the first full solution view: screen, quantify, stress-test, validate, and act.");
  }

  // 6. AI and analytical governance.
  {
    const s = p.slides.add(); s.background.fill = C.white; addTopLinks(s); addTitle(s, "AI has analytical work — policy authority stays human.", "AI / ML boundary");
    const cols = [
      ["MACHINE LEARNING", C.blue, ["Service-intensity estimate", "Anomaly flag", "Corridor typology"]],
      ["DETERMINISTIC MODELS", C.green, ["Climate + energy", "Evidence confidence", "Sensitivity + optimization"]],
      ["LLM PLANNING ASSISTANT", C.coral, ["Explain evidence", "Compare scenarios", "Triage validation"]],
    ];
    cols.forEach((col, i) => { const x = 72 + i * 380; text(s, col[0], x, 190, 330, 25, { fontSize: 14, bold: true, color: col[1] }); line(s, x, 226, 330, col[1], 4); bulletList(s, col[2], x, 252, 330, 178, { fontSize: 21, spaceAfter: 14 }); });
    rect(s, 72, 484, 1090, 102, C.navy, 16);
    text(s, "ML estimates. Deterministic models quantify. City teams control policy. The LLM explains and triages evidence.", 102, 508, 1030, 58, { fontSize: 26, bold: true, color: C.white, align: "center", valign: "middle" });
    text(s, "The assistant never writes scores, rankings, climate values, weights, or portfolio membership.", 72, 610, 1090, 28, { fontSize: 18, color: C.slate, align: "center" });
    addFooter(s, 6); notes(s, "Clarify three distinct roles: ML estimation, deterministic computation, and LLM explanation.");
  }

  // 7. Provenance.
  {
    const s = p.slides.add(); s.background.fill = C.soft; addTopLinks(s); addTitle(s, "Every recommendation carries an evidence trail.", "Data, provenance, validation");
    text(s, "7 PRIMARY SOURCE FAMILIES", 72, 181, 300, 24, { fontSize: 13, bold: true, color: C.green });
    const srcs = ["Historic Sakay GTFS", "WorldPop 2020", "DOE climate + feasibility", "OSM routes + infrastructure", "LTFRB planning sources", "Operator references + ledgers", "Validation + governance records"];
    srcs.forEach((v, i) => { dot(s, 72, 222 + i * 44, 12, i < 5 ? C.green : C.amber); text(s, v, 96, 215 + i * 44, 325, 29, { fontSize: 17, color: C.ink }); });
    line(s, 438, 188, 1, C.line, 366);
    text(s, "VISIBLE FIELD STATUS", 480, 181, 250, 24, { fontSize: 13, bold: true, color: C.blue });
    const states = [["VERIFIED", C.green], ["OBSERVED", C.cyan], ["DERIVED", C.blue], ["ML_ESTIMATED", "#805AD5"], ["PROXY", C.amber], ["SCENARIO", C.coral], ["NEUTRAL PRIOR", C.slate], ["MISSING", "#98A2B3"]];
    states.forEach((st, i) => { label(s, st[0], 480 + (i % 2) * 170, 220 + Math.floor(i / 2) * 63, st[1] + "20", st[1], 150); });
    rect(s, 845, 178, 330, 390, C.white, 18, { style: "solid", fill: C.line, width: 1 });
    metric(s, "20", "dated OSM matches", 878, 211, C.green, 240);
    metric(s, "22", "source geometries", 878, 331, C.blue, 240);
    metric(s, "18", "registered source records", 878, 451, C.amber, 240);
    addSourceLine(s, `MIT code · OSM data © contributors, ODbL · build ${BUILD}`); addFooter(s, 7);
    notes(s, "Seven primary families are represented by 18 registered, dated source records. Claim status is assigned field by field.", ["data/processed/source_manifest.json", "data/processed/build_manifest.json", "NOTICE.md", "LICENSE"]);
  }

  // 8. Current evidence validation.
  {
    const s = p.slides.add(); s.background.fill = C.white; addTopLinks(s); addTitle(s, "A dated external route record now changes the evidence state — without claiming active service.", "Current-evidence validation layer", false, 36);
    await addImage(s, "current-validation.png", 72, 176, 635, 430, "Validated corridor Route Lens with OSM source and review date", { crop: { left: 0.01, top: 0.02, right: 0.01, bottom: 0.02 } });
    label(s, "Historic only", 758, 184, "#FDE8EC", C.coral, 150);
    text(s, "1,522-route screening baseline", 758, 228, 390, 32, { fontSize: 21, bold: true, color: C.ink });
    text(s, "↓ fuzzy endpoint review + one-to-one relation acceptance", 758, 277, 390, 44, { fontSize: 17, color: C.slate });
    label(s, "Observed", 758, 339, C.mint, C.green, 150);
    text(s, "20 corridors with dated OSM route relations", 758, 383, 390, 50, { fontSize: 24, bold: true, color: C.navy2 });
    bulletList(s, ["route=share_taxi convention", "edited 2023-01-01 or later", "actual member-way geometry", "active service remains uncertain"], 758, 456, 385, 146, { fontSize: 17, spaceAfter: 8 });
    addSourceLine(s, "Example: LTFRB_PUJ1034 · OSM relation 11521406 · reviewed 24 Aug 2026"); addFooter(s, 8);
    notes(s, "A current external route record supports the route and geometry claim. It does not certify active operations or franchise authority.", ["data/processed/osm_route_validation.csv", "data/processed/osm_route_geometry.geojson", "https://www.openstreetmap.org/relation/11521406"]);
  }

  // 9. ML service intelligence.
  {
    const s = p.slides.add(); s.background.fill = C.white; addTopLinks(s); addTitle(s, "Machine learning estimates service intensity where evidence is incomplete.", "ML service intelligence", false, 40);
    s.charts.add("bar", {
      position: { left: 72, top: 190, width: 510, height: 320 },
      categories: ["Selected model", "Median baseline"],
      series: [{ name: "MAE", values: [267.70, 4850.34], fill: C.blue, points: [{ idx: 1, fill: C.line }] }],
      barOptions: { direction: "bar", grouping: "clustered", gapWidth: 55 },
      hasLegend: false,
      xAxis: { title: "Mean absolute error — historic vehicle-km/day proxy", majorGridlines: { style: "solid", fill: "#E4E7EC", width: 1 }, textStyle: { fill: C.muted, fontSize: 12 } },
      yAxis: { textStyle: { fill: C.ink, fontSize: 14 }, line: { style: "solid", fill: C.line, width: 1 } },
      dataLabels: { showValue: true, position: "outEnd", textStyle: { fill: C.ink, fontSize: 13, bold: true } },
      chartFill: "none", plotAreaFill: "none", chartLine: NO_LINE, plotAreaLine: NO_LINE,
    });
    text(s, "HistGradientBoostingRegressor", 650, 189, 500, 45, { fontSize: 30, bold: true, color: C.navy2 });
    const facts = [["Target", "Historic schedule-based vehicle-km/day proxy"], ["Validation", "GroupKFold(5) by normalized corridor"], ["Rows", "1,521 training records · 714 corridor groups"], ["Metrics", "MAE 267.70 · RMSE 574.14 · R² 0.9907"], ["Version", SERVICE_MODEL]];
    facts.forEach((f, i) => { text(s, f[0].toUpperCase(), 650, 253 + i * 61, 135, 20, { fontSize: 12, bold: true, color: C.green }); text(s, f[1], 790, 247 + i * 61, 370, 42, { fontSize: 18, color: C.ink }); });
    rect(s, 72, 548, 1090, 72, C.soft, 12);
    text(s, "Only LTFRB_PUJ2451 uses ML: historic activity is MISSING; the model supplies 6,657 vehicle-km/day for the climate input. It is not headway, current service, or ridership.", 92, 565, 1050, 46, { fontSize: 17, color: C.ink, bold: true });
    addSourceLine(s, "Source: model_metrics.json · grouped corridor validation · no score/rank leakage features"); addFooter(s, 9);
    notes(s, "The ML target is service activity, never passenger demand. Validated observations override the model.", ["data/processed/model_metrics.json"]);
  }

  // 10. Typology.
  {
    const s = p.slides.add(); s.background.fill = C.soft; addTopLinks(s); addTitle(s, "Route2Zero compares like with like.", "Corridor typology");
    await addImage(s, "map.png", 72, 174, 690, 430, "Corridor map colored by typology", { crop: { left: 0.04, top: 0.16, right: 0.04, bottom: 0.04 } });
    s.charts.add("bar", {
      position: { left: 805, top: 190, width: 360, height: 265 },
      categories: ["High-stop core", "Dense trunk", "Long connector"],
      series: [{ name: "Routes", values: [869, 631, 22], fill: C.blue, points: [{ idx: 1, fill: C.green }, { idx: 2, fill: C.cyan }] }],
      barOptions: { direction: "bar", grouping: "clustered", gapWidth: 45 }, hasLegend: false,
      xAxis: { visible: false, majorGridlines: null }, yAxis: { textStyle: { fill: C.ink, fontSize: 12 }, line: NO_LINE },
      dataLabels: { showValue: true, position: "outEnd", textStyle: { fill: C.ink, fontSize: 12, bold: true } }, chartFill: "none", plotAreaFill: "none", chartLine: NO_LINE, plotAreaLine: NO_LINE,
    });
    label(s, "Selected k = 3", 815, 478, C.mint, C.green, 150);
    text(s, "Silhouette 0.373", 815, 520, 300, 32, { fontSize: 20, bold: true, color: C.ink });
    text(s, `KMeans · ${TYPOLOGY_MODEL}\nTypology informs comparison, not policy score.`, 815, 557, 340, 70, { fontSize: 17, color: C.slate });
    addFooter(s, 10); notes(s, "The flagship is a Dense Urban Trunk and is an outlier within that cluster. Typology never infers vulnerability or settlement status.", ["data/processed/corridor_typology.csv", "data/processed/model_metrics.json"]);
  }

  // 11. Climate.
  {
    const s = p.slides.add(); s.background.fill = C.white; addTopLinks(s); addTitle(s, "The system estimates climate outcomes — not an ‘emissions score.’", "Climate + energy impact", false, 40);
    const chain = [["+368", "base tCO₂e/year"], ["31,585", "historic daily VKT"], ["50%", "base electric share"], ["−1,112 to +3,025", "bounded range"]];
    chain.forEach((item, i) => { const x = 72 + i * 275; text(s, item[0], x, 210, 230, 62, { fontSize: i === 3 ? 34 : 42, bold: true, color: i === 3 ? C.coral : C.navy2 }); text(s, item[1], x, 280, 230, 36, { fontSize: 17, color: C.slate }); if (i < 3) text(s, "→", x + 235, 225, 34, 36, { fontSize: 30, color: C.line, align: "center" }); });
    s.charts.add("bar", {
      position: { left: 72, top: 370, width: 685, height: 230 }, categories: ["Low", "Base", "High"],
      series: [{ name: "Net tCO₂e/year", values: [-1111.8, 368.0, 3025.3], fill: C.green, points: [{ idx: 0, fill: C.coral }, { idx: 1, fill: C.amber }] }],
      barOptions: { direction: "column", grouping: "clustered", gapWidth: 70 }, hasLegend: false,
      xAxis: { textStyle: { fill: C.ink, fontSize: 13 }, line: { style: "solid", fill: C.line, width: 1 } },
      yAxis: { title: "Net tCO₂e per year", majorGridlines: { style: "solid", fill: "#E4E7EC", width: 1 }, textStyle: { fill: C.muted, fontSize: 11 } },
      dataLabels: { showValue: true, position: "outEnd", textStyle: { fill: C.ink, fontSize: 12, bold: true } }, chartFill: "none", plotAreaFill: "none", chartLine: NO_LINE, plotAreaLine: NO_LINE,
    });
    rect(s, 800, 352, 365, 250, C.soft, 16);
    text(s, "BASE CASE FIRST · SCENARIO", 827, 375, 310, 30, { fontSize: 18, bold: true, color: C.green });
    text(s, "The low case turns negative when a carbon-intensive grid is paired with an inefficient EV assumption. In that combination, electricity emissions exceed avoided diesel emissions.", 827, 419, 304, 92, { fontSize: 16.5, color: C.ink, lineSpacing: 1.0 });
    text(s, "Dominant sensitivity: vehicle efficiency, together with grid intensity.", 827, 526, 304, 54, { fontSize: 16.5, bold: true, color: C.coral });
    addSourceLine(s, "Flagship: Francisco Homes–Cubao · climate-v1.0 · DOE context + explicit scenario assumptions"); addFooter(s, 11);
    notes(s, "Do not hide the negative low case. The result depends on grid and vehicle-efficiency assumptions and must be validated.", ["https://doe.gov.ph/sites/default/files/pdf/e_ipo/2024-Energy-Investment-Kit.pdf", "data/processed/climate_impact.csv"]);
  }

  // 12. Equity.
  {
    const s = p.slides.add(); s.background.fill = C.soft; addTopLinks(s); addTitle(s, "Climate value is not enough if access is left behind.", "Equity + accessibility");
    metric(s, "77.42", "population-exposure score", 72, 192, C.blue, 300);
    metric(s, "25 / 100", "equity evidence confidence", 408, 192, C.coral, 300);
    metric(s, "PROXY", "claim status", 744, 192, C.amber, 300);
    line(s, 72, 340, 1090, C.line, 1);
    text(s, "What exists", 72, 378, 310, 38, { fontSize: 27, bold: true, color: C.navy2 });
    bulletList(s, ["WorldPop population exposure", "Route-level spatial overlap", "Transparent missing-data policy"], 72, 428, 420, 150, { fontSize: 20, spaceAfter: 10 });
    text(s, "What does not yet exist", 620, 378, 410, 38, { fontSize: 27, bold: true, color: C.coral });
    bulletList(s, ["Validated socioeconomic layer", "Accessibility-gap or transit-dependence layer", "Settlement-status evidence"], 620, 428, 500, 150, { fontSize: 20, spaceAfter: 10 });
    rect(s, 72, 581, 1090, 61, C.white, 10);
    text(s, "Next candidate: PSA Small Area Poverty Estimates at city level. It is registered but MISSING from scoring until route-city geometry and aggregation rules are validated.", 90, 594, 1055, 36, { fontSize: 16.5, bold: true, color: C.ink, align: "center" });
    addFooter(s, 12); notes(s, "The current equity view is intentionally narrow. The pilot expands it only with validated area-level evidence.", ["data/processed/equity_v2.csv", "WorldPop PHL 2020 1 km population raster"]);
  }

  // 13. Charging and operator.
  {
    const s = p.slides.add(); s.background.fill = C.white; addTopLinks(s); addTitle(s, "A climate opportunity is not implementation-ready without infrastructure and operators.", "Charging + operator readiness", false, 38);
    rect(s, 72, 184, 510, 410, C.soft, 18);
    text(s, "CHARGING EVIDENCE", 104, 215, 430, 24, { fontSize: 14, bold: true, color: C.green });
    metric(s, "60.45", "readiness score · PROXY", 104, 256, C.green, 300);
    const ch = [["Energy need", "13.16 MWh/day · base"], ["Nearest mapped substation", "0.56 km"], ["Nearest mapped charger", "0.65 km"], ["Candidate terminals", "2 · unverified"]];
    ch.forEach((f, i) => { text(s, f[0], 104, 380 + i * 48, 250, 20, { fontSize: 14, color: C.muted }); text(s, f[1], 345, 374 + i * 48, 200, 30, { fontSize: 17, bold: true, color: C.ink, align: "right" }); });
    rect(s, 620, 184, 542, 410, C.navy, 18);
    text(s, "OPERATOR EVIDENCE", 652, 215, 450, 24, { fontSize: 14, bold: true, color: "#7DE6D1" });
    metric(s, "1 / 8", "named desk reference", 652, 256, "#7DE6D1", 300);
    const op = [["Named reference", "PUJ1405"], ["Consent-based readiness", "0 / 8"], ["Evidence confidence", "5 / 100"], ["Readiness status", "NEUTRAL PRIOR"]];
    op.forEach((f, i) => { text(s, f[0], 652, 380 + i * 48, 250, 20, { fontSize: 14, color: "#A9BCD4" }); text(s, f[1], 910, 374 + i * 48, 220, 30, { fontSize: 17, bold: true, color: C.white, align: "right" }); });
    rect(s, 72, 616, 1090, 35, "#FDE8EC", 8);
    text(s, "UTILITY CAPACITY: NOT VERIFIED — mapped proximity is not capacity, site control, or interconnection approval.", 90, 624, 1055, 20, { fontSize: 15.5, bold: true, color: "#9B1C31", align: "center" });
    addFooter(s, 13); notes(s, "All eight Phase-1 operator searches are recorded. One named cooperative reference was found, but none satisfies the consent-based readiness threshold, so the neutral prior remains.", ["data/processed/charging_readiness.csv", "data/processed/operator_readiness_v2.csv", "config/operator_reference_search.json"]);
  }

  // 14. Feasibility and cost.
  {
    const s = p.slides.add(); s.background.fill = C.soft; addTopLinks(s); addTitle(s, "Put an order of magnitude beside the shortlist — without calling it a budget.", "Feasibility + cost / fleet snapshot", false, 37);
    await addImage(s, "feasibility.png", 72, 177, 630, 340, "Live feasibility snapshot with proxy and missing-status badges", { fit: "contain" });
    const metrics = [["1,943", "vehicles", C.blue], ["102", "chargers", C.green], ["₱4.91B", "vehicle + charger proxy", C.amber], ["MISSING", "financing terms", C.coral]];
    metrics.forEach((m, i) => { const x = 750 + (i % 2) * 205, y = 190 + Math.floor(i / 2) * 135; text(s, m[0], x, y, 190, 50, { fontSize: 34, bold: true, color: m[2] }); text(s, m[1], x, y + 54, 190, 42, { fontSize: 15.5, color: C.slate }); });
    line(s, 750, 447, 395, C.line, 1);
    text(s, "PROXY assumptions", 750, 471, 190, 24, { fontSize: 14, bold: true, color: C.green });
    text(s, "120 km/vehicle-day · ₱2.5M/vehicle · 20 vehicles/charger-day · ₱0.5M/charger", 750, 507, 395, 70, { fontSize: 17, color: C.ink });
    rect(s, 72, 550, 1090, 84, C.white, 12);
    text(s, "Excluded: land/depot, civil works, grid upgrades, interconnection, battery replacement, taxes, insurance, financing, and O&M. Confirm fleet, duty cycle, tariff, depot, and financing before any decision.", 94, 570, 1046, 50, { fontSize: 16.5, bold: true, color: C.ink, align: "center" });
    addFooter(s, 14); notes(s, "These figures are an order-of-magnitude validation scenario, not a supplier quote, procurement estimate, or budget.", ["data/processed/feasibility_cost_scenarios.json", "config/feasibility_cost_config.json"]);
  }

  // 15. Policy model.
  {
    const s = p.slides.add(); s.background.fill = C.soft; addTopLinks(s); addTitle(s, "The policy trade-offs stay visible.", "Human-controlled policy model");
    const weights = [["Climate", 40, C.green], ["Equity", 30, C.blue], ["Charging", 15, C.amber], ["Operator", 15, C.coral]];
    weights.forEach((w, i) => { const y = 202 + i * 88; text(s, w[0], 72, y, 145, 28, { fontSize: 21, bold: true }); rect(s, 235, y + 4, 455, 22, C.line, 11); rect(s, 235, y + 4, 455 * w[1] / 50, 22, w[2], 11); text(s, `${w[1]}%`, 710, y, 80, 28, { fontSize: 20, bold: true, color: w[2], align: "right" }); });
    rect(s, 838, 188, 330, 345, C.white, 18, { style: "solid", fill: C.line, width: 1 });
    label(s, "Default scenario", 870, 218, C.mint, C.green, 175);
    text(s, "Climate + Equity", 870, 267, 270, 43, { fontSize: 29, bold: true, color: C.navy2 });
    text(s, SCENARIO, 870, 318, 270, 29, { fontSize: 16, color: C.muted });
    line(s, 870, 365, 266, C.line, 1);
    text(s, "Named alternatives", 870, 394, 260, 27, { fontSize: 17, bold: true, color: C.ink });
    bulletList(s, ["Equity-first: 25 / 50 / 15 / 10", "Infrastructure-first: 25 / 20 / 35 / 20"], 870, 438, 265, 88, { fontSize: 16.5, spaceAfter: 8 });
    text(s, "Weights are normalized to 100%. They are a city choice — never presented as objectively correct.", 72, 580, 1090, 58, { fontSize: 24, bold: true, color: C.ink });
    addFooter(s, 15); notes(s, "The scenario ID is stable and travels into assistant responses and exports.", ["config/policy_model.json"]);
  }

  // 16. Sensitivity.
  {
    const s = p.slides.add(); s.background.fill = C.white; addTopLinks(s); addTitle(s, "A recommendation is stronger when it survives changing assumptions.", "Uncertainty + rank stability", false, 40);
    text(s, "5,000", 72, 188, 230, 65, { fontSize: 54, bold: true, color: C.blue });
    text(s, "fixed-seed policy-weight simulations", 72, 256, 290, 48, { fontSize: 19, color: C.slate });
    const rows = [["Francisco Homes–Cubao", "rank 1", 1, 1, "100% top-10", "ROBUST PRIORITY", C.green], ["Binangonan–JRC via Angono", "rank 11", 9, 24, "40.7% top-10", "SCENARIO-DEPENDENT", C.amber]];
    rows.forEach((r, i) => { const y = 350 + i * 118; text(s, r[0], 72, y, 350, 28, { fontSize: 20, bold: true }); text(s, r[1], 72, y + 35, 155, 25, { fontSize: 16, color: C.muted }); const x0 = 450, scale = 17; line(s, x0, y + 35, 610, C.line, 8); rect(s, x0 + r[2] * scale, y + 28, Math.max(8, (r[3] - r[2]) * scale), 22, r[6], 11); text(s, `P10 ${r[2]} · P90 ${r[3]}`, x0, y + 58, 250, 24, { fontSize: 14, color: C.muted }); text(s, r[4], 875, y - 1, 180, 25, { fontSize: 18, bold: true, color: r[6], align: "right" }); label(s, r[5], 875, y + 35, r[6] + "22", r[6], 265); });
    rect(s, 72, 603, 1090, 39, C.soft, 10);
    text(s, "Rank stability measures resilience to tested policy weights — not model accuracy.", 92, 611, 1050, 23, { fontSize: 18, bold: true, color: C.ink, align: "center" });
    addFooter(s, 16); notes(s, "Contrast a robust route with a scenario-dependent route. The fixed seed makes the test reproducible.", ["data/processed/sensitivity.csv", "config/sensitivity_config.json"]);
  }

  // 17. Value of information.
  {
    const s = p.slides.add(); s.background.fill = C.soft; addTopLinks(s); addTitle(s, "Route2Zero tells the city which missing evidence is worth collecting first.", "Value of information", false, 39);
    const voi = [["Climate assumptions", "rank swing up to 1,395", "Portfolio flip possible", C.coral], ["Equity population exposure", "rank swing up to 7", "Validate area evidence", C.blue], ["Charging readiness", "rank swing up to 3", "Request utility/site evidence", C.green], ["Operator readiness", "rank swing up to 3", "Interview operator/cooperative", C.amber]];
    voi.forEach((r, i) => { const y = 188 + i * 96; text(s, r[0], 72, y, 330, 30, { fontSize: 23, bold: true, color: r[3] }); text(s, r[1], 430, y, 255, 28, { fontSize: 19, bold: true, color: C.ink }); text(s, r[2], 735, y, 330, 28, { fontSize: 19, color: C.slate }); line(s, 72, y + 55, 1090, C.line, 1); });
    rect(s, 72, 590, 1090, 58, C.navy, 12);
    text(s, "Next action: calibrate vehicle efficiency, electrification share, and grid assumptions before treating the flagship climate case as decision-ready.", 94, 604, 1046, 34, { fontSize: 18, bold: true, color: C.white, align: "center" });
    addFooter(s, 17); notes(s, "The values are deterministic field perturbations, not LLM estimates.", ["data/processed/validation_priorities.json"]);
  }

  // 18. Portfolio.
  {
    const s = p.slides.add(); s.background.fill = C.white; addTopLinks(s); addTitle(s, "Cities pilot programs, not leaderboards.", "Constrained Phase-1 portfolio");
    text(s, "SIMPLE TOP 8", 72, 183, 430, 24, { fontSize: 13, bold: true, color: C.muted });
    text(s, "CONSTRAINED 8", 665, 183, 430, 24, { fontSize: 13, bold: true, color: C.green });
    const removed = ["PUJ1352", "PUJ1240", "PUJ2084", "PUJ1157"];
    const added = ["PUJ1638", "PUJ1153", "PUJ1350", "PUJ1405"];
    for (let i = 0; i < 4; i++) { rect(s, 72, 229 + i * 61, 430, 43, "#FDE8EC", 8); text(s, `${removed[i]}  removed`, 90, 240 + i * 61, 390, 23, { fontSize: 18, bold: true, color: "#9B1C31" }); rect(s, 665, 229 + i * 61, 430, 43, C.mint, 8); text(s, `${added[i]}  added`, 683, 240 + i * 61, 390, 23, { fontSize: 18, bold: true, color: "#08765A" }); }
    text(s, "→", 548, 293, 70, 68, { fontSize: 56, bold: true, color: C.line, align: "center" });
    const constraints = ["max 8", "max 2 / city", "max 1 direction / corridor", "equity ≥ 40", "evidence ≥ C"];
    constraints.forEach((v, i) => label(s, v, 72 + i * 218, 498, i === 0 ? C.lavender : C.soft, i === 0 ? C.blue : C.slate, 196));
    rect(s, 72, 560, 1090, 79, C.navy, 12);
    text(s, "BASE CASE", 94, 575, 150, 18, { fontSize: 12, bold: true, color: "#7DE6D1" });
    text(s, "+2,711 tCO₂e/year", 94, 599, 320, 30, { fontSize: 26, bold: true, color: C.white });
    text(s, "Bounded low–high: −8,191 to +22,288 · avg equity 73.9 · all 8 grade C", 450, 592, 680, 40, { fontSize: 17, bold: true, color: "#D6E0EF", align: "right" });
    addFooter(s, 18, false, `${BUILD} · ${SCENARIO} · ${PORTFOLIO}`); notes(s, "The constrained portfolio changes four of the simple top-eight routes because it enforces corridor and city diversity constraints.", ["data/processed/portfolio_scenarios.json"]);
  }

  // 19. Flagship corridor.
  {
    const s = p.slides.add(); s.background.fill = C.soft; addTopLinks(s); addTitle(s, "One corridor, from raw evidence to pilot decision.", "Flagship · Francisco Homes–Cubao");
    await addImage(s, "route-lens.png", 72, 164, 690, 454, "Route Lens for Francisco Homes to Cubao", { crop: { left: 0.02, top: 0.02, right: 0.02, bottom: 0.02 } });
    const facts = [["Rank / priority", "1 / 79.07"], ["Evidence", "C · 38.34"], ["Stability", "100% top-10"], ["Climate base", "+368 tCO₂e/y"], ["Range", "−1,112 to +3,025"], ["Current status", "historic-only"], ["Geometry", "DERIVED approximation"], ["Portfolio", "Selected"]];
    facts.forEach((f, i) => { text(s, f[0].toUpperCase(), 807, 172 + i * 54, 150, 18, { fontSize: 11.5, bold: true, color: C.green }); text(s, f[1], 960, 166 + i * 54, 220, 30, { fontSize: 16.5, bold: true, color: C.ink, align: "right" }); line(s, 807, 205 + i * 54, 373, C.line, 1); });
    rect(s, 807, 612, 373, 40, "#FDE8EC", 8);
    text(s, "Proceed to pilot validation — not procurement.", 820, 622, 347, 20, { fontSize: 15.5, bold: true, color: "#9B1C31", align: "center" });
    addFooter(s, 19); notes(s, "The flagship is selected by a documented rule. It is deliberately not mislabeled as currently operating or geometrically verified.", ["data/processed/flagship_route.json"]);
  }

  // 20. Pilot, impact, team, and license.
  {
    const s = p.slides.add(); s.background.fill = C.navy; addTopLinks(s, true); addTitle(s, "Six months to turn a defensible shortlist into city-owned evidence.", "Pilot · impact · differentiation · scale", true, 38);
    const months = [["M1", "baseline"], ["M2", "ground truth"], ["M3", "model + route"], ["M4", "grid + operator"], ["M5", "co-design"], ["M6", "handover"]];
    months.forEach((m, i) => { const x = 72 + i * 181; dot(s, x, 181, 36, i % 2 ? C.blue : C.green); text(s, m[0], x, 190, 36, 18, { fontSize: 12, bold: true, color: C.white, align: "center" }); if (i < 5) line(s, x + 36, 199, 145, "#314968", 2); text(s, m[1], x - 4, 232, 150, 28, { fontSize: 14.5, bold: true, color: "#D6E0EF" }); });
    const xs = [72, 438, 804];
    const cards = [["EXPECTED IMPACT", ["8 corridors enter deeper validation", "Base +2,711 tCO₂e/year scenario", "Evidence improvement is measured"]], ["WHY ROUTE2ZERO", ["Not one black-box score", "Field-level status + uncertainty", "Humans control policy"]], ["HOW IT SCALES", ["Metro Manila is the deep pilot", "Local source adapters", "Every city recalibrates"]]];
    cards.forEach((card, i) => { text(s, card[0], xs[i], 306, 310, 22, { fontSize: 13, bold: true, color: i === 1 ? "#7DE6D1" : "#9FB4CE" }); bulletList(s, card[1], xs[i], 345, 315, 150, { fontSize: 17.5, color: C.white, spaceAfter: 9 }); });
    line(s, 72, 520, 1090, "#314968", 1);
    text(s, "Team Larpers", 72, 539, 170, 25, { fontSize: 17, bold: true, color: "#7DE6D1" });
    text(s, TEAM_ROWS[0].join(" · "), 235, 539, 927, 22, { fontSize: 11.5, color: C.white, align: "right", autoFit: "shrinkText" });
    text(s, TEAM_ROWS[1].join(" · "), 235, 568, 927, 22, { fontSize: 11.5, color: C.white, align: "right", autoFit: "shrinkText" });
    rect(s, 72, 606, 1090, 45, "#102D4F", 10);
    text(s, "MIT-licensed code · data licenses remain source-specific · OpenStreetMap © contributors, ODbL", 92, 618, 1050, 22, { fontSize: 15, bold: true, color: "#D6E0EF", align: "center" });
    addFooter(s, 20, true); notes(s, "Close by asking for a six-month validation partnership, not trust in one score.", [GITHUB, LIVE, "LICENSE", "NOTICE.md"]);
  }

  return p;
}

async function demoScreenshotSlide(p, n, titleValue, shot, caption, annotations = [], opts = {}) {
  const s = p.slides.add(); s.background.fill = opts.dark ? C.navy : C.white; addTopLinks(s, opts.dark); addTitle(s, titleValue, opts.kicker ?? "Prototype evidence", opts.dark, opts.titleSize ?? 39);
  await addImage(s, shot, 72, 164, 1090, 468, caption, { crop: opts.crop, radius: 14, borderColor: opts.dark ? "#29466E" : C.line });
  annotations.forEach((a) => annotation(s, ...a));
  addFooter(s, n, opts.dark, opts.meta ?? `${BUILD} · ${SCENARIO} · ${PORTFOLIO}`);
  notes(s, opts.note ?? caption, opts.sources ?? [LIVE, GITHUB]);
  return s;
}

async function buildDemo() {
  const p = Presentation.create({ slideSize: SLIDE });
  // 1 — proof cover.
  {
    const s = p.slides.add(); s.background.fill = C.navy; addTopLinks(s, true);
    await addImage(s, "overview.png", 620, 64, 660, 656, "Route2Zero final dashboard", { radius: 0, border: false, crop: { left: 0.1, top: 0, right: 0, bottom: 0 } });
    rect(s, 550, 0, 730, 720, { type: "gradient", gradientKind: "linear", angleDeg: 0, stops: [{ offset: 0, color: "#07162B" }, { offset: 76000, color: "#07162B75" }, { offset: 100000, color: "#07162B00" }] });
    text(s, "Route2Zero 2.1", 66, 100, 510, 86, { fontSize: 62, bold: true, color: C.white });
    text(s, "Prototype Demonstration", 66, 188, 510, 48, { fontSize: 34, bold: true, color: "#7DE6D1" });
    text(s, "A live decision workflow: screen 1,522 corridors, show what is known, and prioritize the evidence needed for a defensible Phase-1 pilot.", 66, 270, 500, 126, { fontSize: 24, color: "#D6E0EF" });
    const meta = [["BUILD", BUILD], ["MODEL", SERVICE_MODEL], ["SCENARIO", SCENARIO], ["GENERATED", GENERATED]];
    meta.forEach((m, i) => { text(s, m[0], 66, 426 + i * 45, 110, 18, { fontSize: 11, bold: true, color: "#8FA7C8" }); text(s, m[1], 184, 420 + i * 45, 365, 28, { fontSize: 17, bold: true, color: C.white }); });
    text(s, "Values shown are generated from the linked build and scenario — not manually entered.", 66, 623, 500, 38, { fontSize: 15.5, color: "#B5C5DC" });
    addFooter(s, 1, true); notes(s, "Frame this as proof of a reproducible working build.", [LIVE, GITHUB]);
  }
  // 2 — demo decision flow.
  {
    const s = p.slides.add(); s.background.fill = C.white; addTopLinks(s); addTitle(s, "What this demonstration will prove.", "Demo decision");
    text(s, "Which corridors remain strong when climate, equity, charging, operator evidence, and uncertainty are tested together?", 72, 180, 1090, 98, { fontSize: 34, bold: true, color: C.navy2, align: "center" });
    const steps = [["01", "Open network"], ["02", "Select flagship"], ["03", "Inspect evidence"], ["04", "Stress-test"], ["05", "Build portfolio"], ["06", "Ask what next"], ["07", "Export pack"]];
    steps.forEach((st, i) => { const x = 72 + i * 156; dot(s, x + 48, 351, 44, i % 2 ? C.blue : C.green); text(s, st[0], x + 48, 362, 44, 20, { fontSize: 13, bold: true, color: C.white, align: "center" }); if (i < 6) line(s, x + 92, 373, 112, C.line, 3); text(s, st[1], x, 416, 140, 55, { fontSize: 17, bold: true, color: C.ink, align: "center" }); });
    rect(s, 385, 530, 510, 58, C.soft, 12); text(s, `Scenario ${SCENARIO}`, 405, 546, 470, 26, { fontSize: 19, bold: true, color: C.blue, align: "center" });
    addFooter(s, 2); notes(s, "Use one scenario throughout so screenshots and assistant responses remain consistent.");
  }

  await demoScreenshotSlide(p, 3, "The final city decision cockpit.", "overview.png", "Route2Zero Overview dashboard", [[1, 94, 218, "1,522 screened · 20 dated matches"], [2, 921, 222, "Scenario and build state"], [3, 106, 552, "Map, Route Lens, feasibility"]], { kicker: "System overview", note: "The 2.1 interface keeps the city decision, evidence state, and next action in one workflow." });
  await demoScreenshotSlide(p, 4, "A validated corridor shows its source, review date, and observed geometry.", "current-validation.png", "Current OSM validation state in the Route Lens", [[1, 104, 220, "OBSERVED field badges"], [2, 850, 220, "OSM relation 11521406"], [3, 116, 550, "Reviewed 24 Aug 2026"]], { kicker: "Current-evidence validation", titleSize: 36, note: "The dated OSM relation supports the route and geometry claim; active service and franchise authority remain uncertain.", sources: ["data/processed/osm_route_validation.csv", "data/processed/osm_route_geometry.geojson"] });
  await demoScreenshotSlide(p, 5, "Flagship corridor: Francisco Homes–Cubao.", "route-lens.png", "Flagship Route Lens", [[1, 105, 228, "Priority, evidence, stability"], [2, 852, 225, "Eight field-status badges"], [3, 118, 551, "Climate and validation action"]], { kicker: "Flagship Route Lens", note: "The flagship remains historic-only and uses a DERIVED route approximation; the interface does not hide that limitation.", sources: ["data/processed/flagship_route.json"] });

  // 6 — ML output with screenshot and chart.
  {
    const s = p.slides.add(); s.background.fill = C.white; addTopLinks(s); addTitle(s, "The machine-learning layer produces a real route-level estimate.", "ML service intensity", false, 39);
    await addImage(s, "route-lens.png", 72, 170, 640, 445, "Route Lens service intelligence panel", { crop: { left: 0.03, top: 0.17, right: 0.47, bottom: 0.32 } });
    s.charts.add("bar", { position: { left: 765, top: 201, width: 390, height: 230 }, categories: ["Model", "Baseline"], series: [{ name: "MAE", values: [267.70, 4850.34], fill: C.blue, points: [{ idx: 1, fill: C.line }] }], barOptions: { direction: "bar", grouping: "clustered", gapWidth: 50 }, hasLegend: false, xAxis: { visible: false, majorGridlines: null }, yAxis: { textStyle: { fill: C.ink, fontSize: 14 }, line: NO_LINE }, dataLabels: { showValue: true, position: "outEnd", textStyle: { fill: C.ink, fontSize: 12, bold: true } }, chartFill: "none", plotAreaFill: "none", chartLine: NO_LINE, plotAreaLine: NO_LINE });
    text(s, "Historic: MISSING", 765, 461, 190, 28, { fontSize: 18, bold: true, color: C.coral }); text(s, "ML: 6,657", 958, 461, 195, 28, { fontSize: 20, bold: true, color: C.blue, align: "right" });
    text(s, "LTFRB_PUJ2451 is the only route where ML supplies the climate activity input. It is not current service or ridership.", 765, 505, 390, 68, { fontSize: 16.5, color: C.slate });
    label(s, "GroupKFold(5)", 765, 580, C.lavender, C.blue, 158); label(s, "No rank leakage", 945, 580, C.mint, C.green, 185);
    addFooter(s, 6, false, `${BUILD} · ${SCENARIO} · ${PORTFOLIO} · ${SERVICE_MODEL}`); notes(s, "The model target is a historic schedule-based service proxy, not passenger demand.", ["data/processed/model_metrics.json"]);
  }

  await demoScreenshotSlide(p, 7, "The selected route is compared against similar corridors.", "map.png", "Typology map", [[1, 105, 223, "Layer: Corridor typology"], [2, 857, 225, "Three structural groups"], [3, 884, 544, "K = 3 · silhouette 0.373"]], { kicker: "Corridor typology", note: "Typology is unsupervised ML and does not add hidden points to the policy score.", sources: ["data/processed/corridor_typology.csv", "data/processed/model_metrics.json"] });
  await demoScreenshotSlide(p, 8, "Lead with the base climate case; keep the bounded risk beside it.", "route-lens.png", "Flagship climate and energy panel", [[1, 102, 220, "Base +368 tCO₂e/year"], [2, 854, 224, "Low–high shown beside it"], [3, 111, 550, "Negative-low explanation"]], { kicker: "Climate + energy", note: "The low case turns negative when a carbon-intensive grid is paired with an inefficient EV assumption; vehicle efficiency and grid intensity dominate the sensitivity.", sources: ["data/processed/climate_impact.csv", "config/climate_scenarios.json"] });
  await demoScreenshotSlide(p, 9, "The climate recommendation is tested against who and where it serves.", "equity-map.png", "Equity layer and Route Lens", [[1, 102, 221, "Layer: Equity / exposure"], [2, 872, 221, "Population exposure"], [3, 862, 545, "PROXY · second layer MISSING"]], { kicker: "Equity + accessibility", note: "Current build uses population exposure only. PSA city-level poverty estimates are registered as the next validation candidate; no poverty or settlement-status inference is made.", sources: ["data/processed/equity_v2.csv"] });
  await demoScreenshotSlide(p, 10, "Feasibility is visible as a proxy — never disguised as a budget.", "feasibility.png", "Feasibility and model-restraint panel", [[1, 106, 221, "Fleet and charger PROXY"], [2, 842, 221, "Capital proxy"], [3, 854, 548, "Financing MISSING"]], { kicker: "Feasibility + model restraint", note: "The live panel exposes order-of-magnitude fleet and hardware figures, excluded costs, and the single route that uses ML.", sources: ["data/processed/feasibility_cost_scenarios.json", "data/processed/model_metrics.json"] });
  await demoScreenshotSlide(p, 11, "Priority, evidence quality, and stability are different questions.", "route-lens.png", "Route Lens evidence summary", [[1, 112, 225, "Priority 79.07"], [2, 455, 225, "Evidence 38.34 · grade C"], [3, 812, 225, "Stability 100% top-10"]], { kicker: "Evidence confidence", note: "A route can be high priority and still require more evidence.", sources: ["data/processed/evidence_confidence.csv", "data/processed/sensitivity.csv"] });

  // 12 — Monte Carlo real output.
  {
    const s = p.slides.add(); s.background.fill = C.soft; addTopLinks(s); addTitle(s, "Does the recommendation survive changing policy priorities?", "5,000-scenario Monte Carlo", false, 40);
    await addImage(s, "scenario-lab.png", 72, 170, 650, 448, "Scenario Lab stability output", { crop: { left: 0.02, top: 0.05, right: 0.22, bottom: 0.08 } });
    const rows = [["Flagship", "1 → 1", "100%", "ROBUST", C.green], ["Binangonan–JRC", "9 → 24", "40.7%", "DEPENDENT", C.amber]];
    rows.forEach((r, i) => { const y = 218 + i * 156; text(s, r[0], 772, y, 360, 28, { fontSize: 22, bold: true }); text(s, "P10–P90 rank", 772, y + 43, 165, 20, { fontSize: 13, color: C.muted }); text(s, r[1], 956, y + 36, 175, 31, { fontSize: 24, bold: true, color: r[4], align: "right" }); text(s, "Top-10 probability", 772, y + 83, 190, 20, { fontSize: 13, color: C.muted }); text(s, r[2], 956, y + 77, 175, 31, { fontSize: 24, bold: true, color: r[4], align: "right" }); label(s, r[3], 772, y + 119, r[4] + "22", r[4], 210); });
    addFooter(s, 12, false, `${BUILD} · ${SCENARIO} · ${PORTFOLIO} · seed 20260820 · 5,000 simulations`); notes(s, "Rank stability is resilience to the tested policy weights, not predictive accuracy.", ["data/processed/sensitivity.csv"]);
  }

  await demoScreenshotSlide(p, 13, "What could change this decision?", "evidence-ai.png", "Value-of-information queue", [[1, 106, 225, "Climate assumptions: rank swing 1,395"], [2, 855, 225, "Portfolio flip possible"], [3, 118, 550, "Field validation action"]], { kicker: "Value of information", note: "The queue is precomputed by deterministic perturbation.", sources: ["data/processed/validation_priorities.json"] });
  await demoScreenshotSlide(p, 14, "A city can change priorities without hiding the trade-off.", "scenario-lab.png", "Scenario comparison", [[1, 106, 220, "Named policy preset"], [2, 861, 220, "Weights normalized to 100%"], [3, 849, 548, "Scenario ID updates"]], { kicker: "Scenario comparison", note: "The policy scenario is explicit and auditable; the assistant cache is keyed by route, scenario, and build.", sources: ["config/policy_model.json"] });
  await demoScreenshotSlide(p, 15, "Now move from ranking to a city validation program.", "portfolio.png", "Portfolio constraints", [[1, 106, 222, "Maximum eight corridors"], [2, 867, 222, "Evidence and equity constraints"], [3, 852, 548, "Cost is visible, not optimized"]], { kicker: "Phase-1 portfolio inputs", note: "The deterministic shortlist uses evidence and diversity constraints. The new feasibility proxy informs validation but is not presented as a verified budget constraint.", sources: ["config/optimization_scenarios.json", "data/processed/feasibility_cost_scenarios.json"] });
  await demoScreenshotSlide(p, 16, "The optimized portfolio is not simply the top eight routes.", "portfolio.png", "Optimized portfolio result", [[1, 104, 220, "Four routes added by constraints"], [2, 850, 220, "Portfolio scenario range"], [3, 845, 547, "Binding constraints + exclusions"]], { kicker: "Optimized result", note: "The optimizer changes four routes while selecting one route direction per normalized corridor.", sources: ["data/processed/portfolio_scenarios.json"] });
  await demoScreenshotSlide(p, 17, "AI explains the evidence and tells the city what to verify next.", "evidence-ai.png", "Planning and Evidence Assistant", [[1, 105, 221, "Question grounded in portfolio"], [2, 854, 221, "Evidence-backed answer"], [3, 847, 548, "Scenario + source + fallback status"]], { kicker: "Planning & Evidence Assistant", titleSize: 37, note: "The assistant never writes scores, rankings, climate values, weights, or portfolio membership.", sources: ["data/processed/route_planner_cache.json", "netlify-site/netlify/functions/ai-planner.mjs"] });

  // 18 — close and reproducibility.
  {
    const s = p.slides.add(); s.background.fill = C.navy; addTopLinks(s, true); addTitle(s, "The decision can be reproduced, exported, challenged, and rerun.", "Reproducibility + close", true, 39);
    await addImage(s, "method-sources.png", 72, 169, 590, 402, "Method and Sources export and manifest view", { crop: { left: 0.02, top: 0.05, right: 0.18, bottom: 0.05 }, borderColor: "#29466E" });
    const items = [["BUILD", BUILD], ["SCENARIO", SCENARIO], ["MODEL", SERVICE_MODEL], ["SIMULATIONS", "5,000 · fixed seed"], ["FALLBACK", "AI-disabled deterministic path"], ["TESTS", "pipeline · contracts · Netlify build"]];
    items.forEach((it, i) => { text(s, it[0], 717, 178 + i * 58, 150, 20, { fontSize: 12, bold: true, color: "#7DE6D1" }); text(s, it[1], 865, 171 + i * 58, 315, 32, { fontSize: 18, bold: true, color: C.white, align: "right" }); line(s, 717, 211 + i * 58, 463, "#29466E", 1); });
    text(s, `Team Larpers · ${TEAM_ROWS[0].join(" · ")}`, 72, 576, 1090, 14, { fontSize: 8.8, color: "#8FA7C8", align: "center", autoFit: "shrinkText" });
    text(s, TEAM_ROWS[1].join(" · "), 72, 592, 1090, 14, { fontSize: 8.8, color: "#8FA7C8", align: "center", autoFit: "shrinkText" });
    text(s, "SOURCE EVIDENCE → ML → CLIMATE / EQUITY / READINESS → CONFIDENCE → POLICY → SENSITIVITY → PORTFOLIO → VALIDATION", 72, 611, 1090, 25, { fontSize: 14, bold: true, color: "#9FB4CE", align: "center" });
    text(s, "Route2Zero is not asking the city to trust one score. It shows what remains true when assumptions are challenged.", 72, 640, 1090, 31, { fontSize: 18, bold: true, color: C.white, align: "center" });
    addFooter(s, 18, true); notes(s, "Close on auditability and human control.", [LIVE, GITHUB]);
  }
  return p;
}

async function writeBlob(file, blob) {
  await fs.writeFile(file, new Uint8Array(await blob.arrayBuffer()));
}

async function exportDeck(presentation, stem, fileName) {
  const qadir = path.join(QA, stem);
  await fs.mkdir(qadir, { recursive: true });
  for (const [i, slide] of presentation.slides.items.entries()) {
    const n = String(i + 1).padStart(2, "0");
    await writeBlob(path.join(qadir, `slide-${n}.png`), await presentation.export({ slide, format: "png", scale: 1 }));
    await fs.writeFile(path.join(qadir, `slide-${n}.layout.json`), await (await slide.export({ format: "layout" })).text());
  }
  await writeBlob(path.join(qadir, "montage.webp"), await presentation.export({ format: "webp", montage: true, scale: 1 }));
  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(path.join(OUT, fileName));
}

await fs.mkdir(OUT, { recursive: true });
await fs.mkdir(QA, { recursive: true });
const concept = await buildConcept();
if (concept.slides.items.length !== 20) throw new Error(`Concept must be 20 slides; got ${concept.slides.items.length}`);
await exportDeck(concept, "concept", "Route2Zero_Concept_Deck_20_Slides.pptx");
const demo = await buildDemo();
if (demo.slides.items.length !== 18) throw new Error(`Demo must be 18 slides; got ${demo.slides.items.length}`);
await exportDeck(demo, "demo", "Route2Zero_Prototype_Demonstration.pptx");
console.log("Created 20-slide Concept and 18-slide Demonstration decks.");
