# Media Cleaner

**Version 1.2.0** — A web app that shows your Tautulli library sorted by last played and lets you bulk-remove items from **Seerr**, **Radarr**, **Sonarr**, **Lidarr**, and **Tautulli** in one click.

## Screenshot

<p align="center">
  <img src="images/screenshot.jpg" width="600" />
</p>

## What it does

1. Pulls library media from **Tautulli**, sorted by last played (oldest first)
2. Click any column header to sort by title, year, added date, last played, play count, size, or requested by
3. Shows the **Seerr requestor** for each item when available
4. Select one or more items and hit **Remove Selected**
5. For each item the app will:
   - Remove the request and clear media data in **Seerr**
   - Delete the movie/show/artist (and files on disk) from all configured **Radarr**, **Sonarr**, or **Lidarr** instances
   - Purge play history and media cache from **Tautulli**

Items whose Plex metadata can no longer be resolved (e.g. removed from Plex but still cached in Tautulli) will still have their Tautulli history and cache cleaned up — the Seerr and *arr steps are gracefully skipped.

## Setup

```bash
cd cleaner

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your API keys and URLs
```

### Environment variables

| Variable | Description |
|---|---|
| `DEBUG` | Set to `true` for development (Flask dev server, `/api/debug` routes enabled). Default `false` (production WSGI). |
| `STAT` | Set to `true` to enable the `/api/status` connectivity endpoint. Default `true`. |
| `TAUTULLI_URL` | Tautulli base URL (e.g. `http://localhost:8181`) |
| `TAUTULLI_API_KEY` | Tautulli API key (Settings > Web Interface) |
| `OVERSEERR_URL` | Seerr base URL (e.g. `http://localhost:5055`) |
| `OVERSEERR_API_KEY` | Seerr API key (Settings > General) |
| `RADARR_1_URL` | Primary Radarr base URL |
| `RADARR_1_API_KEY` | Primary Radarr API key |
| `RADARR_1_NAME` | Display name (e.g. `Radarr`) |
| `RADARR_2_URL` | Secondary Radarr base URL (leave blank to disable) |
| `RADARR_2_API_KEY` | Secondary Radarr API key |
| `RADARR_2_NAME` | Display name (e.g. `Radarr 4K`) |
| `SONARR_1_URL` | Primary Sonarr base URL |
| `SONARR_1_API_KEY` | Primary Sonarr API key |
| `SONARR_1_NAME` | Display name (e.g. `Sonarr`) |
| `SONARR_2_URL` | Secondary Sonarr base URL (leave blank to disable) |
| `SONARR_2_API_KEY` | Secondary Sonarr API key |
| `SONARR_2_NAME` | Display name (e.g. `Sonarr 4K`) |
| `LIDARR_1_URL` | Primary Lidarr base URL |
| `LIDARR_1_API_KEY` | Primary Lidarr API key |
| `LIDARR_1_NAME` | Display name (e.g. `Lidarr`) |
| `LIDARR_2_URL` | Secondary Lidarr base URL (leave blank to disable) |
| `LIDARR_2_API_KEY` | Secondary Lidarr API key |
| `LIDARR_2_NAME` | Display name (e.g. `Lidarr 4K`) |

Leave any `_URL` blank to skip that instance.

## Run

### Standalone

- **Production (default):** With `DEBUG` unset or `false`, `python app.py` runs **gunicorn** (production WSGI) on port 5000.
- **Development:** Set `DEBUG=true` in `.env`, then `python app.py` runs the Flask dev server with reload.

You can also run gunicorn directly:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:application
```

### Docker

The image runs **gunicorn** inside the container (no Flask dev server). Set `DEBUG` and `STAT` in the compose file or env as needed.

```bash
cd docker

# Edit docker-compose.yaml with your API keys and URLs
docker compose up -d
```

Open **http://localhost:5000** in your browser.

## Usage

1. Select a library from the dropdown and click **Load**
2. Items are sorted by last played (oldest first) — stale content floats to the top
3. The **Requested By** column shows who originally requested the item in Seerr
4. Check the items you want to remove
5. Click **Remove Selected**, confirm, and the app handles the rest

The library type (`movie` vs `show` vs `artist`) determines whether Radarr, Sonarr, or Lidarr instances are used for deletion. Seerr removal is skipped for music libraries since Seerr does not manage music requests.

## License

MIT
