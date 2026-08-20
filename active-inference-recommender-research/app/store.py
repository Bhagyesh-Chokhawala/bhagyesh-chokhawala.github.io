from __future__ import annotations

from copy import deepcopy
from uuid import uuid4

try:
    from .data import DEFAULT_ITEMS, DEFAULT_USERS
    from .models import AuditRecord, Item, UserBeliefState
except ImportError:
    from data import DEFAULT_ITEMS, DEFAULT_USERS
    from models import AuditRecord, Item, UserBeliefState


class InMemoryStore:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.users = {key: value.model_copy(deep=True) for key, value in DEFAULT_USERS.items()}
        self.items = {item.item_id: item.model_copy(deep=True) for item in DEFAULT_ITEMS}
        self.audit: list[AuditRecord] = []

    def get_user(self, user_id: str) -> UserBeliefState:
        return self.users[user_id]

    def get_item(self, item_id: str) -> Item:
        return self.items[item_id]

    def add_audit(self, *, event_type: str, user_id: str, payload: dict, item_id: str | None = None) -> None:
        self.audit.append(
            AuditRecord(
                event_id=str(uuid4()),
                event_type=event_type,
                user_id=user_id,
                item_id=item_id,
                payload=deepcopy(payload),
            )
        )


store = InMemoryStore()
