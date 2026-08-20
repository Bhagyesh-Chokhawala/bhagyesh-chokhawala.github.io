from .movielens import load_movielens1m
from .amazon import load_amazon_beauty
from .synthetic import load_synthetic
from .schema import DatasetBundle


def load_dataset(config: dict):
    name = config["experiment"]["dataset"]
    d = config["data"]
    if name == "movielens1m":
        return load_movielens1m(d["raw_dir"], d.get("positive_rating_threshold", 4.0), d.get("min_user_interactions", 3), d.get("diversity_dimensions", 64), d.get("diversity_seed", 2026))
    if name == "amazon_beauty":
        return load_amazon_beauty(d["raw_dir"], d.get("min_user_interactions", 5), d.get("min_item_interactions", 5), d.get("diversity_dimensions", 64), d.get("diversity_seed", 2026))
    if name == "synthetic":
        return load_synthetic(d.get("diversity_seed", 7))
    raise ValueError(f"Unknown dataset: {name}")
