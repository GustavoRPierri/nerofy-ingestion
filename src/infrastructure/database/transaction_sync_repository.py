import logging

import boto3
from botocore.exceptions import ClientError

from src.domain.entities.sync import TransactionSyncRecord
from src.domain.interfaces.repositories import ITransactionSyncRepository

logger = logging.getLogger(__name__)


class TransactionSyncRepository(ITransactionSyncRepository):
    # DynamoDB: Table=PluggyTransactionSync, PK=accountId (String), Billing=PAY_PER_REQUEST
    def __init__(self, table_name: str = "PluggyTransactionSync"):
        self._table = boto3.resource("dynamodb", region_name="sa-east-1").Table(table_name)

    async def get(self, account_id: str) -> TransactionSyncRecord | None:
        try:
            response = self._table.get_item(Key={"accountId": account_id})
            item = response.get("Item")
            return TransactionSyncRecord.from_dynamo_item(item) if item else None
        except ClientError as e:
            logger.error("Erro ao ler DynamoDB para conta %s: %s", account_id, e)
            raise

    async def save(self, record: TransactionSyncRecord) -> None:
        try:
            self._table.put_item(Item=record.to_dynamo_item())
        except ClientError as e:
            logger.error(
                "Erro ao salvar cursor no DynamoDB para conta %s: %s", record.account_id, e
            )
            raise
