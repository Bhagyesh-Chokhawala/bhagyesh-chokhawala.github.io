from __future__ import annotations
from abc import ABC, abstractmethod
import numpy as np
import torch


class RecommenderModel(torch.nn.Module, ABC):
    @abstractmethod
    def score_all(self, user: int, history: list[int]) -> torch.Tensor:
        """Return scores for all catalog items."""

    def score_batch(self, users: list[int], histories: list[list[int]]) -> torch.Tensor:
        return torch.stack([self.score_all(u, h) for u, h in zip(users, histories)], dim=0)

    @abstractmethod
    def item_representations(self) -> np.ndarray:
        """Return n_items x embedding_dim item representations used by EFE."""
