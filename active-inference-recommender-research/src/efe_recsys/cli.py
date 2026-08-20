from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
from .download import download_dataset
from .experiments import run_experiment
from .reports import generate_reports


def main():
    p = argparse.ArgumentParser(prog="efe-exp", description="Reproducible EFE recommender experiments")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("download", help="Download a benchmark dataset from its official host")
    d.add_argument("dataset", choices=["movielens1m", "amazon_beauty"])
    d.add_argument("--root", default="data/raw")

    r = sub.add_parser("run", help="Train baselines, evaluate EFE, run ablations")
    r.add_argument("--config", required=True)

    rep = sub.add_parser("report", help="Generate paper tables and figures from a result CSV")
    rep.add_argument("--results", required=True)
    rep.add_argument("--out", default="artifacts/report")

    merge = sub.add_parser("merge", help="Merge multiple results_raw.csv files")
    merge.add_argument("inputs", nargs="+")
    merge.add_argument("--out", required=True)

    args = p.parse_args()
    if args.cmd == "download":
        print(download_dataset(args.dataset, args.root))
    elif args.cmd == "run":
        df = run_experiment(args.config)
        print(df.to_string(index=False))
    elif args.cmd == "report":
        print(generate_reports(args.results, args.out))
    elif args.cmd == "merge":
        frames = [pd.read_csv(x) for x in args.inputs]
        out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
        pd.concat(frames, ignore_index=True).to_csv(out, index=False)
        print(out)

if __name__ == "__main__":
    main()
