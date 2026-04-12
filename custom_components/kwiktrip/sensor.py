"""Fuel price sensors for Kwik Trip."""
from __future__ import annotations

import re
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import KwikTripCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: KwikTripCoordinator = hass.data[DOMAIN][entry.entry_id]
    known: set[tuple[int, str]] = set()

    @callback
    def _add_new_entities() -> None:
        new: list[KwikTripFuelSensor] = []
        for store_id, store in (coordinator.data or {}).items():
            for fuel in store.get("fuel", []) or []:
                fuel_type = fuel.get("type")
                if not fuel_type:
                    continue
                key = (store_id, fuel_type)
                if key in known:
                    continue
                known.add(key)
                new.append(KwikTripFuelSensor(coordinator, store_id, fuel_type))
        if new:
            async_add_entities(new)

    _add_new_entities()
    entry.async_on_unload(coordinator.async_add_listener(_add_new_entities))


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


class KwikTripFuelSensor(CoordinatorEntity[KwikTripCoordinator], SensorEntity):
    """A single fuel price sensor at a single store."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "USD/gal"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:gas-station"
    _attr_suggested_display_precision = 2

    def __init__(
        self,
        coordinator: KwikTripCoordinator,
        store_id: int,
        fuel_type: str,
    ) -> None:
        super().__init__(coordinator)
        self._store_id = store_id
        self._fuel_type = fuel_type
        self._attr_unique_id = f"kwiktrip_{store_id}_{_slugify(fuel_type)}"
        self._attr_name = fuel_type.title()

    @property
    def _store(self) -> dict[str, Any]:
        return (self.coordinator.data or {}).get(self._store_id) or {}

    @property
    def _fuel(self) -> dict[str, Any] | None:
        for fuel in self._store.get("fuel", []) or []:
            if fuel.get("type") == self._fuel_type:
                return fuel
        return None

    @property
    def available(self) -> bool:
        return super().available and self._fuel is not None

    @property
    def native_value(self) -> float | None:
        fuel = self._fuel
        if fuel is None:
            return None
        price = fuel.get("currentPrice")
        if price is None:
            return None
        return int(float(price) * 100) / 100

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        fuel = self._fuel or {}
        return {
            "description": fuel.get("description"),
            "fuel_type": self._fuel_type,
        }

    @property
    def device_info(self) -> DeviceInfo:
        store = self._store
        addr = store.get("address") or {}
        configuration_url = None
        if addr.get("latitude") and addr.get("longitude"):
            configuration_url = (
                f"https://www.google.com/maps/search/?api=1&query="
                f"{addr['latitude']},{addr['longitude']}"
            )
        return DeviceInfo(
            identifiers={(DOMAIN, str(self._store_id))},
            manufacturer=MANUFACTURER,
            model="Kwik Trip Store",
            name=store.get("name") or f"Kwik Trip #{self._store_id}",
            suggested_area=addr.get("city"),
            configuration_url=configuration_url,
            sw_version=None,
            hw_version=str(self._store_id),
            serial_number=str(store.get("storeNumber") or self._store_id),
            entry_type=None,
        )
