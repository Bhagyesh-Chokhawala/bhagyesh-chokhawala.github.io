from pathlib import Path
import pandas as pd
from efe_recsys.reports import generate_reports


def test_report_generation(tmp_path: Path):
    rows = []
    for seed in [1,2,3]:
        for method, offset in [("BPR",0), ("LightGCN",.01), ("SASREC",.02), ("Active Inference",.018)]:
            rows.append({"dataset":"toy","seed":seed,"method":method,"variant":"full" if method=="Active Inference" else "baseline","Recall@10":.3+offset,"NDCG@10":.35+offset,"Diversity":.2+offset,"Novelty":2+offset,"Coverage":.3+offset,"AvgPopularity":.5-offset})
        for variant in ["no_epistemic","no_risk","no_ambiguity"]:
            rows.append({"dataset":"toy","seed":seed,"method":f"Active Inference ({variant})","variant":variant,"Recall@10":.31,"NDCG@10":.36,"Diversity":.19,"Novelty":1.9,"Coverage":.28,"AvgPopularity":.55})
    csv = tmp_path / "results.csv"; pd.DataFrame(rows).to_csv(csv, index=False)
    out = tmp_path / "report"
    generate_reports(csv, out)
    assert (out / "table_ranking_accuracy.csv").exists()
    assert (out / "table_ablation.tex").exists()
    assert (out / "fig_novelty_relevance_tradeoff.png").exists()
