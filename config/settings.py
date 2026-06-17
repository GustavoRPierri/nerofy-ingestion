import logging
import os

import boto3
from botocore.exceptions import ClientError
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _fetch_ssm(param_name: str) -> str:
    try:
        response = boto3.client("ssm").get_parameter(Name=param_name, WithDecryption=True)
        return response["Parameter"]["Value"]
    except ClientError as e:
        raise RuntimeError(f"Erro ao buscar parâmetro SSM '{param_name}': {e}") from e


class Settings(BaseSettings):
    aws_region: str = Field(default="sa-east-1", alias="AWS_REGION")
    s3_bronze_bucket: str = Field(default="", alias="S3_BRONZE_BUCKET")
    dynamo_auth_table: str = Field(default="PluggyAuth", alias="DYNAMO_AUTH_TABLE")
    dynamo_sync_table: str = Field(default="PluggyTransactionSync", alias="DYNAMO_SYNC_TABLE")
    pluggy_client_secret: str = Field(default="", alias="PLUGGY_CLIENT_SECRET")
    pluggy_api_url: str = Field(default="https://api.pluggy.ai", alias="PLUGGY_API_URL")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    env: str = Field(default="dev", alias="ENV")
    ssm_pluggy_secret_path: str = Field(default="", alias="SSM_PLUGGY_SECRET_PATH")
    execucao: str = Field(default="aws", alias="EXECUCAO")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def _resolve_secrets(self) -> "Settings":
        if self.execucao.lower() in ("local", "mock"):
            return self
        if not self.pluggy_client_secret:
            if not self.ssm_pluggy_secret_path:
                raise ValueError("Defina PLUGGY_CLIENT_SECRET ou SSM_PLUGGY_SECRET_PATH.")
            self.pluggy_client_secret = _fetch_ssm(self.ssm_pluggy_secret_path)
        return self

    @field_validator("log_level")
    @classmethod
    def _normalize_log_level(cls, v: str) -> str:
        return v.upper()

    def setup_logging(self) -> None:
        logging.basicConfig(
            level=getattr(logging, self.log_level),
            format="%(levelname)s | %(name)s | %(message)s",
            force=True,
        )


settings = Settings()
