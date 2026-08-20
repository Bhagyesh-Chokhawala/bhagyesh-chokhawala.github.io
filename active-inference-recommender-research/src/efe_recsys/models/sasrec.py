from __future__ import annotations
import numpy as np
import torch
from torch import nn
from .base import RecommenderModel


class SASRec(RecommenderModel):
    def __init__(self, n_items: int, dim: int = 64, max_seq_len: int = 100, heads: int = 2, blocks: int = 2, dropout: float = 0.2):
        super().__init__()
        self.n_items, self.max_seq_len = n_items, max_seq_len
        self.item_embedding = nn.Embedding(n_items + 1, dim, padding_idx=0)
        self.pos_embedding = nn.Embedding(max_seq_len, dim)
        layer = nn.TransformerEncoderLayer(d_model=dim, nhead=heads, dim_feedforward=dim * 4, dropout=dropout, batch_first=True, norm_first=True)
        self.encoder = nn.TransformerEncoder(layer, num_layers=blocks)
        self.dropout = nn.Dropout(dropout)
        self.norm = nn.LayerNorm(dim)
        nn.init.normal_(self.item_embedding.weight, std=0.02)
        with torch.no_grad():
            self.item_embedding.weight[0].zero_()

    def encode(self, seq: torch.Tensor) -> torch.Tensor:
        # seq uses 0 as padding and item ids shifted by +1.
        b, l = seq.shape
        pos = torch.arange(l, device=seq.device).unsqueeze(0).expand(b, -1)
        x = self.item_embedding(seq) + self.pos_embedding(pos)
        x = self.dropout(x)
        causal = torch.triu(torch.ones(l, l, device=seq.device, dtype=torch.bool), diagonal=1)
        padding = seq.eq(0)
        x = self.encoder(x, mask=causal, src_key_padding_mask=padding)
        return self.norm(x)

    def training_loss(self, seq: torch.Tensor, pos: torch.Tensor, neg: torch.Tensor) -> torch.Tensor:
        h = self.encode(seq)
        pos_e = self.item_embedding(pos)
        neg_e = self.item_embedding(neg)
        valid = pos.ne(0)
        pos_logits = (h * pos_e).sum(-1)
        neg_logits = (h * neg_e).sum(-1)
        if not valid.any():
            return pos_logits.sum() * 0.0
        loss = torch.nn.functional.binary_cross_entropy_with_logits(pos_logits[valid], torch.ones_like(pos_logits[valid]))
        loss += torch.nn.functional.binary_cross_entropy_with_logits(neg_logits[valid], torch.zeros_like(neg_logits[valid]))
        return loss

    def _padded(self, history: list[int], device) -> torch.Tensor:
        hist = [i + 1 for i in history[-self.max_seq_len :]]
        arr = [0] * (self.max_seq_len - len(hist)) + hist
        return torch.tensor([arr], dtype=torch.long, device=device)

    def score_all(self, user: int, history: list[int]) -> torch.Tensor:
        device = self.item_embedding.weight.device
        seq = self._padded(history, device)
        h = self.encode(seq)[0, -1]
        return self.item_embedding.weight[1:] @ h

    def score_batch(self, users: list[int], histories: list[list[int]]) -> torch.Tensor:
        device = self.item_embedding.weight.device
        rows = []
        for history in histories:
            hist = [i + 1 for i in history[-self.max_seq_len :]]
            rows.append([0] * (self.max_seq_len - len(hist)) + hist)
        seq = torch.tensor(rows, dtype=torch.long, device=device)
        h = self.encode(seq)[:, -1, :]
        return h @ self.item_embedding.weight[1:].T

    def item_representations(self) -> np.ndarray:
        return self.item_embedding.weight[1:].detach().cpu().numpy()
