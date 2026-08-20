from __future__ import annotations

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class UserBeliefState(BaseModel):
    user_id: str
    preference_vector: Dict[str, float]
    uncertainty: float = Field(ge=0.0, le=1.0)
    interactions: int = 0


class Item(BaseModel):
    item_id: str
    title: str
    attributes: Dict[str, float]
    popularity: float = Field(ge=0.0, le=1.0)
    outcome_noise: float = Field(default=0.1, ge=0.0, le=1.0)


class EFEWeights(BaseModel):
    pragmatic: float = Field(default=1.0, ge=0.0)
    epistemic: float = Field(default=0.8, ge=0.0)
    risk: float = Field(default=0.5, ge=0.0)
    ambiguity: float = Field(default=0.4, ge=0.0)


class ComponentTrace(BaseModel):
    pragmatic_mismatch: float
    epistemic_value: float
    exposure_risk: float
    ambiguity: float
    predicted_engagement: float
    efe_score: float
    effective_weights: EFEWeights


class Recommendation(BaseModel):
    rank: int
    item_id: str
    title: str
    trace: ComponentTrace
    explanation: str


class RecommendationResponse(BaseModel):
    user_id: str
    belief_before: UserBeliefState
    candidate_count: int
    recommendations: List[Recommendation]


class FeedbackRequest(BaseModel):
    user_id: str
    item_id: str
    outcome: Literal["like", "dislike", "click", "skip"]


class FeedbackResponse(BaseModel):
    belief_before: UserBeliefState
    belief_after: UserBeliefState
    message: str


class AuditRecord(BaseModel):
    event_id: str
    event_type: Literal["recommendation", "feedback"]
    user_id: str
    item_id: Optional[str] = None
    payload: Dict
