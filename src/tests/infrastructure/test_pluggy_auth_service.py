"""Testa as 3 camadas de cache do PluggyAuthService.

Layer 1 → memória
Layer 2 → DynamoDB (via AuthRepository mockado)
Layer 3 → Pluggy API (via HttpSession mockado)
"""
import asyncio
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock

from src.infrastructure.auth.pluggy_auth_service import PluggyAuthService

FUTURE = datetime.now(timezone.utc) + timedelta(hours=22)
PAST   = datetime.now(timezone.utc) - timedelta(hours=1)


def make_service(
    memory_key=None,
    memory_exp=None,
    dynamo_item=None,
    api_response_key="api-fresh-key",
):
    http = AsyncMock()
    http.post = AsyncMock(return_value={"apiKey": api_response_key})

    repo = AsyncMock()
    repo.get_auth_cache = AsyncMock(return_value=dynamo_item)
    repo.save_auth_cache = AsyncMock()

    svc = PluggyAuthService(http, repo, client_id="client-id", client_secret="secret")
    if memory_key:
        svc._api_key = memory_key
        svc._expires_at = memory_exp
    return svc, http, repo


def run(coro):
    return asyncio.run(coro)


class TestMemoryCache:
    def test_returns_cached_key_without_any_external_call(self):
        svc, http, repo = make_service(memory_key="mem-key", memory_exp=FUTURE)
        key = run(svc.get_valid_api_key())
        assert key == "mem-key"
        http.post.assert_not_called()
        repo.get_auth_cache.assert_not_called()

    def test_expired_memory_falls_through_to_dynamo(self):
        svc, http, repo = make_service(
            memory_key="expired-key",
            memory_exp=PAST,
            dynamo_item={"apiKey": "dynamo-key", "expiresAt": FUTURE.isoformat()},
        )
        key = run(svc.get_valid_api_key())
        assert key == "dynamo-key"
        repo.get_auth_cache.assert_called_once()


class TestDynamoCache:
    def test_returns_dynamo_key_without_api_call(self):
        dynamo_item = {"apiKey": "dynamo-key", "expiresAt": FUTURE.isoformat()}
        svc, http, repo = make_service(dynamo_item=dynamo_item)
        key = run(svc.get_valid_api_key())
        assert key == "dynamo-key"
        http.post.assert_not_called()

    def test_expired_dynamo_falls_through_to_api(self):
        dynamo_item = {"apiKey": "old-key", "expiresAt": PAST.isoformat()}
        svc, http, repo = make_service(dynamo_item=dynamo_item)
        key = run(svc.get_valid_api_key())
        assert key == "api-fresh-key"
        http.post.assert_called_once()

    def test_missing_dynamo_falls_through_to_api(self):
        svc, http, repo = make_service(dynamo_item=None)
        key = run(svc.get_valid_api_key())
        assert key == "api-fresh-key"
        http.post.assert_called_once()


class TestApiRefresh:
    def test_api_key_persisted_to_dynamo_after_refresh(self):
        svc, http, repo = make_service()
        run(svc.get_valid_api_key())
        repo.save_auth_cache.assert_called_once()
        args = repo.save_auth_cache.call_args.args
        assert args[0] == "client-id"
        assert args[1] == "api-fresh-key"

    def test_api_key_cached_in_memory_after_refresh(self):
        svc, http, repo = make_service()
        run(svc.get_valid_api_key())
        assert svc._api_key == "api-fresh-key"
        assert svc._expires_at is not None

    def test_second_call_uses_memory_after_refresh(self):
        svc, http, repo = make_service()
        run(svc.get_valid_api_key())
        run(svc.get_valid_api_key())
        # API deve ser chamada apenas uma vez
        assert http.post.call_count == 1
