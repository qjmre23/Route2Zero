const state = {
  scores: [],
  geojson: null,
  explanations: {},
  filtered: [],
  selectedRouteId: null,
  map: null,
  routeLayer: null,
  pathByRoute: new Map()
};

const columns = {
  emissions: "emissions_potential_score",
  equity: "equity_score",
  grid: "grid_feasibility_score",
  operator: "operator_readiness_score"
};

const els = {
  cityFilter: document.querySelector("#cityFilter"),
  includeUnverified: document.querySelector("#includeUnverified"),
  routeFinder: document.querySelector("#routeFinder"),
  downloadCsv: document.querySelector("#downloadCsv"),
  questionInput: document.querySelector("#questionInput"),
  askButton: document.querySelector("#askButton"),
  answerText: document.querySelector("#answerText"),
  answerSource: document.querySelector("#answerSource"),
  routesMetric: document.querySelector("#routesMetric"),
  completeMetric: document.querySelector("#completeMetric"),
  topMetric: document.querySelector("#topMetric"),
  routeName: document.querySelector("#routeName"),
  routeMeta: document.querySelector("#routeMeta"),
  rankValue: document.querySelector("#rankValue"),
  scoreValue: document.querySelector("#scoreValue"),
  lengthValue: document.querySelector("#lengthValue"),
  sourcePill: document.querySelector("#sourcePill"),
  routeRationale: document.querySelector("#routeRationale"),
  breakdownBars: document.querySelector("#breakdownBars"),
  leaderboardBody: document.querySelector("#leaderboardBody"),
  scatter: document.querySelector("#scatter")
};

const weightInputs = {
  emissions: document.querySelector("#emissionsWeight"),
  equity: document.querySelector("#equityWeight"),
  grid: document.querySelector("#gridWeight"),
  operator: document.querySelector("#operatorWeight")
};

const weightOutputs = {
  emissions: document.querySelector("#emissionsValue"),
  equity: document.querySelector("#equityValue"),
  grid: document.querySelector("#gridValue"),
  operator: document.querySelector("#operatorValue")
};

function parseCsv(text) {
  const rows = [];
  let row = [];
  let value = "";
  let quoted = false;

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    const next = text[i + 1];

    if (char === '"' && quoted && next === '"') {
      value += '"';
      i += 1;
    } else if (char === '"') {
      quoted = !quoted;
    } else if (char === "," && !quoted) {
      row.push(value);
      value = "";
    } else if ((char === "\n" || char === "\r") && !quoted) {
      if (char === "\r" && next === "\n") {
        i += 1;
      }
      row.push(value);
      if (row.some((cell) => cell.length)) {
        rows.push(row);
      }
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

  const headers = rows.shift();
  return rows.map((cells) => Object.fromEntries(headers.map((header, index) => [header, cells[index] ?? ""])));
}

function numeric(row, key) {
  const value = Number(row[key]);
  return Number.isFinite(value) ? value : null;
}

function scoreColor(value) {
  if (!Number.isFinite(value)) return "#8b9b9b";
  const x = Math.max(0, Math.min(100, value)) / 100;
  const low = [217, 79, 79];
  const mid = [242, 173, 46];
  const high = [24, 185, 145];
  const left = x <= 0.5 ? low : mid;
  const right = x <= 0.5 ? mid : high;
  const t = x <= 0.5 ? x * 2 : (x - 0.5) * 2;
  return `rgb(${left.map((channel, index) => Math.round(channel + (right[index] - channel) * t)).join(",")})`;
}

function getWeights() {
  const weights = Object.fromEntries(Object.entries(weightInputs).map(([key, input]) => [key, Number(input.value)]));
  Object.entries(weights).forEach(([key, value]) => {
    weightOutputs[key].value = value;
    weightOutputs[key].textContent = value;
  });
  return weights;
}

function computeLiveScores() {
  const weights = getWeights();
  const total = Object.values(weights).reduce((sum, value) => sum + value, 0);
  const normalized = Object.fromEntries(Object.entries(weights).map(([key, value]) => [key, total ? value / total : 0]));
  const includeUnverified = els.includeUnverified.checked;

  const live = state.scores.map((row) => {
    const values = Object.fromEntries(Object.entries(columns).map(([key, column]) => [key, numeric(row, column)]));
    const complete = Object.values(values).every((value) => value !== null);
    let liveScore = null;
    let confidence = "metric unavailable";

    if (complete && total > 0) {
      liveScore = Object.keys(values).reduce((sum, key) => sum + values[key] * normalized[key], 0);
      confidence = "complete proxy mix";
    } else if (includeUnverified && values.equity === null && values.emissions !== null && values.grid !== null && values.operator !== null) {
      const availableWeight = 1 - normalized.equity;
      if (availableWeight > 0) {
        liveScore = ((values.emissions * normalized.emissions) + (values.grid * normalized.grid) + (values.operator * normalized.operator)) / availableWeight * 0.85;
        confidence = "reduced: equity unavailable";
      }
    }

    return { ...row, liveScore, liveConfidence: confidence, liveRank: null };
  });

  live.sort((a, b) => {
    if (a.liveScore === null && b.liveScore === null) return a.route_id.localeCompare(b.route_id);
    if (a.liveScore === null) return 1;
    if (b.liveScore === null) return -1;
    return b.liveScore - a.liveScore || a.route_id.localeCompare(b.route_id);
  });

  live.forEach((row, index) => {
    if (row.liveScore !== null) row.liveRank = index + 1;
  });

  const city = els.cityFilter.value;
  state.filtered = live.filter((row) => {
    const cities = String(row.cities_served || "");
    const cityMatches = city === "All Metro Manila" || cities.split("|").includes(city);
    const verifiedMatches = includeUnverified || row.equity_score !== "";
    return cityMatches && verifiedMatches;
  });
}

function routeLabel(row) {
  const rank = row.liveRank ? `#${row.liveRank}` : "Unranked";
  return `${rank} - ${row.route_long_name} - ${row.route_id}`;
}

function deterministicRationale(row) {
  const score = row.liveScore?.toFixed(1) ?? "N/A";
  const emissions = Number(row.emissions_potential_score).toFixed(1);
  const equity = row.equity_score ? Number(row.equity_score).toFixed(1) : "unverified";
  return `${row.route_long_name} ranks at ${score}/100 because it combines an emissions activity score of ${emissions}, an equity density proxy of ${equity}, a coarse Luzon grid proxy, and neutral operator readiness. The score is deterministic and uses visible weights; operator readiness remains a placeholder pending cooperative workshops.`;
}

function setSelected(routeId) {
  state.selectedRouteId = routeId;
  els.routeFinder.value = routeId;
  renderDetails();
  renderMap();
}

function renderCityOptions() {
  const cities = new Set(["All Metro Manila"]);
  state.scores.forEach((row) => {
    String(row.cities_served || "").split("|").filter(Boolean).forEach((city) => {
      if (city !== "Unspecified") cities.add(city);
    });
  });
  els.cityFilter.innerHTML = [...cities].sort((a, b) => a === "All Metro Manila" ? -1 : b === "All Metro Manila" ? 1 : a.localeCompare(b)).map((city) => `<option value="${city}">${city}</option>`).join("");
}

function renderMetrics() {
  const complete = state.filtered.filter((row) => row.liveScore !== null);
  els.routesMetric.textContent = state.filtered.length.toLocaleString();
  els.completeMetric.textContent = complete.length.toLocaleString();
  els.topMetric.textContent = complete.length ? Math.max(...complete.map((row) => row.liveScore)).toFixed(1) : "N/A";
}

function renderRouteFinder() {
  els.routeFinder.innerHTML = state.filtered.map((row) => `<option value="${row.route_id}">${routeLabel(row)}</option>`).join("");
  const selectedStillVisible = state.filtered.some((row) => row.route_id === state.selectedRouteId);
  if (!selectedStillVisible) {
    state.selectedRouteId = state.filtered[0]?.route_id || null;
  }
  if (state.selectedRouteId) {
    els.routeFinder.value = state.selectedRouteId;
  }
}

function renderMap() {
  if (!state.map) {
    state.map = L.map("map", { preferCanvas: true }).setView([14.61, 121.01], 10);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors"
    }).addTo(state.map);
  }

  if (state.routeLayer) {
    state.routeLayer.remove();
  }

  const routes = state.filtered.slice(0, 400);
  state.routeLayer = L.layerGroup();
  routes.forEach((row) => {
    const coords = state.pathByRoute.get(row.route_id);
    if (!coords) return;
    const latLngs = coords.map(([lon, lat]) => [lat, lon]);
    const selected = row.route_id === state.selectedRouteId;
    const approximate = row.geometry_source === "stop_sequence_approx";
    L.polyline(latLngs, {
      color: selected ? "#062e34" : scoreColor(row.liveScore),
      weight: selected ? 5 : approximate ? 1.5 : 3.5,
      opacity: selected ? 0.95 : approximate ? 0.35 : 0.8
    })
      .bindTooltip(`${row.route_long_name}<br>Priority ${row.liveScore?.toFixed(1) ?? "N/A"}/100`)
      .on("click", () => setSelected(row.route_id))
      .addTo(state.routeLayer);
  });
  state.routeLayer.addTo(state.map);

  const selectedCoords = state.pathByRoute.get(state.selectedRouteId);
  if (selectedCoords?.length) {
    const bounds = L.latLngBounds(selectedCoords.map(([lon, lat]) => [lat, lon]));
    state.map.fitBounds(bounds.pad(0.25), { animate: false });
  }
}

function renderDetails() {
  const row = state.filtered.find((item) => item.route_id === state.selectedRouteId);
  if (!row) return;

  els.routeName.textContent = row.route_long_name;
  els.routeMeta.textContent = `${row.route_id} - ${String(row.cities_served || "Unspecified").replaceAll("|", " - ")}`;
  els.rankValue.textContent = row.liveRank ? `#${row.liveRank}` : "Unranked";
  els.scoreValue.textContent = row.liveScore?.toFixed(1) ?? "N/A";
  els.lengthValue.textContent = Number(row.length_km).toFixed(1);

  const cached = state.explanations[row.route_id];
  els.sourcePill.textContent = cached?.source === "mantle_bedrock_api" ? "AI-generated summary" : "Deterministic explanation - offline-safe";
  els.routeRationale.textContent = cached?.text || deterministicRationale(row);

  const breakdown = [
    ["Emissions activity", numeric(row, columns.emissions)],
    ["Equity density", numeric(row, columns.equity)],
    ["Grid proxy", numeric(row, columns.grid)],
    ["Operator readiness", numeric(row, columns.operator)]
  ];
  els.breakdownBars.innerHTML = breakdown.map(([label, value]) => {
    const width = value === null ? 0 : Math.max(0, Math.min(100, value));
    const text = value === null ? "N/A" : value.toFixed(1);
    return `<div><div class="bar-label"><span>${label}</span><span>${text}</span></div><div class="bar-track"><div class="bar-fill" style="width:${width}%"></div></div></div>`;
  }).join("");
}

function renderLeaderboard() {
  els.leaderboardBody.innerHTML = state.filtered.filter((row) => row.liveScore !== null).slice(0, 10).map((row) => `
    <tr>
      <td>#${row.liveRank}</td>
      <td>${row.route_long_name}</td>
      <td>${row.primary_city || "Unspecified"}</td>
      <td>${row.liveScore.toFixed(1)}</td>
      <td>${Number(row.emissions_potential_score).toFixed(1)}</td>
      <td>${row.equity_score ? Number(row.equity_score).toFixed(1) : "N/A"}</td>
      <td>${Number(row.grid_feasibility_score).toFixed(1)}</td>
      <td>${Number(row.operator_readiness_score).toFixed(1)}</td>
    </tr>
  `).join("");
}

function renderScatter() {
  const canvas = els.scatter;
  const ratio = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = Math.max(320, Math.floor(rect.width * ratio));
  canvas.height = Math.floor(420 * ratio);
  const ctx = canvas.getContext("2d");
  ctx.scale(ratio, ratio);
  ctx.clearRect(0, 0, rect.width, 420);

  const margin = { left: 54, right: 24, top: 18, bottom: 48 };
  const width = rect.width - margin.left - margin.right;
  const height = 420 - margin.top - margin.bottom;
  const data = state.filtered.filter((row) => row.liveScore !== null && row.emissions_potential_score && row.equity_score);

  ctx.strokeStyle = "#d8e8e3";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(margin.left, margin.top);
  ctx.lineTo(margin.left, margin.top + height);
  ctx.lineTo(margin.left + width, margin.top + height);
  ctx.stroke();

  ctx.fillStyle = "#5b7472";
  ctx.font = "12px system-ui, sans-serif";
  ctx.fillText("Equity density proxy", 8, margin.top + 12);
  ctx.fillText("Emissions activity proxy", margin.left + width - 150, 405);

  data.forEach((row) => {
    const x = margin.left + (Number(row.emissions_potential_score) / 100) * width;
    const y = margin.top + height - (Number(row.equity_score) / 100) * height;
    const radius = Math.max(3, Math.min(12, Math.sqrt(Number(row.trips_per_day_estimate) || 1) / 3.2));
    ctx.beginPath();
    ctx.fillStyle = scoreColor(row.liveScore);
    ctx.globalAlpha = row.route_id === state.selectedRouteId ? 0.95 : 0.55;
    ctx.arc(x, y, row.route_id === state.selectedRouteId ? radius + 3 : radius, 0, Math.PI * 2);
    ctx.fill();
  });
  ctx.globalAlpha = 1;
}

function toCsv(rows) {
  const headers = Object.keys(rows[0] || {});
  const quote = (value) => `"${String(value ?? "").replaceAll('"', '""')}"`;
  return [headers.join(","), ...rows.map((row) => headers.map((header) => quote(row[header])).join(","))].join("\n");
}

function downloadCsv() {
  const blob = new Blob([toCsv(state.filtered)], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `route2zero_${els.cityFilter.value.toLowerCase().replaceAll(" ", "_")}_rankings.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

function currentFacts() {
  const query = els.questionInput.value.toLowerCase();
  let candidates = state.filtered;
  [...els.cityFilter.options].map((option) => option.value).filter((city) => city !== "All Metro Manila").forEach((city) => {
    if (query.includes(city.toLowerCase())) {
      candidates = candidates.filter((row) => String(row.cities_served || "").toLowerCase().includes(city.toLowerCase()));
    }
  });
  return candidates.filter((row) => row.liveScore !== null).slice(0, 5).map((row) => `${row.route_long_name}: ${row.liveScore.toFixed(1)}/100`).join("; ");
}

async function askQuestion() {
  const question = els.questionInput.value.trim();
  if (!question) return;
  const facts = currentFacts();
  els.askButton.disabled = true;
  els.answerSource.classList.add("hidden");
  els.answerText.textContent = "Generating a short answer...";

  try {
    const response = await fetch("/.netlify/functions/explain", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ question, facts })
    });
    const data = await response.json();
    els.answerSource.textContent = data.source === "netlify_function_api" ? "AI-generated via Netlify Function" : "Offline deterministic answer";
    els.answerText.textContent = data.answer || "No answer was returned.";
  } catch {
    els.answerSource.textContent = "Offline deterministic answer";
    els.answerText.textContent = `Based on the current filters, the leading routes are ${facts}. These are deterministic weighted scores; operator readiness remains a placeholder.`;
  } finally {
    els.answerSource.classList.remove("hidden");
    els.askButton.disabled = false;
  }
}

function renderAll() {
  computeLiveScores();
  renderMetrics();
  renderRouteFinder();
  renderDetails();
  renderLeaderboard();
  renderScatter();
  renderMap();
}

async function init() {
  const [scoresText, citiesText, geojson, explanations] = await Promise.all([
    fetch("/data/route2zero_scores.csv").then((response) => response.text()),
    fetch("/data/route_cities.csv").then((response) => response.text()),
    fetch("/data/route2zero_scores.geojson").then((response) => response.json()),
    fetch("/data/route_explanations.json").then((response) => response.json()).catch(() => ({}))
  ]);

  const citiesByRoute = new Map(parseCsv(citiesText).map((row) => [row.route_id, row]));
  state.scores = parseCsv(scoresText).map((row) => ({ ...row, ...(citiesByRoute.get(row.route_id) || {}) }));
  state.geojson = geojson;
  state.explanations = explanations;
  state.geojson.features.forEach((feature) => {
    if (feature.geometry?.type === "LineString") {
      state.pathByRoute.set(String(feature.properties.route_id), feature.geometry.coordinates);
    }
  });

  renderCityOptions();
  renderAll();
}

Object.values(weightInputs).forEach((input) => input.addEventListener("input", renderAll));
els.cityFilter.addEventListener("change", renderAll);
els.includeUnverified.addEventListener("change", renderAll);
els.routeFinder.addEventListener("change", (event) => setSelected(event.target.value));
els.downloadCsv.addEventListener("click", downloadCsv);
els.askButton.addEventListener("click", askQuestion);
window.addEventListener("resize", renderScatter);

init().catch((error) => {
  document.body.innerHTML = `<main class="content"><section class="panel"><h1>Route2Zero could not load data</h1><p>${error.message}</p></section></main>`;
});
