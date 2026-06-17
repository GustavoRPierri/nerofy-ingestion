import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)
_KEY_TTL_HOURS = 23


class PluggyAuthService:
    def __init__(self, http_session, repository, client_id: str, client_secret: str):
        self._http = http_session
        self._repo = repository
        self._client_id = client_id
        self._client_secret = client_secret
        self._api_key: str | None = None
        self._expires_at: datetime | None = None

    async def get_valid_api_key(self) -> str:
        # Layer 1: in-memory cache
        if self._api_key and self._expires_at and datetime.now(timezone.utc) < self._expires_at:
            logger.debug("Auth: cache em memória válido")
            return self._api_key

        # Layer 2: DynamoDB cache
        cached = await self._repo.get_auth_cache(self._client_id)
        if cached:
            expires_at = datetime.fromisoformat(cached["expiresAt"]).replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) < expires_at:
                logger.debug("Auth: cache DynamoDB válido")
                self._api_key = cached["apiKey"]
                self._expires_at = expires_at
                return self._api_key

        # Layer 3: call Pluggy API
        return await self._refresh_api_key()

    async def _refresh_api_key(self) -> str:
        logger.info("Auth: buscando novo api_key da Pluggy")
        data = await self._http.post(
            "https://api.pluggy.ai/auth",
            payload={"clientId": self._client_id, "clientSecret": self._client_secret},
        )
        api_key = data["apiKey"]
        expires_at = datetime.now(timezone.utc) + timedelta(hours=_KEY_TTL_HOURS)

        self._api_key = api_key
        self._expires_at = expires_at

        await self._repo.save_auth_cache(self._client_id, api_key, expires_at)
        return api_key
