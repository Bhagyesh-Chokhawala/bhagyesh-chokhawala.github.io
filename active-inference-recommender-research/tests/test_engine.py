from app.engine import EFERecommender
from app.data import DEFAULT_ITEMS, DEFAULT_USERS


def test_score_is_exact_weighted_decomposition():
    engine = EFERecommender()
    belief = DEFAULT_USERS["user_101"].model_copy(deep=True)
    item = DEFAULT_ITEMS[0]
    trace = engine.scorer.trace(belief, item, exploration_control=0.5, risk_control=1.0)
    w = trace.effective_weights
    expected = (
        w.pragmatic * trace.pragmatic_mismatch
        - w.epistemic * trace.epistemic_value
        + w.risk * trace.exposure_risk
        + w.ambiguity * trace.ambiguity
    )
    assert abs(expected - trace.efe_score) < 1e-5


def test_feedback_reduces_uncertainty_and_updates_preferences():
    engine = EFERecommender()
    before = DEFAULT_USERS["cold_start"].model_copy(deep=True)
    item = DEFAULT_ITEMS[0]
    after = engine.update_belief(before, item, "like")
    assert after.uncertainty < before.uncertainty
    assert after.interactions == before.interactions + 1
    assert after.preference_vector["ai"] > before.preference_vector["ai"]


def test_uncertain_user_gets_more_epistemic_weight():
    engine = EFERecommender()
    cold = DEFAULT_USERS["cold_start"]
    mature = DEFAULT_USERS["user_202"]
    assert engine.scorer.effective_weights(cold).epistemic > engine.scorer.effective_weights(mature).epistemic
