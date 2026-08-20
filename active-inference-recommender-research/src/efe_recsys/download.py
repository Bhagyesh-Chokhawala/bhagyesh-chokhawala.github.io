from __future__ import annotations
from pathlib import Path
import gzip
import shutil
import urllib.request
import zipfile

MOVIELENS_URL = "https://files.grouplens.org/datasets/movielens/ml-1m.zip"
AMAZON_BEAUTY_URL = "https://mcauleylab.ucsd.edu/public_datasets/data/amazon_v2/categoryFilesSmall/All_Beauty_5.json.gz"


def _download(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "efe-recommender-research/0.2"})
    with urllib.request.urlopen(req) as src, target.open("wb") as dst:
        shutil.copyfileobj(src, dst)


def download_dataset(name: str, root: str | Path = "data/raw") -> Path:
    root = Path(root)
    if name == "movielens1m":
        out = root / "movielens1m"
        archive = out / "ml-1m.zip"
        _download(MOVIELENS_URL, archive)
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(out)
        return out
    if name == "amazon_beauty":
        out = root / "amazon_beauty"
        _download(AMAZON_BEAUTY_URL, out / "All_Beauty_5.json.gz")
        return out
    raise ValueError(f"Unknown dataset {name}")
