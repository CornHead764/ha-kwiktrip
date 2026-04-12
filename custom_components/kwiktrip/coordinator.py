"""DataUpdateCoordinator for Kwik Trip."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import KwikTripApiError, KwikTripClient
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class KwikTripCoordinator(DataUpdateCoordinator[dict[int, dict[str, Any]]]):
    """Fetch data for each selected store."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: KwikTripClient,
        store_ids: list[int],
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.client = client
        self.store_ids = store_ids

    async def _async_update_data(self) -> dict[int, dict[str, Any]]:
        try:
            results = await asyncio.gather(
                *(self.client.get_store(sid) for sid in self.store_ids),
                return_exceptions=True,
            )
        except KwikTripApiError as err:
            raise UpdateFailed(str(err)) from err

        data: dict[int, dict[str, Any]] = {}
        for sid, result in zip(self.store_ids, results):
            if isinstance(result, Exception):
                _LOGGER.warning("Failed to fetch store %s: %s", sid, result)
                if self.data and sid in self.data:
                    data[sid] = self.data[sid]
                continue
            data[sid] = result
        if not data:
            raise UpdateFailed("No store data could be fetched")
        return data
