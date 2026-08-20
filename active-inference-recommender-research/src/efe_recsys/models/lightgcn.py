from __future__ import annotations
import numpy as np
import torch
from torch import nn
from .base import RecommenderModel


class LightGCN(RecommenderModel):
    def __init__(self, n_users: int, n_items: int, norm_adj: torch.Tensor, dim: int = 64, layers: int = 3):
        super().__init__()
        self.n_users, self.n_items, self.layers = n_users, n_items, layers
        self.norm_adj = norm_adj.coalesce()
        self.embedding = nn.Embedding(n_users + n_items, dim)
        nn.init.normal_(self.embedding.weight, std=0.1)

    def propagated(self):
        x = self.embedding.weight
        outs = [x]
        for _ in range(self.layers):
            x = torch.sparse.mm(self.norm_adj, x)
            outs.append(x)
        out = torch.stack(outs, dim=0).mean(0)
        return out[: self.n_users], out[self.n_users :]

    def pairwise_loss(self, users, pos, neg):
        ue, ie = self.propagated()
        u, p, n = ue[users], ie[pos], ie[neg]
        return -torch.nn.functional.logsigmoid((u * p).sum(-1) - (u * n).sum(-1)).mean()

    def score_all(self, user: int, history: list[int]) -> torch.Tensor:
        ue, ie = self.propagated()
        return ie @ ue[user]

    def score_batch(self, users: list[int], histories: list[list[int]]) -> torch.Tensor:
        ue, ie = self.propagated()
        idx = torch.tensor(users, dtype=torch.long, device=ue.device)
        return ue[idx] @ ie.T

    def item_representations(self) -> np.ndarray:
        with torch.no_grad():
            _, ie = self.propagated()
        return ie.detach().cpu().numpy()


def build_normalized_adj(n_users: int, n_items: int, train_by_user: dict[int, list[int]], device: torch.device) -> torch.Tensor:
    rows, cols = [], []
    for u, seq in train_by_user.items():
        for i in set(seq):
            v = n_users + i
            rows += [u, v]
            cols += [v, u]
    n = n_users + n_items
    idx = torch.tensor([rows, cols], dtype=torch.long)
    values = torch.ones(len(rows), dtype=torch.float32)
    deg = torch.zeros(n, dtype=torch.float32)
    deg.scatter_add_(0, idx[0], values)
    inv = torch.pow(torch.clamp(deg, min=1.0), -0.5)
    norm_values = values * inv[idx[0]] * inv[idx[1]]
    return torch.sparse_coo_tensor(idx, norm_values, (n, n), device=device).coalesce()
