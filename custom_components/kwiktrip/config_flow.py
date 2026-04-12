"""Config flow for Kwik Trip."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import KwikTripApiError, KwikTripClient
from .const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_MAX_DISTANCE,
    CONF_STORE_IDS,
    DEFAULT_MAX_DISTANCE,
    DOMAIN,
)


class KwikTripConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the Kwik Trip config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._stores: list[dict[str, Any]] = []
        self._search_params: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        default_lat = self.hass.config.latitude
        default_lon = self.hass.config.longitude

        if user_input is not None:
            client = KwikTripClient(async_get_clientsession(self.hass))
            try:
                stores = await client.search_stores(
                    latitude=user_input[CONF_LATITUDE],
                    longitude=user_input[CONF_LONGITUDE],
                    max_distance=user_input[CONF_MAX_DISTANCE],
                )
            except KwikTripApiError:
                errors["base"] = "cannot_connect"
            else:
                if not stores:
                    errors["base"] = "no_stores"
                else:
                    self._stores = stores
                    self._search_params = user_input
                    return await self.async_step_select()

        schema = vol.Schema(
            {
                vol.Required(CONF_LATITUDE, default=default_lat): NumberSelector(
                    NumberSelectorConfig(
                        min=-90, max=90, step=0.0001, mode=NumberSelectorMode.BOX
                    )
                ),
                vol.Required(CONF_LONGITUDE, default=default_lon): NumberSelector(
                    NumberSelectorConfig(
                        min=-180, max=180, step=0.0001, mode=NumberSelectorMode.BOX
                    )
                ),
                vol.Required(
                    CONF_MAX_DISTANCE, default=DEFAULT_MAX_DISTANCE
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1, max=500, step=1, mode=NumberSelectorMode.BOX, unit_of_measurement="mi"
                    )
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_select(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            store_ids = [int(sid) for sid in user_input[CONF_STORE_IDS]]
            if not store_ids:
                errors["base"] = "no_selection"
            else:
                await self.async_set_unique_id(
                    f"kwiktrip-{'-'.join(str(s) for s in sorted(store_ids))}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Kwik Trip ({len(store_ids)} stores)",
                    data={**self._search_params, CONF_STORE_IDS: store_ids},
                )

        options = [
            SelectOptionDict(
                value=str(store["id"]),
                label=_format_store_label(store),
            )
            for store in self._stores
        ]
        schema = vol.Schema(
            {
                vol.Required(CONF_STORE_IDS): SelectSelector(
                    SelectSelectorConfig(
                        options=options,
                        multiple=True,
                        mode=SelectSelectorMode.LIST,
                    )
                ),
            }
        )
        return self.async_show_form(
            step_id="select", data_schema=schema, errors=errors
        )


def _format_store_label(store: dict[str, Any]) -> str:
    name = store.get("name") or f"Kwik Trip #{store.get('id')}"
    addr = store.get("address") or {}
    pieces = [
        addr.get("address1"),
        addr.get("city"),
        addr.get("state"),
    ]
    loc = ", ".join(p for p in pieces if p)
    return f"{name} — {loc}" if loc else name
