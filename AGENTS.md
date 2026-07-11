# Project Instructions

## Home Assistant Custom Component: domino_hub

This is a custom Home Assistant integration for a Domino serial hub that controls covers (awnings/shutters), lights (on/off and dimmers), and reads meteo/temperature sensors via serial communication.

### Key Files

- `dominoService.py` — Serial communication layer (DominoService, Motor, Dimmer, Light, Meteo, RoomTemperature)
- `cover.py` — Cover entities (awnings and shutters)
- `light.py` — Light entities (on/off and dimmers)
- `sensor.py` — Sensor entities (temperature, illuminance, wind, rain)
- `coordinator.py` — DataUpdateCoordinator (currently unused, entities poll independently)
- `__init__.py` — Integration setup, platforms: sensor, light, cover
- `config_flow.py` — Config flow for com port/baud setup

### Home Assistant Instance

- URL: `http://1bs8mxtwoevlqho3.myfritz.net:8123/`
- Long-lived access token: stored in `token.txt`
- API endpoints used:
  - `POST /api/config/automation/config/<id>` — Create/update automation
  - `POST /api/services/automation/reload` — Reload automations
  - `POST /api/services/automation/trigger` — Trigger automation
  - `POST /api/services/automation/toggle` — Enable/disable automation
  - `GET /api/states` — Get all states
  - `GET /api/states/<entity_id>` — Get specific state
  - `POST /api/services/<domain>/<service>` — Call service (e.g., cover.open_cover)

### Automations

- Automations are stored in the `automations/` folder
- YAML format uses `trigger`/`condition`/`action` (singular)
- When creating via API, use `triggers`/`conditions`/`actions` (plural)
- API returns entity_id based on `alias`, not `id` (e.g., alias "Bring Down Covers at Noon" → `automation.bring_down_covers_at_noon`)
- To disable automations at creation, create them then call `automation/toggle` service

### Cover Position Logic

- Awnings: position 0 = closed, 100 = open
- Shutters: position 0 = open, 100 = closed
- `DominoShutterEntity._getOpenPosition()` returns 0, `_getClosePosition()` returns 100
- Covers take ~25-30 seconds to travel fully open to close (or vice versa) — wait at least 30s between open/close and set_position commands

### Shutter Position Mapping (d2 values, from fully open)

d2 is not a target position — it behaves as a speed/duration value. Tested on cover.tapparella_camera_matrimoniale (motor19, num1):

| d2 | d2hex | Result (from fully open) |
|---|---|---|
| 0 | 0x0 | Fully open |
| 10 | 0xa | No movement |
| 11 | 0xb | ~75% closed |
| 12 | 0xc | ~80% closed |
| 13 | 0xd | ~85% closed |
| 14 | 0xe | ~90% closed |
| 15 | 0xf | ~95% closed |
| 16 | 0x10 | ~98% closed |
| 17+ | | Fully closed |

- Roughly ~5% per d2 step in the 12-16 range
- `_setPosition` scales: `d2 = int(pct * 50 / 100)`
- To set 80% closed: d2=12 → pct=24 (position=24 in HA)

### Sensor Entity IDs

- `sensor.external_temperature` — External temperature (°C)
- `sensor.external_illuminance` — External illuminance (lx)
- `sensor.external_rain` — Rain state ("Rain" / "No Rain")
- `sensor.gw1200a_wind_speed` — Wind speed (km/h)
- `sensor.gw1200a_wind_gust` — Wind gust (km/h)

### Cover Entity IDs

- `cover.tenda_cucina`, `cover.tenda_soggiorno`, `cover.tenda_camera_matrimoniale`, `cover.tenda_camera_francesco_sx`, `cover.tenda_camera_francesco_dx` — Awnings
- `cover.tapparella_bagno`, `cover.tapparella_sala_finestra`, `cover.tapparella_cucina`, `cover.tapparella_sala`, `cover.tapparella_camera_matrimoniale`, `cover.tapparella_camera_francesco`, `cover.tapparella_camera_letizia` — Shutters

### Server

- SSH: `openhabian@192.168.1.61`
- Home Assistant config: `/opt/stacks/hass/config/`
- Custom components: `/opt/stacks/hass/config/custom_components/domino_hub/`
- Deployment: `release.sh` copies `.py` and `.json` files to the custom components folder (requires sudo)
- Container: podman, `restart=always` policy set

### Build & Deploy

- Run `./releaseToProd.sh` to deploy changes to the server
- Script SSHes into server, runs `git pull`, then `release.sh`
- `release.sh` uses sudo to copy files to `/opt/stacks/hass/config/custom_components/domino_hub/`
- Server SSH key passphrase is typed interactively via `ssh -t`

### Configuration Backup

- Backup of HA `configuration.yaml` is stored in `config/configuration.yaml`
- The `domino_hub:` YAML block was removed from `configuration.yaml` (integration uses config flow only)
- Sudoers configured for openhabian: `mkdir`, `rm`, `cp`, `ls` (NOPASSWD)

### Known Fixes Applied

- `exchangeMsg()` validates response length ≥6 and raises `DominoCommunicationError` instead of returning None
- `_open_close_lock` (threading.Lock) added around `openCount` and serial port open/close
- `MeteoSensorTemp.update()` validates -20 to +60°C range, skips bad readings, averages only valid values
- `MeteoSensorLux.update()` validates 0–100,000 lx range, skips bad readings, keeps stale value
- `readMessage()` now waits for ≥6 bytes before reading (prevents partial serial responses)
- `async_update()` errors downgraded from ERROR to WARNING (transient serial failures)
- `domino_hub:` YAML block removed from `configuration.yaml`
- Rain sensor state corrected from `"off"` to `"No Rain"`
- `set_cover_position_down` script position changed from 100 to 0
