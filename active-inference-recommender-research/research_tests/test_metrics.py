import numpy as np
from efe_recsys.metrics import recall_at_k, ndcg_at_k, intra_list_diversity, beyond_accuracy


def test_ranking_metrics():
    rec = [3, 7, 9, 1]
    assert recall_at_k(rec, 7, 2) == 1.0
    assert recall_at_k(rec, 7, 1) == 0.0
    assert 0 < ndcg_at_k(rec, 7, 4) < 1


def test_beyond_metrics():
    features = np.eye(4, dtype=float)
    rankings = {0: [0, 1], 1: [2, 3]}
    counts = np.array([10, 5, 2, 1])
    m = beyond_accuracy(rankings, features, counts, k=2)
    assert abs(m["Diversity"] - 1.0) < 1e-12
    assert m["Coverage"] == 1.0
    assert m["Novelty"] > 0
