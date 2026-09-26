#!/usr/bin/env python3
"""Build auditable DEM-derived features for Neyriz v4.

The DEM contributes reproducible terrain features, but does not create mineral
labels and is intentionally not treated as proof of mineralization.
"""
from pathlib import Path
import csv, hashlib, json
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.transform import rowcol

ROOT = Path(__file__).resolve().parents[1]
DEM = ROOT / "data/remote_sensing/aster_gdem_v003/ASTGTMV003_N29E054_dem.tif"
GRID = ROOT / "data/processed/manganese_scored_grid_v3.geojson"
TARGETS = ROOT / "data/processed/manganese_prospectivity.geojson"
OUT_FEATURES = ROOT / "data/processed/manganese_topography_features.geojson"
OUT_TARGETS = ROOT / "data/processed/manganese_targets_v4.geojson"
OUT_TABLE = ROOT / "outputs/tables/manganese_targets_v4.csv"
MANIFEST = ROOT / "data/remote_sensing/remote_sensing_manifest.csv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def robust_stats(values):
    values = values[np.isfinite(values)]
    if values.size == 0:
        return np.nan, np.nan
    return float(np.nanmedian(values)), float(np.nanpercentile(values, 90) - np.nanpercentile(values, 10))


def sample_window(ds, x, y, radius=2):
    r, c = rowcol(ds.transform, x, y)
    if r < 0 or c < 0 or r >= ds.height or c >= ds.width:
        return np.nan, np.nan, np.nan, np.nan
    r0, r1 = max(0, r - radius), min(ds.height, r + radius + 1)
    c0, c1 = max(0, c - radius), min(ds.width, c + radius + 1)
    a = ds.read(1, window=((r0, r1), (c0, c1)), masked=True).astype("float64")
    vals = a.compressed()
    if vals.size == 0:
        return np.nan, np.nan, np.nan, np.nan
    elevation = float(np.median(vals))
    relief = float(np.percentile(vals, 90) - np.percentile(vals, 10))
    # A local plane-free slope proxy: robust elevation range divided by window span.
    pixel_m = max(abs(ds.transform.a) * 111320.0, 1.0)
    span_m = max(pixel_m * max(a.shape), 1.0)
    slope_deg = float(np.degrees(np.arctan(relief / span_m)))
    aspect_deg = np.nan
    return elevation, slope_deg, relief, aspect_deg


def main():
    if not DEM.exists():
        raise FileNotFoundError(DEM)
    grid = gpd.read_file(GRID).to_crs(4326)
    targets = gpd.read_file(TARGETS).to_crs(4326)
    with rasterio.open(DEM) as ds:
        grid_dem = grid.to_crs(ds.crs)
        rows = []
        for geom in grid_dem.geometry:
            p = geom.centroid
            elev, slope, relief, aspect = sample_window(ds, p.x, p.y)
            rows.append({
                "elevation_m": elev,
                "slope_deg": slope,
                "relief_m_local": relief,
                "aspect_deg": aspect,
                "dem_source": "ASTER_GDEM_V003",
                "dem_sha256": sha256(DEM),
                "dem_coverage": "WITHIN_TILE" if np.isfinite(elev) else "OUTSIDE_TILE",
                "topography_use": "FEATURE_READY_NOT_WEIGHTED_WITHOUT_LABELS",
            })
        features = grid.copy()
        for key in rows[0]:
            features[key] = [r[key] for r in rows]
    features.to_file(OUT_FEATURES, driver="GeoJSON")

    # Target polygons retain the existing conservative ranking and add terrain features.
    target_join = targets.merge(
        features[["grid_id", "elevation_m", "slope_deg", "relief_m_local", "dem_coverage"]],
        on="grid_id", how="left", suffixes=("", "_dem")
    )
    target_join["model_version"] = "v4-dem-enriched-screening"
    target_join["model_score_policy"] = "v3_score_retained; terrain features ready for labelled retraining"
    target_join.to_file(OUT_TARGETS, driver="GeoJSON")
    out = target_join.to_crs(4326)
    cent = target_join.to_crs(32640).geometry.centroid.to_crs(4326)
    table = out.drop(columns="geometry").copy()
    table["latitude"] = cent.y
    table["longitude"] = cent.x
    cols = ["candidate_id", "rank", "commodity", "manganese_score", "data_confidence_score", "model_status", "legal_status", "elevation_m", "slope_deg", "relief_m_local", "dem_coverage", "latitude", "longitude", "model_version"]
    table.rename(columns={"candidate_id": "target_id", "manganese_score": "model_score"}, inplace=True)
    table[[c for c in cols if c in table.columns]].to_csv(OUT_TABLE, index=False, encoding="utf-8-sig")

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["scene_id", "source_type", "acquisition_date", "cloud_screen", "crs", "checksum", "source_url", "status", "notes"])
        w.writeheader()
        w.writerow({
            "scene_id": "ASTGTMV003_N29E054",
            "source_type": "DEM",
            "acquisition_date": "2000-03-01/2013-11-30",
            "cloud_screen": "NOT_APPLICABLE",
            "crs": str(ds.crs),
            "checksum": sha256(DEM),
            "source_url": "https://doi.org/10.5067/ASTER/ASTGTM.003",
            "status": "PASS_TOPOGRAPHY_FEATURE_SOURCE",
            "notes": "DEM-derived features are available; not mineral evidence and not used as labels.",
        })
    print(f"Built {len(features)} DEM-enriched grid cells and {len(target_join)} target polygons")


if __name__ == "__main__":
    main()
