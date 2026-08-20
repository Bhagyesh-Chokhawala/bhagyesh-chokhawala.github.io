from __future__ import annotations
from dataclasses import dataclass
import hashlib
import math
import numpy as np

EPS = 1e-9


@dataclass
class GaussianBelief:
    mean: np.ndarray
    var: np.ndarray

    @property
    def uncertainty(self) -> float:
        return float(np.mean(self.var))


def build_belief(history: list[int], item_repr: np.ndarray, *, base_variance: float = 0.35, history_variance_weight: float = 0.65, floor: float = 0.03, ceiling: float = 1.50) -> GaussianBelief:
    if not history:
        dim = item_repr.shape[1]
        return GaussianBelief(np.zeros(dim, dtype=np.float64), np.full(dim, base_variance, dtype=np.float64))
    x = item_repr[np.asarray(history, dtype=int)].astype(np.float64)
    mean = x.mean(axis=0)
    empirical = x.var(axis=0) if len(history) > 1 else np.zeros(x.shape[1], dtype=np.float64)
    shrink = 1.0 / math.sqrt(max(1, len(history)))
    var = base_variance * shrink + history_variance_weight * empirical
    var = np.clip(var, floor, ceiling)
    return GaussianBelief(mean, var)


def gaussian_kl_diag(post_mean: np.ndarray, post_var: np.ndarray, prior_mean: np.ndarray, prior_var: np.ndarray) -> float:
    post_var = np.clip(post_var, EPS, None)
    prior_var = np.clip(prior_var, EPS, None)
    terms = np.log(prior_var / post_var) + (post_var + (post_mean - prior_mean) ** 2) / prior_var - 1.0
    return float(0.5 * np.sum(terms))


def _stable_seed(base_seed: int, user: int) -> int:
    raw = f"{base_seed}:{user}".encode("utf-8")
    return int(hashlib.sha256(raw).hexdigest()[:8], 16)


def expected_kl_information_gain_batch(
    belief: GaussianBelief,
    item_vectors: np.ndarray,
    *,
    user: int,
    samples: int = 96,
    temperature: float = 1.0,
    seed: int = 7,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Vectorized Monte Carlo expected posterior KL for candidate items.

    A common set of latent-state particles is sampled for the user. For every
    candidate simultaneously, Bernoulli likelihoods define hypothetical
    positive/negative posterior importance weights. Each posterior is
    moment-matched to a diagonal Gaussian and compared to the prior with KL.
    """
    rng = np.random.default_rng(_stable_seed(seed, user))
    particles = rng.normal(belief.mean, np.sqrt(belief.var), size=(samples, belief.mean.size))
    item_vectors = np.asarray(item_vectors, dtype=np.float64)
    scale = max(math.sqrt(belief.mean.size) * temperature, EPS)
    logits = particles @ item_vectors.T / scale                       # [M, C]
    probs = 1.0 / (1.0 + np.exp(-np.clip(logits, -30.0, 30.0)))      # [M, C]
    predictive = probs.mean(axis=0)                                   # [C]
    x2 = particles ** 2

    def posterior_stats(likelihood: np.ndarray):
        w = np.clip(likelihood, EPS, None)
        w = w / np.clip(w.sum(axis=0, keepdims=True), EPS, None)       # [M, C]
        mu = w.T @ particles                                           # [C, D]
        second = w.T @ x2                                              # [C, D]
        var = np.clip(second - mu ** 2, EPS, None)
        prior_mu = belief.mean[None, :]
        prior_var = np.clip(belief.var[None, :], EPS, None)
        terms = np.log(prior_var / var) + (var + (mu - prior_mu) ** 2) / prior_var - 1.0
        kl = 0.5 * terms.sum(axis=1)
        return kl

    kl1 = posterior_stats(probs)
    kl0 = posterior_stats(1.0 - probs)
    expected_kl = predictive * kl1 + (1.0 - predictive) * kl0

    p = np.clip(probs, EPS, 1.0 - EPS)
    ambiguity = (-(p * np.log(p) + (1.0 - p) * np.log(1.0 - p))).mean(axis=0)
    return expected_kl.astype(float), predictive.astype(float), ambiguity.astype(float)


def expected_kl_information_gain(
    belief: GaussianBelief,
    item_vector: np.ndarray,
    *,
    user: int,
    item: int | None = None,
    samples: int = 96,
    temperature: float = 1.0,
    seed: int = 7,
) -> tuple[float, float, float]:
    # Scalar compatibility wrapper used by tests and interactive analysis.
    e, p, a = expected_kl_information_gain_batch(
        belief, np.asarray(item_vector)[None, :], user=user, samples=samples,
        temperature=temperature, seed=seed
    )
    return float(e[0]), float(p[0]), float(a[0])
