from __future__ import annotations

from pathlib import Path
import gzip
import json
from .common import iterative_k_core, leave_last_two
from .schema import DatasetBundle


def load_amazon_beauty(raw_dir: str | Path, min_user_interactions: int = 5, min_item_interactions: int = 5, diversity_dimensions: int = 64, diversity_seed: int = 2026) -> DatasetBundle:
    raw_dir = Path(raw_dir)
    candidates = [raw_dir / "All_Beauty_5.json.gz", raw_dir / "All_Beauty_5.json"]
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        raise FileNotFoundError(f"All_Beauty_5.json(.gz) not found under {raw_dir}. Run: efe-exp download amazon_beauty")

    opener = gzip.open if path.suffix == ".gz" else open
    rows = []
    with opener(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            obj = json.loads(line)
            rows.append((str(obj["reviewerID"]), str(obj["asin"]), float(obj.get("overall", 1.0)), int(obj["unixReviewTime"])))

    # The official file is already 5-core; re-checking makes preprocessing explicit and guards custom inputs.
    rows = iterative_k_core(rows, min_user_interactions, min_item_interactions)
    return leave_last_two(rows, "amazon_beauty", min_user_interactions, diversity_dimensions, diversity_seed)
