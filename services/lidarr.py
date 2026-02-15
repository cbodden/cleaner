"""Lidarr API client (multi-instance)."""
import requests


def lidarr_find_artist(instance: dict, mbid) -> dict | None:
    """Find an artist in a Lidarr instance by MusicBrainz artist id."""
    r = requests.get(
        f"{instance['url']}/api/v1/artist",
        params={"apikey": instance["api_key"]},
        timeout=30,
    )
    r.raise_for_status()
    for a in r.json():
        if a.get("foreignArtistId") == str(mbid):
            return a
    return None


def lidarr_delete_artist(instance: dict, artist_id, delete_files: bool = True) -> bool:
    """Delete an artist from a Lidarr instance."""
    r = requests.delete(
        f"{instance['url']}/api/v1/artist/{artist_id}",
        params={
            "apikey": instance["api_key"],
            "deleteFiles": str(delete_files).lower(),
            "addImportListExclusion": "false",
        },
        timeout=15,
    )
    r.raise_for_status()
    return True
