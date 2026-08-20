from __future__ import annotations
from dataclasses import dataclass
import copy
import math
import numpy as np
import torch

from ..models import BPRMF, LightGCN, SASRec, build_normalized_adj
from ..utils.repro import seed_everything, resolve_device
from .sampling import pairwise_batch, sasrec_batch


@dataclass
class TrainResult:
    model: torch.nn.Module
    best_validation_ndcg: float
    epochs_ran: int


def _validation_ndcg(model, bundle, k: int = 10, batch_size: int = 256) -> float:
    vals = []
    users = bundle.users
    model.eval()
    with torch.no_grad():
        for start in range(0, len(users), batch_size):
            us = users[start:start + batch_size]
            histories = [bundle.train_by_user[u] for u in us]
            score_batch = model.score_batch(us, histories).detach().cpu().numpy()
            for row, u in enumerate(us):
                target = bundle.validation_item[u]
                scores = score_batch[row].copy()
                scores[np.asarray(bundle.train_by_user[u], dtype=int)] = -np.inf
                n = min(k, bundle.n_items - len(set(bundle.train_by_user[u])))
                if n <= 0:
                    vals.append(0.0); continue
                top = np.argpartition(-scores, n - 1)[:n]
                top = top[np.argsort(-scores[top])].tolist()
                if target in top:
                    r = top.index(target)
                    vals.append(1.0 / math.log2(r + 2.0))
                else:
                    vals.append(0.0)
    return float(np.mean(vals)) if vals else 0.0


def build_model(model_name: str, bundle, cfg: dict, device: torch.device):
    dim = int(cfg["training"]["embedding_dim"])
    if model_name == "bpr":
        return BPRMF(bundle.n_users, bundle.n_items, dim).to(device)
    if model_name == "lightgcn":
        adj = build_normalized_adj(bundle.n_users, bundle.n_items, bundle.train_by_user, device)
        return LightGCN(bundle.n_users, bundle.n_items, adj, dim, int(cfg["lightgcn"].get("layers", 3))).to(device)
    if model_name == "sasrec":
        s = cfg["sasrec"]
        return SASRec(bundle.n_items, dim, int(s["max_seq_len"]), int(s["heads"]), int(s["blocks"]), float(s["dropout"])).to(device)
    raise ValueError(model_name)


def train_model(model_name: str, bundle, cfg: dict, seed: int) -> TrainResult:
    seed_everything(seed)
    device = resolve_device(cfg["experiment"].get("device", "auto"))
    model = build_model(model_name, bundle, cfg, device)
    tcfg = cfg["training"]
    optimizer = torch.optim.Adam(model.parameters(), lr=float(tcfg["lr"]), weight_decay=float(tcfg.get("weight_decay", 0.0)))
    rng = np.random.default_rng(seed)
    model_cfg = cfg[model_name]
    batch_size = int(model_cfg.get("batch_size", tcfg["batch_size"]))
    samples = int(model_cfg.get("samples_per_epoch", 100000))
    steps = max(1, math.ceil(samples / batch_size))
    best, best_state, stale = -1.0, None, 0
    epochs_ran = 0
    eval_batch_size = int(cfg.get("evaluation", {}).get("batch_size", 256))

    for epoch in range(int(tcfg["epochs"])):
        model.train()
        for _ in range(steps):
            optimizer.zero_grad(set_to_none=True)
            if model_name in {"bpr", "lightgcn"}:
                users, pos, neg = pairwise_batch(bundle, batch_size, rng, device)
                loss = model.pairwise_loss(users, pos, neg)
            else:
                seq, pos, neg = sasrec_batch(bundle, batch_size, int(cfg["sasrec"]["max_seq_len"]), rng, device)
                loss = model.training_loss(seq, pos, neg)
            loss.backward()
            optimizer.step()
        val_ndcg = _validation_ndcg(model, bundle, int(cfg["evaluation"]["k"]), eval_batch_size)
        epochs_ran = epoch + 1
        if val_ndcg > best + 1e-8:
            best = val_ndcg
            best_state = copy.deepcopy(model.state_dict())
            stale = 0
        else:
            stale += 1
            if stale >= int(tcfg.get("patience", 5)):
                break
    if best_state is not None:
        model.load_state_dict(best_state)
    model.eval()
    return TrainResult(model, best, epochs_ran)
