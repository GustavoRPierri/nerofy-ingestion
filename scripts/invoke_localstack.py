#!/usr/bin/env python3
"""Runner de execucao local com LocalStack.

Usa boto3 real (S3 + DynamoDB apontando para LocalStack) e Pluggy mockado.

Uso:
    python scripts/invoke_localstack.py          # event item (padrao)
    python scripts/invoke_localstack.py item
    python scripts/invoke_localstack.py transactions
    python scripts/invoke_localstack.py connector

Requer LocalStack rodando em localhost:4566.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from unittest.mock import patch

# Configurar env ANTES de qualquer import do projeto
os.environ.setdefault("EXECUCAO", "local")
os.environ.setdefault("AWS_ENDPOINT_URL", "http://localhost:4566")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("AWS_DEFAULT_REGION", "sa-east-1")
os.environ.setdefault("AWS_REGION", "sa-east-1")
os.environ.setdefault("S3_BRONZE_BUCKET", "nerofy-bronze-dev")
os.environ.setdefault("DYNAMO_AUTH_TABLE", "PluggyAuth")
os.environ.setdefault("DYNAMO_SYNC_TABLE", "PluggyTransactionSync")
os.environ.setdefault("PLUGGY_CLIENT_SECRET", "mock-secret-local")
os.environ.setdefault("LOG_LEVEL", "DEBUG")

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s | %(name)s | %(message)s")

from src.domain.entities.sqs import SQSEvent
from src.application.event_processor import EventProcessor
from src.infrastructure.storage.s3_adapter import S3Adapter
from src.infrastructure.database.transaction_sync_repository import TransactionSyncRepository
from scripts.local_mock import MockAuthService, MockPluggyClient

logger = logging.getLogger(__name__)

_EVENT_FILES = {
    "item": "events/sqs_item_update.json",
    "transactions": "events/sqs_transactions.json",
    "connector": "events/sqs_connector.json",
}


async def run_event(sqs_event_dict: dict) -> None:
    s3_adapter = S3Adapter(bucket_name=os.environ["S3_BRONZE_BUCKET"])
    sync_repo = TransactionSyncRepository(
        table_name=os.environ.get("DYNAMO_SYNC_TABLE", "PluggyTransactionSync")
    )
    auth_service = MockAuthService()
    mock_client = MockPluggyClient()

    parsed = SQSEvent.model_validate(sqs_event_dict)
    logger.info("Processando %d evento(s) SQS", len(parsed.Records))

    for webhook_event in parsed.events:
        processor = EventProcessor(
            auth_service=auth_service,
            http_session=None,
            storage=s3_adapter,
            sync_repository=sync_repo,
        )
        with patch("src.application.event_processor.PluggyHttpClient", return_value=mock_client):
            await processor.execute(webhook_event)


def main() -> None:
    event_type = sys.argv[1] if len(sys.argv) > 1 else "item"
    event_file = ROOT / _EVENT_FILES.get(event_type, _EVENT_FILES["item"])

    if not event_file.exists():
        print(f"ERRO: arquivo de evento nao encontrado: {event_file}")
        sys.exit(1)

    print("=== Execucao local com LocalStack ===")
    print(f"Evento  : {event_type}")
    print(f"Arquivo : {event_file.relative_to(ROOT)}")
    print(f"Endpoint: {os.environ['AWS_ENDPOINT_URL']}")
    print(f"S3      : s3://{os.environ['S3_BRONZE_BUCKET']}")
    print(f"DynamoDB: {os.environ.get('DYNAMO_SYNC_TABLE', 'PluggyTransactionSync')}")
    print()

    with event_file.open(encoding="utf-8") as f:
        event_dict = json.load(f)

    asyncio.run(run_event(event_dict))
    print("\nConcluido.")


if __name__ == "__main__":
    main()
