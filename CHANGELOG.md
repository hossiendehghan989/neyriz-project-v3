# Changelog

## 2026-09-25 — ASTER GDEM adjacent tiles

- Branch: `dem/adjacent-tiles-20260925`
- Downloaded and validated the eight missing ASTER GDEM V3 DEM tiles for AOI `53.3–55.2°E, 28.6–30.2°N`:
  `N28E053`, `N28E054`, `N28E055`, `N29E053`, `N29E055`, `N30E053`, `N30E054`, `N30E055`.
- Preserved the existing `N29E054` tile; it was not replaced.
- Validation included authenticated download success, TIFF signature, file-size sanity check, SHA-256 manifest, and geospatial checksum/read validation when available.
- No credentials or tokens are included in this changelog.
- Sentinel-2 / CDSE step was not started.
