from __future__ import annotations

from collections import Counter
from typing import Iterable
import numpy as np
from scipy import sparse
from sklearn.decomposition import TruncatedSVD

from .schema import DatasetBundle


def iterative_k_core(rows: list[tuple[str, str, float, int]], min_user: int, min_item: int) -> list[tuple[str, str, float, int]]:
    current = rows
    while True:
        uc = Counter(r[0] for r in current)
        ic = Counter(r[1] for r in current)
        nxt = [r for r in current if uc[r[0]] >= min_user and ic[r[1]] >= min_item]
        if len(nxt) == len(current):
            return nxt
        current = nxt


def leave_last_two(rows: Iterable[tuple[str, str, float, int]], name: str, min_user_interactions: int = 3, diversity_dimensions: int = 64, diversity_seed: int = 2026) -> DatasetBundle:
    by_user: dict[str, list[tuple[str, float, int]]] = {}
    for user, item, rating, ts in rows:
        by_user.setdefault(str(user), []).append((str(item), float(rating), int(ts)))

    by_user = {u: sorted(v, key=lambda x: (x[2], x[0])) for u, v in by_user.items() if len(v) >= min_user_interactions}
    raw_users = sorted(by_user)
    raw_items = sorted({i for vals in by_user.values() for i, _, _ in vals})
    uidx = {u: n for n, u in enumerate(raw_users)}
    iidx = {i: n for n, i in enumerate(raw_items)}

    train: dict[int, list[int]] = {}
    val: dict[int, int] = {}
    test: dict[int, int] = {}
    for u in raw_users:
        seq = [iidx[i] for i, _, _ in by_user[u]]
        if len(seq) < 3:
            continue
        ui = uidx[u]
        train[ui] = seq[:-2]
        val[ui] = seq[-2]
        test[ui] = seq[-1]

    pop = np.zeros(len(raw_items), dtype=np.float64)
    for seq in train.values():
        for item in seq:
            pop[item] += 1.0
    if pop.max() > 0:
        pop = np.log1p(pop) / np.log1p(pop.max())

    # Model-independent item representation for diversity: low-rank item-user co-occurrence.
    rr, cc = [], []
    for u, seq in train.items():
        for item in set(seq):
            rr.append(item); cc.append(u)
    mat = sparse.csr_matrix((np.ones(len(rr)), (rr, cc)), shape=(len(raw_items), len(raw_users)))
    max_dim = max(1, min(diversity_dimensions, max(1, min(mat.shape) - 1)))
    if min(mat.shape) <= 2:
        feats = mat.toarray().astype(np.float32)
    else:
        feats = TruncatedSVD(n_components=max_dim, random_state=diversity_seed).fit_transform(mat).astype(np.float32)
    norms = np.linalg.norm(feats, axis=1, keepdims=True)
    feats = feats / np.clip(norms, 1e-12, None)

    return DatasetBundle(
        name=name,
        n_users=len(raw_users),
        n_items=len(raw_items),
        train_by_user=train,
        validation_item=val,
        test_item=test,
        user_raw_ids=raw_users,
        item_raw_ids=raw_items,
        item_popularity=pop.astype(np.float32),
        diversity_features=feats,
    )
