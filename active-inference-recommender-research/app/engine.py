from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

try:
    from .models import (
        ComponentTrace,
        EFEWeights,
        Item,
        Recommendation,
        RecommendationResponse,
        UserBeliefState,
    )
except ImportError:
    from models import (
        ComponentTrace,
        EFEWeights,
        Item,
        Recommendation,
        RecommendationResponse,
        UserBeliefState,
    )

EPS = 1e-9


def _keys(a: dict[str, float], b: dict[str, float]) -> list[str]:
    return sorted(set(a) | set(b))


def cosine_similarity(a: dict[str, float], b: dict[str, float]) -> float:
    keys = _keys(a, b)
    dot = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in keys)
    na = math.sqrt(sum(a.get(k, 0.0) ** 2 for k in keys))
    nb = math.sqrt(sum(b.get(k, 0.0) ** 2 for k in keys))
    if na <= EPS or nb <= EPS:
        return 0.0
    return max(0.0, min(1.0, dot / (na * nb)))


def binary_entropy(p: float) -> float:
    p = min(max(p, EPS), 1.0 - EPS)
    return -(p * math.log(p) + (1.0 - p) * math.log(1.0 - p)) / math.log(2.0)


class CandidateGenerator:
    """High-recall retrieval stage. Replaceable with BPR, LightGCN, SASRec, ANN search, etc."""

    def generate(self, belief: UserBeliefState, items: Iterable[Item], limit: int = 8) -> list[Item]:
        scored = [
            (0.80 * cosine_similarity(belief.preference_vector, item.attributes) + 0.20 * (1.0 - item.popularity), item)
            for item in items
        ]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in scored[:limit]]


class GenerativeOutcomeModel:
    """Tiny transparent proxy for Q(o | item, belief)."""

    def predict_engagement(self, belief: UserBeliefState, item: Item) -> float:
        similarity = cosine_similarity(belief.preference_vector, item.attributes)
        # Belief uncertainty pulls predictions toward 0.5; item noise does the same.
        confidence = (1.0 - 0.55 * belief.uncertainty) * (1.0 - 0.45 * item.outcome_noise)
        p = 0.5 + (similarity - 0.5) * confidence
        return min(max(p, 0.02), 0.98)


@dataclass
class EFEScorer:
    base_weights: EFEWeights
    outcome_model: GenerativeOutcomeModel

    def effective_weights(self, belief: UserBeliefState, exploration_control: float = 0.5) -> EFEWeights:
        exploration_control = min(max(exploration_control, 0.0), 1.0)
        # The user's state modulates the relevance/exploration balance.
        return EFEWeights(
            pragmatic=self.base_weights.pragmatic * (1.0 + 0.65 * (1.0 - belief.uncertainty)),
            epistemic=self.base_weights.epistemic * (0.35 + 1.65 * belief.uncertainty) * (0.5 + exploration_control),
            risk=self.base_weights.risk,
            ambiguity=self.base_weights.ambiguity,
        )

    def trace(
        self,
        belief: UserBeliefState,
        item: Item,
        exploration_control: float = 0.5,
        risk_control: float = 1.0,
    ) -> ComponentTrace:
        p = self.outcome_model.predict_engagement(belief, item)

        # Pragmatic mismatch: negative log probability of the preferred outcome (engagement).
        pragmatic = -math.log(max(p, EPS))

        # Approximate epistemic value: uncertain users benefit most from informative boundary items
        # and less-popular candidates. This is a POC proxy for expected posterior information gain.
        boundary_information = 1.0 - abs(2.0 * p - 1.0)
        novelty = 1.0 - item.popularity
        epistemic = belief.uncertainty * (0.65 * boundary_information + 0.35 * novelty)

        # Risk: simple exposure/popularity concentration penalty.
        risk = item.popularity * max(risk_control, 0.0)

        # Ambiguity: predictive entropy scaled by item-specific noise.
        ambiguity = binary_entropy(p) * (0.35 + 0.65 * item.outcome_noise)

        weights = self.effective_weights(belief, exploration_control)
        score = (
            weights.pragmatic * pragmatic
            - weights.epistemic * epistemic
            + weights.risk * risk
            + weights.ambiguity * ambiguity
        )

        return ComponentTrace(
            pragmatic_mismatch=round(pragmatic, 6),
            epistemic_value=round(epistemic, 6),
            exposure_risk=round(risk, 6),
            ambiguity=round(ambiguity, 6),
            predicted_engagement=round(p, 6),
            efe_score=round(score, 6),
            effective_weights=weights,
        )


class EFERecommender:
    def __init__(self) -> None:
        self.candidate_generator = CandidateGenerator()
        self.outcome_model = GenerativeOutcomeModel()
        self.scorer = EFEScorer(EFEWeights(), self.outcome_model)

    def recommend(
        self,
        belief: UserBeliefState,
        items: Iterable[Item],
        *,
        top_k: int = 5,
        candidate_limit: int = 8,
        exploration_control: float = 0.5,
        risk_control: float = 1.0,
    ) -> RecommendationResponse:
        candidates = self.candidate_generator.generate(belief, items, limit=candidate_limit)
        ranked = []
        for item in candidates:
            trace = self.scorer.trace(
                belief,
                item,
                exploration_control=exploration_control,
                risk_control=risk_control,
            )
            ranked.append((trace.efe_score, item, trace))

        ranked.sort(key=lambda x: x[0])
        output: list[Recommendation] = []
        for rank, (_, item, trace) in enumerate(ranked[:top_k], start=1):
            reasons = []
            if trace.predicted_engagement >= 0.75:
                reasons.append("strong preference alignment")
            elif trace.predicted_engagement >= 0.60:
                reasons.append("moderate preference alignment")
            else:
                reasons.append("weaker predicted relevance")

            if trace.epistemic_value >= 0.35:
                reasons.append("high information value")
            elif trace.epistemic_value >= 0.20:
                reasons.append("useful exploration value")

            if trace.exposure_risk >= 0.75:
                reasons.append("penalized for high exposure")
            elif trace.exposure_risk <= 0.35:
                reasons.append("supports broader catalog exposure")

            if trace.ambiguity >= 0.35:
                reasons.append("higher predictive ambiguity")

            output.append(
                Recommendation(
                    rank=rank,
                    item_id=item.item_id,
                    title=item.title,
                    trace=trace,
                    explanation="; ".join(reasons).capitalize() + ".",
                )
            )

        return RecommendationResponse(
            user_id=belief.user_id,
            belief_before=belief.model_copy(deep=True),
            candidate_count=len(candidates),
            recommendations=output,
        )

    def update_belief(self, belief: UserBeliefState, item: Item, outcome: str) -> UserBeliefState:
        positive = outcome in {"like", "click"}
        # Stronger update for explicit like/dislike than click/skip.
        eta = 0.18 if outcome in {"like", "dislike"} else 0.09
        new_vector = dict(belief.preference_vector)
        keys = _keys(new_vector, item.attributes)
        for key in keys:
            current = new_vector.get(key, 0.5)
            target = item.attributes.get(key, 0.0) if positive else (1.0 - item.attributes.get(key, 0.0))
            new_vector[key] = min(max(current + eta * (target - current), 0.0), 1.0)

        # Feedback reduces uncertainty, with explicit feedback reducing it more.
        reduction = 0.12 if outcome in {"like", "dislike"} else 0.06
        new_uncertainty = max(0.05, belief.uncertainty * (1.0 - reduction))
        return UserBeliefState(
            user_id=belief.user_id,
            preference_vector={k: round(v, 6) for k, v in new_vector.items()},
            uncertainty=round(new_uncertainty, 6),
            interactions=belief.interactions + 1,
        )


engine = EFERecommender()
