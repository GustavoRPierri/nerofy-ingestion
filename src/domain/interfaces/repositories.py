from abc import ABC, abstractmethod

from src.domain.entities.sync import TransactionSyncRecord


class ITransactionSyncRepository(ABC):
    @abstractmethod
    async def get(self, account_id: str) -> TransactionSyncRecord | None: ...

    @abstractmethod
    async def save(self, record: TransactionSyncRecord) -> None: ...
