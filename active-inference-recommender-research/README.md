# Active Inference Recommender — Experimental Repository

Reproducible research implementation for **Active Inference as an Intrinsically Explainable Recommender Architecture via Epistemic-Pragmatic Score Decomposition**.

This repository extends the original interactive POC into an offline experimental pipeline with:

- MovieLens 1M and Amazon All Beauty 5-core dataset loaders;
- BPR matrix factorization, LightGCN, and SASRec baselines implemented in PyTorch;
- a modular EFE re-ranking layer over a trained baseline candidate generator;
- a numerical **expected posterior KL** epistemic-value estimator rather than the POC novelty proxy;
- full / no-epistemic / no-risk / no-ambiguity ablations;
- Recall@10, NDCG@10, diversity, novelty, coverage, and average-popularity metrics;
- deterministic seed handling, validation-based early stopping, checkpointing, and explanation trace logging;
- automatic CSV/LaTeX result tables and PNG/PDF paper figures;
- unit/smoke tests that do not require downloading the public benchmarks;
- the original FastAPI browser POC retained under `app/` for architecture demonstrations.

> **Research integrity:** the repository contains no fabricated benchmark output. Manuscript tables are generated only after the experiments are actually run. The source datasets are downloaded from their official hosts and are not redistributed here.

## 1. Experimental architecture

```text
                         OFFLINE TRAINING

 MovieLens 1M / Amazon Beauty
              |
              v
     chronological split
       train / val / test
              |
      +-------+--------+
      |       |        |
      v       v        v
     BPR   LightGCN  SASRec
      |       |        |
      +-------+--------+
              |
              v
        baseline scores
              |
        top-N candidates
              |
              v
 +---------------------------------------+
 | Active Inference EFE re-ranking       |
 |                                       |
 | Gaussian belief q(s | history)        |
 | Generative p(o | s, item)             |
 |                                       |
 | Pragmatic  = outcome-preference KL    |
 | Epistemic  = E_o[KL(q(s|o)||q(s))]    |
 | Risk       = exposure/popularity      |
 | Ambiguity  = E_q(s)[H(p(o|s,item))]   |
 |                                       |
 | G = λp Pgm - λe Epi + λr Risk + λa A |
 +---------------------------------------+
              |
      +-------+--------+
      |                |
      v                v
    Top-K        explanation traces
      |
      v
 Recall / NDCG / Diversity / Novelty / Coverage
      |
      v
 automatic CSV + LaTeX tables + PNG/PDF figures
```

## 2. Dataset protocol

### MovieLens 1M

The downloader uses the stable GroupLens MovieLens 1M archive. The experiment treats ratings **>= 4** as positive interactions, then sorts each user's positives chronologically and uses the last interaction for testing, the second-last for validation, and earlier interactions for training.

### Amazon All Beauty 5-core

The downloader uses UCSD's Amazon Review Data 2018 `All_Beauty_5.json.gz`. The 2018 page explicitly retains this older release for reproducing past results. The loader uses `reviewerID`, `asin`, and `unixReviewTime`, treats review/purchase events as implicit positives, re-checks the 5-core constraint, and applies the same chronological leave-last-two split.

Dataset files are intentionally excluded from Git.

## 3. Repository structure

```text
active-inference-recommender-research/
├── app/                         # original interactive FastAPI POC
├── src/efe_recsys/
│   ├── data/                    # MovieLens/Amazon/synthetic loaders + split
│   ├── models/                  # BPR, LightGCN, SASRec
│   ├── efe/                     # Gaussian belief + expected-KL + EFE re-ranker
│   ├── metrics/                 # accuracy and beyond-accuracy metrics
│   ├── experiments/             # training, ranking, ablations, orchestration
│   ├── reports/                 # tables and publication figures
│   ├── utils/                   # configuration and reproducibility helpers
│   ├── cli.py
│   └── download.py
├── configs/
│   ├── movielens1m.yaml
│   ├── amazon_beauty.yaml
│   └── smoke.yaml
├── research_tests/              # benchmark-pipeline tests
├── tests/                       # original API/POC tests
├── docs/
│   ├── EXPERIMENT_PROTOCOL.md
│   └── PAPER_OUTPUT_MAPPING.md
├── scripts/run_publication_experiments.sh
├── Makefile
├── pyproject.toml
├── CITATION.cff
└── REFERENCES.md
```

## 4. Installation

Python 3.11+ is recommended.

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

For a minimal research-only environment:

```bash
pip install -r requirements-research.txt
pip install -e . --no-deps
```

## 5. Validate the repository before long experiments

```bash
pytest
```

Then run the synthetic end-to-end smoke experiment:

```bash
python -m efe_recsys.cli run --config configs/smoke.yaml
```

The smoke configuration trains all three baseline model classes and executes EFE plus all three requested ablations without needing external data. `make smoke` also runs the table/figure generator against those smoke results.

## 6. Download the benchmark datasets

```bash
python -m efe_recsys.cli download movielens1m
python -m efe_recsys.cli download amazon_beauty
```

Equivalent:

```bash
make download-data
```

Expected local files:

```text
data/raw/movielens1m/ml-1m/ratings.dat
data/raw/amazon_beauty/All_Beauty_5.json.gz
```

## 7. Run one dataset

### MovieLens 1M

```bash
python -m efe_recsys.cli run --config configs/movielens1m.yaml
```

### Amazon Beauty

```bash
python -m efe_recsys.cli run --config configs/amazon_beauty.yaml
```

Each configuration runs three seeds by default. Edit the YAML to change epochs, embedding size, candidate pool, EFE weights, or Monte Carlo sample count; do not change these after looking at test results if you intend to report a clean confirmatory experiment.

## 8. Run the complete paper pipeline

```bash
bash scripts/run_publication_experiments.sh
```

or:

```bash
make all
```

The script:

1. trains and evaluates BPR, LightGCN, and SASRec on MovieLens 1M;
2. applies the full EFE re-ranker using the configured base model (SASRec by default);
3. executes `- Epistemic`, `- Risk`, and `- Ambiguity` ablations;
4. repeats the process on Amazon Beauty;
5. merges all seed-level results;
6. generates paper-ready tables and figures.

## 9. Actual expected-KL epistemic computation

The research implementation replaces the demo proxy with a Monte Carlo expected posterior KL estimator.

For a user belief:

```text
q(s | H) = N(mu, diag(var))
```

and candidate item vector `v_i`, the generative outcome model is:

```text
p(o=1 | s, i) = sigmoid(s · v_i / (sqrt(d) * temperature))
```

For each candidate, the implementation:

1. samples latent preference particles from `q(s|H)`;
2. computes each particle's positive-outcome likelihood;
3. forms hypothetical posterior particle weights for `o=1` and `o=0`;
4. moment-matches each weighted posterior to a diagonal Gaussian;
5. computes `KL(q(s|o,i,H) || q(s|H))` for each outcome;
6. averages the KLs using the predictive outcome probability.

Thus:

```text
Epistemic(i) = E_o [ KL( Q(s | o, i, H) || Q(s | H) ) ]
```

The same sampled outcome probabilities also produce the ambiguity term as expected conditional entropy.

Implementation: `src/efe_recsys/efe/belief.py`.

## 10. Baselines

### BPR

Pairwise implicit-feedback matrix factorization trained with BPR-Opt/log-sigmoid ranking loss.

### LightGCN

Bipartite user-item graph propagation using normalized adjacency, no feature transforms or nonlinear graph-convolution layers, with layer-average embeddings and BPR loss.

### SASRec

Causal Transformer-based sequential recommender with item/position embeddings, multi-head self-attention, next-item positive/negative training, and final-state all-item scoring.

The implementations are intentionally self-contained rather than wrappers around a third-party recommender framework, making preprocessing, sampling, and scoring behavior auditable.

## 11. Common evaluation protocol

By default, all baselines are evaluated against the **filtered full catalog**, not against different negative samples. Training items and the validation item are excluded from the test candidate set; the held-out test item remains eligible.

EFE is explicitly a second-stage re-ranker. It receives the top `candidate_pool_size` items from the configured baseline retrieval/ranking model and returns the final Top-K.

The repository computes:

- **Recall@10** — whether the held-out item appears in Top-10.
- **NDCG@10** — position-sensitive gain of the held-out item.
- **Diversity** — mean pairwise cosine dissimilarity within each recommendation list using a training-only, model-independent truncated-SVD item-user representation.
- **Novelty** — mean item self-information from training popularity, with add-one smoothing.
- **Coverage** — unique items exposed across Top-K lists divided by catalog size.
- **AvgPopularity** — diagnostic mean normalized popularity; lower values indicate greater long-tail exposure.

See `docs/EXPERIMENT_PROTOCOL.md` for exact definitions.

## 12. Ablation experiments

The same code path is used for every variant; only the relevant EFE coefficient is zeroed:

```text
full
no_epistemic
no_risk
no_ambiguity
```

This avoids accidentally changing retrieval, preprocessing, or another component while running an ablation.

## 13. Generated experimental artifacts

For each seed/model:

```text
artifacts/<experiment>/seed_<seed>/<model>/model.pt
artifacts/<experiment>/seed_<seed>/<model>/metrics.json
```

For EFE variants:

```text
artifacts/<experiment>/seed_<seed>/efe/full/metrics.json
artifacts/<experiment>/seed_<seed>/efe/full/explanation_traces.jsonl
artifacts/<experiment>/seed_<seed>/efe/no_epistemic/...
artifacts/<experiment>/seed_<seed>/efe/no_risk/...
artifacts/<experiment>/seed_<seed>/efe/no_ambiguity/...
```

Merged paper output:

```text
artifacts/paper/
├── results_summary.csv
├── table_ranking_accuracy.csv
├── table_ranking_accuracy.tex
├── table_beyond_accuracy.csv
├── table_beyond_accuracy.tex
├── table_ablation.csv
├── table_ablation.tex
├── fig_recall.png / .pdf
├── fig_ndcg.png / .pdf
├── fig_diversity.png / .pdf
├── fig_novelty.png / .pdf
├── fig_coverage.png / .pdf
└── fig_novelty_relevance_tradeoff.png / .pdf
```

These correspond directly to the manuscript sections documented in `docs/PAPER_OUTPUT_MAPPING.md`.

## 14. Reproducibility policy

Each configured seed is propagated to Python, NumPy, and PyTorch. Deterministic PyTorch algorithms are requested where available, and cuDNN benchmarking is disabled. Model selection uses validation NDCG, not test performance.

Exact bitwise reproducibility is not promised across different PyTorch versions, devices, CUDA versions, or platforms. For a submitted result set, archive:

```bash
python --version
python -m pip freeze > artifacts/paper/environment.txt
nvidia-smi > artifacts/paper/gpu.txt      # when using CUDA
```

alongside the YAML configurations and generated seed-level result files.

## 15. Interactive architecture demo

The original POC remains available:

```bash
uvicorn app.main:app --reload
```

Open:

- UI: `http://127.0.0.1:8000/`
- OpenAPI: `http://127.0.0.1:8000/docs`

The UI is for explaining EFE decomposition and belief updates. The **research pipeline under `src/efe_recsys/` is the source of benchmark claims**.

## 16. Publication checklist

Before copying numbers into the manuscript:

- run `pytest` cleanly;
- retain all YAML configurations used for the final run;
- use at least the configured three seeds;
- confirm the benchmark source files and preprocessing counts;
- generate tables from `results_raw.csv`, never hand-copy isolated run output;
- archive explanation traces for the full EFE model;
- report mean ± standard deviation across seeds;
- report any deviation from the protocol in `docs/EXPERIMENT_PROTOCOL.md`;
- do not mix synthetic POC numbers with benchmark numbers.

## 17. Research sources

The implementation follows the architectural choices of the accompanying manuscript and the original BPR, LightGCN, and SASRec papers. Dataset URLs are the official GroupLens and UCSD/McAuley Lab hosts. A bibliography is included in `REFERENCES.md` and software citation metadata in `CITATION.cff`.
