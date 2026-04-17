# Kwik Trip — Home Assistant integration

A [HACS](https://hacs.xyz/)-compatible custom integration that pulls live fuel
prices from Kwik Trip's public store locator endpoint and exposes them as
Home Assistant sensors.

> Not affiliated with Kwik Trip, Inc. This integration consumes a public,
> unauthenticated endpoint used by the kwiktrip.com store locator. If Kwik
> Trip changes or restricts that endpoint, this integration will break.

## What you get

- One **device** per selected store (named `KWIK TRIP #1140`, etc.), with its
  store number used as the device serial/hardware ID and a Google Maps link
  as the device's configuration URL.
- One **sensor per fuel type per store**, e.g.:
  - `sensor.kwik_trip_1140_unleaded_87_10_eth`
  - `sensor.kwik_trip_1140_unleaded_premium`
  - `sensor.kwik_trip_1140_diesel_2`
  - `sensor.kwik_trip_1140_e_85`
  - `sensor.kwik_trip_1140_diesel_exhaust_fluid`
- Prices in USD/gal, truncated to 2 decimals (Kwik Trip publishes prices like
  `4.999` — the trailing `.9` is dropped rather than rounded, so you see
  `4.99`).
- The description Kwik Trip uses internally (e.g. `UNL OXY 87-10E`) is
  available as a state attribute on each sensor.

Polling interval: **30 minutes**. If a given store's request fails, the last
successful value is retained until the next poll.

## Install

### Via HACS (recommended)

1. HACS → three-dot menu → **Custom repositories** → add
   `https://github.com/CornHead764/ha-kwiktrip` as an **Integration**.
2. Install **Kwik Trip** from HACS.
3. Restart Home Assistant.
4. Settings → Devices & services → **Add integration** → *Kwik Trip*.

### Manual

Copy `custom_components/kwiktrip/` into your HA `config/custom_components/`
directory and restart.

## Configuration (UI only)

The integration is configured entirely through the UI — nothing goes in
`configuration.yaml`.

### Step 1 — Search

| Field         | Default                       | Notes                                |
| ------------- | ----------------------------- | ------------------------------------ |
| Latitude      | Home Assistant's lat          | Any latitude is accepted.            |
| Longitude     | Home Assistant's long         | Any longitude is accepted.           |
| Max distance  | 10 miles                      | The endpoint uses miles; range 1–500.|

Submitting runs a search against the Kwik Trip locator. If no stores are
found inside the radius you'll get a friendly error and can adjust the
distance.

### Step 2 — Select stores

A multi-select list is shown with every store returned by the search
(labelled `NAME — ADDRESS, CITY, STATE`). Pick one or more and submit —
the integration creates one config entry covering all of them.

You can run the flow again to create a second entry for another set of
stores (e.g. "home stores" vs. "work stores" vs. "trip stores").

### Turning sensors on/off

There's no per-fuel toggle in config because HA already has one: use the
entity registry (Settings → Devices & services → Entities) to **disable** any
fuel sensors you don't care about. Disabled sensors aren't polled into the
state machine or recorder.

## How the endpoint works

Kwik Trip's site uses a single PHP proxy — `/locproxy.php` — for both geo
search and per-store detail. It returns JSON (prefixed with a UTF-8 BOM).

### Geo search

```
GET https://www.kwiktrip.com/locproxy.php
    ?Latitude=43.0334
    &Longitude=-89.4512
    &maxDistance=10
    &limit=100
```

Returns `{ "stores": [ ... ] }`. Each store includes `id`, `name`, `address`,
`latitude`, `longitude`, `phone`, `open24Hours`, delivery/carryout/curbside
flags, and a `properties` array describing site features (ATM, car wash,
CNG, E-85, diesel, etc.) — but **no fuel prices**. This endpoint is used
only during setup to build the "select stores" list.

### Per-store detail

```
GET https://www.kwiktrip.com/locproxy.php?location=1140
```

Returns a single store object with the fields above **plus** a `fuel` array:

```json
"fuel": [
  { "type": "UNLEADED 87 (10% ETH)", "description": "UNL OXY 87-10E",  "currentPrice": 3.899 },
  { "type": "UNLEADED PREMIUM",      "description": "PREMIUM UNL 91",  "currentPrice": 5.099 },
  { "type": "E-85",                  "description": "E-80 (80% E - 20% V)", "currentPrice": 2.999 },
  { "type": "UNLEADED 88",           "description": "UNL OXY 88-15E",  "currentPrice": 3.749 },
  { "type": "DIESEL #2",             "description": "#2 ULSD CLEAR",   "currentPrice": 4.999 },
  { "type": "PREMIUM DIESEL",        "description": "#2 ULSD PREMIUM", "currentPrice": 5.199 },
  { "type": "DIESEL EXHAUST FLUID",  "description": "DIESEL EXHAUST FLUID", "currentPrice": 3.989 }
]
```

This is the endpoint the integration polls every 30 minutes — one request
per selected store, in parallel.

### Quirks the integration handles

- **UTF-8 BOM.** Responses start with `\ufeff`, so `resp.json()` fails with
  `orjson.JSONDecodeError: unexpected character`. The integration reads the
  body as text, strips the BOM, and parses manually.
- **User-Agent gating.** Without a browser-shaped `User-Agent` (and a
  `Referer: https://www.kwiktrip.com/`), some responses come back as HTML
  instead of JSON. The integration sends both headers on every request.
- **Fuel availability varies by store.** Not every Kwik Trip sells E-85,
  diesel, premium, or DEF. The sensor list is built dynamically from what
  each store actually returns, and a new sensor is added automatically if a
  store starts selling a new fuel type later.

## Repository layout

```
custom_components/kwiktrip/
├── __init__.py          # setup/unload, registers the coordinator
├── api.py               # async client for locproxy.php
├── config_flow.py       # two-step UI flow (search → select)
├── const.py             # domain + defaults
├── coordinator.py       # DataUpdateCoordinator, per-store parallel fetch
├── manifest.json
├── sensor.py            # one sensor per fuel type per store
├── strings.json
└── translations/
    └── en.json
hacs.json
```

## License / disclaimer

No warranty. You're scraping a third-party endpoint; be respectful with
poll frequency. 30 minutes is conservative; don't shorten it without good
reason.
