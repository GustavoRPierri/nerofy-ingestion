"""Fixtures para testes de integração contra Lambda efêmera na AWS."""
import json
import os

import boto3
import pytest


@pytest.fixture(scope="session")
def aws_region() -> str:
    return os.environ.get("AWS_DEFAULT_REGION", "sa-east-1")


@pytest.fixture(scope="session")
def test_lambda_name() -> str:
    name = os.environ.get("TEST_LAMBDA_NAME")
    if not name:
        pytest.skip("TEST_LAMBDA_NAME não configurado — testes de integração requerem ambiente AWS.")
    return name


@pytest.fixture(scope="session")
def test_s3_bucket() -> str:
    bucket = os.environ.get("TEST_S3_BUCKET")
    if not bucket:
        pytest.skip("TEST_S3_BUCKET não configurado.")
    return bucket


@pytest.fixture(scope="session")
def test_dynamo_auth_table() -> str:
    table = os.environ.get("TEST_DYNAMO_AUTH_TABLE")
    if not table:
        pytest.skip("TEST_DYNAMO_AUTH_TABLE não configurado.")
    return table


@pytest.fixture(scope="session")
def test_dynamo_sync_table() -> str:
    table = os.environ.get("TEST_DYNAMO_SYNC_TABLE")
    if not table:
        pytest.skip("TEST_DYNAMO_SYNC_TABLE não configurado.")
    return table


@pytest.fixture(scope="session")
def lambda_client(aws_region):
    return boto3.client("lambda", region_name=aws_region)


@pytest.fixture(scope="session")
def s3_client(aws_region):
    return boto3.client("s3", region_name=aws_region)


@pytest.fixture(scope="session")
def dynamo_client(aws_region):
    return boto3.client("dynamodb", region_name=aws_region)


@pytest.fixture
def sqs_event_invalid():
    """Evento SQS mal-formado para testar erro 400."""
    return {"NotRecords": "isso não é um evento SQS válido"}


@pytest.fixture
def sqs_event_valid():
    """Evento SQS bem-formado para testar processamento."""
    payload = {
        "event": "item/updated",
        "id": "evt-inttest-001",
        "itemId": "item-inttest-abc",
        "clientId": "client-inttest-xyz",
    }
    return {
        "Records": [{
            "messageId": "msg-inttest-001",
            "receiptHandle": "rcpt-inttest-001",
            "body": json.dumps(payload),
            "attributes": {"ApproximateReceiveCount": "1"},
            "eventSource": "aws:sqs",
            "awsRegion": "sa-east-1",
        }]
    }
