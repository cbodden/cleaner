import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TAUTULLI_URL = os.getenv("TAUTULLI_URL", "http://localhost:8181").rstrip("/")
TAUTULLI_API_KEY = os.getenv("TAUTULLI_API_KEY", "")

OVERSEERR_URL = os.getenv("OVERSEERR_URL", "http://localhost:5055").rstrip("/")
OVERSEERR_API_KEY = os.getenv("OVERSEERR_API_KEY", "")


def _build_arr_instances(prefix, count=2):
    """Read numbered *arr instance configs from env vars.

    E.g. prefix="RADARR" reads RADARR_1_URL, RADARR_1_API_KEY, RADARR_1_NAME,
    then RADARR_2_URL, etc.  Instances with a blank URL are skipped.
    """
    instances = []
    for i in range(1, count + 1):
        url = os.getenv(f"{prefix}_{i}_URL", "").rstrip("/")
        key = os.getenv(f"{prefix}_{i}_API_KEY", "")
        name = os.getenv(f"{prefix}_{i}_NAME", f"{prefix} {i}")
        if url and key:
            instances.append({"url": url, "api_key": key, "name": name})
    return instances


RADARR_INSTANCES = _build_arr_instances("RADARR")
SONARR_INSTANCES = _build_arr_instances("SONARR")


# ---------------------------------------------------------------------------
# Tautulli helpers
# ---------------------------------------------------------------------------

def tautulli_get(cmd, params=None):
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


def get_tautulli_libraries():
    """Return the list of Tautulli libraries."""
    data = tautulli_get("get_libraries")
    return data if isinstance(data, list) else []


def get_library_media(section_id, length=50, start=0, search=None):
    """Fetch media from a Tautulli library section sorted by last played."""
    params = {
        "section_id": section_id,
        "length": length,
        "start": start,
        "order_column": "last_played",
        "order_dir": "asc",
    }
    if search:
        params["search"] = search
    return tautulli_get("get_library_media_info", params)


def get_metadata(rating_key):
    """Get Tautulli metadata for a single item (includes guids)."""
    return tautulli_get("get_metadata", {"rating_key": rating_key})


def delete_tautulli_history(rating_key):
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


def delete_tautulli_media_info_cache(section_id, rating_key):
    """Remove cached media-info for a single item in Tautulli."""
    tautulli_get("delete_media_info_cache", {
        "section_id": section_id,
        "rating_key": rating_key,
    })


# ---------------------------------------------------------------------------
# Overseerr helpers
# ---------------------------------------------------------------------------

def overseerr_headers():
    return {"X-Api-Key": OVERSEERR_API_KEY, "Content-Type": "application/json"}


def overseerr_find_media(tmdb_id, media_type="movie"):
    """Look up media in Overseerr by TMDB id.

    media_type: "movie" or "show"
    """
    if not OVERSEERR_API_KEY:
        raise ValueError("OVERSEERR_API_KEY is not set — check your .env file")
    endpoint = "movie" if media_type == "movie" else "tv"
    r = requests.get(
        f"{OVERSEERR_URL}/api/v1/{endpoint}/{tmdb_id}",
        headers=overseerr_headers(),
        timeout=15,
    )
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


def overseerr_delete_media(media_id):
    """Delete a media entry from Overseerr (removes request + clears data)."""
    r = requests.delete(
        f"{OVERSEERR_URL}/api/v1/media/{media_id}",
        headers=overseerr_headers(),
        timeout=15,
    )
    r.raise_for_status()
    return True


# ---------------------------------------------------------------------------
# Radarr helpers (multi-instance)
# ---------------------------------------------------------------------------

def radarr_find_movie(instance, tmdb_id):
    """Find a movie in a Radarr instance by its TMDB id."""
    r = requests.get(
        f"{instance['url']}/api/v3/movie",
        params={"apikey": instance["api_key"], "tmdbId": tmdb_id},
        timeout=15,
    )
    r.raise_for_status()
    movies = r.json()
    if isinstance(movies, list) and movies:
        return movies[0]
    return None


def radarr_delete_movie(instance, movie_id, delete_files=True):
    """Delete a movie from a Radarr instance."""
    r = requests.delete(
        f"{instance['url']}/api/v3/movie/{movie_id}",
        params={"apikey": instance["api_key"],
                "deleteFiles": str(delete_files).lower(),
                "addImportExclusion": "false"},
        timeout=15,
    )
    r.raise_for_status()
    return True


# ---------------------------------------------------------------------------
# Sonarr helpers (multi-instance)
# ---------------------------------------------------------------------------

def sonarr_find_series(instance, tvdb_id):
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


def sonarr_find_series_by_tmdb(instance, tmdb_id):
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


def sonarr_delete_series(instance, series_id, delete_files=True):
    """Delete a series from a Sonarr instance."""
    r = requests.delete(
        f"{instance['url']}/api/v3/series/{series_id}",
        params={"apikey": instance["api_key"],
                "deleteFiles": str(delete_files).lower(),
                "addImportExclusion": "false"},
        timeout=15,
    )
    r.raise_for_status()
    return True


# ---------------------------------------------------------------------------
# Utility: extract IDs from Tautulli metadata guids
# ---------------------------------------------------------------------------

def extract_ids(metadata):
    """Pull TMDB and TVDB ids out of Tautulli metadata guids list."""
    guids = metadata.get("guids") or []
    ids = {"tmdb": None, "tvdb": None}
    for g in guids:
        val = g if isinstance(g, str) else g.get("id", "")
        if "tmdb://" in val:
            ids["tmdb"] = val.split("tmdb://")[-1].split("?")[0]
        elif "tvdb://" in val:
            ids["tvdb"] = val.split("tvdb://")[-1].split("?")[0]
    return ids


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    """Connectivity check for all configured services."""
    status = {}

    # Tautulli
    try:
        tautulli_get("get_tautulli_info")
        status["tautulli"] = "ok"
    except Exception as e:
        status["tautulli"] = f"error: {e}"

    # Overseerr
    try:
        if not OVERSEERR_API_KEY:
            raise ValueError("API key not set")
        r = requests.get(f"{OVERSEERR_URL}/api/v1/status",
                         headers=overseerr_headers(), timeout=10)
        r.raise_for_status()
        status["overseerr"] = "ok"
    except Exception as e:
        status["overseerr"] = f"error: {e}"

    # Radarr instances
    for i, inst in enumerate(RADARR_INSTANCES):
        key = f"radarr_{i + 1}"
        try:
            r = requests.get(f"{inst['url']}/api/v3/system/status",
                             params={"apikey": inst["api_key"]}, timeout=10)
            r.raise_for_status()
            status[key] = "ok"
        except Exception as e:
            status[key] = f"error: {e}"

    # Sonarr instances
    for i, inst in enumerate(SONARR_INSTANCES):
        key = f"sonarr_{i + 1}"
        try:
            r = requests.get(f"{inst['url']}/api/v3/system/status",
                             params={"apikey": inst["api_key"]}, timeout=10)
            r.raise_for_status()
            status[key] = "ok"
        except Exception as e:
            status[key] = f"error: {e}"

    return jsonify(status)


@app.route("/api/instances")
def api_instances():
    """Return the configured instance names so the frontend can render chips."""
    return jsonify({
        "radarr": [{"key": f"radarr_{i+1}", "name": inst["name"]}
                   for i, inst in enumerate(RADARR_INSTANCES)],
        "sonarr": [{"key": f"sonarr_{i+1}", "name": inst["name"]}
                   for i, inst in enumerate(SONARR_INSTANCES)],
    })


@app.route("/api/libraries")
def api_libraries():
    """Return all Tautulli libraries."""
    try:
        libs = get_tautulli_libraries()
        return jsonify(libs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/library/<section_id>")
def api_library_media(section_id):
    """Return media items for a library section, sorted by last played."""
    length = request.args.get("length", 50, type=int)
    start = request.args.get("start", 0, type=int)
    search = request.args.get("search", None)
    try:
        data = get_library_media(section_id, length=length, start=start,
                                 search=search)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/overseerr-info", methods=["POST"])
def api_overseerr_info():
    """Batch-lookup Overseerr requestor info for a list of rating keys.

    Expects JSON:
    {
        "rating_keys": ["123", "456", ...],
        "media_type": "movie" | "show"
    }

    Returns a dict keyed by rating_key with requestor info.
    """
    body = request.get_json(force=True)
    rating_keys = body.get("rating_keys", [])
    media_type = body.get("media_type", "movie")

    if not OVERSEERR_API_KEY:
        return jsonify({})

    def _lookup(rk):
        """Resolve one rating key to Overseerr requestor info."""
        result = {"rating_key": rk, "requested_by": None}
        try:
            meta = get_metadata(rk)
            ids = extract_ids(meta)
            tmdb_id = ids.get("tmdb")
            if not tmdb_id:
                return result

            media = overseerr_find_media(tmdb_id, media_type)
            if not media:
                return result

            media_info = media.get("mediaInfo")
            if not media_info:
                return result

            reqs = media_info.get("requests") or []
            requestors = []
            for req in reqs:
                user = req.get("requestedBy") or {}
                name = (user.get("displayName")
                        or user.get("plexUsername")
                        or user.get("email")
                        or None)
                if name and name not in requestors:
                    requestors.append(name)
            if requestors:
                result["requested_by"] = ", ".join(requestors)
        except Exception:
            pass
        return result

    info = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(_lookup, rk): rk for rk in rating_keys}
        for fut in as_completed(futures):
            res = fut.result()
            info[res["rating_key"]] = res

    return jsonify(info)


@app.route("/api/remove", methods=["POST"])
def api_remove():
    """
    Remove media from Overseerr, Radarr/Sonarr (all instances), and Tautulli.

    Expects JSON:
    {
        "rating_key": "...",
        "section_id": "...",
        "media_type": "movie" | "show",
        "tmdb_id": "...",    (optional — resolved via Tautulli if missing)
        "tvdb_id": "..."     (optional — resolved via Tautulli if missing)
    }
    """
    body = request.get_json(force=True)
    rating_key = body.get("rating_key")
    section_id = body.get("section_id")
    media_type = body.get("media_type", "movie")
    tmdb_id = body.get("tmdb_id")
    tvdb_id = body.get("tvdb_id")

    results = {"overseerr": None, "tautulli": None}

    try:
        # Resolve IDs from Tautulli metadata if not provided
        if (not tmdb_id or (media_type == "show" and not tvdb_id)) and rating_key:
            meta = get_metadata(rating_key)
            ids = extract_ids(meta)
            tmdb_id = tmdb_id or ids["tmdb"]
            tvdb_id = tvdb_id or ids["tvdb"]

        if not tmdb_id and not tvdb_id:
            return jsonify({"error": "Could not determine TMDB/TVDB id"}), 400

        # --- Overseerr ---
        try:
            if tmdb_id:
                media = overseerr_find_media(tmdb_id, media_type)
                if media and media.get("mediaInfo"):
                    media_id = media["mediaInfo"]["id"]
                    overseerr_delete_media(media_id)
                    results["overseerr"] = "removed"
                else:
                    results["overseerr"] = "not_found"
            else:
                results["overseerr"] = "skipped (no TMDB id)"
        except Exception as e:
            results["overseerr"] = f"error: {e}"

        # --- Radarr / Sonarr ---
        if media_type == "movie":
            for i, inst in enumerate(RADARR_INSTANCES):
                key = f"radarr_{i + 1}"
                try:
                    if tmdb_id:
                        movie = radarr_find_movie(inst, tmdb_id)
                        if movie:
                            radarr_delete_movie(inst, movie["id"],
                                                delete_files=True)
                            results[key] = "removed"
                        else:
                            results[key] = "not_found"
                    else:
                        results[key] = "skipped (no TMDB id)"
                except Exception as e:
                    results[key] = f"error: {e}"
        else:
            for i, inst in enumerate(SONARR_INSTANCES):
                key = f"sonarr_{i + 1}"
                try:
                    series = None
                    if tvdb_id:
                        series = sonarr_find_series(inst, tvdb_id)
                    if not series and tmdb_id:
                        series = sonarr_find_series_by_tmdb(inst, tmdb_id)
                    if series:
                        sonarr_delete_series(inst, series["id"],
                                             delete_files=True)
                        results[key] = "removed"
                    else:
                        results[key] = "not_found"
                except Exception as e:
                    results[key] = f"error: {e}"

        # --- Tautulli ---
        try:
            if rating_key:
                deleted = delete_tautulli_history(rating_key)
                if section_id:
                    delete_tautulli_media_info_cache(section_id, rating_key)
                results["tautulli"] = f"removed ({deleted} history entries cleared)"
            else:
                results["tautulli"] = "skipped (no rating_key)"
        except Exception as e:
            results["tautulli"] = f"error: {e}"

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
