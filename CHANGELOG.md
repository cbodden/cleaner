# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] - 2025-02-15

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

[1.0.0]: https://github.com/cbodden/cleaner/releases/tag/v1.0.0
