#!/usr/bin/env python3
"""Runner de execucao local com mocks — sem dependencias AWS.

Uso:
    python scripts/invoke_local.py          # event item/updated (padrao)
    python scripts/invoke_local.py item
    python scripts/invoke_local.py transactions
    python scripts/invoke_local.py connector

Requer EXECUCAO=mock no .env.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(dotenv_path=ROOT / ".env", override=True)

if os.environ.get("EXECUCAO", "aws").lower() != "mock":
    print("ERRO: defina EXECUCAO=mock no arquivo .env para usar execucao com mocks.")
    sys.exit(1)

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s | %(name)s | %(message)s")

from scripts.local_mock import (
    MockAuthService,
    MockPluggyClient,
    MockS3Adapter,
    MockSyncRepository,
)
from src.application.event_processor import EventProcessor
from src.domain.entities.sqs import SQSEvent

logger = logging.getLogger(__name__)

_EVENT_FILES = {
    "item": "events/sqs_item_update.json",
    "transactions": "events/sqs_transactions.json",
    "connector": "events/sqs_connector.json",
}


async def run_event(sqs_event_dict: dict) -> None:
    sync_repo = MockSyncRepository()
    s3_adapter = MockS3Adapter()
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

    print("=== Execucao local mockada ===")
    print(f"Evento : {event_type}")
    print(f"Arquivo: {event_file.relative_to(ROOT)}")
    print()

    with event_file.open(encoding="utf-8") as f:
        event_dict = json.load(f)

    asyncio.run(run_event(event_dict))

    print()
    print("Concluido. Saida salva em local_output/")


if __name__ == "__main__":
    main()
