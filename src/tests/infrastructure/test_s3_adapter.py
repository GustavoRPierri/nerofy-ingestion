"""Testa o S3Adapter: particionamento de chave e serialização do payload.

O boto3 é completamente mockado — nenhuma chamada AWS real.
"""

import asyncio
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.infrastructure.storage.s3_adapter import S3Adapter

FIXED_DATE = datetime(2026, 5, 23, 10, 30, 0, tzinfo=timezone.utc)


def make_adapter():
    mock_s3 = MagicMock()
    with patch("boto3.client", return_value=mock_s3):
        adapter = S3Adapter(bucket_name="test-bucket")
    return adapter, mock_s3


def run_save(adapter, base_path, filename, data, fixed_date=FIXED_DATE):
    with patch("src.infrastructure.storage.s3_adapter.datetime") as mock_dt:
        mock_dt.now.return_value = fixed_date
        asyncio.run(adapter.save_json(base_path, filename, data))


class TestS3KeyPartitioning:
    def test_key_contains_year_partition(self):
        adapter, mock_s3 = make_adapter()
        run_save(adapter, "bronze/items/item-abc", "item_evt.json", {})
        key = mock_s3.put_object.call_args.kwargs["Key"]
        assert "year=2026" in key

    def test_key_contains_month_partition_zero_padded(self):
        adapter, mock_s3 = make_adapter()
        run_save(adapter, "bronze/items/item-abc", "item_evt.json", {})
        key = mock_s3.put_object.call_args.kwargs["Key"]
        assert "month=05" in key

    def test_key_contains_day_partition_zero_padded(self):
        adapter, mock_s3 = make_adapter()
        run_save(adapter, "bronze/items/item-abc", "item_evt.json", {})
        key = mock_s3.put_object.call_args.kwargs["Key"]
        assert "day=23" in key

    def test_full_key_structure(self):
        adapter, mock_s3 = make_adapter()
        run_save(adapter, "bronze/items/item-abc", "item_evt.json", {})
        key = mock_s3.put_object.call_args.kwargs["Key"]
        assert key == "bronze/items/item-abc/year=2026/month=05/day=23/item_evt.json"

    def test_bucket_name_passed_correctly(self):
        adapter, mock_s3 = make_adapter()
        run_save(adapter, "bronze/items/item-abc", "file.json", {})
        assert mock_s3.put_object.call_args.kwargs["Bucket"] == "test-bucket"


class TestS3Serialization:
    def test_content_type_is_json(self):
        adapter, mock_s3 = make_adapter()
        run_save(adapter, "base", "file.json", {})
        assert mock_s3.put_object.call_args.kwargs["ContentType"] == "application/json"

    def test_body_is_valid_json_bytes(self):
        adapter, mock_s3 = make_adapter()
        run_save(adapter, "base", "file.json", {"amount": 100.0, "name": "test"})
        body_bytes = mock_s3.put_object.call_args.kwargs["Body"]
        parsed = json.loads(body_bytes.decode("utf-8"))
        assert parsed["amount"] == 100.0
        assert parsed["name"] == "test"

    def test_non_serializable_types_converted_via_default(self):
        adapter, mock_s3 = make_adapter()
        from datetime import date

        run_save(adapter, "base", "file.json", {"date": date(2026, 5, 23)})
        body_bytes = mock_s3.put_object.call_args.kwargs["Body"]
        parsed = json.loads(body_bytes.decode("utf-8"))
        assert "2026-05-23" in parsed["date"]
