.PHONY: install test smoke download-data movielens amazon all report clean

install:
	python -m pip install -e ".[dev]"

test:
	pytest

smoke:
	python -m efe_recsys.cli run --config configs/smoke.yaml
	python -m efe_recsys.cli report --results artifacts/smoke/results_raw.csv --out artifacts/smoke/paper

download-data:
	python -m efe_recsys.cli download movielens1m
	python -m efe_recsys.cli download amazon_beauty

movielens:
	python -m efe_recsys.cli run --config configs/movielens1m.yaml

amazon:
	python -m efe_recsys.cli run --config configs/amazon_beauty.yaml

all:
	bash scripts/run_publication_experiments.sh

report:
	python -m efe_recsys.cli report --results artifacts/combined/results_raw.csv --out artifacts/paper

clean:
	rm -rf artifacts/* .pytest_cache **/__pycache__
