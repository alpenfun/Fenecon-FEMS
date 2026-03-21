"""REST client for FEMS."""

from __future__ import annotations

from typing import Any

import aiohttp


class FemsRestApi:
    """Simple async REST client for FEMS."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        session: aiohttp.ClientSession,
    ) -> None:
        self._host = host
        self._port = port
        self._session = session
        self._auth = aiohttp.BasicAuth(username, password)

    def _url(self, channel_group: str) -> str:
        return f"http://{self._host}:{self._port}/rest/channel/{channel_group}"

    async def async_fetch_group(self, channel_group: str) -> dict[str, Any]:
        """Fetch one grouped channel endpoint and map address -> value."""
        async with self._session.get(
            self._url(channel_group),
            auth=self._auth,
        ) as response:
            response.raise_for_status()
            payload = await response.json()

        result: dict[str, Any] = {}
        for item in payload:
            address = item.get("address")
            value = item.get("value")
            if address is not None:
                result[address] = value
        return result