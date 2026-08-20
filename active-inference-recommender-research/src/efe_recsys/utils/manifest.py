from __future__ import annotations
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import sklearn
import torch


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def environment_manifest() -> dict:
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "torch": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_version": torch.version.cuda,
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scikit_learn": sklearn.__version__,
        "git_commit": git_commit(),
    }


def dataset_manifest(bundle) -> dict:
    train_count = sum(len(v) for v in bundle.train_by_user.values())
    return {
        "dataset": bundle.name,
        "users": bundle.n_users,
        "items": bundle.n_items,
        "train_interactions": train_count,
        "validation_interactions": len(bundle.validation_item),
        "test_interactions": len(bundle.test_item),
    }
