import asyncio
import logging
from datetime import datetime, timezone, timedelta

from src.domain.interfaces.clients import IPluggyClient
from src.domain.interfaces.repositories import ITransactionSyncRepository
from src.domain.entities.sync import TransactionSyncRecord
from src.domain.entities.webhook import ItemEvent, TransactionsEvent, ConnectorEvent
from src.infrastructure.clients.pluggy_http_client import PluggyHttpClient
from src.infrastructure.auth.pluggy_auth_service import PluggyAuthService
from src.infrastructure.storage.s3_adapter import S3Adapter
from src.utils.http_session import HttpSession

logger = logging.getLogger(__name__)
_OVERLAP_DAYS = 3


class EventProcessor:
    def __init__(self, auth_service, http_session, storage, sync_repository):
        self._auth = auth_service
        self._http = http_session
        self._storage = storage
        self._sync_repo = sync_repository

    async def execute(self, event_root) -> None:
        payload = event_root.root
        api_key = await self._auth.get_valid_api_key()
        client = PluggyHttpClient(self._http, api_key)
        match payload:
            case ItemEvent() as item:        await self._handle_item(item, client)
            case TransactionsEvent() as trx: await self._handle_transactions(trx, client)
            case ConnectorEvent() as conn:   await self._handle_connector(conn, client)
            case _: logger.warning("Evento desconhecido: %s", type(payload))

    async def _handle_item(self, item: ItemEvent, client: IPluggyClient) -> None:
        item_data, accounts = await asyncio.gather(
            client.get_item(item.item_id),
            client.get_accounts(item.item_id),
        )
        await self._storage.save_json(
            base_path=f"bronze/items/{item.item_id}",
            filename=f"item_{item.event_id}.json",
            data={"event": item.model_dump(), "item": item_data, "accounts": accounts},
        )
        await asyncio.gather(*[
            self._sync_account(item.item_id, acc["id"], item.event_id, client)
            for acc in accounts
        ])

    async def _sync_account(self, item_id, account_id, event_id, client):
        sync_record = await self._sync_repo.get(account_id)
        synced_at = datetime.now(timezone.utc)
        if sync_record is None:
            from_date = None
        else:
            from_date = (sync_record.last_synced_at - timedelta(days=_OVERLAP_DAYS)).strftime("%Y-%m-%d")
        transactions = await client.get_transactions(account_id, from_date=from_date)
        if transactions:
            await self._storage.save_json(
                base_path=f"bronze/transactions/item_{item_id}/account_{account_id}",
                filename=f"{event_id}.json",
                data={
                    "event_id": event_id,
                    "account_id": account_id,
                    "from_date": from_date,
                    "synced_at": synced_at.isoformat(),
                    "total": len(transactions),
                    "transactions": transactions,
                },
            )
        new_total = (sync_record.total_synced if sync_record else 0) + len(transactions)
        await self._sync_repo.save(TransactionSyncRecord(
            account_id=account_id,
            item_id=item_id,
            last_synced_at=synced_at,
            total_synced=new_total,
        ))

    async def _handle_transactions(self, trx: TransactionsEvent, client: IPluggyClient) -> None:
        transactions = await client.get_transactions(trx.account_id)
        await self._storage.save_json(
            base_path=f"bronze/transactions/item_{trx.item_id}/account_{trx.account_id}",
            filename=f"{trx.event_id}.json",
            data={"event": trx.model_dump(), "total": len(transactions), "transactions": transactions},
        )

    async def _handle_connector(self, conn: ConnectorEvent, client: IPluggyClient) -> None:
        connector_data = await client.get_connector(conn.connector_id)
        await self._storage.save_json(
            base_path=f"bronze/connectors/{conn.connector_id}",
            filename=f"{conn.event_id}.json",
            data={"event": conn.model_dump(), "connector": connector_data},
        )
