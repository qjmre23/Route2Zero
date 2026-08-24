"""Route2Zero: transparent route-electrification priority dashboard."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bedrock_client import deterministic_route_rationale, generate_explanation_with_status  # noqa: E402


PROCESSED = ROOT / "data" / "processed"
DEFAULT_WEIGHTS = {"emissions": 35, "equity": 35, "grid": 15, "operator": 15}


st.set_page_config(
    page_title="Route2Zero | Just Transition Route Priorities",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root { --ink:#082f35; --teal:#087f8c; --mint:#33d6b0; --sun:#ffbe3d; --paper:#f5faf8; }
    .stApp { background: radial-gradient(circle at 85% 5%, #dffaf1 0, transparent 28%), #f7fbfa; color: var(--ink); }
    [data-testid="stSidebar"] { background: linear-gradient(180deg,#062e34 0%,#0a4c53 100%); }
    [data-testid="stSidebar"] * { color:#f5fffc !important; }
    [data-testid="stSidebar"] [data-baseweb="slider"] div { color:#35d5b2 !important; }
    .hero { padding:1.45rem 1.7rem; border-radius:24px; color:white; margin:0 0 1rem 0;
      background:linear-gradient(125deg,#063b43 0%,#087f8c 58%,#20b89e 100%); box-shadow:0 16px 42px rgba(8,73,78,.18); }
    .hero h1 { font-size:clamp(2.15rem,5vw,4rem); line-height:.95; margin:0; letter-spacing:-.05em; color:white; }
    .hero p { max-width:820px; font-size:1.03rem; opacity:.9; margin:.85rem 0 .15rem; }
    .eyebrow { text-transform:uppercase; letter-spacing:.16em; font-size:.72rem; font-weight:800; color:#b9fff0; margin-bottom:.65rem; }
    .confidence { border:1px solid #f1c25b; background:#fff8df; color:#5c4300; padding:.9rem 1rem; border-radius:14px; margin:.6rem 0 1.1rem; }
    .metric-note { color:#55706f; font-size:.82rem; }
    .source-pill { display:inline-block; border-radius:999px; padding:.2rem .55rem; margin-right:.3rem; background:#dff7ef; color:#075c56; font-size:.74rem; font-weight:700; }
    div[data-testid="stMetric"] { background:rgba(255,255,255,.88); border:1px solid #d6e9e4; padding:.8rem 1rem; border-radius:16px; box-shadow:0 8px 24px rgba(18,84,82,.06); }
    div[data-testid="stDataFrame"], div[data-testid="stPlotlyChart"], .st-key-route_map { border-radius:18px; overflow:hidden; }
    h2,h3 { color:#0b5158; letter-spacing:-.025em; }
    @media (max-width: 700px) { .hero { padding:1.1rem; border-radius:18px; } .hero p{font-size:.94rem;} }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_data() -> tuple[pd.DataFrame, dict, pd.DataFrame, pd.DataFrame, dict]:
    scores = pd.read_csv(PROCESSED / "route2zero_scores.csv", dtype={"route_id": str})
    route_cities = pd.read_csv(PROCESSED / "route_cities.csv", dtype={"route_id": str})
    city_summary = pd.read_csv(PROCESSED / "city_summary.csv")
    geojson = json.loads((PROCESSED / "route2zero_scores.geojson").read_text(encoding="utf-8"))
    explanation_path = PROCESSED / "route_explanations.json"
    explanations = json.loads(explanation_path.read_text(encoding="utf-8")) if explanation_path.exists() else {}
    return scores, geojson, route_cities, city_summary, explanations


def score_color(value: float, alpha: int = 220) -> list[int]:
    if pd.isna(value):
        return [128, 143, 143, 110]
    x = max(0.0, min(100.0, float(value))) / 100.0
    low, mid, high = np.array([225, 74, 74]), np.array([245, 166, 35]), np.array([20, 177, 141])
    rgb = low + (mid - low) * (x * 2) if x <= 0.5 else mid + (high - mid) * ((x - 0.5) * 2)
    return [int(channel) for channel in rgb] + [alpha]


def compute_live_score(frame: pd.DataFrame, weights: dict[str, int], include_unverified: bool) -> pd.DataFrame:
    result = frame.copy()
    columns = {
        "emissions": "emissions_potential_score",
        "equity": "equity_score",
        "grid": "grid_feasibility_score",
        "operator": "operator_readiness_score",
    }
    total = sum(weights.values())
    normalized = {key: value / total for key, value in weights.items()}
    result["live_score"] = float("nan")
    complete = result[list(columns.values())].notna().all(axis=1)
    result.loc[complete, "live_score"] = sum(
        result.loc[complete, column] * normalized[key] for key, column in columns.items()
    )
    result["live_confidence"] = np.where(complete, "complete proxy mix", "metric unavailable")
    if include_unverified:
        missing_equity_only = result["equity_score"].isna() & result[
            [columns["emissions"], columns["grid"], columns["operator"]]
        ].notna().all(axis=1)
        available_weight = 1.0 - normalized["equity"]
        if available_weight > 0:
            reduced = (
                result.loc[missing_equity_only, columns["emissions"]] * normalized["emissions"]
                + result.loc[missing_equity_only, columns["grid"]] * normalized["grid"]
                + result.loc[missing_equity_only, columns["operator"]] * normalized["operator"]
            ) / available_weight
            result.loc[missing_equity_only, "live_score"] = reduced * 0.85
            result.loc[missing_equity_only, "live_confidence"] = "reduced: equity unavailable"
    result["live_rank"] = result["live_score"].rank(method="first", ascending=False).astype("Int64")
    return result


def route_paths(geojson: dict) -> dict[str, list[list[float]]]:
    return {
        str(feature["properties"]["route_id"]): feature["geometry"]["coordinates"]
        for feature in geojson["features"]
        if feature.get("geometry", {}).get("type") == "LineString"
    }


scores, geojson, route_cities, city_summary, explanations = load_data()
scores = scores.merge(route_cities, on="route_id", how="left")

with st.sidebar:
    st.markdown("## Route2Zero")
    st.caption("Decision support for a just e-jeepney transition")
    city_options = ["All Metro Manila"] + sorted(
        city for city in route_cities["cities_served"].str.split("|").explode().dropna().unique() if city != "Unspecified"
    )
    city = st.selectbox("City / LGU lens", city_options)
    include_unverified = st.toggle("Include unverified equity routes", value=False)
    st.markdown("### Live score weights")
    emissions_weight = st.slider("Emissions potential", 0, 100, DEFAULT_WEIGHTS["emissions"], 5)
    equity_weight = st.slider("Equity density proxy", 0, 100, DEFAULT_WEIGHTS["equity"], 5)
    grid_weight = st.slider("Grid feasibility", 0, 100, DEFAULT_WEIGHTS["grid"], 5)
    operator_weight = st.slider("Operator readiness", 0, 100, DEFAULT_WEIGHTS["operator"], 5)
    weights = {
        "emissions": emissions_weight,
        "equity": equity_weight,
        "grid": grid_weight,
        "operator": operator_weight,
    }
    if sum(weights.values()) == 0:
        st.warning("At least one weight must be above zero.")
        st.stop()
    st.caption("Weights are normalized automatically. AI never changes these numbers.")

live = compute_live_score(scores, weights, include_unverified)
if city != "All Metro Manila":
    city_mask = live["cities_served"].fillna("").str.split("|").map(lambda values: city in values)
    filtered = live[city_mask].copy()
else:
    filtered = live.copy()
if not include_unverified:
    filtered = filtered[filtered["equity_score"].notna()].copy()
filtered = filtered.sort_values(["live_score", "route_id"], ascending=[False, True], na_position="last")

st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">Metro Manila · Route electrification intelligence</div>
      <h1>Route2Zero</h1>
      <p>Rank e-jeepney corridors by climate impact, equitable service, grid context, and operator readiness — with every proxy and placeholder visible before anyone asks.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    <div class="confidence"><strong>Data confidence is part of the product.</strong> GTFS service dates span 2013–2020; 1,520 of 1,522 geometries connect ordered stops rather than road-snapped shapes. Emissions are an activity proxy, equity uses 2020 WorldPop density rather than settlement boundaries, grid is one Luzon baseline, and operator readiness defaults to 50 pending cooperative workshops.</div>
    """,
    unsafe_allow_html=True,
)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Routes in view", f"{len(filtered):,}")
k2.metric("Complete scores", f"{filtered['live_score'].notna().sum():,}")
k3.metric("Top priority score", f"{filtered['live_score'].max():.1f}" if filtered['live_score'].notna().any() else "N/A")
k4.metric("Equity source", "WorldPop 2020", help="1 km population density proxy, not informal-settlement boundaries")

st.markdown("## Explore priority corridors")
st.caption("Select a line on the map or use the route finder. Color moves from red (lower priority) through amber to green (higher priority); lighter lines are stop-sequence approximations.")
paths = route_paths(geojson)
map_rows = []
approximate_alpha = 48 if len(filtered) > 300 else 150
approximate_width = 1.35 if len(filtered) > 300 else 2.25
for row in filtered.itertuples(index=False):
    path = paths.get(row.route_id)
    if not path:
        continue
    approximate = row.geometry_source == "stop_sequence_approx"
    map_rows.append(
        {
            "route_id": row.route_id,
            "route_name": row.route_long_name,
            "score": None if pd.isna(row.live_score) else round(float(row.live_score), 1),
            "rank": None if pd.isna(row.live_rank) else int(row.live_rank),
            "geometry_source": row.geometry_source,
            "path": path,
            "color": score_color(row.live_score, approximate_alpha if approximate else 235),
            "width": approximate_width if approximate else 4.2,
        }
    )
layer = pdk.Layer(
    "PathLayer",
    id="routes",
    data=map_rows,
    pickable=True,
    auto_highlight=True,
    get_path="path",
    get_color="color",
    get_width="width",
    width_units=pdk.types.String("pixels"),
    width_min_pixels=1,
    highlight_color=[255, 255, 255, 220],
)
deck = pdk.Deck(
    map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    initial_view_state=pdk.ViewState(latitude=14.61, longitude=121.01, zoom=9.4, pitch=0),
    layers=[layer],
    tooltip={
        "html": "<b>{route_name}</b><br/>Priority #{rank} · {score}/100<br/><span style='opacity:.75'>{geometry_source}</span>",
        "style": {"backgroundColor": "#063b43", "color": "white", "fontSize": "13px"},
    },
)
map_event = st.pydeck_chart(
    deck, height=540, width="stretch", selection_mode="single-object", on_select="rerun", key="route_map"
)

selected_from_map = None
try:
    selected_objects = map_event.selection.objects.get("routes", [])
    if selected_objects:
        selected_from_map = selected_objects[0].get("route_id")
except (AttributeError, KeyError, TypeError):
    selected_from_map = None

route_labels = {
    f"#{int(row.live_rank) if pd.notna(row.live_rank) else '—'} · {row.route_long_name} · {row.route_id}": row.route_id
    for row in filtered.itertuples(index=False)
}
default_route_id = selected_from_map or (filtered.iloc[0]["route_id"] if not filtered.empty else None)
label_list = list(route_labels)
default_index = next((i for i, label in enumerate(label_list) if route_labels[label] == default_route_id), 0)
selected_label = st.selectbox("Route finder", label_list, index=default_index if label_list else None)
selected_route_id = selected_from_map or (route_labels.get(selected_label) if selected_label else None)

if selected_route_id:
    selected = filtered.loc[filtered["route_id"].eq(selected_route_id)].iloc[0]
    detail_left, detail_right = st.columns([1.05, 1], gap="large")
    with detail_left:
        st.markdown(f"### {selected['route_long_name']}")
        st.caption(f"{selected['route_id']} · {selected.get('cities_served', 'Unspecified').replace('|', ' · ')}")
        d1, d2, d3 = st.columns(3)
        d1.metric("Live rank", f"#{int(selected['live_rank'])}" if pd.notna(selected['live_rank']) else "Unranked")
        d2.metric("Priority score", f"{selected['live_score']:.1f}" if pd.notna(selected['live_score']) else "N/A")
        d3.metric("Length (km)", f"{selected['length_km']:.1f}")
        cached = explanations.get(selected_route_id)
        rationale = cached["text"] if cached else deterministic_route_rationale(selected)
        source_label = "AI-generated summary" if cached and cached.get("source") == "mantle_bedrock_api" else "Deterministic explanation · offline-safe"
        st.markdown(f"<span class='source-pill'>{source_label}</span>", unsafe_allow_html=True)
        st.write(rationale)
        st.caption(
            f"Estimated {selected['trips_per_day_estimate']:.1f} trips/day at {selected['avg_headway_min']:.1f}-minute average headway. Geometry: {selected['geometry_source']}."
        )
    with detail_right:
        breakdown = pd.DataFrame(
            {
                "Dimension": ["Emissions activity", "Equity density", "Grid proxy", "Operator readiness"],
                "Score": [
                    selected["emissions_potential_score"], selected["equity_score"],
                    selected["grid_feasibility_score"], selected["operator_readiness_score"],
                ],
                "Weight": [emissions_weight, equity_weight, grid_weight, operator_weight],
            }
        )
        chart = px.bar(
            breakdown, x="Score", y="Dimension", orientation="h", color="Score",
            color_continuous_scale=[(0, "#df4d4d"), (.5, "#f4aa28"), (1, "#14b18d")],
            range_x=[0, 100], text=breakdown["Score"].map(lambda value: f"{value:.1f}"),
        )
        chart.update_layout(height=315, margin=dict(l=0, r=10, t=10, b=20), coloraxis_showscale=False, paper_bgcolor="rgba(0,0,0,0)")
        chart.update_traces(textposition="inside")
        st.plotly_chart(chart, width="stretch")

st.markdown("## Priority leaderboard")
top10 = filtered.dropna(subset=["live_score"]).head(10).copy()
display = top10[
    ["live_rank", "route_long_name", "primary_city", "live_score", "emissions_potential_score", "equity_score", "grid_feasibility_score", "operator_readiness_score"]
].rename(
    columns={
        "live_rank": "Rank", "route_long_name": "Route", "primary_city": "Primary city", "live_score": "Priority",
        "emissions_potential_score": "Emissions", "equity_score": "Equity", "grid_feasibility_score": "Grid", "operator_readiness_score": "Operator",
    }
)
st.dataframe(
    display,
    hide_index=True,
    width="stretch",
    column_config={
        "Rank": st.column_config.NumberColumn(format="#%d"),
        "Priority": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f"),
        "Emissions": st.column_config.NumberColumn(format="%.1f"),
        "Equity": st.column_config.NumberColumn(format="%.1f"),
        "Grid": st.column_config.NumberColumn(format="%.1f"),
        "Operator": st.column_config.NumberColumn(format="%.1f"),
    },
)
st.download_button(
    "Download filtered rankings (CSV)",
    filtered.drop(columns=["geometry"], errors="ignore").to_csv(index=False).encode("utf-8"),
    file_name=f"route2zero_{city.lower().replace(' ', '_')}_rankings.csv",
    mime="text/csv",
)

st.markdown("## Compare impact and equity")
scatter_data = filtered.dropna(subset=["emissions_potential_score", "equity_score", "live_score"]).copy()
scatter_data["service_volume"] = scatter_data["trips_per_day_estimate"].clip(lower=1).fillna(1)
scatter = px.scatter(
    scatter_data,
    x="emissions_potential_score", y="equity_score", size="service_volume", color="live_score",
    hover_name="route_long_name", hover_data={"route_id": True, "service_volume": ":.1f", "live_score": ":.1f"},
    labels={"emissions_potential_score": "Emissions activity proxy", "equity_score": "Equity density proxy", "live_score": "Priority"},
    color_continuous_scale=[(0, "#df4d4d"), (.5, "#f4aa28"), (1, "#14b18d")], size_max=24,
)
scatter.update_layout(height=440, margin=dict(l=0, r=0, t=20, b=0), paper_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(scatter, width="stretch")

with st.expander("Ask about route priorities (optional AI explanation)"):
    question = st.text_input("Question", placeholder="Which Marikina routes should we examine first?")
    if st.button("Generate short answer", disabled=not bool(question.strip())):
        query = question.lower()
        candidates = filtered.copy()
        mentioned_cities = [candidate for candidate in city_options[1:] if candidate.lower() in query]
        if mentioned_cities:
            candidates = candidates[candidates["cities_served"].fillna("").str.contains(mentioned_cities[0], case=False)]
        candidates = candidates.dropna(subset=["live_score"]).head(5)
        facts = "; ".join(
            f"{row.route_long_name}: {row.live_score:.1f}/100" for row in candidates.itertuples(index=False)
        )
        fallback = f"Based on the current filters, the leading routes are {facts}. These are deterministic weighted scores; operator readiness remains a placeholder."
        prompt = f"Answer in no more than three short sentences for a city official. Question: {question}. Ranked facts: {facts}. Do not add external facts, change ranking, or call proxies measurements. Mention that operator readiness is a placeholder."
        answer, source = generate_explanation_with_status(prompt, max_tokens=150, fallback=fallback)
        st.markdown(f"<span class='source-pill'>{'AI-generated summary' if source == 'mantle_bedrock_api' else 'Offline deterministic answer'}</span>", unsafe_allow_html=True)
        st.write(answer)

with st.expander("Method, provenance, and honest limitations"):
    st.markdown(
        """
        - **Emissions (35% default):** route kilometres × estimated weekday trips. This is activity volume, not measured tailpipe emissions.
        - **Equity (35%):** population-weighted exposure to high-density 2020 WorldPop cells within a 300 m catchment. It is not an informal-settlement boundary.
        - **Grid (15%):** 2024 Luzon renewable generation share (16.118%) for every route. It does not measure local charger or substation capacity.
        - **Operator (15%):** neutral 50/100 placeholder until cooperative financing workshops provide route-level evidence.
        - **AI boundary:** optional Qwen/Bedrock text explains scores after ranking. No model output enters any score or rank.
        """
    )
    st.caption("Source files and reproducible scripts are included in the project documentation and processed-data outputs.")

st.markdown("---")
st.caption("Route2Zero · AI x City Climate Action Hackathon 2026 · Evidence build 24 August 2026")
