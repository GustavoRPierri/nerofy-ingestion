"""Classes de mock para execucao local sem dependencias AWS (EXECUCAO=mock)."""
import json
import logging
import os
from pathlib import Path

from src.domain.entities.sync import TransactionSyncRecord
from src.domain.interfaces.clients import IPluggyClient
from src.domain.interfaces.repositories import ITransactionSyncRepository

_ROOT = Path(__file__).parent.parent
_OUTPUT_DIR = Path("/tmp/local_output") if os.environ.get("AWS_SAM_LOCAL") else _ROOT / "local_output"

_log = logging.getLogger(__name__)


class MockPluggyClient(IPluggyClient):
    async def get_item(self, item_id: str) -> dict:
        return {
            "id": item_id,
            "status": "UPDATED",
            "connector": {"id": 201, "name": "Itaú", "primaryColor": "#EC7000"},
            "lastUpdatedAt": "2026-05-23T10:00:00Z",
        }

    async def get_accounts(self, item_id: str) -> list[dict]:
        return [
            {"id": "acc-001", "itemId": item_id, "type": "BANK",   "name": "Conta Corrente", "balance": 1500.0},
            {"id": "acc-002", "itemId": item_id, "type": "CREDIT", "name": "Cartão Itaú",    "balance": -300.0},
        ]

    async def get_transactions(self, account_id: str, from_date: str | None = None) -> list[dict]:
        return [
            {"id": "txn-001", "accountId": account_id, "description": "Pix recebido",  "amount":  500.0,  "date": "2026-05-20"},
            {"id": "txn-002", "accountId": account_id, "description": "Mercado Extra", "amount": -120.0,  "date": "2026-05-21"},
            {"id": "txn-003", "accountId": account_id, "description": "Netflix",       "amount":  -45.90, "date": "2026-05-22"},
        ]

    async def get_connector(self, connector_id: int) -> dict:
        return {"id": connector_id, "name": "Itaú", "primaryColor": "#EC7000",
                "imageUrl": "https://cdn.pluggy.ai/assets/connector-icons/201.svg"}


class MockSyncRepository(ITransactionSyncRepository):
    def __init__(self) -> None:
        self._store: dict[str, TransactionSyncRecord] = {}

    async def get(self, account_id: str) -> TransactionSyncRecord | None:
        record = self._store.get(account_id)
        _log.debug("[MockSyncRepo] get(%s) → %s", account_id, record)
        return record

    async def save(self, record: TransactionSyncRecord) -> None:
        self._store[record.account_id] = record
        _log.info("[MockSyncRepo] cursor salvo: account=%s last_synced=%s total=%d",
                  record.account_id, record.last_synced_at.isoformat(), record.total_synced)


class MockAuthService:
    async def get_valid_api_key(self) -> str:
        _log.debug("[MockAuth] retornando api_key fictícia")
        return "mock-api-key-local"


class MockS3Adapter:
    def __init__(self) -> None:
        _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    async def save_json(self, base_path: str, filename: str, data: dict) -> None:
        dest_dir = _OUTPUT_DIR / base_path
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / filename
        dest.write_text(json.dumps(data, default=str, indent=2, ensure_ascii=False), encoding="utf-8")
        _log.info("[MockS3] salvo → %s", dest)
