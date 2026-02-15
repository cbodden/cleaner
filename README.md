# Media Cleaner

A web app that shows your Tautulli library sorted by last played and lets you bulk-remove items from **Overseerr**, **Radarr**, **Sonarr**, and **Tautulli** in one click.

## What it does

1. Pulls library media from **Tautulli**, sorted by last played (oldest first)
2. Shows the **Overseerr requestor** for each item when available
3. Select one or more items and hit **Remove Selected**
4. For each item the app will:
   - Remove the request and clear media data in **Overseerr**
   - Delete the movie/show (and files on disk) from all configured **Radarr** or **Sonarr** instances
   - Purge play history and media cache from **Tautulli**

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
| `TAUTULLI_URL` | Tautulli base URL (e.g. `http://localhost:8181`) |
| `TAUTULLI_API_KEY` | Tautulli API key (Settings > Web Interface) |
| `OVERSEERR_URL` | Overseerr base URL (e.g. `http://localhost:5055`) |
| `OVERSEERR_API_KEY` | Overseerr API key (Settings > General) |
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

Leave any `_URL` blank to skip that instance.

## Run

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

## Usage

1. Select a library from the dropdown and click **Load**
2. Items are sorted by last played (oldest first) — stale content floats to the top
3. The **Requested By** column shows who originally requested the item in Overseerr
4. Check the items you want to remove
5. Click **Remove Selected**, confirm, and the app handles the rest

The library type (`movie` vs `show`) determines whether Radarr or Sonarr instances are used for deletion.

## License

MIT
