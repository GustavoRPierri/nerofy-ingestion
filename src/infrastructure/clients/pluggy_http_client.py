import logging

from src.domain.interfaces.clients import IPluggyClient
from src.utils.http_session import HttpSession

logger = logging.getLogger(__name__)
_BASE_URL = "https://api.pluggy.ai"
_PAGE_SIZE = 500


class PluggyHttpClient(IPluggyClient):
    def __init__(self, http_session: HttpSession, api_key: str):
        self._http = http_session
        self._headers = {"X-API-KEY": api_key}

    async def get_item(self, item_id: str) -> dict:
        return await self._http.get(f"{_BASE_URL}/items/{item_id}", headers=self._headers)

    async def get_accounts(self, item_id: str) -> list[dict]:
        data = await self._http.get(f"{_BASE_URL}/accounts?itemId={item_id}", headers=self._headers)
        return data.get("results", [])

    async def get_transactions(self, account_id: str, from_date: str | None = None) -> list[dict]:
        date_filter = f"&from={from_date}" if from_date else ""
        all_transactions: list[dict] = []
        page = 1
        while True:
            url = (
                f"{_BASE_URL}/transactions?accountId={account_id}"
                f"&page={page}&pageSize={_PAGE_SIZE}{date_filter}"
            )
            data = await self._http.get(url, headers=self._headers)
            all_transactions.extend(data.get("results", []))
            if page >= data.get("totalPages", 1):
                break
            page += 1
        return all_transactions

    async def get_connector(self, connector_id: int) -> dict:
        return await self._http.get(f"{_BASE_URL}/connectors/{connector_id}", headers=self._headers)
