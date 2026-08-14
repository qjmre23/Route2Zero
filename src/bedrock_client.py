"""Small OpenAI-compatible client for the optional Mantle/Bedrock narrative layer."""

from __future__ import annotations

import os
from pathlib import Path

import requests
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

BASE_URL = os.getenv("BASE_URL", "").strip().rstrip("/")
MODEL = os.getenv("MODEL", "").strip()


def generate_explanation_with_status(
    prompt: str,
    max_tokens: int = 300,
    fallback: str = "Explanation unavailable; the numerical score remains fully auditable.",
) -> tuple[str, str]:
    """Return narrative text and source without ever breaking the dashboard."""
    api_key = os.getenv("ABSK_KEY", "").strip()
    enabled = os.getenv("AI_EXPLANATIONS_ENABLED", "true").lower() in {"1", "true", "yes"}
    if not api_key or not BASE_URL or not MODEL or not enabled:
        return fallback, "deterministic_fallback"
    try:
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.3,
            },
            timeout=35,
        )
        response.raise_for_status()
        text = response.json()["choices"][0]["message"]["content"].strip()
        return (text or fallback), ("mantle_bedrock_api" if text else "deterministic_fallback")
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError):
        return fallback, "deterministic_fallback"


def generate_explanation(
    prompt: str,
    max_tokens: int = 300,
    fallback: str = "Explanation unavailable; the numerical score remains fully auditable.",
) -> str:
    """Compatibility wrapper matching the build specification's single-function client."""
    return generate_explanation_with_status(prompt, max_tokens=max_tokens, fallback=fallback)[0]


def deterministic_route_rationale(row: object) -> str:
    """Explain already-computed scores without adding claims or changing the rank."""
    emissions = float(getattr(row, "emissions_potential_score"))
    equity = float(getattr(row, "equity_score"))
    grid = float(getattr(row, "grid_feasibility_score"))
    operator = float(getattr(row, "operator_readiness_score"))
    strongest_name, strongest_value = max(
        {
            "daily service activity": emissions,
            "high-density corridor exposure": equity,
            "regional grid readiness": grid,
            "operator readiness": operator,
        }.items(),
        key=lambda item: item[1],
    )
    return (
        f"This route ranks here because its strongest signal is {strongest_name} "
        f"({strongest_value:.0f}/100); the {grid:.0f}/100 grid value is a shared Luzon proxy and "
        f"the {operator:.0f}/100 operator value remains a neutral placeholder pending cooperative data."
    )
