"""Client for the Kwik Trip locproxy endpoint."""
from __future__ import annotations

from typing import Any

import aiohttp

from .const import DEFAULT_SEARCH_LIMIT, SEARCH_URL


class KwikTripApiError(Exception):
    """Raised when the locproxy endpoint returns an error."""


class KwikTripClient:
    """Thin async client for the locproxy endpoint."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def search_stores(
        self,
        latitude: float,
        longitude: float,
        max_distance: float,
        limit: int = DEFAULT_SEARCH_LIMIT,
    ) -> list[dict[str, Any]]:
        params = {
            "Latitude": latitude,
            "Longitude": longitude,
            "maxDistance": max_distance,
            "limit": limit,
        }
        data = await self._get(params)
        return data.get("stores", []) if isinstance(data, dict) else []

    async def get_store(self, store_id: int | str) -> dict[str, Any]:
        data = await self._get({"location": store_id})
        if not isinstance(data, dict):
            raise KwikTripApiError(f"Unexpected response for store {store_id}")
        return data

    async def _get(self, params: dict[str, Any]) -> Any:
        try:
            async with self._session.get(SEARCH_URL, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                resp.raise_for_status()
                return await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise KwikTripApiError(str(err)) from err
