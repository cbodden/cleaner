"""Plex Media Server API client (optional). Used to refresh library after Radarr deletes files."""

import requests

from config import PLEX_TOKEN, PLEX_URL


def plex_refresh_library(section_id: str) -> bool:
    """Trigger a library refresh in Plex for a specific section.

    Calls GET /library/sections/{section_id}/refresh?X-Plex-Token={token} to force Plex to scan for changes.
    After Radarr/Sonarr/Lidarr delete files, this makes Plex detect the deletions.
    
    Reference: https://www.plexopedia.com/plex-media-server/api/library/scan-single/
    
    Returns True on success (HTTP 200), False if Plex URL/token not configured.
    Raises requests.RequestException on HTTP errors.
    """
    if not PLEX_URL or not PLEX_TOKEN:
        return False
    # Ensure PLEX_URL doesn't have trailing slash
    base_url = PLEX_URL.rstrip('/')
    url = f"{base_url}/library/sections/{section_id}/refresh"
    r = requests.get(
        url,
        params={"X-Plex-Token": PLEX_TOKEN},
        timeout=30,
    )
    r.raise_for_status()
    return True
