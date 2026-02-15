"""Tests for utils.ids."""
import pytest

from utils.ids import extract_ids


def test_extract_ids_empty():
    """Empty metadata returns all None."""
    assert extract_ids({}) == {"tmdb": None, "tvdb": None, "imdb": None, "mbid": None}
    assert extract_ids({"guids": []}) == {"tmdb": None, "tvdb": None, "imdb": None, "mbid": None}


def test_extract_ids_from_guids():
    """IDs extracted from guids list."""
    meta = {
        "guids": [
            "plex://movie/tmdb://12345",
            "plex://movie/tvdb://67890",
            "plex://movie/imdb://tt1111111",
            "plex://music/mbid://abc-def-123",
        ]
    }
    assert extract_ids(meta) == {
        "tmdb": "12345",
        "tvdb": "67890",
        "imdb": "tt1111111",
        "mbid": "abc-def-123",
    }


def test_extract_ids_legacy_guid():
    """Fallback to top-level guid (legacy Plex agent)."""
    meta = {"guid": "com.plexapp.agents.themoviedb://999?lang=en"}
    assert extract_ids(meta)["tmdb"] == "999"
    meta2 = {"guid": "com.plexapp.agents.imdb://tt2222222"}
    assert extract_ids(meta2)["imdb"] == "tt2222222"


def test_extract_ids_guids_dict_format():
    """Guids as list of dicts with id key."""
    meta = {"guids": [{"id": "tmdb://333"}, {"id": "tvdb://444"}]}
    assert extract_ids(meta)["tmdb"] == "333"
    assert extract_ids(meta)["tvdb"] == "444"
