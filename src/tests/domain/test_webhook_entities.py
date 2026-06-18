"""Testa parsing e dispatch das entidades de webhook do domínio.

Nenhuma dependência externa — apenas lógica pura de validação Pydantic.
"""

import pytest
from src.domain.entities.webhook import (
    WebhookEvent,
    ItemEvent,
    TransactionsEvent,
    ConnectorEvent,
)


class TestItemEvent:
    def test_parse_item_updated(self, item_payload):
        event = WebhookEvent.from_raw(item_payload)
        assert isinstance(event.root, ItemEvent)

    def test_fields_mapped_correctly(self, item_payload):
        event = WebhookEvent.from_raw(item_payload)
        assert event.root.item_id == "item-abc123"
        assert event.root.event_id == "evt-item-001"
        assert event.root.client_id == "client-xyz"

    @pytest.mark.parametrize(
        "event_type",
        [
            "item/updated",
            "item/error",
            "item/waiting_user_action",
            "item/login_succeeded",
        ],
    )
    def test_all_item_event_types_dispatch_correctly(self, item_payload, event_type):
        payload = {**item_payload, "event": event_type}
        event = WebhookEvent.from_raw(payload)
        assert isinstance(event.root, ItemEvent)


class TestTransactionsEvent:
    def test_parse_transactions_created(self, transactions_payload):
        event = WebhookEvent.from_raw(transactions_payload)
        assert isinstance(event.root, TransactionsEvent)

    def test_account_id_extracted_from_data(self, transactions_payload):
        event = WebhookEvent.from_raw(transactions_payload)
        assert event.root.account_id == "acc-456"

    def test_item_id_and_event_id_present(self, transactions_payload):
        event = WebhookEvent.from_raw(transactions_payload)
        assert event.root.item_id == "item-abc123"
        assert event.root.event_id == "evt-trx-001"

    @pytest.mark.parametrize(
        "event_type",
        [
            "transactions/created",
            "transactions/deleted",
            "transactions/updated",
        ],
    )
    def test_all_transaction_event_types(self, transactions_payload, event_type):
        payload = {**transactions_payload, "event": event_type}
        event = WebhookEvent.from_raw(payload)
        assert isinstance(event.root, TransactionsEvent)


class TestConnectorEvent:
    def test_parse_connector_updated(self, connector_payload):
        event = WebhookEvent.from_raw(connector_payload)
        assert isinstance(event.root, ConnectorEvent)

    def test_connector_id_extracted_from_data(self, connector_payload):
        event = WebhookEvent.from_raw(connector_payload)
        assert event.root.connector_id == 201

    def test_client_id_present(self, connector_payload):
        event = WebhookEvent.from_raw(connector_payload)
        assert event.root.client_id == "client-xyz"


class TestWebhookEventDispatch:
    def test_client_id_property_delegates_to_root(self, item_payload):
        event = WebhookEvent.from_raw(item_payload)
        assert event.client_id == event.root.client_id

    def test_unknown_event_prefix_raises_value_error(self):
        with pytest.raises(ValueError, match="desconhecido"):
            WebhookEvent.from_raw(
                {
                    "event": "unknown/type",
                    "id": "x",
                    "clientId": "c",
                    "itemId": "i",
                }
            )

    def test_parse_body_from_json_string(self, item_payload):
        import json

        event = WebhookEvent.parse_body(json.dumps(item_payload))
        assert isinstance(event.root, ItemEvent)
