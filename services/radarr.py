"""Radarr API client (multi-instance)."""
import requests


def radarr_find_movie(instance: dict, tmdb_id=None, imdb_id=None) -> dict | None:
    """Find a movie in a Radarr instance by TMDB or IMDB id."""
    if tmdb_id:
        r = requests.get(
            f"{instance['url']}/api/v3/movie",
            params={"apikey": instance["api_key"], "tmdbId": tmdb_id},
            timeout=15,
        )
        r.raise_for_status()
        movies = r.json()
        if isinstance(movies, list) and movies:
            return movies[0]
    if imdb_id:
        r = requests.get(
            f"{instance['url']}/api/v3/movie",
            params={"apikey": instance["api_key"]},
            timeout=30,
        )
        r.raise_for_status()
        for m in r.json():
            if m.get("imdbId") == imdb_id:
                return m
    return None


def radarr_delete_movie(instance: dict, movie_id, delete_files: bool = True) -> bool:
    """Delete a movie from a Radarr instance."""
    r = requests.delete(
        f"{instance['url']}/api/v3/movie/{movie_id}",
        params={
            "apikey": instance["api_key"],
            "deleteFiles": str(delete_files).lower(),
            "addImportExclusion": "false",
        },
        timeout=15,
    )
    r.raise_for_status()
    return True
