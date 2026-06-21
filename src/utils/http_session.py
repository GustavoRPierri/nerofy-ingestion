import logging

from aiohttp import ClientResponseError, ClientSession, TCPConnector

logger = logging.getLogger(__name__)


class HttpSession:
    def __init__(self):
        self._session: ClientSession | None = None

    async def _get_session(self) -> ClientSession:
        if self._session is None or self._session.closed:
            connector = TCPConnector(limit=10, keepalive_timeout=30)
            self._session = ClientSession(connector=connector)
        return self._session

    async def get(self, url: str, headers: dict | None = None) -> dict:
        session = await self._get_session()
        try:
            async with session.get(url, headers=headers) as resp:
                resp.raise_for_status()
                return await resp.json()
        except ClientResponseError as e:
            logger.error("GET %s falhou com status %s: %s", url, e.status, e.message)
            raise

    async def post(self, url: str, payload: dict, headers: dict | None = None) -> dict:
        session = await self._get_session()
        try:
            async with session.post(url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                return await resp.json()
        except ClientResponseError as e:
            logger.error("POST %s falhou com status %s: %s", url, e.status, e.message)
            raise

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
