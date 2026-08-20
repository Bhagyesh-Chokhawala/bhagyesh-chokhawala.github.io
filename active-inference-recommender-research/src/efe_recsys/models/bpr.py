from __future__ import annotations
import numpy as np
import torch
from torch import nn
from .base import RecommenderModel


class BPRMF(RecommenderModel):
    def __init__(self, n_users: int, n_items: int, dim: int = 64):
        super().__init__()
        self.n_users, self.n_items = n_users, n_items
        self.user_embedding = nn.Embedding(n_users, dim)
        self.item_embedding = nn.Embedding(n_items, dim)
        nn.init.normal_(self.user_embedding.weight, std=0.1)
        nn.init.normal_(self.item_embedding.weight, std=0.1)

    def pairwise_loss(self, users, pos, neg):
        u = self.user_embedding(users)
        p = self.item_embedding(pos)
        n = self.item_embedding(neg)
        return -torch.nn.functional.logsigmoid((u * p).sum(-1) - (u * n).sum(-1)).mean()

    def score_all(self, user: int, history: list[int]) -> torch.Tensor:
        u = self.user_embedding.weight[user]
        return self.item_embedding.weight @ u

    def score_batch(self, users: list[int], histories: list[list[int]]) -> torch.Tensor:
        idx = torch.tensor(users, dtype=torch.long, device=self.user_embedding.weight.device)
        return self.user_embedding(idx) @ self.item_embedding.weight.T

    def item_representations(self) -> np.ndarray:
        return self.item_embedding.weight.detach().cpu().numpy()
