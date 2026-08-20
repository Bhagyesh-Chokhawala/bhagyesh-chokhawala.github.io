from __future__ import annotations
from dataclasses import dataclass, asdict
import math
import numpy as np

from .belief import build_belief, expected_kl_information_gain_batch

EPS = 1e-9


@dataclass
class EFEWeights:
    pragmatic: float = 1.0
    epistemic: float = 0.8
    risk: float = 0.5
    ambiguity: float = 0.4


@dataclass
class EFETrace:
    item: int
    pragmatic: float
    epistemic: float
    risk: float
    ambiguity: float
    predictive_engagement: float
    efe: float
    weights: EFEWeights

    def to_dict(self) -> dict:
        out = asdict(self)
        return out


class EFEReranker:
    def __init__(self, cfg: dict, seed: int = 7):
        self.cfg = cfg
        self.seed = seed
        self.base_weights = EFEWeights(
            cfg.get("pragmatic_weight", 1.0),
            cfg.get("epistemic_weight", 0.8),
            cfg.get("risk_weight", 0.5),
            cfg.get("ambiguity_weight", 0.4),
        )

    def weights_for(self, uncertainty: float, ablation: str = "full") -> EFEWeights:
        w = EFEWeights(**asdict(self.base_weights))
        if self.cfg.get("state_dependent_weights", True):
            normalized = uncertainty / max(self.cfg.get("base_variance", 0.35), EPS)
            normalized = float(np.clip(normalized, 0.25, 2.0))
            w.epistemic *= normalized
            w.pragmatic *= float(np.clip(1.5 - 0.5 * normalized, 0.5, 1.5))
        if ablation == "no_epistemic": w.epistemic = 0.0
        elif ablation == "no_risk": w.risk = 0.0
        elif ablation == "no_ambiguity": w.ambiguity = 0.0
        elif ablation == "pragmatic_only": w = EFEWeights(pragmatic=w.pragmatic, epistemic=0.0, risk=0.0, ambiguity=0.0)
        elif ablation != "full": raise ValueError(f"Unknown ablation: {ablation}")
        return w

    def rerank(self, *, user: int, history: list[int], candidates: list[int], item_repr: np.ndarray, item_popularity: np.ndarray, baseline_scores: np.ndarray | None = None, ablation: str = "full") -> tuple[list[int], list[EFETrace]]:
        cfg = self.cfg
        belief = build_belief(
            history,
            item_repr,
            base_variance=cfg.get("base_variance", 0.35),
            history_variance_weight=cfg.get("history_variance_weight", 0.65),
            floor=cfg.get("posterior_variance_floor", 0.03),
            ceiling=cfg.get("posterior_variance_ceiling", 1.50),
        )
        weights = self.weights_for(belief.uncertainty, ablation)
        preference_p = float(np.clip(cfg.get("preference_engagement", 0.90), EPS, 1 - EPS))
        cand_arr = np.asarray(candidates, dtype=int)
        epis, preds, ambs = expected_kl_information_gain_batch(
            belief, item_repr[cand_arr], user=user,
            samples=int(cfg.get("monte_carlo_samples", 96)),
            temperature=float(cfg.get("temperature", 1.0)), seed=self.seed
        )
        traces = []
        for item, epi, pred, amb in zip(candidates, epis, preds, ambs):
            pred = float(np.clip(pred, EPS, 1.0 - EPS))
            pragmatic = pred * math.log(pred / preference_p) + (1.0 - pred) * math.log((1.0 - pred) / (1.0 - preference_p))
            risk = float(item_popularity[item])
            efe = weights.pragmatic * pragmatic - weights.epistemic * float(epi) + weights.risk * risk + weights.ambiguity * float(amb)
            traces.append(EFETrace(item, float(pragmatic), float(epi), risk, float(amb), pred, float(efe), weights))
        traces.sort(key=lambda t: (t.efe, t.item))
        return [t.item for t in traces], traces
