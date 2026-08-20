# Mapping Generated Artifacts to the Manuscript

| Manuscript result | Generated artifact |
|---|---|
| Ranking accuracy table | `artifacts/paper/table_ranking_accuracy.csv/.tex` |
| Beyond-accuracy table | `artifacts/paper/table_beyond_accuracy.csv/.tex` |
| EFE ablation table | `artifacts/paper/table_ablation.csv/.tex` |
| Recall comparison | `artifacts/paper/fig_recall.png/.pdf` |
| NDCG comparison | `artifacts/paper/fig_ndcg.png/.pdf` |
| Diversity comparison | `artifacts/paper/fig_diversity.png/.pdf` |
| Novelty comparison | `artifacts/paper/fig_novelty.png/.pdf` |
| Coverage comparison | `artifacts/paper/fig_coverage.png/.pdf` |
| Novelty–relevance trade-off | `artifacts/paper/fig_novelty_relevance_tradeoff.png/.pdf` |
| Item-level intrinsic explanations | `artifacts/<experiment>/seed_<n>/efe/<variant>/explanation_traces.jsonl` |

The repository intentionally does not pre-populate the manuscript's numerical results. Tables and figures are generated only from locally executed experiments.
