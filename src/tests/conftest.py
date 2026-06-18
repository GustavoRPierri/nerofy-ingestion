"""Fixtures compartilhadas entre todas as camadas de teste."""

import json

import pytest

# ── Payloads de webhook crus (como chegam da Pluggy via SQS) ─────────────────


@pytest.fixture
def item_payload():
    return {
        "event": "item/updated",
        "id": "evt-item-001",
        "itemId": "item-abc123",
        "clientId": "client-xyz",
    }


@pytest.fixture
def transactions_payload():
    return {
        "event": "transactions/created",
        "id": "evt-trx-001",
        "itemId": "item-abc123",
        "clientId": "client-xyz",
        "data": {"accountId": "acc-456"},
    }


@pytest.fixture
def connector_payload():
    return {
        "event": "connector/updated",
        "id": "evt-conn-001",
        "clientId": "client-xyz",
        "data": {"connectorId": 201},
    }


# ── Evento SQS completo (formato real da AWS) ─────────────────────────────────


@pytest.fixture
def sqs_item_event(item_payload):
    return {
        "Records": [
            {
                "messageId": "msg-001",
                "receiptHandle": "rcpt-001",
                "body": json.dumps(item_payload),
                "attributes": {"ApproximateReceiveCount": "1"},
                "eventSource": "aws:sqs",
                "awsRegion": "sa-east-1",
            }
        ]
    }


@pytest.fixture
def sqs_multi_event(item_payload, transactions_payload):
    return {
        "Records": [
            {"body": json.dumps(item_payload)},
            {"body": json.dumps(transactions_payload)},
        ]
    }
