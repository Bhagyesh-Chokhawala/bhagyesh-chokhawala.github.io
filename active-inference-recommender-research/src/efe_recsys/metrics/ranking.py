from __future__ import annotations
import math
import numpy as np


def recall_at_k(recommended: list[int], target: int, k: int = 10) -> float:
    return float(target in recommended[:k])


def ndcg_at_k(recommended: list[int], target: int, k: int = 10) -> float:
    try:
        rank = recommended[:k].index(target)
    except ValueError:
        return 0.0
    return 1.0 / math.log2(rank + 2.0)


def aggregate_accuracy(rankings: dict[int, list[int]], targets: dict[int, int], k: int = 10) -> dict[str, float]:
    users = sorted(set(rankings) & set(targets))
    if not users:
        return {f"Recall@{k}": 0.0, f"NDCG@{k}": 0.0}
    recalls = [recall_at_k(rankings[u], targets[u], k) for u in users]
    ndcgs = [ndcg_at_k(rankings[u], targets[u], k) for u in users]
    return {f"Recall@{k}": float(np.mean(recalls)), f"NDCG@{k}": float(np.mean(ndcgs))}
