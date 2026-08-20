"""Reusable deterministic portfolio selection with explicit infeasibility."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator, Mapping

import pandas as pd

from common import parse_grade


class PortfolioSelectionError(ValueError):
    """Raised when configured constraints cannot produce the requested portfolio."""

    def __init__(self, diagnostics: dict[str, object]):
        self.diagnostics = diagnostics
        super().__init__(
            "Portfolio scenario infeasible: selected "
            f"{diagnostics['selected_count']} of {diagnostics['required_count']} corridors"
        )


class PortfolioSelector:
    """Select routes in a stable order while enforcing every scenario constraint."""

    def __init__(self, scores: pd.DataFrame, scenario: dict):
        self.scores = scores.copy()
        self.scores["route_id"] = self.scores["route_id"].astype(str)
        if not self.scores["route_id"].is_unique:
            raise ValueError("Portfolio selector requires unique route_id values")
        self.scenario = scenario
        self.by_id = self.scores.set_index("route_id", drop=False)
        minimum_grade = parse_grade(scenario["minimum_evidence_grade"])
        eligible_mask = (
            self.scores["evidence_grade"].map(parse_grade).ge(minimum_grade)
            & pd.to_numeric(self.scores["equity_score"], errors="coerce").ge(float(scenario["minimum_equity_score"]))
        )
        if scenario.get("exclude_inactive_routes", True):
            eligible_mask &= ~self.scores["active_status"].eq("inactive")
        self.eligible_ids = self.scores.loc[eligible_mask, "route_id"].tolist()
        self.eligible_id_set = set(self.eligible_ids)
        self.base_transition = self.by_id["just_transition_score"].astype(float).to_dict()
        self.fixed_objective = (
            self.by_id["top_10_probability"].astype(float) * 100.0 * 0.25
            + self.by_id["overall_evidence_confidence"].astype(float) * 0.15
        ).to_dict()
        self.base_order = sorted(self.eligible_ids, key=self._key)

    def _key(self, route_id: str, transition_score: float | None = None) -> tuple[float, float, str]:
        transition = self.base_transition[route_id] if transition_score is None else float(transition_score)
        objective = transition * 0.60 + self.fixed_objective[route_id]
        return (-objective, -transition, route_id)

    def _ordered_ids(self, overrides: Mapping[str, float]) -> Iterator[str]:
        eligible_overrides = {str(key): float(value) for key, value in overrides.items() if str(key) in self.eligible_id_set}
        if not eligible_overrides:
            yield from self.base_order
            return
        if len(eligible_overrides) > 1:
            yield from sorted(
                self.eligible_ids,
                key=lambda route_id: self._key(route_id, eligible_overrides.get(route_id)),
            )
            return
        target, value = next(iter(eligible_overrides.items()))
        target_key = self._key(target, value)
        inserted = False
        for route_id in self.base_order:
            if route_id == target:
                continue
            if not inserted and target_key < self._key(route_id):
                yield target
                inserted = True
            yield route_id
        if not inserted:
            yield target

    def select(self, score_overrides: Mapping[str, float] | None = None) -> list[str]:
        overrides = score_overrides or {}
        selected: list[str] = []
        city_counts: Counter[str] = Counter()
        corridor_counts: Counter[str] = Counter()
        evidence_limited = 0
        blocked: Counter[str] = Counter()
        required = int(self.scenario["max_corridors"])
        for route_id in self._ordered_ids(overrides):
            if len(selected) >= required:
                break
            row = self.by_id.loc[route_id]
            city = str(row["primary_city"])
            if city_counts[city] >= int(self.scenario["maximum_corridors_per_primary_city"]):
                blocked["maximum_corridors_per_primary_city"] += 1
                continue
            corridor = str(row["normalized_corridor_id"])
            if corridor_counts[corridor] >= int(self.scenario["maximum_route_directions_per_corridor"]):
                blocked["maximum_route_directions_per_corridor"] += 1
                continue
            is_limited = row["robustness_label"] == "EVIDENCE-LIMITED"
            if is_limited and evidence_limited >= int(self.scenario["maximum_evidence_limited_corridors"]):
                blocked["maximum_evidence_limited_corridors"] += 1
                continue
            selected.append(route_id)
            city_counts[city] += 1
            corridor_counts[corridor] += 1
            evidence_limited += int(is_limited)
        if len(selected) != required:
            raise PortfolioSelectionError({
                "required_count": required,
                "selected_count": len(selected),
                "eligible_count": len(self.eligible_ids),
                "selected_route_ids": selected,
                "blocking_constraint_counts": dict(blocked),
                "minimum_evidence_grade": self.scenario["minimum_evidence_grade"],
                "minimum_equity_score": self.scenario["minimum_equity_score"],
                "message": "No relaxation was applied; collect missing evidence or explicitly revise the human-controlled scenario.",
            })
        return selected
