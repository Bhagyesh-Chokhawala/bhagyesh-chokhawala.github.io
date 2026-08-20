from __future__ import annotations
import numpy as np
from .common import leave_last_two


def load_synthetic(seed: int = 7, n_users: int = 24, n_items: int = 40):
    rng = np.random.default_rng(seed)
    rows = []
    ts = 1
    for u in range(n_users):
        length = int(rng.integers(8, 14))
        base = (u * 3) % n_items
        items = [(base + int(x)) % n_items for x in rng.choice(18, size=length, replace=False)]
        for item in items:
            rows.append((str(u), str(item), 1.0, ts)); ts += 1
    return leave_last_two(rows, "synthetic", 3, 8, seed)
