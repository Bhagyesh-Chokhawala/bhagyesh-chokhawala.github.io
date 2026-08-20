import gzip
import json
from pathlib import Path

from efe_recsys.data.movielens import load_movielens1m
from efe_recsys.data.amazon import load_amazon_beauty


def test_movielens_loader(tmp_path: Path):
    d = tmp_path / "ml-1m"; d.mkdir()
    lines = []
    ts = 1
    for u in range(1, 4):
        for i in range(1, 7):
            lines.append(f"{u}::{i}::5::{ts}\n"); ts += 1
    (d / "ratings.dat").write_text("".join(lines), encoding="latin-1")
    bundle = load_movielens1m(tmp_path, diversity_dimensions=2)
    assert bundle.n_users == 3
    assert bundle.n_items == 6
    assert all(len(bundle.train_by_user[u]) == 4 for u in bundle.users)
    assert bundle.diversity_features.shape[0] == 6


def test_amazon_loader(tmp_path: Path):
    p = tmp_path / "All_Beauty_5.json.gz"
    with gzip.open(p, "wt", encoding="utf-8") as fh:
        ts = 1
        for u in range(5):
            for i in range(5):
                fh.write(json.dumps({"reviewerID": f"u{u}", "asin": f"i{i}", "overall": 5.0, "unixReviewTime": ts}) + "\n")
                ts += 1
    bundle = load_amazon_beauty(tmp_path, min_user_interactions=5, min_item_interactions=5, diversity_dimensions=2)
    assert bundle.n_users == 5
    assert bundle.n_items == 5
    assert all(len(bundle.train_by_user[u]) == 3 for u in bundle.users)
