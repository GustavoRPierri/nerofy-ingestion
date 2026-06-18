"""Testa a orquestração do EventProcessor.

Todas as dependências de infraestrutura (client, storage, repo, auth)
são substituídas por AsyncMocks — nenhuma chamada HTTP ou AWS real.
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from src.application.event_processor import EventProcessor
from src.domain.entities.sync import TransactionSyncRecord
from src.domain.entities.webhook import WebhookEvent

NOW = datetime(2026, 5, 23, 12, 0, 0, tzinfo=timezone.utc)


# ── Helpers ───────────────────────────────────────────────────────────────────


def make_processor(sync_record=None):
    """Cria um EventProcessor com todas as dependências mockadas."""
    auth = AsyncMock()
    auth.get_valid_api_key = AsyncMock(return_value="test-key")

    storage = AsyncMock()
    storage.save_json = AsyncMock()

    sync_repo = AsyncMock()
    sync_repo.get = AsyncMock(return_value=sync_record)
    sync_repo.save = AsyncMock()

    processor = EventProcessor(
        auth_service=auth,
        http_session=None,
        storage=storage,
        sync_repository=sync_repo,
    )
    return processor, storage, sync_repo


def make_client(accounts=None, transactions=None, item=None, connector=None):
    client = AsyncMock()
    client.get_item = AsyncMock(return_value=item if item is not None else {"id": "item-abc123"})
    client.get_accounts = AsyncMock(
        return_value=accounts if accounts is not None else [{"id": "acc-001"}]
    )
    client.get_transactions = AsyncMock(
        return_value=transactions if transactions is not None else [{"id": "txn-001"}]
    )
    client.get_connector = AsyncMock(
        return_value=connector if connector is not None else {"id": 201, "name": "Itau"}
    )
    return client


def run(coro):
    return asyncio.run(coro)


# ── item/updated ──────────────────────────────────────────────────────────────


class TestHandleItem:
    def test_saves_item_and_transactions(self, item_payload):
        processor, storage, sync_repo = make_processor()
        client = make_client(transactions=[{"id": "txn-001"}])
        event = WebhookEvent.from_raw(item_payload)

        with patch("src.application.event_processor.PluggyHttpClient", return_value=client):
            run(processor.execute(event))

        # 1 save para o item + 1 para as transações da conta
        assert storage.save_json.call_count == 2

    def test_cursor_saved_even_without_transactions(self, item_payload):
        processor, storage, sync_repo = make_processor()
        client = make_client(transactions=[])
        event = WebhookEvent.from_raw(item_payload)

        with patch("src.application.event_processor.PluggyHttpClient", return_value=client):
            run(processor.execute(event))

        storage.save_json.assert_called_once()  # apenas o item
        sync_repo.save.assert_called_once()  # cursor atualizado mesmo assim

    def test_syncs_all_accounts(self, item_payload):
        processor, storage, sync_repo = make_processor()
        client = make_client(
            accounts=[{"id": "acc-001"}, {"id": "acc-002"}],
            transactions=[{"id": "txn-001"}],
        )
        event = WebhookEvent.from_raw(item_payload)

        with patch("src.application.event_processor.PluggyHttpClient", return_value=client):
            run(processor.execute(event))

        assert sync_repo.save.call_count == 2  # um cursor por conta
        assert storage.save_json.call_count == 3  # item + 2 contas


# ── sync incremental vs histórico completo ────────────────────────────────────


class TestSyncAccount:
    def test_first_sync_passes_no_from_date(self, item_payload):
        processor, storage, sync_repo = make_processor(sync_record=None)
        client = make_client(transactions=[])

        run(processor._sync_account("item-abc", "acc-001", "evt-001", client))

        client.get_transactions.assert_called_once_with("acc-001", from_date=None)

    def test_incremental_sync_passes_from_date(self, item_payload):
        existing = TransactionSyncRecord(
            account_id="acc-001",
            item_id="item-abc",
            last_synced_at=NOW,
            total_synced=50,
        )
        processor, storage, sync_repo = make_processor(sync_record=existing)
        client = make_client(transactions=[])

        run(processor._sync_account("item-abc", "acc-001", "evt-001", client))

        call_kwargs = client.get_transactions.call_args.kwargs
        assert call_kwargs["from_date"] is not None

    def test_total_synced_accumulates(self):
        existing = TransactionSyncRecord(
            account_id="acc-001",
            item_id="item-abc",
            last_synced_at=NOW,
            total_synced=10,
        )
        processor, storage, sync_repo = make_processor(sync_record=existing)
        client = make_client(transactions=[{"id": "t1"}, {"id": "t2"}])

        run(processor._sync_account("item-abc", "acc-001", "evt-001", client))

        saved_record: TransactionSyncRecord = sync_repo.save.call_args.args[0]
        assert saved_record.total_synced == 12  # 10 anteriores + 2 novos


# ── transactions/created ──────────────────────────────────────────────────────


class TestHandleTransactions:
    def test_saves_to_correct_s3_path(self, transactions_payload):
        processor, storage, sync_repo = make_processor()
        client = make_client(transactions=[{"id": "txn-001"}])
        event = WebhookEvent.from_raw(transactions_payload)

        with patch("src.application.event_processor.PluggyHttpClient", return_value=client):
            run(processor.execute(event))

        storage.save_json.assert_called_once()
        call_kwargs = storage.save_json.call_args.kwargs
        assert "account_acc-456" in call_kwargs["base_path"]
        assert "item_item-abc123" in call_kwargs["base_path"]


# ── connector/updated ─────────────────────────────────────────────────────────


class TestHandleConnector:
    def test_saves_connector_data(self, connector_payload):
        processor, storage, sync_repo = make_processor()
        client = make_client(connector={"id": 201, "name": "Itau"})
        event = WebhookEvent.from_raw(connector_payload)

        with patch("src.application.event_processor.PluggyHttpClient", return_value=client):
            run(processor.execute(event))

        storage.save_json.assert_called_once()
        call_kwargs = storage.save_json.call_args.kwargs
        assert "connectors" in call_kwargs["base_path"]
        assert "201" in call_kwargs["base_path"]
