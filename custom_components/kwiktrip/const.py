"""Constants for the Kwik Trip integration."""
from __future__ import annotations

from datetime import timedelta

DOMAIN = "kwiktrip"
MANUFACTURER = "Kwik Trip"

CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_MAX_DISTANCE = "max_distance"
CONF_STORE_IDS = "store_ids"

DEFAULT_MAX_DISTANCE = 10
DEFAULT_SEARCH_LIMIT = 100
DEFAULT_SCAN_INTERVAL = timedelta(minutes=30)

SEARCH_URL = "https://www.kwiktrip.com/locproxy.php"
