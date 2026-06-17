import logging
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class AuthRepository:
    # DynamoDB: Table=PluggyAuth, PK=clientId (String), Billing=PAY_PER_REQUEST
    def __init__(self, table_name: str = "PluggyAuth"):
        self._table = boto3.resource("dynamodb", region_name="sa-east-1").Table(table_name)

    async def get_auth_cache(self, client_id: str) -> dict | None:
        try:
            response = self._table.get_item(Key={"clientId": client_id})
            return response.get("Item")
        except ClientError as e:
            logger.error("Erro ao ler cache de auth para clientId %s: %s", client_id, e)
            raise

    async def save_auth_cache(self, client_id: str, api_key: str, expires_at: datetime) -> None:
        try:
            self._table.put_item(Item={
                "clientId":  client_id,
                "apiKey":    api_key,
                "expiresAt": expires_at.isoformat(),
            })
        except ClientError as e:
            logger.error("Erro ao salvar cache de auth para clientId %s: %s", client_id, e)
            raise
