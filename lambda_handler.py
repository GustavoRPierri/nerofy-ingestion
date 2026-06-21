import asyncio
import json
import logging
import os
from typing import List

from config.settings import settings
from src.application.event_processor import EventProcessor
from src.domain.entities.sqs import SQSEvent
from src.domain.entities.webhook import WebhookEvent
from src.infrastructure.auth.auth_repository import AuthRepository
from src.infrastructure.auth.pluggy_auth_service import PluggyAuthService
from src.infrastructure.database.transaction_sync_repository import (
    TransactionSyncRepository,
)
from src.infrastructure.storage.s3_adapter import S3Adapter
from src.utils.http_session import HttpSession

settings.setup_logging()
logger = logging.getLogger(__name__)

http_session = HttpSession()
auth_repo = AuthRepository(table_name=settings.dynamo_auth_table)
sync_repo = TransactionSyncRepository(table_name=settings.dynamo_sync_table)
s3_adapter = S3Adapter(
    bucket_name=settings.s3_bronze_bucket or os.environ.get("S3_BRONZE_BUCKET", "")
)

_LOOP: asyncio.AbstractEventLoop | None = None
_semaphore = asyncio.Semaphore(5)


async def _process_event(event: WebhookEvent) -> None:
    async with _semaphore:
        auth_service = PluggyAuthService(
            http_session=http_session,
            repository=auth_repo,
            client_id=event.client_id,
            client_secret=settings.pluggy_client_secret
            or os.environ.get("PLUGGY_CLIENT_SECRET", ""),
        )
        processor = EventProcessor(
            auth_service=auth_service,
            http_session=http_session,
            storage=s3_adapter,
            sync_repository=sync_repo,
        )
        await processor.execute(event)


async def _process_all(events: List[WebhookEvent]) -> None:
    results = await asyncio.gather(
        *[asyncio.create_task(_process_event(e)) for e in events],
        return_exceptions=True,
    )
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            logger.error("Falha no evento %d: %s", i, r, exc_info=r)


def lambda_handler(event: dict, context) -> dict:
    global _LOOP
    try:
        parsed = SQSEvent.model_validate(event)
    except Exception as e:
        return {"statusCode": 400, "body": json.dumps({"error": str(e)})}
    if _LOOP is None or _LOOP.is_closed():
        _LOOP = asyncio.new_event_loop()
        asyncio.set_event_loop(_LOOP)
    try:
        _LOOP.run_until_complete(_process_all(parsed.events))
    except Exception as e:
        logger.error("Erro crítico: %s", e, exc_info=True)
        return {"statusCode": 500, "body": json.dumps({"error": "Internal processing error"})}
    return {"statusCode": 200, "body": json.dumps({"message": "Events processed successfully"})}
