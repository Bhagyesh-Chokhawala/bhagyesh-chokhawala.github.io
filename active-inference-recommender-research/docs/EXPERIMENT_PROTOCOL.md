# Experiment Protocol

## Datasets

### MovieLens 1M
- Source: GroupLens stable MovieLens 1M release.
- Positive interaction: rating >= 4, matching the manuscript protocol.
- Split: chronological leave-last-two per user: last=test, second-last=validation, earlier=train.

### Amazon All Beauty 5-core (2018)
- Source: UCSD Amazon Review Data 2018, `All_Beauty_5.json.gz`.
- All review/purchase events are treated as implicit positive interactions.
- The input is re-checked for 5-core user/item support before splitting.
- Split: chronological leave-last-two using `unixReviewTime`.

## Candidate protocol
All methods are evaluated on the same filtered full catalog by default. Previously seen training items and the validation item are removed. The held-out test item remains eligible. EFE re-ranking operates on the top-N candidates from the configured base model (default SASRec), making the retrieval/ranking boundary explicit.

## Metrics
- Recall@10: held-out test item appears in top 10.
- NDCG@10: binary-relevance discounted gain of the held-out test item.
- Diversity: mean pairwise cosine dissimilarity in a model-independent truncated-SVD item-user co-occurrence space learned from training data only.
- Novelty: mean self-information of recommended items with add-one smoothing over training popularity.
- Coverage: unique recommended catalog items / catalog size.
- AvgPopularity: mean log-normalized training popularity; lower values indicate more long-tail exposure.

## EFE decomposition
For each candidate item:

`G(i|b) = λp Pragmatic(i) - λe Epistemic(i) + λr Risk(i) + λa Ambiguity(i)`

- Pragmatic: KL between predicted Bernoulli engagement and the configured preferred Bernoulli outcome.
- Epistemic: Monte Carlo expected posterior KL over a Gaussian user belief and Bernoulli observation model.
- Risk: log-normalized training popularity.
- Ambiguity: expected conditional entropy of the Bernoulli outcome under user-state particles.

The explanation trace persists the four terms, predictive engagement, effective weights, and final EFE score for every top-K result.

## Ablations
- Full model
- No epistemic term
- No risk term
- No ambiguity term

## Reproducibility
Every configured seed is applied to Python, NumPy, and PyTorch. Deterministic PyTorch algorithms are requested where supported. Reproducibility is strongest within the same software/hardware stack; exact bitwise equality across different PyTorch releases/platforms is not assumed.
