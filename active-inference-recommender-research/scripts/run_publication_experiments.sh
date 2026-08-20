#!/usr/bin/env bash
set -euo pipefail

python -m efe_recsys.cli run --config configs/movielens1m.yaml
python -m efe_recsys.cli run --config configs/amazon_beauty.yaml
python -m efe_recsys.cli merge \
  artifacts/movielens1m_main/results_raw.csv \
  artifacts/amazon_beauty_main/results_raw.csv \
  --out artifacts/combined/results_raw.csv
python -m efe_recsys.cli report \
  --results artifacts/combined/results_raw.csv \
  --out artifacts/paper
