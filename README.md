# Kwik Trip — Home Assistant integration

Scrapes gas prices from Kwik Trip's public location proxy and exposes a sensor per fuel type per selected store.

## Install (HACS)

1. HACS → three-dot menu → **Custom repositories** → add this repo as an **Integration**.
2. Install **Kwik Trip**, restart Home Assistant.
3. Settings → Devices & services → **Add integration** → *Kwik Trip*.
4. Step 1 — confirm lat/long (defaults to your HA location) and a max distance.
5. Step 2 — select one or more stores from the search results.

A device is created per store. Each available fuel type becomes its own sensor (price in USD/gal). Disable the ones you don't care about in the entity registry.

Data refreshes every 30 minutes.
