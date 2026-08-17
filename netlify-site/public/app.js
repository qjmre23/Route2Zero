const MAPBOX_ACCESS_TOKEN = String(window.ROUTE2ZERO_CONFIG?.mapboxToken || "").trim();
const MAPBOX_STYLE_URL = "mapbox://styles/marwin2323/cmswv687u002u01so2xzd7mrs";

const state = {
  scores: [],
  geojson: null,
  explanations: {},
  filtered: [],
  selectedRouteId: null,
  map: null,
  mapReady: false,
  pathByRoute: new Map(),
  roadGeometryCache: new Map(),
  roadRequestId: 0
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
  exportPdf: document.querySelector("#exportPdf"),
  exportWord: document.querySelector("#exportWord"),
  questionInput: document.querySelector("#questionInput"),
  askButton: document.querySelector("#askButton"),
  answerText: document.querySelector("#answerText"),
  answerSource: document.querySelector("#answerSource"),
  routesMetric: document.querySelector("#routesMetric"),
  completeMetric: document.querySelector("#completeMetric"),
  topMetric: document.querySelector("#topMetric"),
  heroTopScore: document.querySelector("#heroTopScore"),
  routeName: document.querySelector("#routeName"),
  routeMeta: document.querySelector("#routeMeta"),
  rankValue: document.querySelector("#rankValue"),
  scoreValue: document.querySelector("#scoreValue"),
  lengthValue: document.querySelector("#lengthValue"),
  sourcePill: document.querySelector("#sourcePill"),
  routeRationale: document.querySelector("#routeRationale"),
  breakdownBars: document.querySelector("#breakdownBars"),
  leaderboardBody: document.querySelector("#leaderboardBody"),
  scatter: document.querySelector("#scatter"),
  roadStatus: document.querySelector("#roadStatus"),
  weightTotal: document.querySelector("#weightTotal"),
  mobileControlsButton: document.querySelector("#mobileControlsButton"),
  closeControls: document.querySelector("#closeControls"),
  controlsBackdrop: document.querySelector("#controlsBackdrop"),
  openMethod: document.querySelector("#openMethod"),
  methodDetails: document.querySelector("#methodDetails")
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
    if (char === "\"" && quoted && next === "\"") {
      value += "\"";
      i += 1;
    } else if (char === "\"") {
      quoted = !quoted;
    } else if (char === "," && !quoted) {
      row.push(value);
      value = "";
    } else if ((char === "\n" || char === "\r") && !quoted) {
      if (char === "\r" && next === "\n") i += 1;
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
  return rows.map((cells) => Object.fromEntries(headers.map((header, index) => [header, cells[index] || ""])));
}

function numeric(row, key) {
  const value = Number(row[key]);
  return Number.isFinite(value) && row[key] !== "" ? value : null;
}

function escapeHtml(value) {
  return String(value == null ? "" : value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll("\"", "&quot;")
    .replaceAll("'", "&#039;");
}

function scoreColor(value) {
  if (!Number.isFinite(value)) return "#7c8b8b";
  const x = Math.max(0, Math.min(100, value)) / 100;
  const low = [255, 108, 100];
  const mid = [255, 189, 74];
  const high = [85, 222, 192];
  const left = x <= 0.5 ? low : mid;
  const right = x <= 0.5 ? mid : high;
  const t = x <= 0.5 ? x * 2 : (x - 0.5) * 2;
  return "rgb(" + left.map((channel, index) => Math.round(channel + (right[index] - channel) * t)).join(",") + ")";
}

function getWeights() {
  const weights = Object.fromEntries(Object.entries(weightInputs).map(([key, input]) => [key, Number(input.value)]));
  const total = Object.values(weights).reduce((sum, value) => sum + value, 0);
  Object.entries(weights).forEach(([key, value]) => {
    weightOutputs[key].value = value;
    weightOutputs[key].textContent = value;
  });
  els.weightTotal.textContent = total + "%";
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
  let rank = 0;
  live.forEach((row) => {
    if (row.liveScore !== null) {
      rank += 1;
      row.liveRank = rank;
    }
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
  const rank = row.liveRank ? "#" + row.liveRank : "Unranked";
  return rank + " · " + row.route_long_name + " · " + row.route_id;
}

function deterministicRationale(row) {
  const score = row.liveScore == null ? "N/A" : row.liveScore.toFixed(1);
  const emissionsValue = numeric(row, columns.emissions);
  const equityValue = numeric(row, columns.equity);
  const emissions = emissionsValue == null ? "unavailable" : emissionsValue.toFixed(1);
  const equity = equityValue == null ? "unverified" : equityValue.toFixed(1);
  return row.route_long_name + " ranks at " + score + "/100 by combining an emissions activity score of " + emissions + ", an equity density proxy of " + equity + ", a coarse Luzon grid proxy and neutral operator readiness. The ranking is deterministic and responds only to the visible weights; operator readiness remains a placeholder pending cooperative workshops.";
}

function renderCityOptions() {
  const cities = new Set(["All Metro Manila"]);
  state.scores.forEach((row) => {
    String(row.cities_served || "").split("|").filter(Boolean).forEach((city) => {
      if (city !== "Unspecified") cities.add(city);
    });
  });
  const ordered = [...cities].sort((a, b) => a === "All Metro Manila" ? -1 : b === "All Metro Manila" ? 1 : a.localeCompare(b));
  els.cityFilter.innerHTML = ordered.map((city) => "<option value=\"" + escapeHtml(city) + "\">" + escapeHtml(city) + "</option>").join("");
}

function renderMetrics() {
  const complete = state.filtered.filter((row) => row.liveScore !== null);
  const top = complete.length ? Math.max(...complete.map((row) => row.liveScore)).toFixed(1) : "N/A";
  els.routesMetric.textContent = state.filtered.length.toLocaleString();
  els.completeMetric.textContent = complete.length.toLocaleString();
  els.topMetric.textContent = top;
  els.heroTopScore.textContent = top;
}

function renderRouteFinder() {
  els.routeFinder.innerHTML = state.filtered.map((row) => "<option value=\"" + escapeHtml(row.route_id) + "\">" + escapeHtml(routeLabel(row)) + "</option>").join("");
  const selectedStillVisible = state.filtered.some((row) => row.route_id === state.selectedRouteId);
  if (!selectedStillVisible) state.selectedRouteId = state.filtered[0] ? state.filtered[0].route_id : null;
  if (state.selectedRouteId) els.routeFinder.value = state.selectedRouteId;
}

function renderDetails() {
  const row = state.filtered.find((item) => item.route_id === state.selectedRouteId);
  if (!row) return;
  els.routeName.textContent = row.route_long_name;
  els.routeMeta.textContent = row.route_id + " · " + String(row.cities_served || "Unspecified").replaceAll("|", " · ");
  els.rankValue.textContent = row.liveRank ? "#" + row.liveRank : "Unranked";
  els.scoreValue.textContent = row.liveScore == null ? "N/A" : row.liveScore.toFixed(1);
  const length = numeric(row, "length_km");
  els.lengthValue.textContent = length == null ? "N/A" : length.toFixed(1);
  const cached = state.explanations[row.route_id];
  els.sourcePill.textContent = cached && cached.source === "mantle_bedrock_api" ? "AI-generated summary" : "Deterministic · offline-safe";
  els.routeRationale.textContent = cached && cached.text ? cached.text : deterministicRationale(row);
  const breakdown = [
    ["Emissions activity", numeric(row, columns.emissions)],
    ["Equity density", numeric(row, columns.equity)],
    ["Grid proxy", numeric(row, columns.grid)],
    ["Operator readiness", numeric(row, columns.operator)]
  ];
  els.breakdownBars.innerHTML = breakdown.map(([label, value]) => {
    const width = value === null ? 0 : Math.max(0, Math.min(100, value));
    const text = value === null ? "N/A" : value.toFixed(1);
    return "<div><div class=\"bar-label\"><span>" + escapeHtml(label) + "</span><span>" + text + "</span></div><div class=\"bar-track\"><div class=\"bar-fill\" style=\"width:" + width + "%\"></div></div></div>";
  }).join("");
}

function renderLeaderboard() {
  els.leaderboardBody.innerHTML = state.filtered.filter((row) => row.liveScore !== null).slice(0, 12).map((row) => {
    const equity = numeric(row, columns.equity);
    return "<tr data-route-id=\"" + escapeHtml(row.route_id) + "\" class=\"" + (row.route_id === state.selectedRouteId ? "selected-row" : "") + "\"><td>#" + row.liveRank + "</td><td><b>" + escapeHtml(row.route_long_name) + "</b><br><small>" + escapeHtml(row.route_id) + "</small></td><td>" + escapeHtml(row.primary_city || "Unspecified") + "</td><td>" + row.liveScore.toFixed(1) + "</td><td>" + Number(row.emissions_potential_score).toFixed(1) + "</td><td>" + (equity == null ? "N/A" : equity.toFixed(1)) + "</td><td>" + Number(row.grid_feasibility_score).toFixed(1) + "</td><td>" + Number(row.operator_readiness_score).toFixed(1) + "</td></tr>";
  }).join("");
}

function renderScatter() {
  const canvas = els.scatter;
  const ratio = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  const cssWidth = Math.max(300, rect.width);
  const cssHeight = window.innerWidth < 560 ? 320 : 400;
  canvas.width = Math.floor(cssWidth * ratio);
  canvas.height = Math.floor(cssHeight * ratio);
  const ctx = canvas.getContext("2d");
  ctx.scale(ratio, ratio);
  ctx.clearRect(0, 0, cssWidth, cssHeight);
  const margin = { left: 46, right: 18, top: 18, bottom: 44 };
  const width = cssWidth - margin.left - margin.right;
  const height = cssHeight - margin.top - margin.bottom;
  const data = state.filtered.filter((row) => row.liveScore !== null && numeric(row, columns.emissions) !== null && numeric(row, columns.equity) !== null);
  ctx.strokeStyle = "#d9e2d8";
  ctx.lineWidth = 1;
  for (let tick = 0; tick <= 4; tick += 1) {
    const x = margin.left + width * tick / 4;
    const y = margin.top + height * tick / 4;
    ctx.beginPath(); ctx.moveTo(x, margin.top); ctx.lineTo(x, margin.top + height); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(margin.left, y); ctx.lineTo(margin.left + width, y); ctx.stroke();
  }
  ctx.fillStyle = "#627273";
  ctx.font = "11px DM Sans, sans-serif";
  ctx.fillText("Equity", 6, margin.top + 6);
  ctx.fillText("Emissions potential", Math.max(margin.left, margin.left + width - 105), cssHeight - 9);
  data.forEach((row) => {
    const x = margin.left + Number(row.emissions_potential_score) / 100 * width;
    const y = margin.top + height - Number(row.equity_score) / 100 * height;
    const radius = Math.max(2.5, Math.min(10, Math.sqrt(Number(row.trips_per_day_estimate) || 1) / 3.5));
    ctx.beginPath();
    ctx.fillStyle = scoreColor(row.liveScore);
    ctx.globalAlpha = row.route_id === state.selectedRouteId ? 1 : 0.52;
    ctx.arc(x, y, row.route_id === state.selectedRouteId ? radius + 3 : radius, 0, Math.PI * 2);
    ctx.fill();
    if (row.route_id === state.selectedRouteId) {
      ctx.strokeStyle = "#071a20";
      ctx.lineWidth = 2;
      ctx.stroke();
    }
  });
  ctx.globalAlpha = 1;
}

function emptyFeatureCollection() {
  return { type: "FeatureCollection", features: [] };
}

function routePointCollection() {
  const features = state.filtered.filter((row) => row.liveScore !== null).slice(0, 500).map((row) => {
    const coords = state.pathByRoute.get(row.route_id);
    if (!coords || !coords.length) return null;
    const midpoint = coords[Math.floor(coords.length / 2)];
    return {
      type: "Feature",
      properties: { routeId: row.route_id, title: row.route_long_name, score: Number(row.liveScore.toFixed(2)), rank: row.liveRank },
      geometry: { type: "Point", coordinates: midpoint }
    };
  }).filter(Boolean);
  return { type: "FeatureCollection", features };
}

function updateRoadStatus(message, type) {
  els.roadStatus.className = "road-status" + (type ? " " + type : "");
  els.roadStatus.querySelector("span").textContent = message;
}

function setMapCursor(layer, cursor) {
  state.map.on("mouseenter", layer, () => { state.map.getCanvas().style.cursor = cursor; });
  state.map.on("mouseleave", layer, () => { state.map.getCanvas().style.cursor = ""; });
}

function initialiseMap() {
  if (!MAPBOX_ACCESS_TOKEN) {
    updateRoadStatus("Mapbox is not configured. Add MAPBOX_TOKEN in Netlify.", "error");
    return;
  }
  if (!window.mapboxgl) {
    updateRoadStatus("Mapbox could not load. Check your connection.", "error");
    return;
  }
  state.map = new window.mapboxgl.Map({
    accessToken: MAPBOX_ACCESS_TOKEN,
    container: "map",
    style: MAPBOX_STYLE_URL,
    center: [121.02, 14.61],
    zoom: 9.55,
    pitch: 22,
    bearing: -8,
    attributionControl: true,
    preserveDrawingBuffer: true
  });
  state.map.addControl(new window.mapboxgl.NavigationControl({ visualizePitch: true }), "top-right");
  state.map.addControl(new window.mapboxgl.FullscreenControl(), "top-right");
  state.map.on("load", () => {
    state.mapReady = true;
    state.map.addSource("route-points", { type: "geojson", data: routePointCollection(), cluster: true, clusterMaxZoom: 13, clusterRadius: 42 });
    state.map.addLayer({ id: "route-clusters", type: "circle", source: "route-points", filter: ["has", "point_count"], paint: { "circle-color": "#0b3435", "circle-radius": ["step", ["get", "point_count"], 17, 25, 22, 90, 28], "circle-stroke-color": "#c8f65b", "circle-stroke-width": 2, "circle-opacity": 0.93 } });
    state.map.addLayer({ id: "cluster-count", type: "symbol", source: "route-points", filter: ["has", "point_count"], layout: { "text-field": ["get", "point_count_abbreviated"], "text-size": 11 }, paint: { "text-color": "#ffffff" } });
    state.map.addLayer({ id: "route-points-layer", type: "circle", source: "route-points", filter: ["!", ["has", "point_count"]], paint: { "circle-color": ["interpolate", ["linear"], ["get", "score"], 0, "#ff6c64", 50, "#ffbd4a", 100, "#55dec0"], "circle-radius": ["interpolate", ["linear"], ["zoom"], 8, 4, 13, 7], "circle-stroke-color": "#ffffff", "circle-stroke-width": 1.5, "circle-opacity": 0.9 } });
    state.map.addSource("selected-route", { type: "geojson", data: { type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: [] } } });
    state.map.addLayer({ id: "selected-route-casing", type: "line", source: "selected-route", layout: { "line-cap": "round", "line-join": "round" }, paint: { "line-color": "#071a20", "line-width": ["interpolate", ["linear"], ["zoom"], 9, 6, 15, 12], "line-opacity": 0.92 } });
    state.map.addLayer({ id: "selected-route-line", type: "line", source: "selected-route", layout: { "line-cap": "round", "line-join": "round" }, paint: { "line-color": "#c8f65b", "line-width": ["interpolate", ["linear"], ["zoom"], 9, 3, 15, 7], "line-opacity": 1 } });
    state.map.addSource("selected-endpoints", { type: "geojson", data: emptyFeatureCollection() });
    state.map.addLayer({ id: "selected-endpoints-layer", type: "circle", source: "selected-endpoints", paint: { "circle-radius": 7, "circle-color": ["match", ["get", "kind"], "start", "#55dec0", "#ffbd4a"], "circle-stroke-color": "#071a20", "circle-stroke-width": 2 } });
    state.map.on("click", "route-clusters", (event) => {
      const feature = state.map.queryRenderedFeatures(event.point, { layers: ["route-clusters"] })[0];
      if (!feature) return;
      state.map.getSource("route-points").getClusterExpansionZoom(feature.properties.cluster_id, (error, zoom) => {
        if (!error) state.map.easeTo({ center: feature.geometry.coordinates, zoom });
      });
    });
    state.map.on("click", "route-points-layer", (event) => {
      const feature = event.features && event.features[0];
      if (!feature) return;
      setSelected(String(feature.properties.routeId), true);
    });
    state.map.on("mouseenter", "route-points-layer", (event) => {
      const feature = event.features && event.features[0];
      if (!feature) return;
      new window.mapboxgl.Popup({ closeButton: false, closeOnClick: false, offset: 12, className: "route-hover-popup" })
        .setLngLat(feature.geometry.coordinates)
        .setHTML("<div class=\"map-popup\"><b>" + escapeHtml(feature.properties.title) + "</b><span>Priority " + Number(feature.properties.score).toFixed(1) + "/100 · Rank #" + feature.properties.rank + "</span></div>")
        .addTo(state.map);
    });
    state.map.on("mouseleave", "route-points-layer", () => {
      const popup = document.querySelector(".route-hover-popup");
      if (popup) popup.remove();
    });
    setMapCursor("route-clusters", "pointer");
    setMapCursor("route-points-layer", "pointer");
    drawSelectedRoadRoute();
  });
  state.map.on("error", (event) => {
    if (!state.mapReady && event && event.error) updateRoadStatus("Map style could not load. Verify the Mapbox style is public.", "error");
  });
}

function refreshMapPoints() {
  if (!state.mapReady) return;
  state.map.getSource("route-points").setData(routePointCollection());
  const row = state.filtered.find((item) => item.route_id === state.selectedRouteId);
  if (row) {
    state.map.setPaintProperty("selected-route-line", "line-color", scoreColor(row.liveScore));
  }
}

function cleanedCoordinates(routeId) {
  const coords = state.pathByRoute.get(routeId) || [];
  const valid = coords.filter((point) => Array.isArray(point) && point.length >= 2 && Number.isFinite(Number(point[0])) && Number.isFinite(Number(point[1]))).map((point) => [Number(point[0]), Number(point[1])]);
  return valid.filter((point, index) => index === 0 || point[0] !== valid[index - 1][0] || point[1] !== valid[index - 1][1]);
}

function coordinateChunks(coords, size) {
  const chunks = [];
  for (let start = 0; start < coords.length - 1; start += size - 1) {
    const chunk = coords.slice(start, start + size);
    if (chunk.length >= 2) chunks.push(chunk);
  }
  return chunks;
}

async function requestRoadGeometry(routeId) {
  if (state.roadGeometryCache.has(routeId)) return state.roadGeometryCache.get(routeId);
  const coords = cleanedCoordinates(routeId);
  if (coords.length < 2) throw new Error("This route does not have enough ordered coordinates.");
  const chunks = coordinateChunks(coords, 25);
  const results = await Promise.all(chunks.map(async (chunk) => {
    const coordinates = chunk.map((point) => point[0].toFixed(6) + "," + point[1].toFixed(6)).join(";");
    const url = "https://api.mapbox.com/directions/v5/mapbox/driving/" + coordinates + "?alternatives=false&continue_straight=true&geometries=geojson&overview=full&steps=false&access_token=" + encodeURIComponent(MAPBOX_ACCESS_TOKEN);
    const response = await fetch(url);
    const data = await response.json();
    if (!response.ok || !data.routes || !data.routes[0] || !data.routes[0].geometry) throw new Error(data.message || "Mapbox could not build this street path.");
    return data.routes[0].geometry.coordinates;
  }));
  const merged = [];
  results.forEach((part) => part.forEach((point, index) => {
    if (index > 0 || merged.length === 0) merged.push(point);
  }));
  if (merged.length < 2) throw new Error("Mapbox returned an empty street path.");
  state.roadGeometryCache.set(routeId, merged);
  return merged;
}

function fitMapToCoordinates(coords) {
  if (!state.mapReady || !coords.length) return;
  const bounds = coords.reduce((box, coord) => box.extend(coord), new window.mapboxgl.LngLatBounds(coords[0], coords[0]));
  state.map.fitBounds(bounds, { padding: window.innerWidth < 560 ? 48 : 78, maxZoom: 14.5, duration: 900 });
}

async function drawSelectedRoadRoute() {
  if (!state.mapReady || !state.selectedRouteId) return;
  const routeId = state.selectedRouteId;
  const requestId = ++state.roadRequestId;
  const raw = cleanedCoordinates(routeId);
  const lineSource = state.map.getSource("selected-route");
  const endpointSource = state.map.getSource("selected-endpoints");
  lineSource.setData({ type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: [] } });
  if (raw.length >= 2) {
    endpointSource.setData({ type: "FeatureCollection", features: [
      { type: "Feature", properties: { kind: "start" }, geometry: { type: "Point", coordinates: raw[0] } },
      { type: "Feature", properties: { kind: "end" }, geometry: { type: "Point", coordinates: raw[raw.length - 1] } }
    ] });
    fitMapToCoordinates(raw);
  } else {
    endpointSource.setData(emptyFeatureCollection());
  }
  updateRoadStatus("Matching the selected corridor to drivable streets…", "");
  try {
    const roadCoords = await requestRoadGeometry(routeId);
    if (requestId !== state.roadRequestId || routeId !== state.selectedRouteId) return;
    lineSource.setData({ type: "Feature", properties: { routeId }, geometry: { type: "LineString", coordinates: roadCoords } });
    fitMapToCoordinates(roadCoords);
    updateRoadStatus("Street-following route ready · Mapbox Directions", "success");
  } catch (error) {
    if (requestId !== state.roadRequestId || routeId !== state.selectedRouteId) return;
    lineSource.setData({ type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: [] } });
    updateRoadStatus("No reliable road path shown: " + error.message, "error");
  }
}

function setSelected(routeId, scrollToMap) {
  if (!state.filtered.some((row) => row.route_id === routeId)) return;
  state.selectedRouteId = routeId;
  els.routeFinder.value = routeId;
  renderDetails();
  renderLeaderboard();
  renderScatter();
  refreshMapPoints();
  drawSelectedRoadRoute();
  if (scrollToMap) document.querySelector("#map-section").scrollIntoView({ behavior: "smooth", block: "start" });
}

function toCsv(rows) {
  const headers = Object.keys(rows[0] || {});
  const quote = (value) => "\"" + String(value == null ? "" : value).replaceAll("\"", "\"\"") + "\"";
  return [headers.join(","), ...rows.map((row) => headers.map((header) => quote(row[header])).join(","))].join("\n");
}

function safeFilePart(value) {
  return String(value || "metro_manila").toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "");
}

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 500);
}

function downloadCsv() {
  const exportRows = state.filtered.map((row) => ({ ...row, live_priority_score: row.liveScore == null ? "" : row.liveScore.toFixed(3), live_rank: row.liveRank || "", live_confidence: row.liveConfidence }));
  triggerDownload(new Blob([toCsv(exportRows)], { type: "text/csv;charset=utf-8" }), "route2zero_" + safeFilePart(els.cityFilter.value) + "_rankings.csv");
}

function selectedRow() {
  return state.filtered.find((row) => row.route_id === state.selectedRouteId) || state.filtered[0];
}

function topRows(limit) {
  return state.filtered.filter((row) => row.liveScore !== null).slice(0, limit);
}

function mapImage() {
  try { return state.mapReady ? state.map.getCanvas().toDataURL("image/png") : ""; } catch { return ""; }
}

function exportPdfReport() {
  if (!window.jspdf || !window.jspdf.jsPDF) {
    window.alert("The PDF exporter is still loading. Please try again in a moment.");
    return;
  }
  const row = selectedRow();
  if (!row) return;
  const doc = new window.jspdf.jsPDF({ unit: "mm", format: "a4", orientation: "portrait" });
  const weights = getWeights();
  doc.setFillColor(7, 26, 32); doc.rect(0, 0, 210, 42, "F");
  doc.setTextColor(200, 246, 91); doc.setFont("helvetica", "bold"); doc.setFontSize(22); doc.text("Route2Zero", 15, 18);
  doc.setTextColor(232, 244, 240); doc.setFontSize(10); doc.setFont("helvetica", "normal"); doc.text("Electrification Priority Brief · " + els.cityFilter.value + " · 2026", 15, 28);
  doc.setTextColor(11, 35, 40); doc.setFont("helvetica", "bold"); doc.setFontSize(15); doc.text("Selected corridor", 15, 54);
  doc.setFontSize(12); doc.text(doc.splitTextToSize(row.route_long_name, 178), 15, 63);
  doc.setFont("helvetica", "normal"); doc.setFontSize(9); doc.setTextColor(92, 110, 110); doc.text(row.route_id + " · " + String(row.cities_served || "Unspecified").replaceAll("|", " · "), 15, 72);
  doc.setTextColor(11, 35, 40); doc.setFont("helvetica", "bold"); doc.setFontSize(22); doc.text(row.liveScore == null ? "N/A" : row.liveScore.toFixed(1), 165, 62);
  doc.setFontSize(8); doc.text("PRIORITY / 100", 165, 69);
  const image = mapImage();
  let tableStart = 87;
  if (image) {
    doc.addImage(image, "PNG", 15, 79, 180, 72, undefined, "FAST");
    doc.setFont("helvetica", "normal"); doc.setFontSize(6.5); doc.setTextColor(100, 115, 115); doc.text("Street-following planning visualisation · Map © Mapbox · Data © OpenStreetMap", 15, 155);
    tableStart = 164;
  }
  doc.setFont("helvetica", "bold"); doc.setFontSize(11); doc.setTextColor(11, 35, 40); doc.text("Top recommendations", 15, tableStart);
  const rows = topRows(8).map((item) => ["#" + item.liveRank, item.route_long_name, item.primary_city || "—", item.liveScore.toFixed(1)]);
  doc.autoTable({ startY: tableStart + 5, head: [["Rank", "Route", "Primary city", "Priority"]], body: rows, margin: { left: 15, right: 15 }, styles: { fontSize: 7.5, cellPadding: 2.2 }, headStyles: { fillColor: [15, 113, 111], textColor: 255 }, alternateRowStyles: { fillColor: [243, 246, 240] }, columnStyles: { 0: { cellWidth: 15 }, 2: { cellWidth: 34 }, 3: { cellWidth: 20 } } });
  doc.addPage();
  doc.setFillColor(7, 26, 32); doc.rect(0, 0, 210, 24, "F"); doc.setTextColor(200, 246, 91); doc.setFontSize(15); doc.text("Decision logic and next steps", 15, 15);
  doc.setTextColor(11, 35, 40); doc.setFontSize(11); doc.text("Scenario weights", 15, 36);
  doc.setFont("helvetica", "normal"); doc.setFontSize(9); doc.text("Emissions " + weights.emissions + "%  ·  Equity " + weights.equity + "%  ·  Grid " + weights.grid + "%  ·  Operator " + weights.operator + "%", 15, 44);
  doc.setFont("helvetica", "bold"); doc.setFontSize(11); doc.text("Why this route", 15, 58);
  doc.setFont("helvetica", "normal"); doc.setFontSize(9); doc.text(doc.splitTextToSize(deterministicRationale(row), 180), 15, 67);
  const methodY = 96;
  doc.setFont("helvetica", "bold"); doc.setFontSize(11); doc.text("Known assumptions", 15, methodY);
  doc.setFont("helvetica", "normal"); doc.setFontSize(8.5);
  const notes = [
    "Emissions: route kilometres × estimated weekday trips; an activity proxy, not measured tailpipe emissions.",
    "Equity: population-weighted exposure to 2020 WorldPop density within a 300 m corridor catchment.",
    "Grid: 2024 Luzon renewable generation share, not local charger or substation capacity.",
    "Operator: neutral 50/100 placeholder pending cooperative workshops.",
    "Geometry: Mapbox builds a drivable street path from ordered GTFS coordinates; this is not an official franchise boundary.",
    "AI: optional text explains deterministic scores after ranking and never changes them."
  ];
  let y = methodY + 9;
  notes.forEach((note) => { doc.text("• " + doc.splitTextToSize(note, 174).join("\n  "), 17, y); y += 15; });
  doc.setFillColor(232, 239, 229); doc.roundedRect(15, y + 2, 180, 45, 3, 3, "F");
  doc.setFont("helvetica", "bold"); doc.setFontSize(10); doc.text("Recommended next-step pilot", 21, y + 13);
  doc.setFont("helvetica", "normal"); doc.setFontSize(8.5); doc.text(doc.splitTextToSize("Validate the highest-priority corridors with LGUs and cooperatives; collect fleet, fuel, ridership, depot and financing evidence; conduct distribution-grid screening; then compare investment scenarios before procurement.", 165), 21, y + 23);
  doc.save("route2zero_" + safeFilePart(els.cityFilter.value) + "_decision_brief.pdf");
}

function wordReportHtml() {
  const row = selectedRow();
  const weights = getWeights();
  const image = mapImage();
  const tableRows = topRows(12).map((item) => "<tr><td>#" + item.liveRank + "</td><td>" + escapeHtml(item.route_long_name) + "</td><td>" + escapeHtml(item.primary_city || "—") + "</td><td>" + item.liveScore.toFixed(1) + "</td></tr>").join("");
  return "<!doctype html><html><head><meta charset=\"utf-8\"><style>body{font-family:Arial,sans-serif;color:#0b2328;margin:38px}h1{color:#0f716f}h2{margin-top:28px;border-bottom:2px solid #c8f65b;padding-bottom:6px}.meta{color:#627273}.score{font-size:28px;font-weight:bold;color:#0f716f}table{width:100%;border-collapse:collapse}th,td{border:1px solid #d9e2d8;padding:8px;text-align:left}th{background:#0f716f;color:white}.note{background:#f3f6f0;padding:14px}img{width:100%;max-width:720px}</style></head><body><h1>Route2Zero Electrification Priority Brief</h1><p class=\"meta\">" + escapeHtml(els.cityFilter.value) + " · 2026 · Deterministic decision support</p><h2>Selected corridor</h2><h3>" + escapeHtml(row.route_long_name) + "</h3><p>" + escapeHtml(row.route_id) + " · " + escapeHtml(String(row.cities_served || "Unspecified").replaceAll("|", " · ")) + "</p><p class=\"score\">" + (row.liveScore == null ? "N/A" : row.liveScore.toFixed(1)) + "/100 · Rank #" + (row.liveRank || "—") + "</p>" + (image ? "<img src=\"" + image + "\"><p class=\"meta\">Street-following planning visualisation · Map © Mapbox · Data © OpenStreetMap</p>" : "") + "<h2>Why this route</h2><p>" + escapeHtml(deterministicRationale(row)) + "</p><h2>Scenario weights</h2><p>Emissions " + weights.emissions + "% · Equity " + weights.equity + "% · Grid " + weights.grid + "% · Operator " + weights.operator + "%</p><h2>Top recommendations</h2><table><thead><tr><th>Rank</th><th>Route</th><th>Primary city</th><th>Priority</th></tr></thead><tbody>" + tableRows + "</tbody></table><h2>Method and limitations</h2><div class=\"note\"><p><b>Emissions:</b> activity proxy based on route kilometres and estimated weekday trips.</p><p><b>Equity:</b> 2020 WorldPop density within a 300 m catchment.</p><p><b>Grid:</b> Luzon-wide renewable share, not local capacity.</p><p><b>Operator:</b> neutral placeholder pending workshops.</p><p><b>Geometry:</b> Mapbox street path from ordered GTFS coordinates; not an official franchise boundary.</p><p><b>AI:</b> explains only; never scores or ranks.</p></div><h2>Recommended next step</h2><p>Validate priority corridors with LGUs and cooperatives, collect operational evidence, screen local grid capacity, and compare investment scenarios before procurement.</p></body></html>";
}

function exportWordReport() {
  triggerDownload(new Blob(["\ufeff", wordReportHtml()], { type: "application/msword;charset=utf-8" }), "route2zero_" + safeFilePart(els.cityFilter.value) + "_decision_brief.doc");
}

function currentFacts() {
  const query = els.questionInput.value.toLowerCase();
  let candidates = state.filtered;
  [...els.cityFilter.options].map((option) => option.value).filter((city) => city !== "All Metro Manila").forEach((city) => {
    if (query.includes(city.toLowerCase())) candidates = candidates.filter((row) => String(row.cities_served || "").toLowerCase().includes(city.toLowerCase()));
  });
  return candidates.filter((row) => row.liveScore !== null).slice(0, 5).map((row) => row.route_long_name + ": " + row.liveScore.toFixed(1) + "/100").join("; ");
}

async function askQuestion() {
  const question = els.questionInput.value.trim();
  if (!question) return;
  const facts = currentFacts();
  els.askButton.disabled = true;
  els.answerSource.classList.add("hidden");
  els.answerText.textContent = "Generating a concise evidence brief…";
  try {
    const response = await fetch("/.netlify/functions/explain", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ question, facts }) });
    const data = await response.json();
    els.answerSource.textContent = data.source === "netlify_function_api" ? "AI-generated via secure Netlify Function" : "Offline deterministic answer";
    els.answerText.textContent = data.answer || "No answer was returned.";
  } catch {
    els.answerSource.textContent = "Offline deterministic answer";
    els.answerText.textContent = "Based on the current filters, the leading routes are " + facts + ". These are deterministic weighted scores; operator readiness remains a placeholder.";
  } finally {
    els.answerSource.classList.remove("hidden");
    els.askButton.disabled = false;
  }
}

function renderAll() {
  const previousSelected = state.selectedRouteId;
  computeLiveScores();
  renderMetrics();
  renderRouteFinder();
  renderDetails();
  renderLeaderboard();
  renderScatter();
  refreshMapPoints();
  if (state.mapReady && previousSelected !== state.selectedRouteId) drawSelectedRoadRoute();
}

function setControlsOpen(open) {
  document.body.classList.toggle("controls-open", open);
  els.mobileControlsButton.setAttribute("aria-expanded", String(open));
  els.controlsBackdrop.setAttribute("aria-hidden", String(!open));
}

async function init() {
  const [scoresText, citiesText, geojson, explanations] = await Promise.all([
    fetch("/data/route2zero_scores.csv").then((response) => { if (!response.ok) throw new Error("Scores data could not be loaded."); return response.text(); }),
    fetch("/data/route_cities.csv").then((response) => { if (!response.ok) throw new Error("City data could not be loaded."); return response.text(); }),
    fetch("/data/route2zero_scores.geojson").then((response) => { if (!response.ok) throw new Error("Route geometry could not be loaded."); return response.json(); }),
    fetch("/data/route_explanations.json").then((response) => response.ok ? response.json() : {}).catch(() => ({}))
  ]);
  const citiesByRoute = new Map(parseCsv(citiesText).map((row) => [row.route_id, row]));
  state.scores = parseCsv(scoresText).map((row) => ({ ...row, ...(citiesByRoute.get(row.route_id) || {}) }));
  state.geojson = geojson;
  state.explanations = explanations;
  state.geojson.features.forEach((feature) => {
    if (feature.geometry && feature.geometry.type === "LineString") state.pathByRoute.set(String(feature.properties.route_id), feature.geometry.coordinates);
  });
  renderCityOptions();
  renderAll();
  initialiseMap();
}

Object.values(weightInputs).forEach((input) => input.addEventListener("input", renderAll));
els.cityFilter.addEventListener("change", renderAll);
els.includeUnverified.addEventListener("change", renderAll);
els.routeFinder.addEventListener("change", (event) => setSelected(event.target.value, false));
els.leaderboardBody.addEventListener("click", (event) => {
  const row = event.target.closest("tr[data-route-id]");
  if (row) setSelected(row.dataset.routeId, true);
});
els.downloadCsv.addEventListener("click", downloadCsv);
els.exportPdf.addEventListener("click", exportPdfReport);
els.exportWord.addEventListener("click", exportWordReport);
els.askButton.addEventListener("click", askQuestion);
els.questionInput.addEventListener("keydown", (event) => { if ((event.ctrlKey || event.metaKey) && event.key === "Enter") askQuestion(); });
els.mobileControlsButton.addEventListener("click", () => setControlsOpen(!document.body.classList.contains("controls-open")));
els.closeControls.addEventListener("click", () => setControlsOpen(false));
els.controlsBackdrop.addEventListener("click", () => setControlsOpen(false));
els.openMethod.addEventListener("click", () => {
  els.methodDetails.open = true;
  els.methodDetails.scrollIntoView({ behavior: "smooth", block: "center" });
});
window.addEventListener("resize", () => { renderScatter(); if (window.innerWidth > 840) setControlsOpen(false); });

init().catch((error) => {
  document.querySelector(".content").innerHTML = "<section class=\"panel\"><h1>Route2Zero could not load</h1><p>" + escapeHtml(error.message) + "</p><p>Please refresh the page or verify the generated data files.</p></section>";
});
