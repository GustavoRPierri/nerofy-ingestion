from datetime import datetime, timezone

from pydantic import BaseModel


class TransactionSyncRecord(BaseModel):
    account_id: str
    item_id: str
    last_synced_at: datetime
    total_synced: int

    @property
    def is_first_sync(self) -> bool:
        return self.total_synced == 0

    def to_dynamo_item(self) -> dict:
        return {
            "accountId": self.account_id,
            "itemId": self.item_id,
            "lastSyncedAt": self.last_synced_at.isoformat(),
            "totalSynced": self.total_synced,
        }

    @classmethod
    def from_dynamo_item(cls, item: dict) -> "TransactionSyncRecord":
        return cls(
            account_id=item["accountId"],
            item_id=item["itemId"],
            last_synced_at=datetime.fromisoformat(item["lastSyncedAt"]).replace(
                tzinfo=timezone.utc
            ),
            total_synced=int(item.get("totalSynced", 0)),
        )
