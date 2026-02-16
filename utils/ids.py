"""Extract external IDs from Tautulli/Plex metadata."""


def _extract_from_guid_string(s: str, ids: dict) -> None:
    """Fill ids dict from a single guid string (e.g. com.plexapp.agents.themoviedb://12345?lang=en)."""
    if not s or not isinstance(s, str):
        return
    s = s.strip()
    if not ids["tmdb"] and ("themoviedb://" in s or "tmdb://" in s):
        for prefix in ("themoviedb://", "tmdb://"):
            if prefix in s:
                ids["tmdb"] = s.split(prefix)[-1].split("?")[0].split("/")[0]
                break
    if not ids["tvdb"] and ("thetvdb://" in s or "tvdb://" in s):
        for prefix in ("thetvdb://", "tvdb://"):
            if prefix in s:
                ids["tvdb"] = s.split(prefix)[-1].split("?")[0].split("/")[0]
                break
    if not ids["imdb"] and "imdb://" in s:
        ids["imdb"] = s.split("imdb://")[-1].split("?")[0].split("/")[0]
    if not ids["mbid"] and "mbid://" in s:
        ids["mbid"] = s.split("mbid://")[-1].split("?")[0].split("/")[0]


def _deep_find_guids(obj, ids: dict) -> None:
    """Recursively scan dict/list for any string that looks like a Plex guid and extract IDs."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str):
                _extract_from_guid_string(v, ids)
            else:
                _deep_find_guids(v, ids)
    elif isinstance(obj, list):
        for item in obj:
            _deep_find_guids(item, ids)


def extract_ids(metadata: dict | list) -> dict:
    """Pull TMDB, TVDB, IMDB, and MusicBrainz ids out of Tautulli metadata.

    Accepts a dict or list (raw get_metadata response). Recursively scans for
    any string that looks like a Plex guid (themoviedb://, imdb://, etc.).
    """
    ids = {"tmdb": None, "tvdb": None, "imdb": None, "mbid": None}
    if isinstance(metadata, list):
        _deep_find_guids(metadata, ids)
        return ids
    if not isinstance(metadata, dict):
        return ids

    guids = metadata.get("guids") or []
    for g in guids:
        val = g if isinstance(g, str) else g.get("id", "")
        if "tmdb://" in val:
            ids["tmdb"] = val.split("tmdb://")[-1].split("?")[0]
        elif "themoviedb://" in val:
            ids["tmdb"] = val.split("themoviedb://")[-1].split("?")[0]
        elif "tvdb://" in val:
            ids["tvdb"] = val.split("tvdb://")[-1].split("?")[0]
        elif "thetvdb://" in val:
            ids["tvdb"] = val.split("thetvdb://")[-1].split("?")[0]
        elif "imdb://" in val:
            ids["imdb"] = val.split("imdb://")[-1].split("?")[0]
        elif "mbid://" in val:
            ids["mbid"] = val.split("mbid://")[-1].split("?")[0]

    # Fallback: legacy Plex agent guid stored at the top level
    top_guid = metadata.get("guid", "") or metadata.get("grandparent_guid", "")
    if top_guid:
        if not ids["imdb"] and "imdb://" in top_guid:
            ids["imdb"] = top_guid.split("imdb://")[-1].split("?")[0]
        if not ids["tmdb"] and "themoviedb://" in top_guid:
            ids["tmdb"] = top_guid.split("themoviedb://")[-1].split("?")[0]
        if not ids["tvdb"] and "thetvdb://" in top_guid:
            ids["tvdb"] = top_guid.split("thetvdb://")[-1].split("/")[0].split("?")[0]

    # Fallback: direct ID fields (Tautulli/Plex sometimes expose these)
    def _str_id(val):
        if val is None:
            return None
        s = str(val).strip()
        return s if s else None

    if not ids["tmdb"]:
        ids["tmdb"] = _str_id(metadata.get("tmdb_id") or metadata.get("themoviedb_id"))
    if not ids["tvdb"]:
        ids["tvdb"] = _str_id(metadata.get("tvdb_id") or metadata.get("thetvdb_id"))
    if not ids["imdb"]:
        ids["imdb"] = _str_id(metadata.get("imdb_id"))
    if not ids["mbid"]:
        ids["mbid"] = _str_id(metadata.get("mbid") or metadata.get("musicbrainz_id"))

    # Last resort: recursively scan entire structure for any guid-like string
    _deep_find_guids(metadata, ids)

    return ids
