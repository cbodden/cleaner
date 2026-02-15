"""Tautulli API client."""
import requests

from config import TAUTULLI_API_KEY, TAUTULLI_URL


def tautulli_get(cmd: str, params: dict | None = None) -> dict | list:
    """Call the Tautulli API."""
    if not TAUTULLI_API_KEY:
        raise ValueError("TAUTULLI_API_KEY is not set — check your .env file")
    p = {"apikey": TAUTULLI_API_KEY, "cmd": cmd}
    if params:
        p.update(params)
    url = f"{TAUTULLI_URL}/api/v2"
    r = requests.get(url, params=p, timeout=30)
    r.raise_for_status()
    ct = r.headers.get("Content-Type", "")
    if "json" not in ct and "javascript" not in ct:
        raise ValueError(
            f"Tautulli returned non-JSON (Content-Type: {ct}). "
            f"Check TAUTULLI_URL ({TAUTULLI_URL}) and TAUTULLI_API_KEY."
        )
    data = r.json()
    resp = data.get("response", {})
    if resp.get("result") != "success":
        msg = resp.get("message", "unknown error")
        raise ValueError(f"Tautulli API error: {msg}")
    return resp.get("data", {})


def get_tautulli_libraries() -> list:
    """Return the list of Tautulli libraries."""
    data = tautulli_get("get_libraries")
    return data if isinstance(data, list) else []


def get_library_media(
    section_id,
    length: int = 50,
    start: int = 0,
    search: str | None = None,
    order_column: str = "last_played",
    order_dir: str = "asc",
):
    """Fetch media from a Tautulli library section."""
    params = {
        "section_id": section_id,
        "length": length,
        "start": start,
        "order_column": order_column,
        "order_dir": order_dir,
    }
    if search:
        params["search"] = search
    return tautulli_get("get_library_media_info", params)


def get_metadata(rating_key) -> dict:
    """Get Tautulli metadata for a single item (includes guids)."""
    return tautulli_get("get_metadata", {"rating_key": rating_key})


def delete_tautulli_history(rating_key) -> int:
    """Delete all Tautulli play history for a rating key."""
    data = tautulli_get("get_history", {
        "rating_key": rating_key,
        "length": 10000,
    })
    rows = data.get("data", []) if isinstance(data, dict) else []
    if rows:
        row_ids = ",".join(str(r["id"]) for r in rows if "id" in r)
        if row_ids:
            tautulli_get("delete_history", {"row_ids": row_ids})
    return len(rows)


def delete_tautulli_media_info_cache(section_id, rating_key) -> None:
    """Remove cached media-info for a single item in Tautulli."""
    tautulli_get("delete_media_info_cache", {
        "section_id": section_id,
        "rating_key": rating_key,
    })
