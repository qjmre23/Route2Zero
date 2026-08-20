const MAPBOX_ACCESS_TOKEN = String(window.ROUTE2ZERO_CONFIG?.mapboxToken || "").trim();
const MAPBOX_STYLE_URL = String(window.ROUTE2ZERO_CONFIG?.mapboxStyleUrl || "mapbox://styles/marwin2323/cmswv687u002u01so2xzd7mrs").trim();

const DEFAULT_WEIGHTS = Object.freeze({ climate: 40, equity: 30, charging: 15, operator: 15 });
const PRESETS = Object.freeze({
  default: { title: "Climate + Equity", weights: DEFAULT_WEIGHTS },
  equity: { title: "Equity-first", weights: { climate: 30, equity: 45, charging: 15, operator: 10 } },
  infrastructure: { title: "Infrastructure-first", weights: { climate: 30, equity: 20, charging: 35, operator: 15 } }
});
const SAVED_SCENARIOS_KEY = "route2zero.savedScenarios.v2";
const MAX_SAVED_SCENARIOS = 24;

const SCORE_COLUMNS = Object.freeze({
  climate: "climate_impact_score",
  equity: "equity_score",
  charging: "charging_readiness_score",
  operator: "operator_effective_score"
});

const LAYERS = Object.freeze({
  priority: { label: "Priority", field: "liveScore", kind: "numeric" },
  climate: { label: "Climate impact", field: "climate_impact_score", kind: "numeric" },
  equity: { label: "Equity / exposure", field: "equity_score", kind: "numeric" },
  charging: { label: "Charging evidence", field: "charging_readiness_score", kind: "numeric" },
  evidence: { label: "Evidence confidence", field: "overall_evidence_confidence", kind: "numeric" },
  stability: { label: "Rank stability", field: "rank_stability_score", kind: "numeric" },
  typology: { label: "Corridor typology", field: "corridor_cluster_id", kind: "typology" },
  validation: { label: "Validation status", field: "validation_status", kind: "validation" }
});

const state = {
  scores: [],
  filtered: [],
  defaultRanked: [],
  geojson: null,
  pathByRoute: new Map(),
  selectedRouteId: null,
  build: {},
  report: {},
  sources: {},
  modelMetrics: {},
  portfolioData: {},
  defaultPortfolio: null,
  portfolioRows: [],
  portfolioScenarioId: "",
  portfolioIsPrecomputed: true,
  validationPriorities: {},
  routePlannerCache: {},
  plannerSummary: {},
  flagship: {},
  normalizedWeights: { ...DEFAULT_WEIGHTS },
  scenarioId: "",
  scenarioCreatedAt: "",
  savedScenarios: [],
  activePreset: "default",
  activeLayer: "priority",
  map: null,
  mapReady: false,
  mapResizeObserver: null,
  hoverPopup: null,
  roadGeometryCache: new Map(),
  roadAbort: null,
  roadRequestId: 0,
  assistantCache: new Map(),
  controlsOpen: false,
  tourIndex: -1,
  tourStarter: null
};

const byId = (id) => document.getElementById(id);
const els = {
  controls: byId("controls"),
  controlsBackdrop: byId("controlsBackdrop"),
  mobileControlsButton: byId("mobileControlsButton"),
  closeControls: byId("closeControls"),
  cityFilter: byId("cityFilter"),
  includeHistoric: byId("includeHistoric"),
  weightTotal: byId("weightTotal"),
  sidebarScenarioId: byId("sidebarScenarioId"),
  scenarioTitle: byId("scenarioTitle"),
  resetScenario: byId("resetScenario"),
  saveScenario: byId("saveScenario"),
  copyScenario: byId("copyScenario"),
  savedScenarioSelect: byId("savedScenarioSelect"),
  loadScenario: byId("loadScenario"),
  deleteScenario: byId("deleteScenario"),
  scenarioManagerStatus: byId("scenarioManagerStatus"),
  routesMetric: byId("routesMetric"),
  validatedMetric: byId("validatedMetric"),
  robustMetric: byId("robustMetric"),
  scenarioMetric: byId("scenarioMetric"),
  heroRobustCount: byId("heroRobustCount"),
  routeFinder: byId("routeFinder"),
  mapLayer: byId("mapLayer"),
  mapLegend: byId("mapLegend"),
  mapCount: byId("mapCount"),
  roadStatus: byId("roadStatus"),
  routeStatusPill: byId("routeStatusPill"),
  routeName: byId("routeName"),
  routeMeta: byId("routeMeta"),
  routeRationale: byId("routeRationale"),
  priorityClaim: byId("priorityClaim"),
  priorityValue: byId("priorityValue"),
  priorityDetail: byId("priorityDetail"),
  evidenceClaim: byId("evidenceClaim"),
  evidenceValue: byId("evidenceValue"),
  evidenceDetail: byId("evidenceDetail"),
  climateClaim: byId("climateClaim"),
  climateRange: byId("climateRange"),
  climateDetail: byId("climateDetail"),
  equityClaim: byId("equityClaim"),
  equityScore: byId("equityScore"),
  equityDetail: byId("equityDetail"),
  chargingClaim: byId("chargingClaim"),
  chargingScore: byId("chargingScore"),
  chargingDetail: byId("chargingDetail"),
  operatorClaim: byId("operatorClaim"),
  operatorScore: byId("operatorScore"),
  operatorDetail: byId("operatorDetail"),
  robustnessClaim: byId("robustnessClaim"),
  robustnessScore: byId("robustnessScore"),
  robustnessDetail: byId("robustnessDetail"),
  typologyClaim: byId("typologyClaim"),
  typologyValue: byId("typologyValue"),
  typologyDetail: byId("typologyDetail"),
  decisionChangeTitle: byId("decisionChangeTitle"),
  decisionChangeCopy: byId("decisionChangeCopy"),
  currentRank: byId("currentRank"),
  medianRank: byId("medianRank"),
  rankRange: byId("rankRange"),
  scenarioLabId: byId("scenarioLabId"),
  activeWeightBars: byId("activeWeightBars"),
  scenarioComparison: byId("scenarioComparison"),
  portfolioMax: byId("portfolioMax"),
  portfolioGrade: byId("portfolioGrade"),
  portfolioEquity: byId("portfolioEquity"),
  buildPortfolio: byId("buildPortfolio"),
  portfolioScenarioId: byId("portfolioScenarioId"),
  portfolioCount: byId("portfolioCount"),
  portfolioClimate: byId("portfolioClimate"),
  portfolioEquityMetric: byId("portfolioEquityMetric"),
  portfolioEvidence: byId("portfolioEvidence"),
  portfolioModePill: byId("portfolioModePill"),
  portfolioList: byId("portfolioList"),
  portfolioDelta: byId("portfolioDelta"),
  portfolioConstraints: byId("portfolioConstraints"),
  leaderboardBody: byId("leaderboardBody"),
  mobileRouteCards: byId("mobileRouteCards"),
  evidenceQueue: byId("evidenceQueue"),
  questionInput: byId("questionInput"),
  askButton: byId("askButton"),
  answerSource: byId("answerSource"),
  answerText: byId("answerText"),
  sourceHealth: byId("sourceHealth"),
  openMethod: byId("openMethod"),
  methodDetails: byId("methodDetails"),
  exportPdf: byId("exportPdf"),
  exportWord: byId("exportWord"),
  downloadCsv: byId("downloadCsv"),
  downloadAudit: byId("downloadAudit"),
  startWalkthroughTop: byId("startWalkthroughTop"),
  startWalkthroughHero: byId("startWalkthroughHero"),
  walkthroughPanel: byId("walkthroughPanel"),
  walkthroughStep: byId("walkthroughStep"),
  walkthroughTime: byId("walkthroughTime"),
  walkthroughTitle: byId("walkthroughTitle"),
  walkthroughCopy: byId("walkthroughCopy"),
  walkthroughBack: byId("walkthroughBack"),
  walkthroughNext: byId("walkthroughNext"),
  walkthroughClose: byId("walkthroughClose")
};

const weightInputs = {
  climate: byId("climateWeight"),
  equity: byId("equityWeight"),
  charging: byId("chargingWeight"),
  operator: byId("operatorWeight")
};

const weightOutputs = {
  climate: byId("climateValue"),
  equity: byId("equityValue"),
  charging: byId("chargingValue"),
  operator: byId("operatorValue")
};

function parseCsv(text) {
  const rows = [];
  let row = [];
  let value = "";
  let quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    const next = text[index + 1];
    if (char === "\"" && quoted && next === "\"") {
      value += "\"";
      index += 1;
    } else if (char === "\"") {
      quoted = !quoted;
    } else if (char === "," && !quoted) {
      row.push(value);
      value = "";
    } else if ((char === "\n" || char === "\r") && !quoted) {
      if (char === "\r" && next === "\n") index += 1;
      row.push(value);
      if (row.some((cell) => cell.length)) rows.push(row);
      row = [];
      value = "";
    } else {
      value += char;
    }
  }
  if (value || row.length) {
    row.push(value);
    rows.push(row);
  }
  const headers = rows.shift() || [];
  return rows.map((cells) => Object.fromEntries(headers.map((header, index) => [header, cells[index] ?? ""])));
}

function numeric(row, key) {
  const value = Number(row?.[key]);
  return row?.[key] !== "" && row?.[key] != null && Number.isFinite(value) ? value : null;
}

function bool(value) {
  return value === true || String(value).toLowerCase() === "true" || String(value) === "1";
}

function escapeHtml(value) {
  return String(value == null ? "" : value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll("\"", "&quot;")
    .replaceAll("'", "&#039;");
}

function formatNumber(value, digits = 0) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "N/A";
  return new Intl.NumberFormat("en-PH", { maximumFractionDigits: digits, minimumFractionDigits: digits }).format(number);
}

function formatSigned(value, digits = 0) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "N/A";
  return `${number > 0 ? "+" : ""}${formatNumber(number, digits)}`;
}

function safeFilePart(value) {
  return String(value || "metro_manila").toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "");
}

function hashString(value) {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(16).padStart(8, "0");
}

function getRawWeights() {
  return Object.fromEntries(Object.entries(weightInputs).map(([key, input]) => [key, Number(input.value)]));
}

function getNormalizedWeights() {
  const raw = getRawWeights();
  const rawTotal = Object.values(raw).reduce((sum, value) => sum + value, 0);
  const basis = rawTotal > 0 ? raw : DEFAULT_WEIGHTS;
  const total = Object.values(basis).reduce((sum, value) => sum + value, 0);
  const normalized = Object.fromEntries(Object.entries(basis).map(([key, value]) => [key, value / total * 100]));
  Object.entries(normalized).forEach(([key, value]) => {
    const rounded = Math.round(value);
    weightOutputs[key].value = `${rounded}%`;
    weightOutputs[key].textContent = `${rounded}%`;
    weightInputs[key].setAttribute("aria-valuetext", `${rounded}% normalized policy weight`);
  });
  els.weightTotal.textContent = "100%";
  els.weightTotal.title = rawTotal === 100 ? "Raw weights already total 100%" : `Raw total ${rawTotal}%; normalized for scoring`;
  return normalized;
}

function validationFilterValue() {
  return els.includeHistoric.checked ? "historic_baseline_plus_supplied_validation" : "supplied_current_validation_only";
}

function optimizationConstraints() {
  return {
    max_corridors: Number(els.portfolioMax.value),
    minimum_evidence_grade: els.portfolioGrade.value,
    minimum_equity_score: Number(els.portfolioEquity.value),
    maximum_corridors_per_primary_city: 2,
    maximum_directions_per_corridor: 1
  };
}

function canonicalPolicyWeights() {
  const keys = ["climate", "equity", "charging", "operator"];
  const canonical = Object.fromEntries(keys.map((key) => [key, Number(Number(state.normalizedWeights[key]).toFixed(4))]));
  const total = Object.values(canonical).reduce((sum, value) => sum + value, 0);
  const adjustmentKey = keys.reduce((best, key) => state.normalizedWeights[key] > state.normalizedWeights[best] ? key : best, keys[0]);
  canonical[adjustmentKey] = Number((canonical[adjustmentKey] + 100 - total).toFixed(4));
  return canonical;
}

function scenarioAnalyticalInputs() {
  const reference = state.scores[0] || {};
  return {
    city_filter: els.cityFilter.value,
    policy_weights: canonicalPolicyWeights(),
    climate_assumption_set: reference.climate_assumption_set || "not_reported",
    validation_filter: validationFilterValue(),
    sensitivity_mode: reference.sensitivity_mode || "not_reported",
    optimization_constraints: optimizationConstraints(),
    source_build_id: state.build.build_id || "unknown"
  };
}

function defaultPolicyActive() {
  return Object.keys(DEFAULT_WEIGHTS).every((key) => Math.abs(state.normalizedWeights[key] - DEFAULT_WEIGHTS[key]) < 0.01)
    && els.cityFilter.value === "All Metro Manila"
    && els.includeHistoric.checked
    && Number(els.portfolioMax.value) === 8
    && els.portfolioGrade.value === "C"
    && Number(els.portfolioEquity.value) === 40;
}

function updateScenarioId() {
  const signature = JSON.stringify(scenarioAnalyticalInputs());
  const nextId = defaultPolicyActive() && state.build.default_scenario_id
    ? state.build.default_scenario_id
    : `scn-live-${hashString(signature)}`;
  if (nextId !== state.scenarioId) state.scenarioCreatedAt = new Date().toISOString();
  state.scenarioId = nextId;
}

function suggestedScenarioTitle() {
  const lens = PRESETS[state.activePreset]?.title || "Custom policy";
  const city = els.cityFilter.value === "All Metro Manila" ? "Metro Manila" : els.cityFilter.value;
  return `${lens} · ${city}`;
}

function currentScenarioObject(title = "") {
  const inputs = scenarioAnalyticalInputs();
  if (!state.scenarioCreatedAt) state.scenarioCreatedAt = new Date().toISOString();
  return {
    scenario_id: state.scenarioId,
    title: boundedScenarioTitle(title || els.scenarioTitle.value || suggestedScenarioTitle()),
    city_filter: inputs.city_filter,
    policy_weights: inputs.policy_weights,
    climate_assumption_set: inputs.climate_assumption_set,
    validation_filter: inputs.validation_filter,
    sensitivity_mode: inputs.sensitivity_mode,
    optimization_constraints: inputs.optimization_constraints,
    created_at: state.scenarioCreatedAt,
    source_build_id: inputs.source_build_id
  };
}

function boundedScenarioTitle(value) {
  return String(value || "").replace(/[\u0000-\u001f\u007f]/g, " ").replace(/\s+/g, " ").trim().slice(0, 80) || "Untitled policy scenario";
}

function savedScenarioIsValid(scenario) {
  if (!scenario || typeof scenario !== "object" || Array.isArray(scenario)) return false;
  const requiredText = ["scenario_id", "title", "city_filter", "climate_assumption_set", "validation_filter", "sensitivity_mode", "created_at", "source_build_id"];
  if (requiredText.some((field) => typeof scenario[field] !== "string" || !scenario[field])) return false;
  const weights = scenario.policy_weights;
  const constraints = scenario.optimization_constraints;
  if (!weights || typeof weights !== "object" || Array.isArray(weights) || !constraints || typeof constraints !== "object" || Array.isArray(constraints)) return false;
  const values = ["climate", "equity", "charging", "operator"].map((key) => Number(weights[key]));
  return values.every((value) => Number.isFinite(value) && value >= 0 && value <= 100)
    && Math.abs(values.reduce((sum, value) => sum + value, 0) - 100) < .1;
}

function readSavedScenarios() {
  try {
    const parsed = JSON.parse(localStorage.getItem(SAVED_SCENARIOS_KEY) || "[]");
    if (!Array.isArray(parsed)) return [];
    const unique = new Map();
    parsed.filter(savedScenarioIsValid).forEach((scenario) => unique.set(scenario.scenario_id, scenario));
    return [...unique.values()].slice(0, MAX_SAVED_SCENARIOS);
  } catch {
    return [];
  }
}

function persistSavedScenarios() {
  try {
    localStorage.setItem(SAVED_SCENARIOS_KEY, JSON.stringify(state.savedScenarios.slice(0, MAX_SAVED_SCENARIOS)));
    return true;
  } catch {
    return false;
  }
}

function setScenarioManagerStatus(message) {
  els.scenarioManagerStatus.textContent = message;
}

function renderSavedScenarioOptions(selectedId = "") {
  const selected = selectedId || els.savedScenarioSelect.value;
  els.savedScenarioSelect.innerHTML = state.savedScenarios.length
    ? `<option value="">Choose a saved scenario</option>${state.savedScenarios.map((scenario) => `<option value="${escapeHtml(scenario.scenario_id)}">${escapeHtml(scenario.title)} · ${escapeHtml(scenario.scenario_id)}</option>`).join("")}`
    : "<option value=\"\">No saved scenarios</option>";
  if (state.savedScenarios.some((scenario) => scenario.scenario_id === selected)) els.savedScenarioSelect.value = selected;
  updateSavedScenarioButtons();
}

function updateSavedScenarioButtons() {
  const hasSelection = Boolean(els.savedScenarioSelect.value);
  els.loadScenario.disabled = !hasSelection;
  els.deleteScenario.disabled = !hasSelection;
}

function resetScenarioToDefault() {
  els.cityFilter.value = "All Metro Manila";
  els.includeHistoric.checked = true;
  Object.entries(DEFAULT_WEIGHTS).forEach(([key, value]) => { weightInputs[key].value = value; });
  els.portfolioMax.value = "8";
  els.portfolioGrade.value = "C";
  els.portfolioEquity.value = "40";
  state.activePreset = "default";
  document.querySelectorAll("[data-preset]").forEach((button) => button.classList.toggle("active", button.dataset.preset === "default"));
  els.scenarioTitle.value = "Climate + Equity · Metro Manila";
  renderAll();
  setScenarioManagerStatus(`Reset to ${state.scenarioId}. Saved scenarios were not deleted.`);
}

function saveCurrentScenario() {
  const scenario = currentScenarioObject();
  const existing = state.savedScenarios.findIndex((item) => item.scenario_id === scenario.scenario_id);
  if (existing >= 0) state.savedScenarios.splice(existing, 1);
  state.savedScenarios.unshift(scenario);
  state.savedScenarios = state.savedScenarios.slice(0, MAX_SAVED_SCENARIOS);
  if (!persistSavedScenarios()) {
    setScenarioManagerStatus("This browser blocked local scenario storage. Copy the JSON instead.");
    return;
  }
  renderSavedScenarioOptions(scenario.scenario_id);
  setScenarioManagerStatus(`Saved “${scenario.title}” as ${scenario.scenario_id} on this device.`);
}

function setSelectValueIfAvailable(select, value) {
  if ([...select.options].some((option) => option.value === String(value))) select.value = String(value);
}

function loadSelectedScenario() {
  const saved = state.savedScenarios.find((scenario) => scenario.scenario_id === els.savedScenarioSelect.value);
  if (!saved) {
    setScenarioManagerStatus("Choose a saved scenario first.");
    return;
  }
  setSelectValueIfAvailable(els.cityFilter, saved.city_filter);
  els.includeHistoric.checked = saved.validation_filter === "historic_baseline_plus_supplied_validation";
  Object.entries(saved.policy_weights).forEach(([key, value]) => {
    if (!weightInputs[key]) return;
    const step = weightInputs[key].step;
    weightInputs[key].step = "any";
    weightInputs[key].value = Number(value);
    weightInputs[key].step = step;
  });
  setSelectValueIfAvailable(els.portfolioMax, saved.optimization_constraints.max_corridors);
  setSelectValueIfAvailable(els.portfolioGrade, saved.optimization_constraints.minimum_evidence_grade);
  setSelectValueIfAvailable(els.portfolioEquity, saved.optimization_constraints.minimum_equity_score);
  state.scenarioId = saved.scenario_id;
  state.scenarioCreatedAt = saved.created_at;
  els.scenarioTitle.value = boundedScenarioTitle(saved.title);
  inferPreset();
  renderAll();
  const currentId = state.scenarioId;
  setScenarioManagerStatus(currentId === saved.scenario_id
    ? `Loaded “${saved.title}” (${currentId}).`
    : `Loaded the saved controls and re-hashed them as ${currentId} for the current build.`);
}

function deleteSelectedScenario() {
  const saved = state.savedScenarios.find((scenario) => scenario.scenario_id === els.savedScenarioSelect.value);
  if (!saved) return;
  if (!window.confirm(`Delete the locally saved scenario “${saved.title}”?`)) return;
  state.savedScenarios = state.savedScenarios.filter((scenario) => scenario.scenario_id !== saved.scenario_id);
  persistSavedScenarios();
  renderSavedScenarioOptions();
  setScenarioManagerStatus(`Deleted “${saved.title}” from this device. The live controls were not changed.`);
}

function legacyClipboardCopy(text) {
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.select();
  const copied = document.execCommand("copy");
  textarea.remove();
  return copied;
}

async function copyCurrentScenarioJson() {
  const scenario = currentScenarioObject();
  const text = JSON.stringify(scenario, null, 2);
  try {
    if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(text);
    else if (!legacyClipboardCopy(text)) throw new Error("clipboard unavailable");
    setScenarioManagerStatus(`Copied normalized scenario JSON for ${scenario.scenario_id}.`);
  } catch {
    setScenarioManagerStatus("Clipboard access was blocked. Save the scenario locally or use the JSON audit export.");
  }
}

function routeIsCurrent(row) {
  const status = String(row.validation_status || "").toLowerCase();
  const active = String(row.active_status || "").toLowerCase();
  return !["", "historic_only", "unvalidated"].includes(status) && !["uncertain", "inactive"].includes(active);
}

function computeLiveScores() {
  state.normalizedWeights = getNormalizedWeights();
  const scored = state.scores.map((row) => {
    const values = Object.fromEntries(Object.entries(SCORE_COLUMNS).map(([key, column]) => [key, numeric(row, column)]));
    const complete = Object.values(values).every((value) => value !== null);
    const liveScore = complete
      ? Object.keys(values).reduce((sum, key) => sum + values[key] * state.normalizedWeights[key] / 100, 0)
      : null;
    return { ...row, liveScore, liveRank: null };
  });
  scored.sort((left, right) => {
    if (left.liveScore === null && right.liveScore === null) return String(left.route_id).localeCompare(String(right.route_id));
    if (left.liveScore === null) return 1;
    if (right.liveScore === null) return -1;
    return right.liveScore - left.liveScore || String(left.route_id).localeCompare(String(right.route_id));
  });
  let rank = 0;
  scored.forEach((row) => {
    if (row.liveScore !== null) row.liveRank = ++rank;
  });
  const city = els.cityFilter.value;
  state.filtered = scored.filter((row) => {
    const cities = String(row.cities_served || "").split("|");
    const cityMatches = city === "All Metro Manila" || cities.includes(city);
    const validationMatches = els.includeHistoric.checked || routeIsCurrent(row);
    return cityMatches && validationMatches;
  });
  updateScenarioId();
}

function activeRow() {
  return state.filtered.find((row) => String(row.route_id) === String(state.selectedRouteId)) || state.filtered[0] || null;
}

function routeLabel(row) {
  const rank = row.liveRank ? `#${row.liveRank}` : "Unranked";
  return `${rank} · ${row.route_long_name} · ${row.route_id}`;
}

function renderCityOptions() {
  const cities = new Set(["All Metro Manila"]);
  state.scores.forEach((row) => String(row.cities_served || "").split("|").filter(Boolean).forEach((city) => cities.add(city)));
  const ordered = [...cities].sort((left, right) => left === "All Metro Manila" ? -1 : right === "All Metro Manila" ? 1 : left.localeCompare(right));
  els.cityFilter.innerHTML = ordered.map((city) => `<option value="${escapeHtml(city)}">${escapeHtml(city)}</option>`).join("");
}

function renderMetrics() {
  const routeCount = Number(state.report.rows_processed) || state.scores.length;
  const validatedCount = Number(state.report.current_validation_count) || state.scores.filter(routeIsCurrent).length;
  const robustCount = Number(state.report.robust_priority_count) || state.scores.filter((row) => String(row.robustness_label).toUpperCase() === "ROBUST PRIORITY").length;
  els.routesMetric.textContent = routeCount.toLocaleString();
  els.validatedMetric.textContent = validatedCount.toLocaleString();
  els.robustMetric.textContent = robustCount.toLocaleString();
  els.heroRobustCount.textContent = robustCount.toLocaleString();
  els.scenarioMetric.textContent = state.scenarioId;
  els.sidebarScenarioId.textContent = state.scenarioId;
  els.scenarioLabId.textContent = state.scenarioId;
}

function renderRouteFinder() {
  els.routeFinder.innerHTML = state.filtered.map((row) => `<option value="${escapeHtml(row.route_id)}">${escapeHtml(routeLabel(row))}</option>`).join("");
  const selectedVisible = state.filtered.some((row) => String(row.route_id) === String(state.selectedRouteId));
  if (!selectedVisible) state.selectedRouteId = state.filtered[0]?.route_id || null;
  if (state.selectedRouteId) els.routeFinder.value = state.selectedRouteId;
}

function deterministicRouteSummary(row) {
  const climateLow = numeric(row, "net_co2e_avoided_t_year_low");
  const climateHigh = numeric(row, "net_co2e_avoided_t_year_high");
  const historicService = numeric(row, "trips_per_day_estimate");
  const mlService = numeric(row, "ml_service_intensity_prediction");
  const missing = row.highest_value_missing_evidence || "current service validation";
  const serviceContext = mlService === null
    ? `Historic schedule service proxy: ${formatNumber(historicService)} trips/day; no ML comparator is available.`
    : `Historic schedule service proxy: ${formatNumber(historicService)} trips/day; ML comparator: ${formatNumber(mlService)} for anomaly analysis, not ridership.`;
  return `${row.route_long_name} is #${row.liveRank || "—"} at ${formatNumber(row.liveScore, 1)}/100 under ${state.scenarioId}. ${serviceContext} Its climate scenario spans ${formatSigned(climateLow)} to ${formatSigned(climateHigh)} tCO₂e/year, while evidence remains Grade ${row.evidence_grade || "—"}. Validate ${missing} before the shortlist is treated as an investment decision.`;
}

function renderRouteLens() {
  const row = activeRow();
  if (!row) {
    els.routeName.textContent = "No routes match this scope";
    els.routeMeta.textContent = "Turn on the historic screening baseline or change the city scope.";
    return;
  }
  const plannerCache = state.routePlannerCache[row.route_id];
  const plannerScenario = plannerCache?.scenario_id || row.scenario_id;
  const useCached = plannerCache?.answer && plannerScenario === state.scenarioId;
  const climateLow = numeric(row, "net_co2e_avoided_t_year_low");
  const climateBase = numeric(row, "net_co2e_avoided_t_year_base");
  const climateHigh = numeric(row, "net_co2e_avoided_t_year_high");
  const topTen = numeric(row, "top_10_probability");
  const evidence = numeric(row, "overall_evidence_confidence");
  const charging = numeric(row, "charging_readiness_score");
  const operator = numeric(row, "operator_effective_score");
  const equity = numeric(row, "equity_score");

  els.routeName.textContent = row.route_long_name;
  els.routeMeta.textContent = `${row.route_id} · ${String(row.cities_served || "Unspecified").replaceAll("|", " · ")} · ${formatNumber(row.length_km, 1)} km`;
  els.routeRationale.textContent = useCached ? plannerCache.answer : deterministicRouteSummary(row);
  els.routeStatusPill.textContent = routeIsCurrent(row) ? "Current validation supplied" : "Historic screening baseline · current status unverified";

  els.priorityClaim.textContent = "DERIVED";
  els.priorityValue.textContent = `${formatNumber(row.liveScore, 1)}/100`;
  els.priorityDetail.textContent = `Live rank #${row.liveRank || "—"} · human-controlled weights`;

  els.evidenceClaim.textContent = String(row.evidence_claim_status || "DERIVED").replaceAll("_", " ");
  els.evidenceValue.textContent = `${row.evidence_grade || "—"} · ${formatNumber(evidence, 1)}`;
  els.evidenceDetail.textContent = row.evidence_limitations || "Evidence limitations unavailable";

  els.climateClaim.textContent = String(row.climate_claim_status || "SCENARIO").replaceAll("_", " ");
  els.climateRange.textContent = `${formatSigned(climateLow)} → ${formatSigned(climateHigh)}`;
  els.climateDetail.textContent = `Base ${formatSigned(climateBase)} tCO₂e/year · ${row.climate_assumption_set || "scenario assumptions"}`;

  els.equityClaim.textContent = String(row.equity_claim_status || "PROXY").replaceAll("_", " ");
  els.equityScore.textContent = `${formatNumber(equity, 1)}/100`;
  els.equityDetail.textContent = row.equity_limitation || "Population exposure proxy";

  els.chargingClaim.textContent = String(row.charging_claim_status || "PROXY").replaceAll("_", " ");
  els.chargingScore.textContent = `${formatNumber(charging, 1)}/100`;
  els.chargingDetail.textContent = `${formatNumber(row.nearest_substation_distance_km, 2)} km to mapped substation · capacity unverified`;

  els.operatorClaim.textContent = String(row.operator_claim_status || "NEUTRAL_PRIOR").replaceAll("_", " ");
  els.operatorScore.textContent = `${formatNumber(operator, 1)}/100`;
  els.operatorDetail.textContent = bool(row.operator_readiness_placeholder) ? "Neutral prior · consent-based evidence not yet supplied" : "Observed operator evidence supplied";

  els.robustnessClaim.textContent = `${formatNumber(row.simulations)} TESTS`;
  els.robustnessScore.textContent = topTen === null ? "N/A" : `${formatNumber(topTen * 100)}% top-10`;
  els.robustnessDetail.textContent = `${row.robustness_label || "Not assessed"} · baseline sensitivity reference`;

  els.typologyClaim.textContent = String(row.typology_claim_status || "ML_ESTIMATED").replaceAll("_", " ");
  els.typologyValue.textContent = row.corridor_type_label || "Unclassified";
  els.typologyDetail.textContent = `${row.clustering_model_version || "model unavailable"}${bool(row.cluster_outlier_flag) ? " · pattern outlier" : ""}`;

  const missing = row.highest_value_missing_evidence || "current service validation";
  els.decisionChangeTitle.textContent = `Highest-value gap: ${String(missing).replaceAll("_", " ")}`;
  els.decisionChangeCopy.textContent = `${row.validation_priority_reason || "Collect direct evidence before proceeding."} Tested rank swing: up to ${formatNumber(row.maximum_rank_swing)} places${bool(row.portfolio_flip_possible) ? "; this field can flip portfolio membership." : "."}`;
  els.currentRank.textContent = `#${row.liveRank || "—"}`;
  els.medianRank.textContent = `#${formatNumber(row.median_rank)}`;
  els.rankRange.textContent = `#${formatNumber(row.rank_p10)}–#${formatNumber(row.rank_p90)}`;

  const lensCards = document.querySelectorAll(".lens-card");
  if (lensCards[1]) lensCards[1].title = row.evidence_limitations || "";
  if (lensCards[2]) lensCards[2].title = "Scenario values depend on electrification share, vehicle efficiency and grid assumptions.";
  if (lensCards[3]) lensCards[3].title = row.equity_limitation || "";
  if (lensCards[4]) lensCards[4].title = row.charging_limitation || "";
}

function renderActiveWeights() {
  const labels = { climate: "Climate", equity: "Equity", charging: "Charging", operator: "Operator" };
  els.activeWeightBars.innerHTML = Object.entries(state.normalizedWeights).map(([key, value]) => `<div><div class="weight-bar-label"><span>${labels[key]}</span><span>${formatNumber(value)}%</span></div><div class="weight-track"><div class="weight-fill" style="width:${Math.max(0, Math.min(100, value))}%"></div></div></div>`).join("");
}

function renderScenarioComparison() {
  const row = activeRow();
  const currentTop = new Set(state.filtered.filter((item) => item.liveRank && item.liveRank <= 10).map((item) => item.route_id));
  const defaultTop = new Set(state.defaultRanked.slice(0, 10).map((item) => item.route_id));
  const entered = [...currentTop].filter((routeId) => !defaultTop.has(routeId));
  const left = [...defaultTop].filter((routeId) => !currentTop.has(routeId));
  const defaultRank = Number(row?.rank);
  const rankDelta = row && Number.isFinite(defaultRank) ? defaultRank - Number(row.liveRank) : 0;
  const scoreDelta = row ? Number(row.liveScore) - Number(row.just_transition_score) : 0;
  const defaultPortfolioIds = new Set(state.defaultPortfolio?.selected_route_ids || []);
  const currentPortfolioIds = new Set(state.portfolioRows.map((item) => item.route_id));
  const portfolioEntered = [...currentPortfolioIds].filter((routeId) => !defaultPortfolioIds.has(routeId));
  const portfolioLeft = [...defaultPortfolioIds].filter((routeId) => !currentPortfolioIds.has(routeId));
  const defaultPortfolioRows = state.scores.filter((item) => defaultPortfolioIds.has(item.route_id));
  const currentClimate = portfolioClimateSummary(state.portfolioRows).base;
  const defaultClimate = portfolioClimateSummary(defaultPortfolioRows).base;
  const average = (rows, field) => rows.length
    ? rows.reduce((sum, item) => sum + (numeric(item, field) || 0), 0) / rows.length
    : 0;
  const equityDelta = average(state.portfolioRows, "equity_score") - average(defaultPortfolioRows, "equity_score");
  const evidenceDelta = average(state.portfolioRows, "overall_evidence_confidence") - average(defaultPortfolioRows, "overall_evidence_confidence");
  els.scenarioComparison.innerHTML = [
    ["Selected rank change", rankDelta === 0 ? "No change" : `${rankDelta > 0 ? "▲" : "▼"} ${Math.abs(rankDelta)} places`],
    ["Selected score change", formatSigned(scoreDelta, 1)],
    ["Entering top 10", entered.length ? entered.slice(0, 3).join(", ") : "None"],
    ["Leaving top 10", left.length ? left.slice(0, 3).join(", ") : "None"],
    ["Portfolio change", portfolioEntered.length || portfolioLeft.length ? `${portfolioEntered.length} in · ${portfolioLeft.length} out` : "No change"],
    ["Climate impact change", `${formatSigned(currentClimate - defaultClimate)} tCO₂e/yr`],
    ["Average equity change", formatSigned(equityDelta, 1)],
    ["Evidence-quality change", formatSigned(evidenceDelta, 1)]
  ].map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("");
}

function gradeRank(grade) {
  return ({ A: 1, B: 2, C: 3, D: 4, E: 5 })[String(grade || "E").toUpperCase()] || 5;
}

function usePrecomputedPortfolio() {
  return defaultPolicyActive()
    && Number(els.portfolioMax.value) === 8
    && els.portfolioGrade.value === "C"
    && Number(els.portfolioEquity.value) === 40
    && state.defaultPortfolio;
}

function deriveInteractivePortfolio() {
  const max = Number(els.portfolioMax.value);
  const gradeLimit = gradeRank(els.portfolioGrade.value);
  const equityFloor = Number(els.portfolioEquity.value);
  const cityCount = new Map();
  const corridors = new Set();
  const selected = [];
  for (const row of state.filtered) {
    if (row.liveScore === null || gradeRank(row.evidence_grade) > gradeLimit || Number(row.equity_score) < equityFloor) continue;
    const corridor = row.normalized_corridor_id || row.route_id;
    const city = row.primary_city || "Unspecified";
    if (corridors.has(corridor) || (cityCount.get(city) || 0) >= 2) continue;
    selected.push(row);
    corridors.add(corridor);
    cityCount.set(city, (cityCount.get(city) || 0) + 1);
    if (selected.length >= max) break;
  }
  return selected;
}

function portfolioClimateSummary(rows) {
  return rows.reduce((totals, row) => ({
    low: totals.low + (numeric(row, "net_co2e_avoided_t_year_low") || 0),
    base: totals.base + (numeric(row, "net_co2e_avoided_t_year_base") || 0),
    high: totals.high + (numeric(row, "net_co2e_avoided_t_year_high") || 0)
  }), { low: 0, base: 0, high: 0 });
}

function renderPortfolio() {
  const precomputed = usePrecomputedPortfolio();
  state.portfolioIsPrecomputed = Boolean(precomputed);
  if (precomputed) {
    const selectedIds = new Set(state.defaultPortfolio.selected_route_ids || []);
    state.portfolioRows = [...state.scores].filter((row) => selectedIds.has(row.route_id)).sort((left, right) => (state.defaultPortfolio.selected_route_ids || []).indexOf(left.route_id) - (state.defaultPortfolio.selected_route_ids || []).indexOf(right.route_id));
    state.portfolioScenarioId = state.defaultPortfolio.scenario_id;
  } else {
    state.portfolioRows = deriveInteractivePortfolio();
    const signature = `${state.scenarioId}|${els.portfolioMax.value}|${els.portfolioGrade.value}|${els.portfolioEquity.value}|${state.portfolioRows.map((row) => row.route_id).join("|")}`;
    state.portfolioScenarioId = `prt-live-${hashString(signature)}`;
  }
  const rows = state.portfolioRows;
  const climate = precomputed?.portfolio_climate_impact_t_year || portfolioClimateSummary(rows);
  const averageEquity = rows.length ? rows.reduce((sum, row) => sum + (numeric(row, "equity_score") || 0), 0) / rows.length : 0;
  const gradeCounts = rows.reduce((counts, row) => ({ ...counts, [row.evidence_grade || "—"]: (counts[row.evidence_grade || "—"] || 0) + 1 }), {});
  const simpleTop = state.filtered.slice(0, Number(els.portfolioMax.value));
  const simpleIds = new Set(simpleTop.map((row) => row.route_id));
  const selectedIds = new Set(rows.map((row) => row.route_id));
  const added = precomputed ? (state.defaultPortfolio.added_by_constraints || []) : rows.filter((row) => !simpleIds.has(row.route_id)).map((row) => row.route_id);
  const removed = precomputed ? (state.defaultPortfolio.removed_by_constraints || []) : simpleTop.filter((row) => !selectedIds.has(row.route_id)).map((row) => row.route_id);
  const nearSelection = state.filtered.filter((row) => row.liveScore !== null && !selectedIds.has(row.route_id)).slice(0, 3);

  els.portfolioScenarioId.textContent = state.portfolioScenarioId;
  els.portfolioCount.textContent = rows.length.toLocaleString();
  els.portfolioClimate.textContent = `${formatSigned(climate.low)} → ${formatSigned(climate.high)}`;
  els.portfolioEquityMetric.textContent = formatNumber(precomputed?.average_equity_score ?? averageEquity, 1);
  els.portfolioEvidence.textContent = Object.entries(precomputed?.evidence_grade_distribution || gradeCounts).map(([grade, count]) => `${grade}:${count}`).join(" · ") || "None";
  els.portfolioModePill.textContent = precomputed ? "Precomputed default" : "Interactive deterministic preview";
  els.portfolioList.innerHTML = rows.length
    ? rows.map((row, index) => `<div class="portfolio-item"><b>${String(index + 1).padStart(2, "0")}</b><button type="button" data-route-id="${escapeHtml(row.route_id)}">${escapeHtml(row.route_long_name)}<small>${escapeHtml(row.primary_city || "Unspecified")} · Grade ${escapeHtml(row.evidence_grade || "—")}</small></button><span>${formatNumber(row.liveScore ?? row.just_transition_score, 1)}</span></div>`).join("")
    : `<p class="portfolio-alert" role="status"><strong>No feasible shortlist.</strong> No route satisfies Grade ${escapeHtml(els.portfolioGrade.value)} or better, equity ≥${escapeHtml(els.portfolioEquity.value)}, and the current city/validation scope. Relax a conflicting constraint; no substitute result has been fabricated.</p>`;
  const nearSelectionRows = nearSelection.map((row) => {
    const reason = row.portfolio_exclusion_reason
      || (gradeRank(row.evidence_grade) > gradeRank(els.portfolioGrade.value) ? `evidence Grade ${row.evidence_grade || "missing"}`
        : Number(row.equity_score) < Number(els.portfolioEquity.value) ? `equity ${formatNumber(row.equity_score, 1)} below floor`
          : "corridor or city-diversity constraint");
    return `<li><b>${escapeHtml(row.route_id)}</b> · ${escapeHtml(reason)}</li>`;
  }).join("");
  els.portfolioDelta.innerHTML = `<p>${precomputed ? "The pipeline enforces corridor and city diversity instead of simply taking the first eight rows." : "This preview applies the active policy score, evidence floor, equity floor, one direction per corridor and at most two corridors per primary city."}</p><div class="delta-group"><div><b>Added by constraints</b><span>${escapeHtml(added.length ? added.slice(0, 5).join(", ") : "None")}</span></div><div><b>Removed from top-N</b><span>${escapeHtml(removed.length ? removed.slice(0, 5).join(", ") : "None")}</span></div></div><div class="near-selection"><b>Near selection / exclusion reason</b><ul>${nearSelectionRows || "<li>No eligible near-selection route.</li>"}</ul></div>`;
  const constraints = precomputed?.binding_constraints || [
    `maximum ${els.portfolioMax.value} corridors`,
    "maximum 2 corridors per primary city",
    "maximum 1 direction per normalized corridor",
    `minimum evidence grade ${els.portfolioGrade.value}`,
    `minimum equity score ${els.portfolioEquity.value}`
  ];
  els.portfolioConstraints.innerHTML = constraints.map((constraint) => `<li>${escapeHtml(constraint)}</li>`).join("");
}

function renderLeaderboard() {
  const rows = state.filtered.filter((row) => row.liveScore !== null).slice(0, 12);
  els.leaderboardBody.innerHTML = rows.map((row) => {
    const climateLow = numeric(row, "net_co2e_avoided_t_year_low");
    const climateHigh = numeric(row, "net_co2e_avoided_t_year_high");
    return `<tr class="${row.route_id === state.selectedRouteId ? "selected-row" : ""}"><td>#${row.liveRank}</td><td><button class="route-table-button" type="button" data-route-id="${escapeHtml(row.route_id)}">${escapeHtml(row.route_long_name)}<small>${escapeHtml(row.route_id)}</small></button></td><td>${escapeHtml(row.primary_city || "Unspecified")}</td><td><b>${formatNumber(row.liveScore, 1)}</b></td><td>${escapeHtml(row.evidence_grade || "—")} · ${formatNumber(row.overall_evidence_confidence, 1)}</td><td>${formatSigned(climateLow)} → ${formatSigned(climateHigh)}</td><td>${escapeHtml(row.robustness_label || "Not assessed")}</td></tr>`;
  }).join("");
  els.mobileRouteCards.innerHTML = rows.map((row) => `<button class="mobile-route-card ${row.route_id === state.selectedRouteId ? "selected" : ""}" type="button" data-route-id="${escapeHtml(row.route_id)}"><b>#${row.liveRank}</b><span><strong>${escapeHtml(row.route_long_name)}</strong><small>${escapeHtml(row.primary_city || "Unspecified")} · Evidence ${escapeHtml(row.evidence_grade || "—")}</small></span><span>${formatNumber(row.liveScore, 1)}</span></button>`).join("");
}

function renderEvidenceQueue() {
  const portfolioIds = new Set(state.portfolioRows.map((row) => row.route_id));
  const rows = [...state.filtered].filter((row) => numeric(row, "validation_priority_score") !== null).sort((left, right) => {
    const portfolioDifference = Number(portfolioIds.has(right.route_id)) - Number(portfolioIds.has(left.route_id));
    const flipDifference = Number(bool(right.portfolio_flip_possible)) - Number(bool(left.portfolio_flip_possible));
    return portfolioDifference || flipDifference || Number(right.validation_priority_score) - Number(left.validation_priority_score) || Number(right.maximum_rank_swing) - Number(left.maximum_rank_swing);
  }).slice(0, 6);
  const evidenceOwner = (field) => {
    const value = String(field || "").toLowerCase();
    if (value.includes("operator") || value.includes("fleet") || value.includes("depot")) return "Operator / cooperative";
    if (value.includes("charging") || value.includes("utility") || value.includes("capacity")) return "Utility + LGU energy team";
    if (value.includes("climate") || value.includes("efficiency") || value.includes("emission")) return "LGU climate team";
    if (value.includes("equity") || value.includes("accessibility") || value.includes("socioeconomic")) return "LGU + community research";
    if (value.includes("geometry") || value.includes("route") || value.includes("service") || value.includes("active")) return "LGU + field team";
    return "Field validation team";
  };
  els.evidenceQueue.innerHTML = rows.map((row, index) => {
    const field = row.highest_value_missing_evidence || "current validation";
    const signal = bool(row.portfolio_flip_possible) ? "Portfolio flip possible" : `Priority ${formatNumber(row.validation_priority_score)}`;
    return `<div class="evidence-item"><b>${String(index + 1).padStart(2, "0")}</b><button type="button" data-route-id="${escapeHtml(row.route_id)}">${escapeHtml(row.route_long_name)}<small>${escapeHtml(String(field).replaceAll("_", " "))} · up to ${formatNumber(row.maximum_rank_swing)}-place swing</small></button><span><b>${escapeHtml(evidenceOwner(field))}</b><small>${escapeHtml(signal)}</small></span></div>`;
  }).join("");
}

function renderSourceHealth() {
  const models = state.build.model_versions || {};
  const sourceCount = state.sources.source_count ?? state.sources.sources?.length ?? 0;
  const warnings = state.report.warnings || [];
  const total = state.scores.length || 1;
  const percentage = (count) => `${formatNumber(count / total * 100, 1)}%`;
  const currentCount = state.scores.filter(routeIsCurrent).length;
  const operatorVerified = state.scores.filter((row) => !bool(row.operator_readiness_placeholder)).length;
  const chargingVerified = state.scores.filter((row) => bool(row.charging_site_verified)).length;
  const reliableGeometry = state.scores.filter((row) => bool(row.geometry_verified) || ["A", "B"].includes(String(row.geometry_reliability_grade).toUpperCase())).length;
  const incompleteScores = state.scores.filter((row) => !bool(row.score_complete)).length;
  const sourcePeriods = [...new Set((state.sources.sources || []).map((source) => source.reference_period).filter(Boolean))];
  const criticalMissing = Object.values(state.report.critical_missing_values || {}).reduce((sum, value) => sum + (Number(value) || 0), 0);
  const gapCounts = state.scores.reduce((counts, row) => {
    const field = String(row.highest_value_missing_evidence || "unspecified").replaceAll("_", " ");
    counts[field] = (counts[field] || 0) + 1;
    return counts;
  }, {});
  const leadingGaps = Object.entries(gapCounts).sort((left, right) => right[1] - left[1]).slice(0, 3).map(([field, count]) => `${field} (${count})`).join(" · ");
  els.sourceHealth.innerHTML = [
    ["Pipeline", `${state.report.status || "Unknown"} · ${formatNumber(state.report.rows_processed)} rows`],
    ["Build", `${state.build.build_id || "Unknown"} · ${state.build.build_timestamp_utc || "Unknown time"}`],
    ["Models", `${models.service_intensity || "No service model"} · ${models.corridor_typology || "No typology model"}`],
    ["Sources", `${sourceCount} registered · checksummed build manifest`],
    ["Source periods", sourcePeriods.length ? sourcePeriods.join(" · ") : "No source dates reported"],
    ["Evidence coverage", `${percentage(total - currentCount)} historic-only · ${percentage(currentCount)} current validation · ${percentage(operatorVerified)} operator evidence · ${percentage(chargingVerified)} verified charging site · ${percentage(reliableGeometry)} reliable geometry`],
    ["Missing values", `${criticalMissing} missing values across monitored analytical fields · ${incompleteScores} incomplete policy-score rows · leading evidence gaps: ${leadingGaps || "none reported"}`],
    ["Current validation", `${formatNumber(state.report.current_validation_count)} routes · historic status remains explicit`],
    ["Pipeline warnings", warnings.length ? warnings.join(" ") : "No warnings reported"]
  ].map(([title, copy]) => `<div><strong>${escapeHtml(title)}</strong>${escapeHtml(copy)}</div>`).join("");
}

function layerValue(row) {
  const definition = LAYERS[state.activeLayer];
  if (definition.field === "liveScore") return row.liveScore;
  return definition.kind === "numeric" ? numeric(row, definition.field) : String(row[definition.field] || "unknown");
}

function routePointCollection() {
  const selectedPortfolio = new Set(state.portfolioRows.map((row) => String(row.route_id)));
  const features = state.filtered.map((row) => {
    const coordinates = state.pathByRoute.get(String(row.route_id));
    if (!coordinates?.length) return null;
    const midpoint = coordinates[Math.floor(coordinates.length / 2)];
    return {
      type: "Feature",
      properties: {
        routeId: String(row.route_id),
        title: row.route_long_name,
        score: Number(row.liveScore?.toFixed(2) || 0),
        rank: row.liveRank || 0,
        value: layerValue(row),
        category: String(layerValue(row)),
        layerLabel: LAYERS[state.activeLayer].label,
        evidenceGrade: row.evidence_grade || "—",
        robustness: row.robustness_label || "Not assessed",
        validation: row.validation_status || "unvalidated",
        portfolio: selectedPortfolio.has(String(row.route_id)) ? 1 : 0,
        selected: String(row.route_id) === String(state.selectedRouteId) ? 1 : 0
      },
      geometry: { type: "Point", coordinates: midpoint }
    };
  }).filter(Boolean);
  return { type: "FeatureCollection", features };
}

function mapColorExpression() {
  const definition = LAYERS[state.activeLayer];
  if (definition.kind === "typology") {
    return ["match", ["get", "category"], "0", "#5bb8f5", "1", "#50ddbd", "2", "#c7f459", "3", "#ffbf4b", "#9ca9aa"];
  }
  if (definition.kind === "validation") {
    return ["match", ["get", "category"], "validated_current", "#50ddbd", "observed_current", "#5bb8f5", "historic_only", "#ffbf4b", "#9ca9aa"];
  }
  return ["interpolate", ["linear"], ["coalesce", ["to-number", ["get", "value"]], 0], 0, "#ff7068", 50, "#ffbf4b", 100, "#50ddbd"];
}

function renderMapLegend() {
  const definition = LAYERS[state.activeLayer];
  if (definition.kind === "typology") {
    const types = [...new Map(state.filtered.map((row) => [String(row.corridor_cluster_id), row.corridor_type_label])).entries()].slice(0, 4);
    const colors = ["#5bb8f5", "#50ddbd", "#c7f459", "#ffbf4b"];
    els.mapLegend.innerHTML = types.map(([cluster, label], index) => `<span><i style="background:${colors[Number(cluster) % colors.length] || colors[index]}"></i>${escapeHtml(label || `Cluster ${cluster}`)}</span>`).join("");
  } else if (definition.kind === "validation") {
    els.mapLegend.innerHTML = "<span><i style=\"background:#50ddbd\"></i>Current validated</span><span><i style=\"background:#5bb8f5\"></i>Current observed</span><span><i style=\"background:#ffbf4b\"></i>Historic only</span>";
  } else {
    els.mapLegend.innerHTML = `<span><i style="background:#ff7068"></i>Lower ${escapeHtml(definition.label)}</span><span><i style="background:#ffbf4b"></i>Mid</span><span><i style="background:#50ddbd"></i>Higher</span>`;
  }
  els.mapCount.textContent = `${state.filtered.length.toLocaleString()} of ${state.scores.length.toLocaleString()} routes shown · all current-scope points loaded`;
}

function emptyFeatureCollection() {
  return { type: "FeatureCollection", features: [] };
}

function updateRoadStatus(message, type = "") {
  els.roadStatus.className = `road-status${type ? ` ${type}` : ""}`;
  els.roadStatus.querySelector("span").textContent = message;
}

function initialiseMap() {
  if (!MAPBOX_ACCESS_TOKEN) {
    updateRoadStatus("Mapbox is unavailable. The route list and evidence panels remain usable.", "error");
    byId("map").innerHTML = "<div class=\"map-empty\">Mapbox configuration unavailable.</div>";
    return;
  }
  if (!window.mapboxgl) {
    updateRoadStatus("Mapbox could not load. Check the network connection.", "error");
    return;
  }
  state.map = new window.mapboxgl.Map({
    accessToken: MAPBOX_ACCESS_TOKEN,
    container: "map",
    style: MAPBOX_STYLE_URL,
    center: [121.02, 14.61],
    zoom: 9.45,
    pitch: 18,
    bearing: -7,
    attributionControl: true,
    preserveDrawingBuffer: true
  });
  state.map.addControl(new window.mapboxgl.NavigationControl({ visualizePitch: true }), "top-right");
  state.map.addControl(new window.mapboxgl.FullscreenControl(), "top-right");
  state.map.on("load", () => {
    state.mapReady = true;
    state.map.addSource("route-points", { type: "geojson", data: routePointCollection(), cluster: true, clusterMaxZoom: 13, clusterRadius: 42 });
    state.map.addLayer({ id: "route-clusters", type: "circle", source: "route-points", filter: ["has", "point_count"], paint: { "circle-color": "#0a3436", "circle-radius": ["step", ["get", "point_count"], 17, 25, 22, 90, 28], "circle-stroke-color": "#c7f459", "circle-stroke-width": 2, "circle-opacity": .93 } });
    state.map.addLayer({ id: "cluster-count", type: "symbol", source: "route-points", filter: ["has", "point_count"], layout: { "text-field": ["get", "point_count_abbreviated"], "text-size": 11 }, paint: { "text-color": "#ffffff" } });
    state.map.addLayer({ id: "route-points-layer", type: "circle", source: "route-points", filter: ["!", ["has", "point_count"]], paint: { "circle-color": mapColorExpression(), "circle-radius": ["interpolate", ["linear"], ["zoom"], 8, ["case", ["==", ["get", "selected"], 1], 7, 4], 13, ["case", ["==", ["get", "selected"], 1], 11, 7]], "circle-stroke-color": ["case", ["==", ["get", "portfolio"], 1], "#071a20", "#ffffff"], "circle-stroke-width": ["case", ["==", ["get", "selected"], 1], 4, ["==", ["get", "portfolio"], 1], 2.5, 1.4], "circle-opacity": .92 } });
    state.map.addSource("selected-route", { type: "geojson", data: { type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: [] } } });
    state.map.addLayer({ id: "selected-route-casing", type: "line", source: "selected-route", layout: { "line-cap": "round", "line-join": "round" }, paint: { "line-color": "#06191f", "line-width": ["interpolate", ["linear"], ["zoom"], 9, 7, 15, 13], "line-opacity": .94, "line-dasharray": [2, 1.3] } });
    state.map.addLayer({ id: "selected-route-line", type: "line", source: "selected-route", layout: { "line-cap": "round", "line-join": "round" }, paint: { "line-color": "#c7f459", "line-width": ["interpolate", ["linear"], ["zoom"], 9, 3.5, 15, 7.5], "line-opacity": 1, "line-dasharray": [2, 1.3] } });
    state.map.addSource("selected-endpoints", { type: "geojson", data: emptyFeatureCollection() });
    state.map.addLayer({ id: "selected-endpoints-layer", type: "circle", source: "selected-endpoints", paint: { "circle-radius": 7, "circle-color": ["match", ["get", "kind"], "start", "#50ddbd", "#ffbf4b"], "circle-stroke-color": "#06191f", "circle-stroke-width": 2 } });

    state.map.on("click", "route-clusters", (event) => {
      const feature = state.map.queryRenderedFeatures(event.point, { layers: ["route-clusters"] })[0];
      if (!feature) return;
      state.map.getSource("route-points").getClusterExpansionZoom(feature.properties.cluster_id, (error, zoom) => {
        if (!error) state.map.easeTo({ center: feature.geometry.coordinates, zoom });
      });
    });
    state.map.on("click", "route-points-layer", (event) => {
      const feature = event.features?.[0];
      if (feature) setSelected(String(feature.properties.routeId), true);
    });
    state.map.on("mouseenter", "route-points-layer", (event) => {
      state.map.getCanvas().style.cursor = "pointer";
      const feature = event.features?.[0];
      if (!feature) return;
      state.hoverPopup?.remove();
      const value = LAYERS[state.activeLayer].kind === "numeric" ? formatNumber(feature.properties.value, 1) : feature.properties.value;
      state.hoverPopup = new window.mapboxgl.Popup({ closeButton: false, closeOnClick: false, offset: 12, className: "route-hover-popup" })
        .setLngLat(feature.geometry.coordinates)
        .setHTML(`<div class="map-popup"><b>${escapeHtml(feature.properties.title)}</b><span>#${escapeHtml(feature.properties.rank)} · ${escapeHtml(feature.properties.layerLabel)} ${escapeHtml(value)}</span><span>Evidence ${escapeHtml(feature.properties.evidenceGrade)} · ${escapeHtml(feature.properties.robustness)}</span><span>Status: ${escapeHtml(String(feature.properties.validation).replaceAll("_", " "))}</span></div>`)
        .addTo(state.map);
    });
    state.map.on("mouseleave", "route-points-layer", () => {
      state.map.getCanvas().style.cursor = "";
      state.hoverPopup?.remove();
      state.hoverPopup = null;
    });
    state.map.on("mouseenter", "route-clusters", () => { state.map.getCanvas().style.cursor = "pointer"; });
    state.map.on("mouseleave", "route-clusters", () => { state.map.getCanvas().style.cursor = ""; });
    renderMapLegend();
    refreshMapData();
    drawSelectedRoadRoute();
  });
  state.map.on("error", (event) => {
    if (!state.mapReady && event?.error) updateRoadStatus("The Mapbox style could not load. Verify that the public style is accessible.", "error");
  });
  state.mapResizeObserver = new ResizeObserver(() => state.map?.resize());
  state.mapResizeObserver.observe(byId("map"));
}

function refreshMapData() {
  renderMapLegend();
  if (!state.mapReady) return;
  const source = state.map.getSource("route-points");
  if (source) source.setData(routePointCollection());
  if (state.map.getLayer("route-points-layer")) state.map.setPaintProperty("route-points-layer", "circle-color", mapColorExpression());
}

function cleanedCoordinates(routeId) {
  const coordinates = state.pathByRoute.get(String(routeId)) || [];
  const valid = coordinates.filter((point) => Array.isArray(point) && point.length >= 2 && Number.isFinite(Number(point[0])) && Number.isFinite(Number(point[1]))).map((point) => [Number(point[0]), Number(point[1])]);
  return valid.filter((point, index) => index === 0 || point[0] !== valid[index - 1][0] || point[1] !== valid[index - 1][1]);
}

function coordinateChunks(coordinates, size = 25) {
  const chunks = [];
  for (let start = 0; start < coordinates.length - 1; start += size - 1) {
    const chunk = coordinates.slice(start, start + size);
    if (chunk.length >= 2) chunks.push(chunk);
  }
  return chunks;
}

async function requestRoadGeometry(routeId, signal) {
  if (state.roadGeometryCache.has(routeId)) return state.roadGeometryCache.get(routeId);
  try {
    const stored = sessionStorage.getItem(`r2z-road-${routeId}`);
    const parsed = stored ? JSON.parse(stored) : null;
    if (Array.isArray(parsed) && parsed.length >= 2) {
      state.roadGeometryCache.set(routeId, parsed);
      return parsed;
    }
  } catch { /* Session cache is optional. */ }
  const coordinates = cleanedCoordinates(routeId);
  if (coordinates.length < 2) throw new Error("not enough ordered coordinates");
  const results = [];
  for (const chunk of coordinateChunks(coordinates)) {
    const coordinateString = chunk.map((point) => `${point[0].toFixed(6)},${point[1].toFixed(6)}`).join(";");
    const url = `https://api.mapbox.com/directions/v5/mapbox/driving/${coordinateString}?alternatives=false&continue_straight=true&geometries=geojson&overview=full&steps=false&access_token=${encodeURIComponent(MAPBOX_ACCESS_TOKEN)}`;
    const response = await fetch(url, { signal });
    const data = await response.json();
    if (!response.ok || !data.routes?.[0]?.geometry?.coordinates) throw new Error(data.message || "road match unavailable");
    results.push(data.routes[0].geometry.coordinates);
  }
  const merged = [];
  results.forEach((part) => part.forEach((point, index) => {
    if (index > 0 || merged.length === 0) merged.push(point);
  }));
  if (merged.length < 2) throw new Error("empty road match");
  state.roadGeometryCache.set(routeId, merged);
  try { sessionStorage.setItem(`r2z-road-${routeId}`, JSON.stringify(merged)); } catch { /* Memory cache remains available. */ }
  return merged;
}

function fitMapToCoordinates(coordinates) {
  if (!state.mapReady || coordinates.length < 2) return;
  const bounds = coordinates.reduce((box, coordinate) => box.extend(coordinate), new window.mapboxgl.LngLatBounds(coordinates[0], coordinates[0]));
  state.map.fitBounds(bounds, { padding: window.innerWidth < 700 ? { top: 72, right: 42, bottom: 90, left: 42 } : 78, maxZoom: 14.5, duration: 850 });
}

function applyRouteLineStyle(_row, fallback) {
  if (!state.mapReady) return;
  const dash = fallback ? [1, 1.6] : [1000, 0];
  const color = fallback ? "#ffbf4b" : "#c7f459";
  state.map.setPaintProperty("selected-route-line", "line-dasharray", dash);
  state.map.setPaintProperty("selected-route-casing", "line-dasharray", dash);
  state.map.setPaintProperty("selected-route-line", "line-color", color);
}

async function drawSelectedRoadRoute() {
  if (!state.mapReady || !state.selectedRouteId) return;
  state.roadAbort?.abort();
  state.roadAbort = new AbortController();
  const requestId = ++state.roadRequestId;
  const row = activeRow();
  const raw = cleanedCoordinates(state.selectedRouteId);
  const lineSource = state.map.getSource("selected-route");
  const endpointSource = state.map.getSource("selected-endpoints");
  if (!row || raw.length < 2) {
    lineSource.setData({ type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: [] } });
    endpointSource.setData(emptyFeatureCollection());
    updateRoadStatus("This corridor does not have enough coordinates to map.", "error");
    return;
  }
  lineSource.setData({ type: "Feature", properties: { routeId: row.route_id, source: "gtfs_stop_sequence" }, geometry: { type: "LineString", coordinates: raw } });
  endpointSource.setData({ type: "FeatureCollection", features: [
    { type: "Feature", properties: { kind: "start" }, geometry: { type: "Point", coordinates: raw[0] } },
    { type: "Feature", properties: { kind: "end" }, geometry: { type: "Point", coordinates: raw[raw.length - 1] } }
  ] });
  applyRouteLineStyle(row, true);
  fitMapToCoordinates(raw);
  updateRoadStatus("Matching the ordered GTFS corridor to drivable streets…");
  try {
    const road = await requestRoadGeometry(row.route_id, state.roadAbort.signal);
    if (requestId !== state.roadRequestId || row.route_id !== state.selectedRouteId) return;
    lineSource.setData({ type: "Feature", properties: { routeId: row.route_id, source: "mapbox_directions" }, geometry: { type: "LineString", coordinates: road } });
    applyRouteLineStyle(row, false);
    fitMapToCoordinates(road);
    const geometryNote = bool(row.geometry_verified) ? "source geometry verified" : `source geometry Grade ${row.geometry_reliability_grade || "—"}, unverified`;
    updateRoadStatus(`Street-following Mapbox path ready · ${geometryNote}`, "success");
  } catch (error) {
    if (error?.name === "AbortError" || requestId !== state.roadRequestId) return;
    applyRouteLineStyle(row, true);
    updateRoadStatus("Mapbox road match unavailable · dashed GTFS stop-sequence fallback shown", "warning");
  }
}

function setSelected(routeId, scrollToLens = false) {
  if (!state.filtered.some((row) => String(row.route_id) === String(routeId))) return;
  state.selectedRouteId = String(routeId);
  els.routeFinder.value = state.selectedRouteId;
  renderRouteLens();
  renderScenarioComparison();
  renderLeaderboard();
  renderEvidenceQueue();
  refreshMapData();
  drawSelectedRoadRoute();
  if (scrollToLens) byId("route-lens").scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderAll() {
  const previousSelected = state.selectedRouteId;
  computeLiveScores();
  renderMetrics();
  renderRouteFinder();
  renderRouteLens();
  renderActiveWeights();
  renderPortfolio();
  renderScenarioComparison();
  renderLeaderboard();
  renderEvidenceQueue();
  refreshMapData();
  if (state.mapReady && previousSelected !== state.selectedRouteId) drawSelectedRoadRoute();
}

function setPreset(name) {
  const preset = PRESETS[name] || PRESETS.default;
  Object.entries(preset.weights).forEach(([key, value]) => { weightInputs[key].value = value; });
  state.activePreset = name;
  document.querySelectorAll("[data-preset]").forEach((button) => button.classList.toggle("active", button.dataset.preset === name));
  renderAll();
}

function inferPreset() {
  const normalized = getNormalizedWeights();
  const matched = Object.entries(PRESETS).find(([, preset]) => Object.keys(DEFAULT_WEIGHTS).every((key) => Math.abs(normalized[key] - preset.weights[key]) < .01));
  state.activePreset = matched?.[0] || "custom";
  document.querySelectorAll("[data-preset]").forEach((button) => button.classList.toggle("active", button.dataset.preset === state.activePreset));
}

function assistantContext(question) {
  const row = activeRow();
  return {
    question,
    scenario: {
      scenario_id: state.scenarioId,
      build_id: state.build.build_id,
      policy_model_version: row?.policy_model_version || "policy-v2.0",
      climate_assumption_set: row?.climate_assumption_set || "not reported",
      sensitivity_method: row?.sensitivity_method || "not reported",
      sensitivity_mode: row?.sensitivity_mode || "not reported",
      weights: Object.fromEntries(Object.entries(canonicalPolicyWeights()).map(([key, value]) => [key, Number((value / 100).toFixed(6))])),
      city_scope: els.cityFilter.value,
      historic_baseline_included: els.includeHistoric.checked,
      validation_filter: els.includeHistoric.checked ? "historic baseline plus supplied current validation" : "supplied current validation only"
    },
    route: row ? {
      route_id: row.route_id,
      route_long_name: row.route_long_name,
      live_rank: row.liveRank,
      live_priority_score: Number(row.liveScore?.toFixed(2)),
      evidence_grade: row.evidence_grade,
      evidence_confidence: numeric(row, "overall_evidence_confidence"),
      robustness_label: row.robustness_label,
      top_10_probability: numeric(row, "top_10_probability"),
      rank_p10: numeric(row, "rank_p10"),
      rank_p90: numeric(row, "rank_p90"),
      climate_low_t_year: numeric(row, "net_co2e_avoided_t_year_low"),
      climate_base_t_year: numeric(row, "net_co2e_avoided_t_year_base"),
      climate_high_t_year: numeric(row, "net_co2e_avoided_t_year_high"),
      equity_score: numeric(row, "equity_score"),
      charging_readiness_score: numeric(row, "charging_readiness_score"),
      operator_effective_score: numeric(row, "operator_effective_score"),
      highest_value_missing_evidence: row.highest_value_missing_evidence,
      maximum_rank_swing: numeric(row, "maximum_rank_swing"),
      portfolio_flip_possible: bool(row.portfolio_flip_possible),
      validation_priority_reason: row.validation_priority_reason,
      validation_status: row.validation_status,
      active_status: row.active_status,
      utility_capacity_verified: bool(row.utility_capacity_verified),
      operator_readiness_placeholder: bool(row.operator_readiness_placeholder),
      claim_statuses: {
        climate: row.climate_claim_status,
        equity: row.equity_claim_status,
        charging: row.charging_claim_status,
        operator: row.operator_claim_status
      }
    } : null,
    portfolio: {
      portfolio_scenario_id: state.portfolioScenarioId,
      mode: state.portfolioIsPrecomputed ? "precomputed_default" : "interactive_preview",
      selected_route_ids: state.portfolioRows.map((item) => item.route_id),
      constraints: { max_corridors: Number(els.portfolioMax.value), minimum_evidence_grade: els.portfolioGrade.value, minimum_equity_score: Number(els.portfolioEquity.value) }
    }
  };
}

function localAssistantFallback(context) {
  const route = context.route;
  if (!route) return { answer: "No route is available in the current scope.", actions: ["Restore the historic screening baseline or change the city scope."] };
  const missing = String(route.highest_value_missing_evidence || "current service validation").replaceAll("_", " ");
  return {
    answer: `${route.route_long_name} is #${route.live_rank} under ${context.scenario.scenario_id}. Validate ${missing} first because the deterministic perturbation test allows a rank swing of up to ${formatNumber(route.maximum_rank_swing)} places${route.portfolio_flip_possible ? " and can change portfolio membership" : ""}.`,
    actions: ["Confirm current route status and observed service.", "Request utility evidence before claiming charging capacity.", "Collect consent-based operator and depot evidence."]
  };
}

function renderAssistantAnswer(data) {
  const answer = escapeHtml(data.answer || "No answer was returned.");
  const actions = Array.isArray(data.actions) ? data.actions.slice(0, 5) : [];
  els.answerText.innerHTML = `<p>${answer}</p>${actions.length ? `<ul>${actions.map((action) => `<li>${escapeHtml(action)}</li>`).join("")}</ul>` : ""}`;
  const sourceLabels = {
    netlify_function_api: "AI-generated · structured evidence",
    deterministic_fallback: data.ai_status === "disabled" ? "AI disabled · evidence-only response" : "AI unavailable · evidence-only response",
    precomputed_planner_cache: "Precomputed evidence plan"
  };
  els.answerSource.textContent = sourceLabels[data.source] || "Structured evidence response";
  els.answerSource.classList.remove("hidden");
}

async function askQuestion() {
  const question = els.questionInput.value.trim();
  if (!question) {
    els.questionInput.focus();
    return;
  }
  const context = assistantContext(question);
  const key = `${state.scenarioId}|${context.route?.route_id || "none"}|${question.toLowerCase()}`;
  if (state.assistantCache.has(key)) {
    renderAssistantAnswer(state.assistantCache.get(key));
    return;
  }
  els.askButton.disabled = true;
  els.askButton.setAttribute("aria-busy", "true");
  els.answerSource.classList.add("hidden");
  els.answerText.textContent = "Building a scenario-aware evidence brief…";
  try {
    const response = await fetch("/.netlify/functions/explain", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(context) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Assistant unavailable");
    const result = { ...data, scenario_id: data.scenario_id || state.scenarioId };
    if (result.source === "netlify_function_api") state.assistantCache.set(key, result);
    renderAssistantAnswer(result);
  } catch {
    const fallback = { ...localAssistantFallback(context), source: "deterministic_fallback", ai_status: "function_unavailable", scenario_id: state.scenarioId };
    renderAssistantAnswer(fallback);
  } finally {
    els.askButton.disabled = false;
    els.askButton.removeAttribute("aria-busy");
  }
}

function toCsv(rows) {
  const headers = Object.keys(rows[0] || {});
  const quote = (value) => `"${String(value == null ? "" : value).replaceAll("\"", "\"\"")}"`;
  return [headers.join(","), ...rows.map((row) => headers.map((header) => quote(row[header])).join(","))].join("\n");
}

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 800);
}

function knownLimitations(row) {
  return [...new Set([
    ...(state.report.warnings || []),
    row?.evidence_limitations,
    row?.equity_limitation,
    row?.charging_limitation,
    "Historic GTFS defines the screening universe and does not prove current 2026 service."
  ].filter(Boolean))];
}

function auditManifest() {
  const row = activeRow();
  return {
    exported_at_utc: new Date().toISOString(),
    build_id: state.build.build_id,
    build_timestamp_utc: state.build.build_timestamp_utc,
    pipeline_version: state.build.pipeline_version,
    model_versions: state.build.model_versions,
    model_metrics_summary: state.build.model_metrics_summary || state.modelMetrics,
    source_registry_version: state.sources.registry_version,
    source_registry_checksum_sha256: state.sources.registry_checksum_sha256,
    source_versions: (state.sources.sources || []).map((source) => ({ source_id: source.source_id, reference_period: source.reference_period, retrieval_date: source.retrieval_date, currentness: source.currentness, checksum_sha256: source.checksum_sha256 })),
    config_checksums: state.build.config_checksums,
    scenario: currentScenarioObject(),
    uncertainty_method: row?.sensitivity_method || "not reported",
    selected_route: row ? { route_id: row.route_id, route_long_name: row.route_long_name, live_rank: row.liveRank, live_priority_score: Number(row.liveScore?.toFixed(3)), evidence_grade: row.evidence_grade, evidence_confidence: numeric(row, "overall_evidence_confidence"), robustness_label: row.robustness_label, rank_p10: numeric(row, "rank_p10"), rank_p90: numeric(row, "rank_p90"), highest_value_missing_evidence: row.highest_value_missing_evidence, validation_status: row.validation_status } : null,
    portfolio: assistantContext("").portfolio,
    governance: { llm_ranking_influence: false, policy_weights_human_controlled: true, optimization_method: state.portfolioIsPrecomputed ? "deterministic_selection" : "deterministic_client_preview" },
    known_limitations: knownLimitations(row),
    disclaimer: row?.decision_support_disclaimer || "This output is decision support, not authorization for procurement, lending, franchise cancellation, or investment."
  };
}

function downloadCsv() {
  const rows = state.filtered.map((row) => ({
    route_id: row.route_id,
    route_long_name: row.route_long_name,
    primary_city: row.primary_city,
    live_rank: row.liveRank,
    live_priority_score: row.liveScore == null ? "" : row.liveScore.toFixed(3),
    evidence_grade: row.evidence_grade,
    evidence_confidence: row.overall_evidence_confidence,
    climate_low_t_year: row.net_co2e_avoided_t_year_low,
    climate_base_t_year: row.net_co2e_avoided_t_year_base,
    climate_high_t_year: row.net_co2e_avoided_t_year_high,
    equity_score: row.equity_score,
    charging_readiness_score: row.charging_readiness_score,
    operator_effective_score: row.operator_effective_score,
    top_10_probability: row.top_10_probability,
    robustness_label: row.robustness_label,
    rank_p10: row.rank_p10,
    rank_p90: row.rank_p90,
    rank_stability_score: row.rank_stability_score,
    validation_status: row.validation_status,
    active_status: row.active_status,
    validation_date: row.validation_date,
    validation_source_reference: row.source_reference,
    highest_value_missing_evidence: row.highest_value_missing_evidence,
    evidence_limitations: row.evidence_limitations,
    freshness_score: row.freshness_score,
    directness_score: row.directness_score,
    spatial_specificity_score: row.spatial_specificity_score,
    completeness_score: row.completeness_score,
    external_validation_score: row.external_validation_score,
    climate_source_ids: row.climate_source_ids,
    equity_source_ids: row.equity_source_ids,
    charging_source_ids: row.charging_source_ids,
    operator_source_ids: row.operator_source_ids,
    feature_source_ids: row.feature_source_ids,
    climate_claim_status: row.climate_claim_status,
    equity_claim_status: row.equity_claim_status,
    charging_claim_status: row.charging_claim_status,
    operator_claim_status: row.operator_claim_status,
    policy_model_version: row.policy_model_version,
    ml_model_version: row.ml_model_version,
    clustering_model_version: row.clustering_model_version,
    ml_service_intensity_used: row.ml_service_intensity_used,
    ml_typology_used_for_score: row.ml_typology_used_for_score,
    llm_ranking_influence: row.llm_ranking_influence,
    sensitivity_method: row.sensitivity_method,
    sensitivity_mode: row.sensitivity_mode,
    climate_assumption_set: row.climate_assumption_set,
    build_id: state.build.build_id,
    scenario_id: state.scenarioId,
    portfolio_scenario_id: state.portfolioScenarioId
  }));
  triggerDownload(new Blob([toCsv(rows)], { type: "text/csv;charset=utf-8" }), `route2zero_${safeFilePart(state.scenarioId)}_corridors.csv`);
}

function downloadAudit() {
  triggerDownload(new Blob([JSON.stringify(auditManifest(), null, 2)], { type: "application/json;charset=utf-8" }), `route2zero_${safeFilePart(state.scenarioId)}_audit.json`);
}

function mapImage() {
  try { return state.mapReady ? state.map.getCanvas().toDataURL("image/png") : ""; } catch { return ""; }
}

function exportPdfReport() {
  if (!window.jspdf?.jsPDF) {
    window.alert("The PDF exporter is still loading. Please try again.");
    return;
  }
  const row = activeRow();
  if (!row) return;
  const doc = new window.jspdf.jsPDF({ unit: "mm", format: "a4", orientation: "portrait" });
  const manifest = auditManifest();
  const climate = portfolioClimateSummary(state.portfolioRows);
  doc.setFillColor(6, 25, 31); doc.rect(0, 0, 210, 44, "F");
  doc.setTextColor(199, 244, 89); doc.setFont("helvetica", "bold"); doc.setFontSize(22); doc.text("Route2Zero 2.0", 15, 18);
  doc.setTextColor(232, 244, 240); doc.setFont("helvetica", "normal"); doc.setFontSize(9); doc.text("Evidence-aware e-jeepney corridor decision brief", 15, 28);
  doc.setFontSize(7); doc.text(`Build ${manifest.build_id} · Scenario ${state.scenarioId} · Portfolio ${state.portfolioScenarioId}`, 15, 37);
  doc.setTextColor(10, 36, 41); doc.setFont("helvetica", "bold"); doc.setFontSize(14); doc.text("Selected corridor", 15, 56);
  doc.setFontSize(11); doc.text(doc.splitTextToSize(row.route_long_name, 150), 15, 65);
  doc.setFont("helvetica", "normal"); doc.setFontSize(8); doc.setTextColor(92, 110, 110); doc.text(`${row.route_id} · ${String(row.cities_served || "Unspecified").replaceAll("|", " · ")}`, 15, 76);
  doc.setTextColor(10, 36, 41); doc.setFont("helvetica", "bold"); doc.setFontSize(21); doc.text(formatNumber(row.liveScore, 1), 169, 62); doc.setFontSize(7); doc.text(`PRIORITY · RANK #${row.liveRank}`, 162, 69);
  const image = mapImage();
  let y = 84;
  if (image) {
    doc.addImage(image, "PNG", 15, y, 180, 72, undefined, "FAST");
    doc.setFont("helvetica", "normal"); doc.setFontSize(6.5); doc.setTextColor(100, 115, 115); doc.text("Street-following planning visualisation · Map © Mapbox · Data © OpenStreetMap", 15, y + 76);
    y += 84;
  }
  doc.setTextColor(10, 36, 41); doc.setFont("helvetica", "bold"); doc.setFontSize(10); doc.text("Eight-signal route lens", 15, y);
  const lensRows = [
    ["Evidence", `${row.evidence_grade} · ${formatNumber(row.overall_evidence_confidence, 1)}/100`, row.evidence_claim_status],
    ["Climate", `${formatSigned(row.net_co2e_avoided_t_year_low)} to ${formatSigned(row.net_co2e_avoided_t_year_high)} tCO2e/year`, row.climate_claim_status],
    ["Equity", `${formatNumber(row.equity_score, 1)}/100`, row.equity_claim_status],
    ["Charging", `${formatNumber(row.charging_readiness_score, 1)}/100`, row.charging_claim_status],
    ["Operator", `${formatNumber(row.operator_effective_score, 1)}/100`, row.operator_claim_status],
    ["Robustness", `${formatNumber(Number(row.top_10_probability) * 100)}% top-10`, row.robustness_label],
    ["Typology", row.corridor_type_label, row.typology_claim_status]
  ];
  doc.autoTable({ startY: y + 5, head: [["Signal", "Value", "Status"]], body: lensRows, margin: { left: 15, right: 15 }, styles: { fontSize: 7.3, cellPadding: 2.1 }, headStyles: { fillColor: [13, 119, 114], textColor: 255 }, alternateRowStyles: { fillColor: [241, 245, 239] } });
  doc.addPage();
  doc.setFillColor(6, 25, 31); doc.rect(0, 0, 210, 25, "F"); doc.setTextColor(199, 244, 89); doc.setFont("helvetica", "bold"); doc.setFontSize(14); doc.text("Phase-1 evidence-validation portfolio", 15, 16);
  doc.setTextColor(10, 36, 41); doc.setFontSize(10); doc.text(`Climate range ${formatSigned(climate.low)} to ${formatSigned(climate.high)} tCO2e/year`, 15, 36);
  doc.setFont("helvetica", "normal"); doc.setFontSize(8); doc.text(`Scenario ${state.scenarioId} · Portfolio ${state.portfolioScenarioId} · ${state.portfolioIsPrecomputed ? "precomputed default" : "interactive preview"}`, 15, 44);
  const portfolioRows = state.portfolioRows.map((item, index) => [`${index + 1}`, item.route_long_name, item.primary_city || "—", item.evidence_grade || "—", formatNumber(item.liveScore ?? item.just_transition_score, 1)]);
  doc.autoTable({ startY: 50, head: [["#", "Corridor", "Primary city", "Evidence", "Priority"]], body: portfolioRows, margin: { left: 15, right: 15 }, styles: { fontSize: 7.1, cellPadding: 2.1 }, headStyles: { fillColor: [13, 119, 114], textColor: 255 }, alternateRowStyles: { fillColor: [241, 245, 239] } });
  const finalY = doc.lastAutoTable?.finalY || 110;
  doc.setFont("helvetica", "bold"); doc.setFontSize(10); doc.text("Responsible-use boundary", 15, finalY + 14);
  doc.setFont("helvetica", "normal"); doc.setFontSize(8); doc.text(doc.splitTextToSize("ML estimates historic service patterns. Deterministic models quantify climate scenarios, evidence confidence, sensitivity and portfolio selection. Policy weights remain human-controlled. The language model explains structured evidence and never edits a score or policy choice.", 180), 15, finalY + 23);
  doc.setFont("helvetica", "bold"); doc.text("Highest-value evidence gap", 15, finalY + 47);
  doc.setFont("helvetica", "normal"); doc.text(doc.splitTextToSize(`${String(row.highest_value_missing_evidence || "current validation").replaceAll("_", " ")}: ${row.validation_priority_reason || "Collect direct evidence before proceeding."}`, 180), 15, finalY + 56);
  doc.setFillColor(232, 239, 229); doc.roundedRect(15, finalY + 78, 180, 34, 3, 3, "F"); doc.setFont("helvetica", "bold"); doc.text("Decision support only", 21, finalY + 90); doc.setFont("helvetica", "normal"); doc.text(doc.splitTextToSize(row.decision_support_disclaimer || "Validate evidence before procurement, lending, franchise or investment action.", 165), 21, finalY + 99);

  doc.addPage();
  doc.setFillColor(6, 25, 31); doc.rect(0, 0, 210, 25, "F"); doc.setTextColor(199, 244, 89); doc.setFont("helvetica", "bold"); doc.setFontSize(14); doc.text("Audit metadata and known limitations", 15, 16);
  const auditRows = [
    ["Exported", manifest.exported_at_utc],
    ["Build / pipeline", `${manifest.build_id} · ${manifest.pipeline_version}`],
    ["Policy scenario", `${state.scenarioId} · ${JSON.stringify(manifest.scenario.policy_weights)}`],
    ["Climate assumptions", manifest.scenario.climate_assumption_set],
    ["Validation filter", manifest.scenario.validation_filter],
    ["Uncertainty", `${manifest.uncertainty_method} · ${manifest.scenario.sensitivity_mode}`],
    ["Service model", manifest.model_versions?.service_intensity || "not reported"],
    ["Typology model", manifest.model_versions?.corridor_typology || "not reported"],
    ["Source registry", `${manifest.source_registry_version || "not reported"} · ${manifest.source_versions.length} registered sources`]
  ];
  doc.autoTable({ startY: 33, head: [["Audit field", "Value"]], body: auditRows, margin: { left: 15, right: 15 }, styles: { fontSize: 7.3, cellPadding: 2.2 }, headStyles: { fillColor: [13, 119, 114], textColor: 255 }, columnStyles: { 0: { cellWidth: 42 } } });
  const auditY = doc.lastAutoTable?.finalY || 96;
  doc.setTextColor(10, 36, 41); doc.setFont("helvetica", "bold"); doc.setFontSize(10); doc.text("Source periods", 15, auditY + 14);
  const sourceLines = manifest.source_versions.map((source) => `${source.source_id}: ${source.reference_period || "not reported"} · retrieved ${source.retrieval_date || "not reported"}`);
  doc.setFont("helvetica", "normal"); doc.setFontSize(7.3); doc.text(doc.splitTextToSize(sourceLines.join("\n"), 180), 15, auditY + 23);
  doc.setFont("helvetica", "bold"); doc.setFontSize(10); doc.text("Known limitations", 15, auditY + 66);
  doc.setFont("helvetica", "normal"); doc.setFontSize(7.3); doc.text(doc.splitTextToSize(manifest.known_limitations.map((item) => `• ${item}`).join("\n"), 180), 15, auditY + 75);
  doc.setFont("helvetica", "bold"); doc.setFontSize(8); doc.text(doc.splitTextToSize(manifest.disclaimer, 180), 15, 276);
  doc.save(`route2zero_${safeFilePart(state.scenarioId)}_decision_brief.pdf`);
}

function wordReportHtml() {
  const row = activeRow();
  const manifest = auditManifest();
  const portfolioRows = state.portfolioRows.map((item, index) => `<tr><td>${index + 1}</td><td>${escapeHtml(item.route_long_name)}</td><td>${escapeHtml(item.primary_city || "—")}</td><td>${escapeHtml(item.evidence_grade || "—")}</td><td>${formatNumber(item.liveScore ?? item.just_transition_score, 1)}</td></tr>`).join("");
  const sourceRows = manifest.source_versions.map((source) => `<tr><td>${escapeHtml(source.source_id)}</td><td>${escapeHtml(source.reference_period || "not reported")}</td><td>${escapeHtml(source.retrieval_date || "not reported")}</td></tr>`).join("");
  const limitationItems = manifest.known_limitations.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  return `<!doctype html><html><head><meta charset="utf-8"><style>body{font-family:Arial,sans-serif;color:#0a2429;margin:38px;line-height:1.5}h1{color:#0d7772}h2{margin-top:28px;border-bottom:2px solid #c7f459;padding-bottom:6px}.meta{color:#607173}.score{font-size:28px;font-weight:bold;color:#0d7772}table{width:100%;border-collapse:collapse}th,td{border:1px solid #d5e0d6;padding:8px;text-align:left}th{background:#0d7772;color:white}.note{background:#f1f5ef;padding:14px}</style></head><body>
  <h1>Route2Zero 2.0 Decision Brief</h1><p class="meta">Exported ${escapeHtml(manifest.exported_at_utc)} · Build ${escapeHtml(manifest.build_id)} · Scenario ${escapeHtml(state.scenarioId)} · Portfolio ${escapeHtml(state.portfolioScenarioId)}</p>
  <h2>Selected corridor</h2><h3>${escapeHtml(row.route_long_name)}</h3><p>${escapeHtml(row.route_id)} · ${escapeHtml(String(row.cities_served || "Unspecified").replaceAll("|", " · "))}</p><p class="score">${formatNumber(row.liveScore, 1)}/100 · Rank #${row.liveRank}</p><p>${escapeHtml(deterministicRouteSummary(row))}</p>
  <h2>Eight-signal route lens</h2><ul><li>Evidence: Grade ${escapeHtml(row.evidence_grade)} (${formatNumber(row.overall_evidence_confidence, 1)}/100)</li><li>Climate scenario: ${formatSigned(row.net_co2e_avoided_t_year_low)} to ${formatSigned(row.net_co2e_avoided_t_year_high)} tCO2e/year</li><li>Equity exposure: ${formatNumber(row.equity_score, 1)}/100 (${escapeHtml(row.equity_claim_status)})</li><li>Charging readiness: ${formatNumber(row.charging_readiness_score, 1)}/100; utility capacity unverified</li><li>Operator readiness: ${formatNumber(row.operator_effective_score, 1)}/100 (${escapeHtml(row.operator_claim_status)})</li><li>Robustness: ${formatNumber(Number(row.top_10_probability) * 100)}% top-10 across ${formatNumber(row.simulations)} scenarios</li><li>Typology: ${escapeHtml(row.corridor_type_label)}</li></ul>
  <h2>Phase-1 evidence-validation portfolio</h2><table><thead><tr><th>#</th><th>Corridor</th><th>Primary city</th><th>Evidence</th><th>Priority</th></tr></thead><tbody>${portfolioRows}</tbody></table>
  <h2>Audit metadata</h2><table><tbody><tr><th>Policy weights</th><td>${escapeHtml(JSON.stringify(manifest.scenario.policy_weights))}</td></tr><tr><th>Climate assumptions</th><td>${escapeHtml(manifest.scenario.climate_assumption_set)}</td></tr><tr><th>Validation filter</th><td>${escapeHtml(manifest.scenario.validation_filter)}</td></tr><tr><th>Uncertainty method</th><td>${escapeHtml(`${manifest.uncertainty_method} · ${manifest.scenario.sensitivity_mode}`)}</td></tr><tr><th>Service model</th><td>${escapeHtml(manifest.model_versions?.service_intensity || "not reported")}</td></tr><tr><th>Typology model</th><td>${escapeHtml(manifest.model_versions?.corridor_typology || "not reported")}</td></tr></tbody></table>
  <h2>Source versions</h2><table><thead><tr><th>Source ID</th><th>Reference period</th><th>Retrieved</th></tr></thead><tbody>${sourceRows}</tbody></table>
  <h2>Known limitations</h2><ul>${limitationItems}</ul><h2>Responsible-use boundary</h2><div class="note"><p>ML estimates where appropriate. Deterministic models quantify impacts, uncertainty and selection. Policy weights remain human-controlled. The LLM explains structured evidence and never changes a score or policy choice.</p><p><b>Decision support only:</b> ${escapeHtml(manifest.disclaimer)}</p></div><p><a href="https://route2zero.netlify.app/">Live dashboard</a> · <a href="https://github.com/qjmre23/Route2Zero">GitHub repository</a></p></body></html>`;
}

function exportWordReport() {
  if (!activeRow()) return;
  triggerDownload(new Blob(["\ufeff", wordReportHtml()], { type: "application/msword;charset=utf-8" }), `route2zero_${safeFilePart(state.scenarioId)}_decision_brief.doc`);
}

const mobileControlsQuery = window.matchMedia("(max-width: 900px)");

function syncControlsA11y() {
  if (mobileControlsQuery.matches) {
    els.controls.inert = !state.controlsOpen;
    els.controls.setAttribute("aria-hidden", String(!state.controlsOpen));
  } else {
    state.controlsOpen = false;
    document.body.classList.remove("controls-open");
    els.controls.inert = false;
    els.controls.removeAttribute("aria-hidden");
    els.mobileControlsButton.setAttribute("aria-expanded", "false");
    els.controlsBackdrop.setAttribute("aria-hidden", "true");
  }
}

function setControlsOpen(open, restoreFocus = true) {
  if (!mobileControlsQuery.matches) return;
  state.controlsOpen = Boolean(open);
  document.body.classList.toggle("controls-open", state.controlsOpen);
  els.mobileControlsButton.setAttribute("aria-expanded", String(state.controlsOpen));
  els.controlsBackdrop.setAttribute("aria-hidden", String(!state.controlsOpen));
  syncControlsA11y();
  if (state.controlsOpen) requestAnimationFrame(() => els.closeControls.focus());
  else if (restoreFocus) requestAnimationFrame(() => els.mobileControlsButton.focus());
}

function trapControlsFocus(event) {
  if (!state.controlsOpen || event.key !== "Tab") return;
  const focusable = [...els.controls.querySelectorAll("button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), a[href]")].filter((element) => !element.inert && element.offsetParent !== null);
  if (!focusable.length) return;
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
}

const tourSteps = [
  { target: "#overview", time: "0–12 sec", title: "Start with the city decision", copy: "Route2Zero screens the full historic route universe and shows immediately that current validation is still missing.", action: () => setPreset("default") },
  { target: "#corridor-map", time: "12–28 sec", title: "Follow the corridor on real streets", copy: "The selected flagship is road-matched through Mapbox. A dashed line keeps unverified source geometry visibly distinct.", action: () => { state.activeLayer = "priority"; els.mapLayer.value = "priority"; setSelected(state.flagship.route_id || state.build.flagship_route_id || state.selectedRouteId, false); } },
  { target: "#route-lens", time: "28–42 sec", title: "Read eight signals, not one score", copy: "Climate scenarios, evidence, equity, charging, operator readiness, robustness and ML typology stay separate and claim-labelled." },
  { target: "#scenario-lab", time: "42–57 sec", title: "Test a human policy choice", copy: "Switch to Equity-first and watch live ranks, top-ten membership and the scenario ID change from actual data.", action: () => setPreset("equity") },
  { target: "#phase1-portfolio", time: "57–71 sec", title: "Build a constrained Phase-1 shortlist", copy: "The default eight-corridor portfolio is a real precomputed pipeline output and visibly differs from simple top-N sorting.", action: () => setPreset("default") },
  { target: "#evidence-ai", time: "71–85 sec", title: "Ask what must be validated first", copy: "The assistant is grounded in the active route, scenario and evidence queue. Exported reports carry build, model and scenario metadata.", action: () => { els.questionInput.value = "What should the city validate first for this corridor?"; const context = assistantContext(els.questionInput.value); renderAssistantAnswer({ ...localAssistantFallback(context), source: "precomputed_planner_cache" }); } }
];

function activateTourStep(index) {
  document.querySelectorAll(".tour-focus").forEach((element) => element.classList.remove("tour-focus"));
  state.tourIndex = Math.max(0, Math.min(tourSteps.length - 1, index));
  const step = tourSteps[state.tourIndex];
  step.action?.();
  const target = document.querySelector(step.target);
  target?.classList.add("tour-focus");
  target?.scrollIntoView({ behavior: "smooth", block: "start" });
  els.walkthroughStep.textContent = `${state.tourIndex + 1} / ${tourSteps.length}`;
  els.walkthroughTime.textContent = step.time;
  els.walkthroughTitle.textContent = step.title;
  els.walkthroughCopy.textContent = step.copy;
  els.walkthroughBack.disabled = state.tourIndex === 0;
  els.walkthroughNext.textContent = state.tourIndex === tourSteps.length - 1 ? "Finish" : "Next";
}

function startWalkthrough(event) {
  state.tourStarter = event?.currentTarget || document.activeElement;
  els.walkthroughPanel.classList.remove("hidden");
  els.walkthroughPanel.setAttribute("aria-live", "polite");
  activateTourStep(0);
  requestAnimationFrame(() => els.walkthroughNext.focus());
}

function endWalkthrough() {
  document.querySelectorAll(".tour-focus").forEach((element) => element.classList.remove("tour-focus"));
  els.walkthroughPanel.classList.add("hidden");
  state.tourIndex = -1;
  state.tourStarter?.focus?.();
}

async function fetchTextRequired(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${url} could not be loaded (${response.status}).`);
  return response.text();
}

async function fetchJsonRequired(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${url} could not be loaded (${response.status}).`);
  return response.json();
}

async function init() {
  syncControlsA11y();
  const [scoresText, geojson, build, report, portfolios, priorities, plannerCache, plannerSummary, sources, modelMetrics, flagship] = await Promise.all([
    fetchTextRequired("/data/route2zero_scores.csv"),
    fetchJsonRequired("/data/route2zero_scores.geojson"),
    fetchJsonRequired("/data/build_manifest.json"),
    fetchJsonRequired("/data/pipeline_report.json"),
    fetchJsonRequired("/data/portfolio_scenarios.json"),
    fetchJsonRequired("/data/validation_priorities.json"),
    fetchJsonRequired("/data/route_planner_cache.json"),
    fetchJsonRequired("/data/planner_summary.json"),
    fetchJsonRequired("/data/source_manifest.json"),
    fetchJsonRequired("/data/model_metrics.json"),
    fetchJsonRequired("/data/flagship_route.json")
  ]);
  state.scores = parseCsv(scoresText);
  state.geojson = geojson;
  state.build = build;
  state.report = report;
  state.portfolioData = portfolios;
  state.defaultPortfolio = portfolios.scenarios?.[0] || null;
  state.validationPriorities = priorities;
  state.routePlannerCache = plannerCache;
  state.plannerSummary = plannerSummary;
  state.sources = sources;
  state.modelMetrics = modelMetrics;
  state.flagship = flagship;
  state.defaultRanked = [...state.scores].filter((row) => numeric(row, "just_transition_score") !== null).sort((left, right) => Number(left.rank) - Number(right.rank));
  geojson.features.forEach((feature) => {
    if (feature.geometry?.type === "LineString") state.pathByRoute.set(String(feature.properties.route_id), feature.geometry.coordinates);
  });
  renderCityOptions();
  state.savedScenarios = readSavedScenarios();
  state.selectedRouteId = flagship.route_id || build.flagship_route_id || state.defaultRanked[0]?.route_id || state.scores[0]?.route_id;
  renderAll();
  els.scenarioTitle.value = suggestedScenarioTitle();
  renderSavedScenarioOptions();
  renderSourceHealth();
  initialiseMap();
}

Object.values(weightInputs).forEach((input) => input.addEventListener("input", () => { inferPreset(); renderAll(); }));
document.querySelectorAll("[data-preset]").forEach((button) => button.addEventListener("click", () => setPreset(button.dataset.preset)));
els.cityFilter.addEventListener("change", renderAll);
els.includeHistoric.addEventListener("change", renderAll);
els.resetScenario.addEventListener("click", resetScenarioToDefault);
els.saveScenario.addEventListener("click", saveCurrentScenario);
els.copyScenario.addEventListener("click", copyCurrentScenarioJson);
els.savedScenarioSelect.addEventListener("change", updateSavedScenarioButtons);
els.loadScenario.addEventListener("click", loadSelectedScenario);
els.deleteScenario.addEventListener("click", deleteSelectedScenario);
els.routeFinder.addEventListener("change", (event) => setSelected(event.target.value, false));
els.mapLayer.addEventListener("change", (event) => { state.activeLayer = event.target.value; refreshMapData(); });
els.buildPortfolio.addEventListener("click", renderAll);
[els.portfolioMax, els.portfolioGrade, els.portfolioEquity].forEach((control) => control.addEventListener("change", renderAll));

function delegatedRouteSelection(event) {
  const button = event.target.closest("[data-route-id]");
  if (button) setSelected(button.dataset.routeId, true);
}

els.leaderboardBody.addEventListener("click", delegatedRouteSelection);
els.mobileRouteCards.addEventListener("click", delegatedRouteSelection);
els.portfolioList.addEventListener("click", delegatedRouteSelection);
els.evidenceQueue.addEventListener("click", delegatedRouteSelection);
els.askButton.addEventListener("click", askQuestion);
els.questionInput.addEventListener("keydown", (event) => { if ((event.ctrlKey || event.metaKey) && event.key === "Enter") askQuestion(); });
document.querySelectorAll("[data-question]").forEach((button) => button.addEventListener("click", () => { els.questionInput.value = button.dataset.question; askQuestion(); }));
els.openMethod.addEventListener("click", () => { els.methodDetails.open = true; els.methodDetails.scrollIntoView({ behavior: "smooth", block: "center" }); requestAnimationFrame(() => els.methodDetails.querySelector("summary")?.focus()); });

els.exportPdf.addEventListener("click", exportPdfReport);
els.exportWord.addEventListener("click", exportWordReport);
els.downloadCsv.addEventListener("click", downloadCsv);
els.downloadAudit.addEventListener("click", downloadAudit);
els.mobileControlsButton.addEventListener("click", () => setControlsOpen(!state.controlsOpen));
els.closeControls.addEventListener("click", () => setControlsOpen(false));
els.controlsBackdrop.addEventListener("click", () => setControlsOpen(false));
els.controls.addEventListener("keydown", trapControlsFocus);
mobileControlsQuery.addEventListener("change", syncControlsA11y);

els.startWalkthroughTop.addEventListener("click", startWalkthrough);
els.startWalkthroughHero.addEventListener("click", startWalkthrough);
els.walkthroughBack.addEventListener("click", () => activateTourStep(state.tourIndex - 1));
els.walkthroughNext.addEventListener("click", () => { if (state.tourIndex >= tourSteps.length - 1) endWalkthrough(); else activateTourStep(state.tourIndex + 1); });
els.walkthroughClose.addEventListener("click", endWalkthrough);

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    if (state.tourIndex >= 0) endWalkthrough();
    else if (state.controlsOpen) setControlsOpen(false);
  }
});

document.addEventListener("pointerdown", (event) => {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const target = event.target.closest("button");
  if (!target || target.disabled) return;
  const rect = target.getBoundingClientRect();
  const ripple = document.createElement("span");
  ripple.className = "click-ripple";
  ripple.style.left = `${event.clientX - rect.left}px`;
  ripple.style.top = `${event.clientY - rect.top}px`;
  target.appendChild(ripple);
  setTimeout(() => ripple.remove(), 650);
});

window.addEventListener("resize", () => state.map?.resize());

init().catch((error) => {
  document.querySelector(".content").innerHTML = `<section class="panel"><h1>Route2Zero could not load</h1><p>${escapeHtml(error.message)}</p><p>Run the Route2Zero 2.0 pipeline and Netlify build so all versioned data products are available.</p></section>`;
});
