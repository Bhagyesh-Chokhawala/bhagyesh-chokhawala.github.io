import numpy as np
from efe_recsys.efe.belief import GaussianBelief, expected_kl_information_gain, gaussian_kl_diag


def test_gaussian_kl_identity_zero():
    mu = np.array([0.1, -0.2])
    var = np.array([0.4, 0.7])
    assert abs(gaussian_kl_diag(mu, var, mu, var)) < 1e-12


def test_expected_kl_is_positive_and_deterministic():
    belief = GaussianBelief(np.zeros(4), np.ones(4) * 0.5)
    item = np.array([1.0, -0.5, 0.2, 0.3])
    a = expected_kl_information_gain(belief, item, user=1, item=2, samples=256, seed=11)
    b = expected_kl_information_gain(belief, item, user=1, item=2, samples=256, seed=11)
    assert a == b
    assert a[0] > 0.0
    assert 0.0 < a[1] < 1.0
    assert a[2] > 0.0
