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


def test_extract_ids_plex_style_guids():
    """Plex-style agent guids in array use themoviedb/thetvdb (no tmdb:///tvdb://)."""
    meta = {
        "guids": [
            "com.plexapp.agents.themoviedb://12345?lang=en",
            "com.plexapp.agents.thetvdb://67890",
            "com.plexapp.agents.imdb://tt0783233",
        ]
    }
    assert extract_ids(meta)["tmdb"] == "12345"
    assert extract_ids(meta)["tvdb"] == "67890"
    assert extract_ids(meta)["imdb"] == "tt0783233"


def test_extract_ids_direct_fields():
    """Direct tmdb_id/imdb_id/tvdb_id fields when guids are missing."""
    meta = {"tmdb_id": 12345, "imdb_id": "tt0783233", "tvdb_id": "67890"}
    assert extract_ids(meta)["tmdb"] == "12345"
    assert extract_ids(meta)["imdb"] == "tt0783233"
    assert extract_ids(meta)["tvdb"] == "67890"


def test_extract_ids_guid_with_path():
    """Single guid with path (e.g. thetvdb://121361/6/1?lang=en) yields series id only."""
    meta = {"guid": "com.plexapp.agents.thetvdb://121361/6/1?lang=en"}
    assert extract_ids(meta)["tvdb"] == "121361"
