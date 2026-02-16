"""API routes."""
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from flask import Blueprint, jsonify, request

from config import (
    DEBUG,
    LIDARR_INSTANCES,
    OVERSEERR_API_KEY,
    OVERSEERR_URL,
    RADARR_INSTANCES,
    SONARR_INSTANCES,
    STAT,
)
from services import lidarr, overseerr, radarr, sonarr, tautulli
from utils.ids import extract_ids

api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route("/debug")
def api_debug():
    """Debug: show libraries, a sample item, and its metadata resolution. Only when DEBUG=true in env."""
    if not DEBUG:
        return jsonify({"error": "Debug routes are disabled"}), 404
    out = {}
    try:
        libs = tautulli.get_tautulli_libraries()
        out["libraries"] = [
            {
                "section_id": l.get("section_id"),
                "section_name": l.get("section_name"),
                "section_type": l.get("section_type"),
            }
            for l in libs
        ]
    except Exception as e:
        out["libraries_error"] = str(e)
        return jsonify(out)

    for lib in libs:
        sid = lib.get("section_id")
        try:
            data = tautulli.get_library_media(sid, length=1, start=0)
            items = data.get("data", []) if isinstance(data, dict) else []
            if not items:
                continue
            item = items[0]
            out["sample_library"] = sid
            out["sample_item_keys"] = list(item.keys())
            out["sample_item"] = item

            rk = item.get("rating_key")
            out["rating_key"] = rk
            if rk:
                meta = tautulli.get_metadata(rk)
                out["metadata_from_rating_key"] = meta
                out["extracted_ids"] = extract_ids(meta)
            break
        except Exception as e:
            out[f"library_{sid}_error"] = str(e)

    return jsonify(out)


@api_bp.route("/debug/library/<section_id>")
def api_debug_library(section_id):
    """Return raw Tautulli response for a library. Only when DEBUG=true in env."""
    if not DEBUG:
        return jsonify({"error": "Debug routes are disabled"}), 404
    try:
        data = tautulli.get_library_media(section_id, length=2, start=0)
        items = data.get("data", []) if isinstance(data, dict) else []
        section_type = None
        try:
            libs = tautulli.get_tautulli_libraries()
            for lib in (libs or []):
                if str(lib.get("section_id")) == str(section_id):
                    section_type = lib.get("section_type")
                    break
        except Exception:
            pass
        return jsonify({
            "section_id": section_id,
            "section_type": section_type,
            "response_keys": list(data.keys()) if isinstance(data, dict) else [],
            "first_item_keys": list(items[0].keys()) if items else [],
            "first_item": items[0] if items else None,
            "second_item": items[1] if len(items) > 1 else None,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/status")
def api_status():
    """Connectivity check for all configured services. Only when STAT=true in env.

    Returns a dict keyed by service name.  Each value is either an object
    {"status": "ok", "version": "..."} or a string "error: ...".
    """
    if not STAT:
        return jsonify({"error": "Status endpoint is disabled"}), 404
    result = {}

    try:
        info = tautulli.tautulli_get("get_tautulli_info")
        version = info.get("tautulli_version", "")
        name = (
            info.get("tautulli_product")
            or info.get("product")
            or info.get("app_name")
            or "Tautulli"
        )
        result["tautulli"] = {"status": "ok", "version": version, "name": name}
    except Exception as e:
        result["tautulli"] = f"error: {e}"

    try:
        if not OVERSEERR_API_KEY:
            raise ValueError("API key not set")
        r = requests.get(
            f"{OVERSEERR_URL}/api/v1/status",
            headers=overseerr.overseerr_headers(),
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        version = data.get("version", "")
        name = (
            data.get("applicationTitle")
            or data.get("title")
            or data.get("name")
            or "Seerr"
        )
        result["overseerr"] = {"status": "ok", "version": version, "name": name}
    except Exception as e:
        result["overseerr"] = f"error: {e}"

    for i, inst in enumerate(RADARR_INSTANCES):
        key = f"radarr_{i + 1}"
        try:
            r = requests.get(
                f"{inst['url']}/api/v3/system/status",
                params={"apikey": inst["api_key"]},
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()
            version = data.get("version", "")
            name = (
                data.get("instanceName")
                or data.get("appName")
                or data.get("name")
                or inst["name"]
            )
            result[key] = {"status": "ok", "version": version, "name": name}
        except Exception as e:
            result[key] = f"error: {e}"

    for i, inst in enumerate(SONARR_INSTANCES):
        key = f"sonarr_{i + 1}"
        try:
            r = requests.get(
                f"{inst['url']}/api/v3/system/status",
                params={"apikey": inst["api_key"]},
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()
            version = data.get("version", "")
            name = (
                data.get("instanceName")
                or data.get("appName")
                or data.get("name")
                or inst["name"]
            )
            result[key] = {"status": "ok", "version": version, "name": name}
        except Exception as e:
            result[key] = f"error: {e}"

    for i, inst in enumerate(LIDARR_INSTANCES):
        key = f"lidarr_{i + 1}"
        try:
            r = requests.get(
                f"{inst['url']}/api/v1/system/status",
                params={"apikey": inst["api_key"]},
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()
            version = data.get("version", "")
            name = (
                data.get("instanceName")
                or data.get("appName")
                or data.get("name")
                or inst["name"]
            )
            result[key] = {"status": "ok", "version": version, "name": name}
        except Exception as e:
            result[key] = f"error: {e}"

    return jsonify(result)


@api_bp.route("/instances")
def api_instances():
    """Return the configured instance names so the frontend can render chips."""
    return jsonify({
        "radarr": [
            {"key": f"radarr_{i+1}", "name": inst["name"]}
            for i, inst in enumerate(RADARR_INSTANCES)
        ],
        "sonarr": [
            {"key": f"sonarr_{i+1}", "name": inst["name"]}
            for i, inst in enumerate(SONARR_INSTANCES)
        ],
        "lidarr": [
            {"key": f"lidarr_{i+1}", "name": inst["name"]}
            for i, inst in enumerate(LIDARR_INSTANCES)
        ],
    })


@api_bp.route("/libraries")
def api_libraries():
    """Return all Tautulli libraries (for combined view we only need types)."""
    try:
        libs = tautulli.get_tautulli_libraries()
        return jsonify(libs if isinstance(libs, list) else [])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/library/combined")
def api_library_combined():
    """Return media from all libraries of one type (movie/show/artist), merged and sorted.
    Each item includes library_name (Tautulli section_name) and section_id for remove flow.
    """
    section_type = (request.args.get("type") or "movie").lower()
    if section_type not in ("movie", "show", "artist"):
        return jsonify({"error": "type must be movie, show, or artist"}), 400
    length = request.args.get("length", 50, type=int)
    start = request.args.get("start", 0, type=int)
    search = request.args.get("search", "").strip() or None
    library_name_filter = request.args.get("library_name", "").strip() or None
    order_column = request.args.get("order_column", "last_played")
    order_dir = request.args.get("order_dir", "asc")
    allowed_columns = {"sort_title", "year", "added_at", "last_played", "play_count", "file_size", "library_name"}
    if order_column not in allowed_columns:
        order_column = "last_played"
    if order_dir not in ("asc", "desc"):
        order_dir = "asc"
    try:
        libs = tautulli.get_tautulli_libraries()
        if not isinstance(libs, list):
            libs = []
        # Only libraries of this type
        libs_of_type = [l for l in libs if (l.get("section_type") or "").lower() == section_type]
        if not libs_of_type:
            return jsonify({
                "data": [],
                "recordsFiltered": 0,
                "recordsTotal": 0,
                "section_type": section_type,
            })

        fetch_per_lib = max(length + start, 50)
        all_items = []
        for lib in libs_of_type:
            sid = lib.get("section_id")
            sname = (lib.get("section_name") or "").strip() or "—"
            try:
                data = tautulli.get_library_media(
                    sid,
                    length=fetch_per_lib,
                    start=0,
                    search=search,
                    order_column=order_column,
                    order_dir=order_dir,
                    section_type=section_type,
                )
                items = data.get("data") if isinstance(data.get("data"), list) else []
                for item in items:
                    if isinstance(item, dict):
                        item = dict(item)
                        item["library_name"] = sname
                        item["section_id"] = str(sid)
                        all_items.append(item)
            except Exception:
                continue

        if library_name_filter:
            want = library_name_filter.strip().lower()
            all_items = [i for i in all_items if (i.get("library_name") or "").strip().lower() == want]

        # Sort merged list (Tautulli may return timestamps/counts as strings)
        def sort_key(i):
            val = i.get(order_column)
            if order_column == "library_name":
                return (1, (str(val) or "").strip().lower())
            if val is None or val == "":
                return (0, 0) if order_column in ("last_played", "added_at", "play_count", "file_size") else (1, "")
            if order_column in ("last_played", "added_at", "play_count", "file_size"):
                try:
                    n = int(val) if not isinstance(val, (int, float)) else val
                    return (0, n)
                except (TypeError, ValueError):
                    return (1, str(val))
            return (1, (str(val) or "").lower())

        reverse = order_dir == "desc"
        all_items.sort(key=sort_key, reverse=reverse)
        total = len(all_items)
        page_items = all_items[start : start + length]

        # File size normalization for shows
        if section_type == "show":
            for item in page_items:
                if isinstance(item, dict):
                    fs, tfs = item.get("file_size"), item.get("total_file_size")
                    if (fs is None or fs == 0 or fs == "") and tfs is not None:
                        item["file_size"] = tfs
                    if (item.get("file_size") or 0) == 0:
                        for key in ("total_file_size", "size", "total_size"):
                            v = item.get(key)
                            if v is not None and v != "":
                                try:
                                    n = int(v) if isinstance(v, str) else v
                                    if n > 0:
                                        item["file_size"] = n
                                        break
                                except (TypeError, ValueError):
                                    pass

        out = {
            "data": page_items,
            "recordsFiltered": total,
            "recordsTotal": total,
            "section_type": section_type,
            "libraries": [l.get("section_name") or "" for l in libs_of_type],
        }
        return jsonify(out)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/overseerr-info", methods=["POST"])
def api_overseerr_info():
    """Batch-lookup Seerr requestor info for a list of rating keys.

    Expects JSON:
    {
        "rating_keys": ["123", "456", ...],
        "media_type": "movie" | "show"
    }

    Returns a dict keyed by rating_key with requestor info.
    """
    try:
        body = request.get_json(force=True, silent=True) or {}
    except Exception:
        return jsonify({"error": "Invalid JSON body"}), 400
    rating_keys = body.get("rating_keys", [])
    media_type = body.get("media_type", "movie")

    if not OVERSEERR_API_KEY:
        return jsonify({})

    def _lookup(rk):
        result = {"rating_key": rk, "requested_by": None}
        try:
            meta = tautulli.get_metadata(rk)
            ids = extract_ids(meta)
            tmdb_id = ids.get("tmdb")
            if not tmdb_id:
                return result

            media = overseerr.overseerr_find_media(tmdb_id, media_type)
            if not media:
                return result

            media_info = media.get("mediaInfo")
            if not media_info:
                return result

            reqs = media_info.get("requests") or []
            requestors = []
            for req in reqs:
                user = req.get("requestedBy") or {}
                name = (
                    user.get("displayName")
                    or user.get("plexUsername")
                    or user.get("email")
                    or None
                )
                if name and name not in requestors:
                    requestors.append(name)
            if requestors:
                result["requested_by"] = ", ".join(requestors)
        except Exception:
            pass
        return result

    try:
        info = {}
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = {pool.submit(_lookup, rk): rk for rk in rating_keys}
            for fut in as_completed(futures):
                res = fut.result()
                info[res["rating_key"]] = res
        return jsonify(info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/remove", methods=["POST"])
def api_remove():
    """
    Remove media from Seerr, Radarr/Sonarr/Lidarr (all instances), and
    Tautulli.

    Expects JSON:
    {
        "rating_key": "...",
        "section_id": "...",
        "media_type": "movie" | "show" | "artist",
        "tmdb_id": "...",    (optional — resolved via Tautulli if missing)
        "tvdb_id": "...",    (optional — resolved via Tautulli if missing)
        "mbid": "..."        (optional — resolved via Tautulli if missing)
    }
    """
    body = request.get_json(force=True)
    rating_key = body.get("rating_key")
    section_id = body.get("section_id")
    media_type = body.get("media_type", "movie")
    tmdb_id = body.get("tmdb_id")
    tvdb_id = body.get("tvdb_id")
    imdb_id = body.get("imdb_id")
    mbid = body.get("mbid")

    results = {"overseerr": None, "tautulli": None}

    try:
        if rating_key:
            needs_resolve = (
                (not tmdb_id and not imdb_id)
                or (media_type == "show" and not tvdb_id)
                or (media_type == "artist" and not mbid)
            )
            if needs_resolve:
                meta = tautulli.get_metadata(rating_key)
                ids = extract_ids(meta)
                tmdb_id = tmdb_id or ids["tmdb"]
                tvdb_id = tvdb_id or ids["tvdb"]
                imdb_id = imdb_id or ids["imdb"]
                mbid = mbid or ids["mbid"]

        has_ids = tmdb_id or tvdb_id or imdb_id or mbid

        if not has_ids:
            results["overseerr"] = "skipped (no IDs resolved)"
        elif media_type == "artist":
            results["overseerr"] = "skipped (music)"
        else:
            try:
                if tmdb_id:
                    media = overseerr.overseerr_find_media(tmdb_id, media_type)
                    if media and media.get("mediaInfo"):
                        media_id = media["mediaInfo"]["id"]
                        overseerr.overseerr_delete_media(media_id)
                        results["overseerr"] = "removed"
                    else:
                        results["overseerr"] = "not_found"
                else:
                    results["overseerr"] = "skipped (no TMDB id)"
            except Exception as e:
                results["overseerr"] = f"error: {e}"

        if not has_ids:
            results["arr"] = "skipped (no IDs resolved)"
        elif media_type == "movie":
            for i, inst in enumerate(RADARR_INSTANCES):
                key = f"radarr_{i + 1}"
                try:
                    movie = radarr.radarr_find_movie(
                        inst, tmdb_id=tmdb_id, imdb_id=imdb_id
                    )
                    if movie:
                        radarr.radarr_delete_movie(inst, movie["id"], delete_files=True)
                        results[key] = "removed"
                    else:
                        results[key] = "not_found"
                except Exception as e:
                    results[key] = f"error: {e}"
        elif media_type == "artist":
            for i, inst in enumerate(LIDARR_INSTANCES):
                key = f"lidarr_{i + 1}"
                try:
                    if mbid:
                        artist = lidarr.lidarr_find_artist(inst, mbid)
                        if artist:
                            lidarr.lidarr_delete_artist(
                                inst, artist["id"], delete_files=True
                            )
                            results[key] = "removed"
                        else:
                            results[key] = "not_found"
                    else:
                        results[key] = "skipped (no MusicBrainz id)"
                except Exception as e:
                    results[key] = f"error: {e}"
        else:
            for i, inst in enumerate(SONARR_INSTANCES):
                key = f"sonarr_{i + 1}"
                try:
                    series = None
                    if tvdb_id:
                        series = sonarr.sonarr_find_series(inst, tvdb_id)
                    if not series and tmdb_id:
                        series = sonarr.sonarr_find_series_by_tmdb(inst, tmdb_id)
                    if series:
                        sonarr.sonarr_delete_series(
                            inst, series["id"], delete_files=True
                        )
                        results[key] = "removed"
                    else:
                        results[key] = "not_found"
                except Exception as e:
                    results[key] = f"error: {e}"

        try:
            if rating_key:
                deleted = tautulli.delete_tautulli_history(rating_key)
                if section_id:
                    tautulli.delete_tautulli_media_info_cache(section_id, rating_key)
                results["tautulli"] = (
                    f"removed ({deleted} history entries cleared)"
                )
            else:
                results["tautulli"] = "skipped (no rating_key)"
        except Exception as e:
            results["tautulli"] = f"error: {e}"

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
