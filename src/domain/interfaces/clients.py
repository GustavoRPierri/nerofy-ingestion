from abc import ABC, abstractmethod


class IPluggyClient(ABC):
    @abstractmethod
    async def get_item(self, item_id: str) -> dict: ...

    @abstractmethod
    async def get_accounts(self, item_id: str) -> list[dict]: ...

    @abstractmethod
    async def get_transactions(self, account_id: str, from_date: str | None = None) -> list[dict]: ...

    @abstractmethod
    async def get_connector(self, connector_id: int) -> dict: ...
