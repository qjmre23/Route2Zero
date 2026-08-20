"""Create structured scenario-grounded planning answers with deterministic fallback."""

from __future__ import annotations

import sys

import pandas as pd

from common import PROCESSED_DIR, ensure_output_dirs, read_json, write_json


def main() -> int:
    ensure_output_dirs()
    scores = pd.read_csv(PROCESSED_DIR / "route2zero_scores.csv", dtype={"route_id": str})
    priorities_payload = read_json(PROCESSED_DIR / "validation_priorities.json")
    priorities = {entry["route_id"]: entry["priorities"] for entry in priorities_payload["routes"]}
    portfolio = read_json(PROCESSED_DIR / "portfolio_scenarios.json")["scenarios"][0]
    cache = {}
    for row in scores.itertuples(index=False):
        route_priorities = priorities.get(row.route_id, [])
        first = route_priorities[0] if route_priorities else None
        priority_line = (
            f"Validate {first['field_name'].replace('_', ' ')} first; the tested range moves the route by up to {first['max_rank_swing']} places."
            if first else "No decision-sensitive missing field was computed."
        )
        answer = (
            f"{row.route_long_name} is #{int(row.rank)} under scenario {row.scenario_id}, with a priority score of {row.just_transition_score:.1f}, "
            f"evidence grade {row.evidence_grade}, and {row.top_10_probability * 100:.0f}% top-10 frequency across {int(row.simulations):,} tested policy scenarios. "
            + priority_line
        )
        cache[row.route_id] = {
            "answer": answer,
            "evidence_points": [
                f"Scenario climate range: {row.net_co2e_avoided_t_year_low:.0f} to {row.net_co2e_avoided_t_year_high:.0f} tCO2e/year.",
                f"Evidence confidence: {row.overall_evidence_confidence:.1f}/100 ({row.evidence_grade}).",
                f"Rank P10-P90: #{int(row.rank_p10)} to #{int(row.rank_p90)}.",
                f"Phase-1 portfolio: {'selected' if row.phase1_selected else 'not selected'}.",
            ],
            "uncertainty_notes": [
                "The GTFS service baseline is historic, not proof of 2026 operations.",
                "Climate figures are scenarios, not measured emission reductions.",
                "Mapped infrastructure proximity does not verify utility capacity.",
            ],
            "validation_actions": [
                item["deterministic_reason"] for item in route_priorities[:3]
            ],
            "cited_route_ids": [row.route_id],
            "cited_fields": [
                "just_transition_score", "evidence_grade", "top_10_probability",
                "rank_p10", "rank_p90", "net_co2e_avoided_t_year_low",
                "net_co2e_avoided_t_year_high", "phase1_selected",
            ],
            "scenario_id": row.scenario_id,
            "portfolio_scenario_id": portfolio["scenario_id"],
            "source": "deterministic_fallback",
            "llm_ranking_influence": False,
        }
    write_json(PROCESSED_DIR / "route_planner_cache.json", cache)
    feasible = portfolio["status"] == "feasible"
    if feasible:
        portfolio_answer = "Prioritize the route-field combinations with the largest tested rank swing or portfolio-flip risk, beginning with operator evidence and utility/charging-site verification for selected corridors."
        portfolio_points = [
            f"Portfolio {portfolio['scenario_id']} contains {len(portfolio['selected_route_ids'])} corridors.",
            f"Its scenario climate range is {portfolio['portfolio_climate_impact_t_year']['low']:.0f} to {portfolio['portfolio_climate_impact_t_year']['high']:.0f} tCO2e/year.",
            "Every selected corridor retains explicit evidence and robustness fields.",
        ]
    else:
        diagnostics = portfolio.get("infeasibility_diagnostics") or {}
        portfolio_answer = "The configured evidence and equity constraints are currently infeasible. Validate missing layers or explicitly revise the human-controlled scenario before naming a pilot portfolio."
        portfolio_points = [
            f"Portfolio {portfolio['scenario_id']} selected no routes and applied no automatic constraint relaxation.",
            f"Eligible routes recorded by the selector: {diagnostics.get('eligible_count', 0)}.",
            "An infeasible result is a valid decision-support outcome, not permission to invent missing evidence.",
        ]
    summary = {
        "question": "What should the city validate first before piloting this portfolio?",
        "answer": portfolio_answer,
        "evidence_points": portfolio_points,
        "validation_actions": [
            "Confirm current route status and service observations.",
            "Request utility evidence before any claim about available charging capacity.",
            "Collect consent-based operator, depot and financing evidence.",
        ],
        "scenario_id": portfolio["source_scenario_id"],
        "portfolio_scenario_id": portfolio["scenario_id"],
        "source": "deterministic_fallback",
        "llm_ranking_influence": False,
    }
    write_json(PROCESSED_DIR / "planner_summary.json", summary)
    print(f"[PASS] structured planning cache: {len(cache):,} route-scoped answers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
