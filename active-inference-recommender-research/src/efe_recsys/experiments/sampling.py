from __future__ import annotations
import numpy as np
import torch


def raw_train_counts(bundle) -> np.ndarray:
    counts = np.zeros(bundle.n_items, dtype=np.int64)
    for seq in bundle.train_by_user.values():
        for i in seq:
            counts[i] += 1
    return counts


def pairwise_batch(bundle, batch_size: int, rng: np.random.Generator, device: torch.device):
    users = rng.choice(bundle.users, size=batch_size, replace=True)
    pos, neg = [], []
    for u in users:
        seq = bundle.train_by_user[int(u)]
        p = int(seq[int(rng.integers(0, len(seq)))])
        seen = set(seq)
        n = int(rng.integers(0, bundle.n_items))
        while n in seen:
            n = int(rng.integers(0, bundle.n_items))
        pos.append(p); neg.append(n)
    return (
        torch.tensor(users, dtype=torch.long, device=device),
        torch.tensor(pos, dtype=torch.long, device=device),
        torch.tensor(neg, dtype=torch.long, device=device),
    )


def sasrec_batch(bundle, batch_size: int, max_seq_len: int, rng: np.random.Generator, device: torch.device):
    users = rng.choice(bundle.users, size=batch_size, replace=True)
    seqs, poss, negs = [], [], []
    for u in users:
        hist = bundle.train_by_user[int(u)]
        if len(hist) < 2:
            hist = hist + hist
        input_items = hist[:-1][-max_seq_len:]
        pos_items = hist[1:][-max_seq_len:]
        seen = set(hist)
        neg_items = []
        for _ in pos_items:
            n = int(rng.integers(0, bundle.n_items))
            while n in seen:
                n = int(rng.integers(0, bundle.n_items))
            neg_items.append(n)
        pad = max_seq_len - len(input_items)
        seqs.append([0] * pad + [i + 1 for i in input_items])
        poss.append([0] * pad + [i + 1 for i in pos_items])
        negs.append([0] * pad + [i + 1 for i in neg_items])
    return tuple(torch.tensor(x, dtype=torch.long, device=device) for x in (seqs, poss, negs))
