# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.2.0] - 2026-02-15

### Added

- **Search** — Search box appears when a library is loaded; searches only within the selected library and shows only matching items.
- **Production WSGI** — `wsgi.py` and gunicorn; with `DEBUG=false`, `python app.py` runs gunicorn instead of the Flask dev server. Docker image uses gunicorn in CMD.
- **DEBUG and STAT env flags** — `DEBUG` enables Flask debug mode and `/api/debug` routes; `STAT` enables `/api/status`. Both configurable via `.env` and Docker.

### Changed

- **Show library file column** — For TV show libraries, file column shows "—" when Tautulli does not provide file size (avoids incorrect "Missing" when files exist).
- **README and Docker** — Document DEBUG/STAT, standalone vs Docker run; compose and Dockerfile set production defaults; workflow triggers on `docker/**` and app files.

## [1.1.0] - 2026-02-15

### Changed

- **Seerr branding** — UI and docs use "Seerr" (Overseerr-compatible); request server chip and toasts show name from API.
- **Status chip names** — All service chips (Tautulli, Seerr, Radarr, Sonarr, Lidarr) show name from respective API or instance config.
- **Codebase refactor** — App split into config, services (tautulli, overseerr, radarr, sonarr, lidarr), routes (main, api), and utils; Flask app factory.

### Fixed

- **app.py** — Removed duplicate legacy code; entry point is create_app only.

## [1.0.0] - 2026-02-15

### Added

- **Lidarr support** — Remove music from Lidarr instances (primary and optional secondary), with column sorting for library view.
- **Docker support** — Alpine-based image and GitHub Actions workflow to build and push to `ghcr.io`. Docker Compose example uses pre-built image.
- **Column sorting** — Sort library by title, year, added date, last played, play count, size, or requested by (click column headers).
- **Screenshot and README** — Screenshot section and images folder for documentation.
- **Debug endpoint** — Endpoint for troubleshooting metadata resolution (IMDB/TMDB IDs).

### Changed

- **ID resolution** — Extract IMDB IDs from Tautulli guids and legacy Plex agent formats; Radarr lookup falls back to IMDB when TMDB is unavailable.
- **Graceful skip** — When no IDs can be resolved, Seerr and *arr steps are skipped instead of failing; Tautulli cleanup still runs.
- **Artist library display** — Correct file badge and Seerr skip behavior for music libraries.

### Fixed

- Missing Plex metadata no longer blocks removal; Tautulli history and cache are still cleaned when Plex metadata is unavailable.

[1.2.0]: https://github.com/cbodden/cleaner/releases/tag/v1.2.0
[1.1.0]: https://github.com/cbodden/cleaner/releases/tag/v1.1.0
[1.0.0]: https://github.com/cbodden/cleaner/releases/tag/v1.0.0
