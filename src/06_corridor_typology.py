"""Create deterministic, unsupervised corridor typologies for interpretation."""

from __future__ import annotations

import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.metrics import silhouette_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from common import CONFIG_DIR, MODELS_DIR, PROCESSED_DIR, ensure_output_dirs, read_json, stable_hash, utc_now_iso, write_json


def human_labels(centres: pd.DataFrame) -> dict[int, str]:
    labels: dict[int, str] = {}
    remaining = set(centres.index)
    rules = [
        ("corridor_population_proxy", "Dense Urban Trunk", True),
        ("length_km", "Long Regional Connector", True),
        ("stops_per_km", "High-Stop-Density Core", True),
        ("length_km", "Local Feeder", False),
    ]
    for column, label, highest in rules:
        if not remaining:
            break
        subset = centres.loc[list(remaining), column]
        cluster = int(subset.idxmax() if highest else subset.idxmin())
        labels[cluster] = label
        remaining.remove(cluster)
    generic = ["Urban Connector", "Peripheral Feeder", "Cross-City Corridor", "Mixed Service Corridor"]
    for index, cluster in enumerate(sorted(remaining)):
        labels[int(cluster)] = generic[index % len(generic)]
    return labels


def main() -> int:
    ensure_output_dirs()
    config = read_json(CONFIG_DIR / "model_config.json")
    features = list(config["typology"]["features"])
    seed = int(config["random_seed"])
    frame = pd.read_csv(PROCESSED_DIR / "route_features.csv", dtype={"route_id": str})
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    x_imputed = imputer.fit_transform(frame[features])
    x_scaled = scaler.fit_transform(x_imputed)

    evaluations: list[dict[str, object]] = []
    candidates: dict[int, KMeans] = {}
    for k in range(int(config["typology"]["k_min"]), int(config["typology"]["k_max"]) + 1):
        model = KMeans(n_clusters=k, n_init=30, random_state=seed)
        labels = model.fit_predict(x_scaled)
        counts = pd.Series(labels).value_counts()
        score = float(silhouette_score(x_scaled, labels))
        evaluations.append({"k": k, "silhouette_score": round(score, 4), "minimum_cluster_size": int(counts.min())})
        candidates[k] = model
    viable = [item for item in evaluations if item["minimum_cluster_size"] >= max(10, int(len(frame) * 0.01))]
    selected_eval = max(viable or evaluations, key=lambda item: item["silhouette_score"])
    selected_k = int(selected_eval["k"])
    model = candidates[selected_k]
    labels = model.labels_.astype(int)

    raw_centres = scaler.inverse_transform(model.cluster_centers_)
    centres = pd.DataFrame(raw_centres, columns=features)
    label_map = human_labels(centres)
    distances = model.transform(x_scaled).min(axis=1)
    threshold_by_cluster = {
        int(cluster): float(np.quantile(distances[labels == cluster], 0.95)) for cluster in np.unique(labels)
    }
    pca = PCA(n_components=2, random_state=seed)
    coords = pca.fit_transform(x_scaled)
    model_version = "typology-v1-" + stable_hash({"features": features, "k": selected_k, "seed": seed}, 8)
    bundle = Pipeline([("imputer", imputer), ("scaler", scaler), ("kmeans", model)])
    joblib.dump(bundle, MODELS_DIR / "corridor_typology.joblib")
    metadata = {
        "model_version": model_version,
        "method": "StandardScaler + KMeans",
        "feature_columns": features,
        "random_seed": seed,
        "evaluated_cluster_counts": evaluations,
        "selected_k": selected_k,
        "selected_silhouette_score": selected_eval["silhouette_score"],
        "cluster_labels": {str(key): value for key, value in label_map.items()},
        "typology_used_for_policy_score": False,
        "trained_at_utc": utc_now_iso(),
        "limitations": "Typology describes structural similarity; it does not infer income, vulnerability or settlement status.",
    }
    write_json(MODELS_DIR / "corridor_typology_metadata.json", metadata)
    metrics = read_json(PROCESSED_DIR / "model_metrics.json")
    metrics["corridor_typology"] = metadata
    write_json(PROCESSED_DIR / "model_metrics.json", metrics)

    output = frame[["route_id"]].copy()
    output["corridor_cluster_id"] = labels
    output["corridor_type_label"] = [label_map[int(value)] for value in labels]
    output["cluster_distance"] = np.round(distances, 4)
    output["cluster_outlier_flag"] = [distance >= threshold_by_cluster[int(cluster)] for distance, cluster in zip(distances, labels, strict=False)]
    output["typology_pca_x"] = np.round(coords[:, 0], 4)
    output["typology_pca_y"] = np.round(coords[:, 1], 4)
    output["clustering_model_version"] = model_version
    output["typology_claim_status"] = "ML_ESTIMATED"
    output.to_csv(PROCESSED_DIR / "corridor_typology.csv", index=False)
    print(f"[PASS] corridor typology: k={selected_k}, silhouette={selected_eval['silhouette_score']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
