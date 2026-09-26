# Changelog

## 2026-09-25 — ASTER GDEM adjacent tiles

- Branch: `dem/adjacent-tiles-20260925`
- Downloaded and validated the eight missing ASTER GDEM V3 DEM tiles for AOI `53.3–55.2°E, 28.6–30.2°N`:
  `N28E053`, `N28E054`, `N28E055`, `N29E053`, `N29E055`, `N30E053`, `N30E054`, `N30E055`.
- Preserved the existing `N29E054` tile; it was not replaced.
- Validation included authenticated download success, TIFF signature, file-size sanity check, SHA-256 manifest, and geospatial checksum/read validation when available.
- No credentials or tokens are included in this changelog.
- Sentinel-2 / CDSE step was not started.

## 2026-09-26 — Step 9A supplemental label audit (v3.1)
- Re-audited the 25 existing source-backed A-class rows and checked additional official MRDS and peer-reviewed sources for the Neyriz AOI.
- Added 0 label rows: Nasirabad coordinate duplicates existing MN-001; MRDS Sahik and Parpa coordinates are Town references with 10,000 m stated accuracy; Chesmehbidouh has the same Town/10,000 m limitation and possible Khajeh-Jamali alias.
- Stored candidate decisions and source URLs in `data/acquired/research_step_04_label_supplement/step09a_supplemental_search.json` and a Persian summary in `docs/step_09a_supplemental_search_fa.md`.
- Added a reproducible inventory updater and recorded hashes for the Step 9A source/derived files and nine adjacent ASTER DEM tiles. All nine tile hashes verify.
- The 10 manganese screening targets, model inputs/weights, prospectivity layers and maps were not modified. No label was promoted to model or independent-test use.
- Official 1:100,000 map files remain unavailable in this environment because data.gov.ir connections closed; Sentinel-2 scene download remains blocked because Earthdata/CDSE credentials are not configured.
- Validation scripts pass except the independent-validation evaluator correctly reports BLOCKED: no independent test labels. Evidence gates remain `BLOCKED_INSUFFICIENT_DATA`.
