"""Generate evidence-aware markdown briefs for the Phase-1 portfolio."""

from __future__ import annotations

import sys

import pandas as pd

from common import DOCS_DIR, PROCESSED_DIR, ensure_output_dirs


def main() -> int:
    ensure_output_dirs()
    scores = pd.read_csv(PROCESSED_DIR / "route2zero_scores.csv", dtype={"route_id": str})
    selected = scores[scores["phase1_selected"].astype(bool)].sort_values("rank")
    output_dir = DOCS_DIR / "policy_briefs"
    output_dir.mkdir(parents=True, exist_ok=True)
    for existing_brief in output_dir.glob("*.md"):
        existing_brief.unlink()
    for row in selected.itertuples(index=False):
        text = f"""# Route2Zero validation brief: {row.route_long_name}

**Route ID:** `{row.route_id}`

**Default scenario:** `{row.scenario_id}`

**Phase-1 portfolio:** `{row.portfolio_scenario_id}`

**Recommended status:** Proceed to evidence validation; not procurement authorization.

## Decision snapshot

- Priority: **#{int(row.rank)} / 1,522**, score **{row.just_transition_score:.1f}/100**.
- Evidence: **{row.evidence_grade}**, {row.overall_evidence_confidence:.1f}/100.
- Rank stability: **{row.top_10_probability * 100:.0f}% top-10 frequency** across {int(row.simulations):,} policy scenarios; P10-P90 rank **#{int(row.rank_p10)}-#{int(row.rank_p90)}**.
- Climate range: **{row.net_co2e_avoided_t_year_low:.0f} to {row.net_co2e_avoided_t_year_high:.0f} tCO2e/year** under low/high planning assumptions. This is a scenario, not a measured reduction.
- Electricity requirement: **{row.electricity_kwh_day_low:.0f} to {row.electricity_kwh_day_high:.0f} kWh/day** under the tested service-electrification assumptions.

## Evidence card

- Service input: `{row.service_intensity_claim_status}` from `{row.service_intensity_source}`.
- Geometry: **{row.geometry_reliability_grade}**, {row.geometry_reliability_score:.0f}/100; `{row.geometry_source}`. Planning geometry is not an official franchise trace.
- Equity: **{row.equity_score:.1f}/100**, population-exposure proxy only. No informal-settlement status is inferred.
- Charging evidence: **{row.charging_readiness_score:.1f}/100**; nearest mapped substation {row.nearest_substation_distance_km:.1f} km; utility capacity **not verified**.
- Operator: **{row.operator_effective_score:.1f}/100**, `{row.operator_claim_status}`.
- Corridor type: **{row.corridor_type_label}**; typology does not add hidden policy points.

## What to validate first

1. **{row.highest_value_missing_evidence.replace('_', ' ').title()}** - tested swing up to {int(row.maximum_rank_swing)} rank positions.
2. Confirm current route activity, headway, service window and operator/cooperative.
3. Request site-control and utility evidence before any claim about available charging capacity.
4. Review the population-exposure proxy with local accessibility and equity evidence.

## Governance boundary

ML estimates a historic service-activity proxy where data are incomplete. Deterministic models quantify climate scenarios, evidence quality, rank stability and portfolio selection. Human users control policy weights and constraints. The LLM does not edit scores, climate values or policy choices.

*Decision support only. Route2Zero does not authorize procurement, lending, franchise cancellation or investment.*
"""
        (output_dir / f"{row.route_id}.md").write_text(text, encoding="utf-8")
    print(f"[PASS] policy briefs: {len(selected)} Phase-1 corridor briefs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
