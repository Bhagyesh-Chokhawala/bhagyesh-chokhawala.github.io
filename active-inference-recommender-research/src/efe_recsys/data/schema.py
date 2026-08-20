from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
import numpy as np


@dataclass
class DatasetBundle:
    name: str
    n_users: int
    n_items: int
    train_by_user: Dict[int, List[int]]
    validation_item: Dict[int, int]
    test_item: Dict[int, int]
    user_raw_ids: List[str]
    item_raw_ids: List[str]
    item_popularity: np.ndarray
    diversity_features: np.ndarray

    @property
    def users(self) -> list[int]:
        return sorted(self.test_item)

    def seen_items(self, user: int, include_validation: bool = True) -> set[int]:
        seen = set(self.train_by_user.get(user, []))
        if include_validation and user in self.validation_item:
            seen.add(self.validation_item[user])
        return seen
