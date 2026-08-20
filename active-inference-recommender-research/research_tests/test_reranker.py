import numpy as np
from efe_recsys.efe import EFEReranker


def cfg():
    return {
        "monte_carlo_samples": 128,
        "temperature": 1.0,
        "preference_engagement": 0.9,
        "posterior_variance_floor": 0.03,
        "posterior_variance_ceiling": 1.5,
        "base_variance": 0.4,
        "history_variance_weight": 0.6,
        "pragmatic_weight": 1.0,
        "epistemic_weight": 0.8,
        "risk_weight": 0.5,
        "ambiguity_weight": 0.4,
        "state_dependent_weights": False,
    }


def test_score_decomposition_and_ablation():
    item_repr = np.array([[1.,0.], [0.,1.], [.7,.7], [-.5,.5]])
    pop = np.array([1.0, .2, .4, .1])
    rr = EFEReranker(cfg(), seed=9)
    _, traces = rr.rerank(user=0, history=[0, 2], candidates=[1,3], item_repr=item_repr, item_popularity=pop, ablation="full")
    t = traces[0]
    w = t.weights
    expected = w.pragmatic*t.pragmatic - w.epistemic*t.epistemic + w.risk*t.risk + w.ambiguity*t.ambiguity
    assert abs(expected - t.efe) < 1e-10
    _, no_epi = rr.rerank(user=0, history=[0, 2], candidates=[1,3], item_repr=item_repr, item_popularity=pop, ablation="no_epistemic")
    assert all(x.weights.epistemic == 0.0 for x in no_epi)
