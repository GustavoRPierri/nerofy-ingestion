import json
import logging
from datetime import datetime, timezone

import boto3

logger = logging.getLogger(__name__)


class S3Adapter:
    def __init__(self, bucket_name: str):
        self._bucket = bucket_name
        self._s3 = boto3.client("s3")

    async def save_json(self, base_path: str, filename: str, data: dict) -> None:
        now = datetime.now(timezone.utc)
        key = f"{base_path}/year={now.year}/month={now.month:02d}/day={now.day:02d}/{filename}"
        body = json.dumps(data, default=str, ensure_ascii=False)
        self._s3.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=body.encode("utf-8"),
            ContentType="application/json",
        )
        logger.info("Salvo s3://%s/%s", self._bucket, key)
