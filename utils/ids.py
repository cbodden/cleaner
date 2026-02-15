"""Extract external IDs from Tautulli/Plex metadata."""


def extract_ids(metadata: dict) -> dict:
    """Pull TMDB, TVDB, IMDB, and MusicBrainz ids out of Tautulli metadata guids list.

    Also checks top-level metadata fields (e.g. ``guid``) as a fallback for
    older Plex agent formats like ``com.plexapp.agents.imdb://tt1234567``.
    """
    guids = metadata.get("guids") or []
    ids = {"tmdb": None, "tvdb": None, "imdb": None, "mbid": None}

    for g in guids:
        val = g if isinstance(g, str) else g.get("id", "")
        if "tmdb://" in val:
            ids["tmdb"] = val.split("tmdb://")[-1].split("?")[0]
        elif "tvdb://" in val:
            ids["tvdb"] = val.split("tvdb://")[-1].split("?")[0]
        elif "imdb://" in val:
            ids["imdb"] = val.split("imdb://")[-1].split("?")[0]
        elif "mbid://" in val:
            ids["mbid"] = val.split("mbid://")[-1].split("?")[0]

    # Fallback: legacy Plex agent guid stored at the top level
    top_guid = metadata.get("guid", "")
    if top_guid:
        if not ids["imdb"] and "imdb://" in top_guid:
            ids["imdb"] = top_guid.split("imdb://")[-1].split("?")[0]
        if not ids["tmdb"] and "themoviedb://" in top_guid:
            ids["tmdb"] = top_guid.split("themoviedb://")[-1].split("?")[0]
        if not ids["tvdb"] and "thetvdb://" in top_guid:
            ids["tvdb"] = top_guid.split("thetvdb://")[-1].split("?")[0]

    return ids
