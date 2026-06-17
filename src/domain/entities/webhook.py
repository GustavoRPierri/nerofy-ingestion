import json
from typing import ClassVar
from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator


class BaseEvent(BaseModel):
    event: str
    event_id: str = Field(alias="id")
    client_id: str = Field(alias="clientId")
    item_id: str | None = Field(default=None, alias="itemId")

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class ItemEvent(BaseEvent):
    VALID_EVENTS: ClassVar[list[str]] = [
        "item/updated",
        "item/error",
        "item/waiting_user_action",
        "item/login_succeeded",
    ]
    item_id: str = Field(alias="itemId")


class TransactionsEvent(BaseEvent):
    VALID_EVENTS: ClassVar[list[str]] = [
        "transactions/created",
        "transactions/deleted",
        "transactions/updated",
    ]
    item_id: str = Field(alias="itemId")
    account_id: str = Field(default="", alias="accountId")

    @model_validator(mode="before")
    @classmethod
    def _extract_data(cls, values):
        if isinstance(values, dict) and "data" in values:
            data = values.get("data") or {}
            if isinstance(data, dict) and "accountId" in data:
                values = {**values, "accountId": data["accountId"]}
        return values


class ConnectorEvent(BaseEvent):
    VALID_EVENTS: ClassVar[list[str]] = [
        "connector/created",
        "connector/updated",
    ]
    connector_id: int = Field(default=0, alias="connectorId")

    @model_validator(mode="before")
    @classmethod
    def _extract_data(cls, values):
        if isinstance(values, dict) and "data" in values:
            data = values.get("data") or {}
            if isinstance(data, dict) and "connectorId" in data:
                values = {**values, "connectorId": data["connectorId"]}
        return values


_PREFIX_MAP = {
    "item": ItemEvent,
    "transactions": TransactionsEvent,
    "connector": ConnectorEvent,
}


class WebhookEvent(RootModel[ItemEvent | TransactionsEvent | ConnectorEvent]):

    @classmethod
    def from_raw(cls, data: dict) -> "WebhookEvent":
        event_str = data.get("event", "")
        prefix = event_str.split("/")[0] if "/" in event_str else event_str
        model_cls = _PREFIX_MAP.get(prefix)
        if model_cls is None:
            raise ValueError(f"Tipo de evento desconhecido: {event_str!r}")
        return cls(root=model_cls.model_validate(data))

    @classmethod
    def parse_body(cls, body: str) -> "WebhookEvent":
        return cls.from_raw(json.loads(body))

    @property
    def client_id(self) -> str:
        return self.root.client_id
