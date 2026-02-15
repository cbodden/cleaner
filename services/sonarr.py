"""Sonarr API client (multi-instance)."""
import requests


def sonarr_find_series(instance: dict, tvdb_id) -> dict | None:
    """Find a series in a Sonarr instance by its TVDB id."""
    r = requests.get(
        f"{instance['url']}/api/v3/series",
        params={"apikey": instance["api_key"], "tvdbId": tvdb_id},
        timeout=15,
    )
    r.raise_for_status()
    series = r.json()
    if isinstance(series, list) and series:
        return series[0]
    return None


def sonarr_find_series_by_tmdb(instance: dict, tmdb_id) -> dict | None:
    """Fallback: find series by iterating all series and matching tmdbId."""
    r = requests.get(
        f"{instance['url']}/api/v3/series",
        params={"apikey": instance["api_key"]},
        timeout=30,
    )
    r.raise_for_status()
    for s in r.json():
        if str(s.get("tmdbId", "")) == str(tmdb_id):
            return s
    return None


def sonarr_delete_series(instance: dict, series_id, delete_files: bool = True) -> bool:
    """Delete a series from a Sonarr instance."""
    r = requests.delete(
        f"{instance['url']}/api/v3/series/{series_id}",
        params={
            "apikey": instance["api_key"],
            "deleteFiles": str(delete_files).lower(),
            "addImportExclusion": "false",
        },
        timeout=15,
    )
    r.raise_for_status()
    return True
