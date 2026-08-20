from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

METRICS = ["Recall@10", "NDCG@10", "Diversity", "Novelty", "Coverage", "AvgPopularity"]
BASE_ORDER = ["BPR", "LightGCN", "SASREC", "Active Inference"]


def _fmt(mean: float, std: float) -> str:
    return f"{mean:.4f} ± {std:.4f}"


def aggregate_results(df: pd.DataFrame) -> pd.DataFrame:
    metrics = [c for c in METRICS if c in df.columns]
    grouped = df.groupby(["dataset", "method", "variant"], dropna=False)[metrics].agg(["mean", "std"]).reset_index()
    grouped.columns = ["dataset", "method", "variant"] + [f"{m}_{s}" for m in metrics for s in ("mean", "std")]
    return grouped


def _paper_table(df: pd.DataFrame, metrics: list[str]) -> pd.DataFrame:
    base = df[df["method"].isin(BASE_ORDER)].copy()
    rows = []
    for (dataset, method), g in base.groupby(["dataset", "method"]):
        row = {"Dataset": dataset, "Model": method}
        for m in metrics:
            if m in g:
                row[m] = _fmt(float(g[m].mean()), float(g[m].std(ddof=1) if len(g) > 1 else 0.0))
        rows.append(row)
    out = pd.DataFrame(rows)
    if not out.empty:
        out["_order"] = out["Model"].map({m: i for i, m in enumerate(BASE_ORDER)}).fillna(999)
        out = out.sort_values(["Dataset", "_order"]).drop(columns="_order")
    return out


def _ablation_table(df: pd.DataFrame) -> pd.DataFrame:
    ablations = df[df["variant"].isin(["full", "no_epistemic", "no_risk", "no_ambiguity"])].copy()
    labels = {"full": "Full model", "no_epistemic": "- Epistemic", "no_risk": "- Risk", "no_ambiguity": "- Ambiguity"}
    rows = []
    for (dataset, variant), g in ablations.groupby(["dataset", "variant"]):
        row = {"Dataset": dataset, "Variant": labels[variant]}
        for m in ["Recall@10", "Diversity", "Coverage"]:
            if m in g:
                row[m] = _fmt(float(g[m].mean()), float(g[m].std(ddof=1) if len(g) > 1 else 0.0))
        rows.append(row)
    return pd.DataFrame(rows)


def _save_table(table: pd.DataFrame, stem: Path) -> None:
    table.to_csv(stem.with_suffix(".csv"), index=False)
    stem.with_suffix(".tex").write_text(table.to_latex(index=False, escape=False), encoding="utf-8")


def _bar_plot(summary: pd.DataFrame, metric: str, out: Path) -> None:
    methods = [m for m in BASE_ORDER if m in set(summary["method"])]
    if not methods:
        return
    datasets = sorted(summary["dataset"].unique())
    x = np.arange(len(methods), dtype=float)
    width = 0.8 / max(1, len(datasets))
    fig, ax = plt.subplots(figsize=(8, 4.8))
    for j, ds in enumerate(datasets):
        vals, errs = [], []
        for m in methods:
            row = summary[(summary.dataset == ds) & (summary.method == m)]
            vals.append(float(row[f"{metric}_mean"].iloc[0]) if len(row) else 0.0)
            errs.append(float(row[f"{metric}_std"].iloc[0]) if len(row) and not pd.isna(row[f"{metric}_std"].iloc[0]) else 0.0)
        ax.bar(x + (j - (len(datasets)-1)/2)*width, vals, width, yerr=errs, capsize=3, label=ds)
    ax.set_xticks(x, methods, rotation=15)
    ax.set_ylabel(metric)
    ax.set_title(f"{metric} across recommender architectures")
    ax.grid(axis="y", alpha=0.2)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out.with_suffix(".png"), dpi=220)
    fig.savefig(out.with_suffix(".pdf"))
    plt.close(fig)


def _tradeoff_plot(df: pd.DataFrame, out: Path) -> None:
    base = df[df["method"].isin(BASE_ORDER)].groupby(["dataset", "method"])[["NDCG@10", "Novelty"]].mean().reset_index()
    if base.empty:
        return
    fig, ax = plt.subplots(figsize=(6.4, 5.2))
    for _, r in base.iterrows():
        ax.scatter(r["Novelty"], r["NDCG@10"], s=65)
        ax.annotate(f"{r['method']}\n{r['dataset']}", (r["Novelty"], r["NDCG@10"]), xytext=(5, 4), textcoords="offset points", fontsize=8)
    ax.set_xlabel("Novelty")
    ax.set_ylabel("NDCG@10")
    ax.set_title("Novelty–relevance trade-off")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(out.with_suffix(".png"), dpi=220)
    fig.savefig(out.with_suffix(".pdf"))
    plt.close(fig)


def generate_reports(results_csv: str | Path, output_dir: str | Path) -> dict[str, Path]:
    results_csv, output_dir = Path(results_csv), Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(results_csv)
    summary = aggregate_results(df)
    summary.to_csv(output_dir / "results_summary.csv", index=False)

    ranking = _paper_table(df, ["Recall@10", "NDCG@10"])
    beyond = _paper_table(df, ["Diversity", "Novelty", "Coverage"])
    ablation = _ablation_table(df)
    _save_table(ranking, output_dir / "table_ranking_accuracy")
    _save_table(beyond, output_dir / "table_beyond_accuracy")
    _save_table(ablation, output_dir / "table_ablation")

    for metric, stem in [("Recall@10", "fig_recall"), ("NDCG@10", "fig_ndcg"), ("Diversity", "fig_diversity"), ("Novelty", "fig_novelty"), ("Coverage", "fig_coverage")]:
        if f"{metric}_mean" in summary:
            _bar_plot(summary, metric, output_dir / stem)
    _tradeoff_plot(df, output_dir / "fig_novelty_relevance_tradeoff")
    return {"summary": output_dir / "results_summary.csv", "ranking": output_dir / "table_ranking_accuracy.csv", "beyond": output_dir / "table_beyond_accuracy.csv", "ablation": output_dir / "table_ablation.csv"}
