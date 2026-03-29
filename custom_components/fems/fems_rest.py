# custom_components/fems/fems_rest.py
"""REST client for FEMS."""

from __future__ import annotations

import json
import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class FemsRestApi:
    """Robust async REST client for FEMS."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize REST API client."""
        self._host = host
        self._port = port
        self._session = session
        self._auth = aiohttp.BasicAuth(username, password)

    def _url(self, channel_group: str) -> str:
        """Build endpoint URL."""
        return f"http://{self._host}:{self._port}/rest/channel/{channel_group}"

    async def async_fetch_group(self, channel_group: str) -> dict[str, Any]:
        """Fetch one grouped channel endpoint and map address -> value."""
        url = self._url(channel_group)

        async with self._session.get(
            url,
            auth=self._auth,
        ) as response:
            status = response.status
            content_type = response.headers.get("Content-Type", "")
            text = await response.text()

            _LOGGER.debug(
                "FEMS REST response | group=%s | status=%s | content_type=%s | body=%s",
                channel_group,
                status,
                content_type,
                text[:1000],
            )

            response.raise_for_status()

        payload = self._parse_payload(channel_group, text)

        result: dict[str, Any] = {}

        if isinstance(payload, list):
            for item in payload:
                if not isinstance(item, dict):
                    _LOGGER.warning(
                        "FEMS REST %s: unexpected list item type: %r",
                        channel_group,
                        item,
                    )
                    continue

                address = item.get("address")
                value = item.get("value")

                if address is not None:
                    result[str(address)] = value
                else:
                    _LOGGER.warning(
                        "FEMS REST %s: item without address: %r",
                        channel_group,
                        item,
                    )

        elif isinstance(payload, dict):
            if "address" in payload and "value" in payload:
                result[str(payload["address"])] = payload.get("value")
            else:
                _LOGGER.warning(
                    "FEMS REST %s: JSON object received instead of list: %r",
                    channel_group,
                    payload,
                )
        else:
            _LOGGER.warning(
                "FEMS REST %s: unsupported payload type %s",
                channel_group,
                type(payload).__name__,
            )

        _LOGGER.debug(
            "FEMS REST parsed %s entries for %s",
            len(result),
            channel_group,
        )

        return result

    def _parse_payload(self, channel_group: str, text: str) -> Any:
        """Parse JSON payload robustly, even with wrong content type."""
        cleaned = text.strip()

        if not cleaned:
            _LOGGER.warning("FEMS REST %s: empty response body", channel_group)
            return []

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as err:
            _LOGGER.error(
                "FEMS REST %s: invalid JSON: %s | body=%s",
                channel_group,
                err,
                cleaned[:2000],
            )
            raise
