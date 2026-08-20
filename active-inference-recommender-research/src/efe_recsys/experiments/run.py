from __future__ import annotations
from pathlib import Path
import json
import pandas as pd
import torch

from ..data import load_dataset
from ..utils.io import ensure_dir, load_config, write_json
from ..utils.manifest import environment_manifest, dataset_manifest
from .train import train_model
from .evaluate import rank_baseline, rank_efe, evaluate_rankings

MODELS = ["bpr", "lightgcn", "sasrec"]
ABLATIONS = ["full", "no_epistemic", "no_risk", "no_ambiguity"]


def run_experiment(config_path: str | Path) -> pd.DataFrame:
    cfg = load_config(config_path)
    bundle = load_dataset(cfg)
    root = ensure_dir(Path(cfg["experiment"].get("artifact_dir", "artifacts")) / cfg["experiment"]["name"])
    write_json(root / "run_manifest.json", {"environment": environment_manifest(), "dataset": dataset_manifest(bundle), "config": cfg})
    rows = []
    for seed in cfg["experiment"]["seeds"]:
        trained = {}
        for model_name in MODELS:
            result = train_model(model_name, bundle, cfg, int(seed))
            trained[model_name] = result.model
            model_dir = ensure_dir(root / f"seed_{seed}" / model_name)
            torch.save(result.model.state_dict(), model_dir / "model.pt")
            baseline_rankings = rank_baseline(result.model, bundle, cfg)
            metrics = evaluate_rankings(baseline_rankings, bundle, cfg)
            row = {"dataset": bundle.name, "seed": seed, "method": model_name.upper() if model_name != "lightgcn" else "LightGCN", "variant": "baseline", **metrics, "validation_ndcg": result.best_validation_ndcg, "epochs": result.epochs_ran}
            rows.append(row)
            write_json(model_dir / "metrics.json", row)

        base_name = cfg["efe"].get("base_model", "sasrec")
        base_model = trained[base_name]
        for ablation in ABLATIONS:
            rankings, audit = rank_efe(base_model, bundle, cfg, int(seed), ablation)
            metrics = evaluate_rankings(rankings, bundle, cfg)
            method = "Active Inference" if ablation == "full" else f"Active Inference ({ablation})"
            row = {"dataset": bundle.name, "seed": seed, "method": method, "variant": ablation, **metrics}
            rows.append(row)
            out = ensure_dir(root / f"seed_{seed}" / "efe" / ablation)
            write_json(out / "metrics.json", row)
            # Full top-K traces can be large; JSONL keeps them streamable and auditable.
            with (out / "explanation_traces.jsonl").open("w", encoding="utf-8") as fh:
                for user, traces in audit.items():
                    fh.write(json.dumps({"user": user, "traces": traces}) + "\n")

    df = pd.DataFrame(rows)
    df.to_csv(root / "results_raw.csv", index=False)
    return df
