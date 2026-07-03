"""Testa a entidade TransactionSyncRecord: serialização, desserialização e propriedades.

Camada de domínio pura — sem dependências de infraestrutura.
"""

from datetime import datetime, timezone

import pytest

from src.domain.entities.sync import TransactionSyncRecord

NOW = datetime(2026, 5, 23, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def record():
    return TransactionSyncRecord(
        account_id="acc-001",
        item_id="item-abc",
        last_synced_at=NOW,
        total_synced=150,
    )


class TestTransactionSyncRecordSerialization:
    def test_to_dynamo_item_keys(self, record):
        item = record.to_dynamo_item()
        assert set(item.keys()) == {"accountId", "itemId", "lastSyncedAt", "totalSynced"}

    def test_to_dynamo_item_values(self, record):
        item = record.to_dynamo_item()
        assert item["accountId"] == "acc-001"
        assert item["itemId"] == "item-abc"
        assert item["totalSynced"] == 150

    def test_from_dynamo_item_roundtrip(self, record):
        restored = TransactionSyncRecord.from_dynamo_item(record.to_dynamo_item())
        assert restored.account_id == record.account_id
        assert restored.item_id == record.item_id
        assert restored.total_synced == record.total_synced
        assert restored.last_synced_at == record.last_synced_at

    def test_timezone_preserved_after_roundtrip(self, record):
        restored = TransactionSyncRecord.from_dynamo_item(record.to_dynamo_item())
        assert restored.last_synced_at.tzinfo is not None


class TestTransactionSyncRecordProperties:
    def test_is_first_sync_false_when_has_synced(self, record):
        assert record.is_first_sync is False

    def test_is_first_sync_true_when_total_zero(self):
        first = TransactionSyncRecord(
            account_id="acc-001",
            item_id="item-abc",
            last_synced_at=NOW,
            total_synced=0,
        )
        assert first.is_first_sync is True

    def test_total_synced_zero_is_first_sync(self):
        record = TransactionSyncRecord(
            account_id="acc-001",
            item_id="item-abc",
            last_synced_at=NOW,
            total_synced=0,
        )
        assert record.total_synced == 0
        assert record.is_first_sync is True
