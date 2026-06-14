"""Client for the Kwik Trip locproxy endpoint."""
from __future__ import annotations

import json
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
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.kwiktrip.com/",
        }
        try:
            async with self._session.get(
                SEARCH_URL,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                resp.raise_for_status()
                text = await resp.text()
        except aiohttp.ClientError as err:
            raise KwikTripApiError(str(err)) from err
        try:
            return json.loads(text.lstrip("\ufeff"))
        except ValueError as err:
            snippet = text[:200].replace("\n", " ")
            raise KwikTripApiError(
                f"Non-JSON response from Kwik Trip: {snippet!r}"
            ) from err
