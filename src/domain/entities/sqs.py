from pydantic import BaseModel, ConfigDict

from src.domain.entities.webhook import WebhookEvent


class SQSRecord(BaseModel):
    body: str
    model_config = ConfigDict(extra="ignore")


class SQSEvent(BaseModel):
    Records: list[SQSRecord]
    model_config = ConfigDict(extra="ignore")

    @property
    def events(self) -> list[WebhookEvent]:
        return [WebhookEvent.parse_body(record.body) for record in self.Records]
