# ASTER GDEM V003 — Neyriz tile

The repository includes the authenticated Earthdata download for granule `ASTGTMV003_N29E054_dem.tif`.

- Coverage: approximately 53.999861–55.000139 E, 28.999861–30.000139 N
- Collection: ASTER Global Digital Elevation Model V003
- CMR metadata: `data/acquired/research_step_02_remote_sensing_dem/aster_gdem_cmr_full.json`
- Checksum and source provenance: `metadata.json`

This is an input layer for terrain derivatives, not a mineral-occurrence label. Adjacent tiles are needed before claiming full-AOI coverage.


## Adjacent-tile branch update — 2026-09-25
This branch now contains all nine ASTER GDEM V003 tiles required to cover the approximate screening envelope `53.3–55.2°E, 28.6–30.2°N`: `N28E053` through `N30E055` in the 3×3 tile block. SHA-256 values are recorded in `data/acquired/aster_gdem_v003_sha256.txt` and were verified on 2026-09-26. This does not mean new terrain derivatives or Sentinel-2 features were calculated; ASTER is topographic context only and is not mineralization evidence.
