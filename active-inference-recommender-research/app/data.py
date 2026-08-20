from __future__ import annotations

try:
    from .models import Item, UserBeliefState
except ImportError:
    from models import Item, UserBeliefState


DEFAULT_USERS = {
    "user_101": UserBeliefState(
        user_id="user_101",
        preference_vector={"ai": 0.90, "architecture": 0.85, "business": 0.70, "entertainment": 0.20},
        uncertainty=0.65,
        interactions=3,
    ),
    "user_202": UserBeliefState(
        user_id="user_202",
        preference_vector={"ai": 0.35, "architecture": 0.25, "business": 0.55, "entertainment": 0.90},
        uncertainty=0.30,
        interactions=18,
    ),
    "cold_start": UserBeliefState(
        user_id="cold_start",
        preference_vector={"ai": 0.50, "architecture": 0.50, "business": 0.50, "entertainment": 0.50},
        uncertainty=0.95,
        interactions=0,
    ),
}


DEFAULT_ITEMS = [
    Item(
        item_id="I001",
        title="Explainable AI for Enterprise Architecture",
        attributes={"ai": 0.95, "architecture": 0.90, "business": 0.75, "entertainment": 0.10},
        popularity=0.82,
        outcome_noise=0.10,
    ),
    Item(
        item_id="I002",
        title="Active Inference for Recommender Systems",
        attributes={"ai": 0.96, "architecture": 0.62, "business": 0.50, "entertainment": 0.15},
        popularity=0.34,
        outcome_noise=0.18,
    ),
    Item(
        item_id="I003",
        title="Streaming Entertainment Trends",
        attributes={"ai": 0.15, "architecture": 0.10, "business": 0.35, "entertainment": 0.97},
        popularity=0.96,
        outcome_noise=0.08,
    ),
    Item(
        item_id="I004",
        title="Governance Models for Adaptive AI Platforms",
        attributes={"ai": 0.88, "architecture": 0.84, "business": 0.88, "entertainment": 0.05},
        popularity=0.56,
        outcome_noise=0.13,
    ),
    Item(
        item_id="I005",
        title="Graph-Based Collaborative Filtering in Practice",
        attributes={"ai": 0.70, "architecture": 0.60, "business": 0.35, "entertainment": 0.30},
        popularity=0.68,
        outcome_noise=0.12,
    ),
    Item(
        item_id="I006",
        title="Human-AI Collaboration and Decision Support",
        attributes={"ai": 0.85, "architecture": 0.58, "business": 0.82, "entertainment": 0.25},
        popularity=0.46,
        outcome_noise=0.20,
    ),
    Item(
        item_id="I007",
        title="Independent Cinema Discovery Guide",
        attributes={"ai": 0.05, "architecture": 0.05, "business": 0.10, "entertainment": 0.86},
        popularity=0.20,
        outcome_noise=0.22,
    ),
    Item(
        item_id="I008",
        title="Responsible Marketplace Exposure Strategies",
        attributes={"ai": 0.55, "architecture": 0.52, "business": 0.92, "entertainment": 0.18},
        popularity=0.28,
        outcome_noise=0.16,
    ),
    Item(
        item_id="I009",
        title="Sequential Decision-Making Under Uncertainty",
        attributes={"ai": 0.93, "architecture": 0.72, "business": 0.58, "entertainment": 0.12},
        popularity=0.40,
        outcome_noise=0.17,
    ),
    Item(
        item_id="I010",
        title="Popular Business Leadership Stories",
        attributes={"ai": 0.30, "architecture": 0.32, "business": 0.90, "entertainment": 0.52},
        popularity=0.90,
        outcome_noise=0.09,
    ),
]
