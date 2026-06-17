"""Testa parsing do envelope SQS e conversão para WebhookEvents.

Verifica que SQSEvent lida corretamente com o formato real da AWS,
incluindo campos extras que devem ser ignorados.
"""
import json
import pytest
from src.domain.entities.sqs import SQSEvent
from src.domain.entities.webhook import ItemEvent, TransactionsEvent


class TestSQSEventParsing:
    def test_parse_single_record(self, sqs_item_event):
        parsed = SQSEvent.model_validate(sqs_item_event)
        assert len(parsed.Records) == 1

    def test_extra_sqs_fields_are_ignored(self, sqs_item_event):
        parsed = SQSEvent.model_validate(sqs_item_event)
        assert len(parsed.events) == 1

    def test_events_returns_correct_types(self, sqs_item_event):
        events = SQSEvent.model_validate(sqs_item_event).events
        assert isinstance(events[0].root, ItemEvent)

    def test_multiple_records_parsed_independently(self, sqs_multi_event):
        parsed = SQSEvent.model_validate(sqs_multi_event)
        events = parsed.events
        assert len(events) == 2
        assert isinstance(events[0].root, ItemEvent)
        assert isinstance(events[1].root, TransactionsEvent)

    def test_client_id_accessible_from_event(self, sqs_item_event):
        events = SQSEvent.model_validate(sqs_item_event).events
        assert events[0].client_id == "client-xyz"
