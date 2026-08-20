from __future__ import annotations
import numpy as np


def intra_list_diversity(items: list[int], features: np.ndarray) -> float:
    if len(items) < 2:
        return 0.0
    x = features[np.asarray(items, dtype=int)]
    sims = np.clip(x @ x.T, -1.0, 1.0)
    tri = np.triu_indices(len(items), k=1)
    return float(np.mean(1.0 - sims[tri]))


def novelty(items: list[int], raw_train_counts: np.ndarray, total_interactions: int) -> float:
    if not items:
        return 0.0
    probs = (raw_train_counts[np.asarray(items, dtype=int)] + 1.0) / (total_interactions + len(raw_train_counts))
    return float(np.mean(-np.log2(probs)))


def beyond_accuracy(rankings: dict[int, list[int]], features: np.ndarray, raw_train_counts: np.ndarray, k: int = 10) -> dict[str, float]:
    users = sorted(rankings)
    if not users:
        return {"Diversity": 0.0, "Novelty": 0.0, "Coverage": 0.0, "AvgPopularity": 0.0}
    total = int(raw_train_counts.sum())
    lists = [rankings[u][:k] for u in users]
    diversity = np.mean([intra_list_diversity(xs, features) for xs in lists])
    nov = np.mean([novelty(xs, raw_train_counts, total) for xs in lists])
    exposed = set(i for xs in lists for i in xs)
    coverage = len(exposed) / max(1, len(raw_train_counts))
    pop_norm = np.log1p(raw_train_counts) / max(np.log1p(raw_train_counts.max()), 1e-9)
    avg_pop = np.mean([np.mean(pop_norm[np.asarray(xs, dtype=int)]) if xs else 0.0 for xs in lists])
    return {"Diversity": float(diversity), "Novelty": float(nov), "Coverage": float(coverage), "AvgPopularity": float(avg_pop)}
