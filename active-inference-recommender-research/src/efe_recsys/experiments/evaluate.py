from __future__ import annotations
import numpy as np
import torch
from ..efe import EFEReranker
from ..metrics import aggregate_accuracy, beyond_accuracy
from .sampling import raw_train_counts


def _score_batches(model, bundle, batch_size: int = 256):
    users = bundle.users
    model.eval()
    with torch.no_grad():
        for start in range(0, len(users), batch_size):
            us = users[start:start + batch_size]
            histories = [bundle.train_by_user[u] for u in us]
            scores = model.score_batch(us, histories).detach().cpu().numpy()
            yield us, scores


def rank_baseline(model, bundle, cfg: dict) -> dict[int, list[int]]:
    k = int(cfg["evaluation"]["k"])
    batch_size = int(cfg["evaluation"].get("batch_size", 256))
    rankings = {}
    for users, score_batch in _score_batches(model, bundle, batch_size):
        for row, u in enumerate(users):
            scores = score_batch[row].copy()
            seen = set(bundle.train_by_user[u])
            if cfg["evaluation"].get("exclude_validation_from_candidates", True):
                seen.add(bundle.validation_item[u])
            scores[np.asarray(list(seen), dtype=int)] = -np.inf
            n = min(k, bundle.n_items - len(seen))
            if n <= 0:
                rankings[u] = []; continue
            top = np.argpartition(-scores, n - 1)[:n]
            rankings[u] = top[np.argsort(-scores[top])].tolist()
    return rankings


def rank_efe(model, bundle, cfg: dict, seed: int, ablation: str = "full") -> tuple[dict[int, list[int]], dict[int, list[dict]]]:
    k = int(cfg["evaluation"]["k"])
    pool_size = int(cfg["evaluation"].get("candidate_pool_size", 200))
    batch_size = int(cfg["evaluation"].get("batch_size", 256))
    item_repr = model.item_representations().astype(np.float64)
    reranker = EFEReranker(cfg["efe"], seed=seed)
    rankings, audit = {}, {}
    for users, score_batch in _score_batches(model, bundle, batch_size):
        for row, u in enumerate(users):
            history = bundle.train_by_user[u]
            scores = score_batch[row].copy()
            seen = set(history)
            if cfg["evaluation"].get("exclude_validation_from_candidates", True):
                seen.add(bundle.validation_item[u])
            scores[np.asarray(list(seen), dtype=int)] = -np.inf
            n = min(pool_size, bundle.n_items - len(seen))
            if n <= 0:
                rankings[u], audit[u] = [], []; continue
            cand = np.argpartition(-scores, n - 1)[:n]
            cand = cand[np.argsort(-scores[cand])].tolist()
            ordered, traces = reranker.rerank(user=u, history=history, candidates=cand, item_repr=item_repr, item_popularity=bundle.item_popularity, baseline_scores=scores, ablation=ablation)
            rankings[u] = ordered[:k]
            audit[u] = [t.to_dict() for t in traces[:k]]
    return rankings, audit


def evaluate_rankings(rankings: dict[int, list[int]], bundle, cfg: dict) -> dict[str, float]:
    k = int(cfg["evaluation"]["k"])
    metrics = aggregate_accuracy(rankings, bundle.test_item, k)
    counts = raw_train_counts(bundle)
    metrics.update(beyond_accuracy(rankings, bundle.diversity_features, counts, k))
    return metrics
