from __future__ import annotations

from pathlib import Path
from .common import leave_last_two
from .schema import DatasetBundle


def load_movielens1m(raw_dir: str | Path, positive_rating_threshold: float = 4.0, min_user_interactions: int = 3, diversity_dimensions: int = 64, diversity_seed: int = 2026) -> DatasetBundle:
    raw_dir = Path(raw_dir)
    path = raw_dir / "ml-1m" / "ratings.dat"
    if not path.exists():
        path = raw_dir / "ratings.dat"
    if not path.exists():
        raise FileNotFoundError(f"MovieLens ratings.dat not found under {raw_dir}. Run: efe-exp download movielens1m")

    rows = []
    with path.open("r", encoding="latin-1") as fh:
        for line in fh:
            user, item, rating, ts = line.rstrip("\n").split("::")
            if float(rating) >= positive_rating_threshold:
                rows.append((user, item, float(rating), int(ts)))
    return leave_last_two(rows, "movielens1m", min_user_interactions, diversity_dimensions, diversity_seed)
