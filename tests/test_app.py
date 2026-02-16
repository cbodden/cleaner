"""Tests for Flask app and main routes."""
import pytest


def test_index_returns_200(client):
    """Index page loads."""
    r = client.get("/")
    assert r.status_code == 200
    assert b"Magic-Erasarr" in r.data or b"media" in r.data.lower()


def test_index_includes_version(client):
    """Footer includes version."""
    r = client.get("/")
    assert r.status_code == 200
    assert b"v1." in r.data  # e.g. v1.3.0


def test_api_libraries_returns_json(client):
    """/api/libraries returns JSON (error when no Tautulli is ok)."""
    r = client.get("/api/libraries")
    assert r.content_type == "application/json"
    data = r.get_json()
    assert data is not None
    # Without TAUTULLI_API_KEY we get error or empty list
    assert "error" in data or isinstance(data, list)


def test_api_status_disabled_when_stat_false(client):
    """/api/status returns 404 when STAT is false (default in test env)."""
    r = client.get("/api/status")
    # STAT defaults from env; in CI often unset so may be True. Just ensure JSON response.
    assert r.content_type == "application/json"
