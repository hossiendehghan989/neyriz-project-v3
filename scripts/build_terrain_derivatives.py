#!/usr/bin/env python3
"""Build checksum-verified ASTER terrain derivatives for the Neyriz project.

This script creates reproducible terrain products only. It does not change the
manganese prospectivity score, infer a reserve or grade, or validate legal status.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer
from rasterio.enums import Resampling
from rasterio.features import geometry_mask
from rasterio.merge import merge
from rasterio.transform import Affine
from rasterio.warp import reproject, transform_bounds
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
WGS84 = "EPSG:4326"
DEFAULT_METRIC_CRS = "EPSG:32640"
SOURCE_DIR = ROOT / "data/remote_sensing/aster_gdem_v003"
CHECKSUM_MANIFEST = ROOT / "data/acquired/aster_gdem_v003_sha256.txt"
OUTPUT_DIR = ROOT / "data/processed/terrain"
TARGET_TABLE = ROOT / "outputs/tables/manganese_targets.csv"
TARGET_TERRAIN_TABLE = ROOT / "outputs/tables/manganese_targets_terrain_v31.csv"
RUN_MANIFEST = ROOT / "outputs/validation/terrain_run_manifest_v31.json"
NODATA = -9999.0


class TerrainPipelineError(RuntimeError):
    """Raised when an input or output does not meet the terrain pipeline contract."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_checksum_manifest(path: Path) -> dict[str, str]:
    if not path.exists():
        raise TerrainPipelineError(f"Checksum manifest is missing: {path.relative_to(ROOT)}")
    rows: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            expected, relative_path = line.split(maxsplit=1)
        except ValueError as exc:
            raise TerrainPipelineError(f"Malformed checksum row: {line}") from exc
        rows[relative_path.strip()] = expected.strip().lower()
    if not rows:
        raise TerrainPipelineError("Checksum manifest has no entries")
    return rows


def verify_checksums() -> list[dict[str, Any]]:
    """Verify every listed DEM tile before it is eligible for processing."""
    checksums = parse_checksum_manifest(CHECKSUM_MANIFEST)
    records: list[dict[str, Any]] = []
    for relative_path, expected in sorted(checksums.items()):
        path = ROOT / relative_path
        if not path.exists():
            raise TerrainPipelineError(f"Checksum-listed DEM tile is missing: {relative_path}")
        actual = sha256(path)
        if actual != expected:
            raise TerrainPipelineError(
                f"Checksum mismatch for {relative_path}: expected {expected}, got {actual}"
            )
        records.append(
            {
                "path": relative_path,
                "sha256": actual,
                "size_bytes": path.stat().st_size,
                "status": "VERIFIED",
            }
        )
    return records


def load_aoi(aoi_file: Path | None, buffer_m: float, target_crs: str) -> tuple[gpd.GeoDataFrame, str]:
    """Load an explicit AOI or make a clearly labelled provisional evidence envelope."""
    if aoi_file:
        if not aoi_file.exists():
            raise TerrainPipelineError(f"AOI file is missing: {aoi_file}")
        aoi = gpd.read_file(aoi_file)
        if aoi.empty or aoi.crs is None:
            raise TerrainPipelineError("AOI must contain at least one geometry and an explicit CRS")
        aoi = aoi.to_crs(WGS84)
        source = f"EXPLICIT_AOI:{aoi_file.relative_to(ROOT) if aoi_file.is_relative_to(ROOT) else aoi_file}"
    else:
        evidence_files = [
            ROOT / "data/reference/supplied_steps/step_02_geology_neyriz/host_lithology_units.geojson",
            ROOT / "data/reference/supplied_steps/step_03_faults_targets_neyriz/faults_step03.geojson",
            ROOT / "data/reference/supplied_steps/step_01_manganese_nasirabad_neyriz/manganese_confirmed_step01.geojson",
        ]
        frames = []
        for path in evidence_files:
            if not path.exists():
                raise TerrainPipelineError(f"Cannot construct provisional AOI; missing {path.relative_to(ROOT)}")
            frame = gpd.read_file(path)
            if frame.empty or frame.crs is None:
                raise TerrainPipelineError(f"Cannot construct provisional AOI; invalid {path.relative_to(ROOT)}")
            frames.append(frame.to_crs(target_crs))
        geometry = unary_union([geom for frame in frames for geom in frame.geometry if geom is not None])
        if geometry.is_empty:
            raise TerrainPipelineError("Cannot construct provisional AOI from empty project evidence")
        # A small metric buffer protects edge derivatives; the envelope makes the processing window explicit.
        aoi_metric = gpd.GeoDataFrame(
            {"aoi_status": ["PROVISIONAL_EVIDENCE_ENVELOPE"]},
            geometry=[geometry.buffer(buffer_m).envelope],
            crs=target_crs,
        )
        aoi = aoi_metric.to_crs(WGS84)
        source = "PROVISIONAL_EVIDENCE_ENVELOPE_FROM_EXISTING_PROJECT_LAYERS"
    if not aoi.geometry.is_valid.all():
        aoi["geometry"] = aoi.geometry.make_valid()
    return aoi, source


def selected_sources(aoi_bounds: tuple[float, float, float, float]) -> list[Path]:
    """Return only checksum-listed tiles that intersect the requested AOI bounds."""
    paths: list[Path] = []
    for relative_path in parse_checksum_manifest(CHECKSUM_MANIFEST):
        path = ROOT / relative_path
        with rasterio.open(path) as dataset:
            if dataset.crs is None or dataset.crs.to_string() != WGS84:
                raise TerrainPipelineError(f"Expected EPSG:4326 DEM tile: {path.relative_to(ROOT)}")
            left, bottom, right, top = dataset.bounds
            minx, miny, maxx, maxy = aoi_bounds
            intersects = not (right <= minx or left >= maxx or top <= miny or bottom >= maxy)
            if intersects:
                paths.append(path)
    if not paths:
        raise TerrainPipelineError("No checksum-verified DEM tile intersects the AOI")
    return paths


def aligned_metric_grid(
    bounds: tuple[float, float, float, float], resolution_m: float
) -> tuple[Affine, int, int]:
    minx, miny, maxx, maxy = bounds
    minx = math.floor(minx / resolution_m) * resolution_m
    miny = math.floor(miny / resolution_m) * resolution_m
    maxx = math.ceil(maxx / resolution_m) * resolution_m
    maxy = math.ceil(maxy / resolution_m) * resolution_m
    width = max(1, int(round((maxx - minx) / resolution_m)))
    height = max(1, int(round((maxy - miny) / resolution_m)))
    return Affine(resolution_m, 0.0, minx, 0.0, -resolution_m, maxy), width, height


def box_sum(array: np.ndarray, radius: int) -> np.ndarray:
    """Return centered box sums with zero padding, without a scipy dependency."""
    if radius < 0:
        raise ValueError("radius must be non-negative")
    padded = np.pad(array, radius, mode="constant", constant_values=0.0)
    integral = np.zeros((padded.shape[0] + 1, padded.shape[1] + 1), dtype=np.float64)
    integral[1:, 1:] = padded.cumsum(axis=0, dtype=np.float64).cumsum(axis=1, dtype=np.float64)
    height, width = array.shape
    window = radius * 2 + 1
    y0 = np.arange(height)[:, None]
    x0 = np.arange(width)[None, :]
    y1 = y0 + window
    x1 = x0 + window
    return integral[y1, x1] - integral[y0, x1] - integral[y1, x0] + integral[y0, x0]


def terrain_derivatives(dem: np.ndarray, resolution_m: float) -> dict[str, np.ndarray]:
    """Calculate terrain derivatives in a metric CRS, preserving nodata as NaN."""
    if dem.ndim != 2 or resolution_m <= 0:
        raise ValueError("DEM must be two-dimensional and resolution must be positive")
    with np.errstate(invalid="ignore", divide="ignore"):
        dz_dy, dz_dx = np.gradient(dem, resolution_m, resolution_m)
        slope = np.degrees(np.arctan(np.hypot(dz_dx, dz_dy)))
        aspect = (np.degrees(np.arctan2(dz_dx, -dz_dy)) + 360.0) % 360.0
        aspect[slope <= 0.1] = np.nan

        d2z_dx2 = np.gradient(dz_dx, resolution_m, axis=1)
        d2z_dy2 = np.gradient(dz_dy, resolution_m, axis=0)
        d2z_dxdy = np.gradient(dz_dx, resolution_m, axis=0)
        p2_q2 = dz_dx**2 + dz_dy**2
        profile_denominator = p2_q2 * (1.0 + p2_q2) ** 1.5
        profile_curvature = -(
            dz_dx**2 * d2z_dx2 + 2.0 * dz_dx * dz_dy * d2z_dxdy + dz_dy**2 * d2z_dy2
        ) / profile_denominator
        profile_curvature[profile_denominator < 1e-12] = np.nan

        valid = np.isfinite(dem)
        count = box_sum(valid.astype(np.float64), radius=1)
        total = box_sum(np.where(valid, dem, 0.0), radius=1)
        total_sq = box_sum(np.where(valid, dem**2, 0.0), radius=1)
        mean = total / np.where(count == 0, np.nan, count)
        variance = np.maximum(total_sq / np.where(count == 0, np.nan, count) - mean**2, 0.0)
        roughness = np.sqrt(variance)
        roughness[count < 5] = np.nan

        altitude = np.radians(45.0)
        azimuth = np.radians(315.0)
        # Aspect is undefined on a flat surface, but its hillshade remains well defined.
        hillshade_aspect = np.where(np.isfinite(aspect), aspect, 0.0)
        shaded = 255.0 * (
            np.cos(altitude) * np.cos(np.radians(slope))
            + np.sin(altitude) * np.sin(np.radians(slope)) * np.cos(azimuth - np.radians(hillshade_aspect))
        )
        hillshade = np.clip(shaded, 0.0, 255.0)

    valid_dem = np.isfinite(dem)
    for result in (slope, aspect, profile_curvature, roughness, hillshade):
        result[~valid_dem] = np.nan
    return {
        "dem_elevation_m": dem,
        "slope_degrees": slope,
        "aspect_degrees": aspect,
        "profile_curvature_per_m": profile_curvature,
        "roughness_stddev_m_3x3": roughness,
        "hillshade_315az_45alt": hillshade,
    }


def raster_stats(array: np.ndarray) -> dict[str, float | int | None]:
    valid = array[np.isfinite(array)]
    if valid.size == 0:
        return {"valid_cells": 0, "min": None, "max": None, "mean": None, "std": None}
    return {
        "valid_cells": int(valid.size),
        "min": round(float(np.min(valid)), 6),
        "max": round(float(np.max(valid)), 6),
        "mean": round(float(np.mean(valid)), 6),
        "std": round(float(np.std(valid)), 6),
    }


def write_raster(
    path: Path,
    array: np.ndarray,
    transform: Affine,
    crs: str,
    derivative: str,
    units: str,
) -> None:
    output = np.where(np.isfinite(array), array, NODATA).astype("float32")
    profile = {
        "driver": "GTiff",
        "height": output.shape[0],
        "width": output.shape[1],
        "count": 1,
        "dtype": "float32",
        "crs": crs,
        "transform": transform,
        "nodata": NODATA,
        "compress": "deflate",
        "predictor": 3,
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
        "BIGTIFF": "IF_SAFER",
    }
    with rasterio.open(path, "w", **profile) as dataset:
        dataset.write(output, 1)
        dataset.update_tags(
            PRODUCT="Neyriz terrain derivative v3.1",
            DERIVATIVE=derivative,
            UNITS=units,
            SOURCE="ASTER GDEM V003; checksum-verified source tiles",
            MODEL_INTEGRATION="NOT_APPLIED",
        )


def sample_targets(raster_paths: dict[str, Path], run_id: str) -> int:
    """Create a non-modelled terrain attribute table for the existing target list."""
    if not TARGET_TABLE.exists():
        print("INFO — manganese target table not found; terrain target table was not created")
        return 0
    targets = pd.read_csv(TARGET_TABLE)
    required_columns = {"target_id", "latitude", "longitude", "model_score"}
    missing = required_columns.difference(targets.columns)
    if missing:
        raise TerrainPipelineError(f"Target table lacks required columns: {sorted(missing)}")
    transformer = Transformer.from_crs(WGS84, DEFAULT_METRIC_CRS, always_xy=True)
    xs, ys = transformer.transform(targets["longitude"].to_numpy(), targets["latitude"].to_numpy())
    coordinates = list(zip(xs, ys))
    for column, path in raster_paths.items():
        with rasterio.open(path) as dataset:
            values = [float(value[0]) for value in dataset.sample(coordinates)]
        values = [np.nan if value <= NODATA + 1 else value for value in values]
        targets[f"terrain_{column}"] = values
    targets["terrain_run_id"] = run_id
    targets["terrain_feature_status"] = "DERIVED_NOT_MODELLED"
    targets["terrain_model_integration"] = "NOT_APPLIED"
    targets.to_csv(TARGET_TERRAIN_TABLE, index=False, encoding="utf-8-sig")
    return len(targets)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--aoi-file",
        type=Path,
        help="Optional CRS-defined AOI vector. Without it, a labelled provisional evidence envelope is used.",
    )
    parser.add_argument(
        "--aoi-buffer-m",
        type=float,
        default=1000.0,
        help="Buffer around existing evidence when --aoi-file is not supplied (default: 1000 m).",
    )
    parser.add_argument(
        "--resolution-m",
        type=float,
        default=30.0,
        help="Metric output resolution in metres (default: 30).",
    )
    parser.add_argument(
        "--target-crs",
        default=DEFAULT_METRIC_CRS,
        help=f"Metric CRS for derivatives (default: {DEFAULT_METRIC_CRS}).",
    )
    parser.add_argument(
        "--skip-checksum-verification",
        action="store_true",
        help="Skip source checksum verification; intended only for diagnostics, never production.",
    )
    args = parser.parse_args()
    if args.aoi_buffer_m < 0 or args.resolution_m <= 0:
        raise TerrainPipelineError("AOI buffer must be non-negative and resolution must be positive")
    if args.target_crs != DEFAULT_METRIC_CRS:
        raise TerrainPipelineError(f"Only {DEFAULT_METRIC_CRS} is approved for this Neyriz terrain workflow")

    checksum_records = (
        [{"status": "SKIPPED_DIAGNOSTIC_ONLY"}]
        if args.skip_checksum_verification
        else verify_checksums()
    )
    print(f"PASS — verified {len(checksum_records)} checksum-listed DEM tile(s)")

    aoi, aoi_source = load_aoi(args.aoi_file, args.aoi_buffer_m, args.target_crs)
    aoi_bounds = tuple(float(value) for value in aoi.total_bounds)
    source_paths = selected_sources(aoi_bounds)
    print(f"PASS — selected {len(source_paths)} DEM tile(s) for AOI")

    with rasterio.Env():
        datasets = [rasterio.open(path) for path in source_paths]
        try:
            source, source_transform = merge(datasets, bounds=aoi_bounds, nodata=NODATA, dtype="float32")
            source_dem = source[0]
            source_crs = datasets[0].crs
        finally:
            for dataset in datasets:
                dataset.close()

    metric_bounds = transform_bounds(source_crs, args.target_crs, *aoi_bounds, densify_pts=21)
    output_transform, width, height = aligned_metric_grid(metric_bounds, args.resolution_m)
    destination = np.full((height, width), NODATA, dtype="float32")
    reproject(
        source=source_dem,
        destination=destination,
        src_transform=source_transform,
        src_crs=source_crs,
        src_nodata=NODATA,
        dst_transform=output_transform,
        dst_crs=args.target_crs,
        dst_nodata=NODATA,
        resampling=Resampling.bilinear,
    )
    dem = np.where(destination <= NODATA + 1, np.nan, destination).astype("float64")
    aoi_metric = aoi.to_crs(args.target_crs)
    inside_aoi = geometry_mask(
        [geometry.__geo_interface__ for geometry in aoi_metric.geometry],
        out_shape=dem.shape,
        transform=output_transform,
        invert=True,
    )
    dem[~inside_aoi] = np.nan
    if int(np.isfinite(dem).sum()) < 100:
        raise TerrainPipelineError("AOI contains fewer than 100 valid DEM cells after reprojection")

    derivatives = terrain_derivatives(dem, args.resolution_m)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    aoi_path = OUTPUT_DIR / "aoi_used_v31.geojson"
    aoi_to_write = aoi.copy()
    aoi_to_write["aoi_source"] = aoi_source
    aoi_to_write.to_file(aoi_path, driver="GeoJSON")

    specifications = {
        "dem_elevation_m": ("dem_elevation_m.tif", "elevation", "metres"),
        "slope_degrees": ("slope_degrees.tif", "slope", "degrees"),
        "aspect_degrees": ("aspect_degrees.tif", "aspect", "degrees clockwise from north"),
        "profile_curvature_per_m": ("profile_curvature_per_m.tif", "profile_curvature", "1/metre"),
        "roughness_stddev_m_3x3": ("roughness_stddev_m_3x3.tif", "roughness", "metres, 3x3-cell standard deviation"),
        "hillshade_315az_45alt": ("hillshade_315az_45alt.tif", "hillshade", "0-255; azimuth 315°, altitude 45°"),
    }
    raster_paths: dict[str, Path] = {}
    derivative_metadata: dict[str, Any] = {}
    for name, (filename, derivative, units) in specifications.items():
        path = OUTPUT_DIR / filename
        write_raster(path, derivatives[name], output_transform, args.target_crs, derivative, units)
        raster_paths[name] = path
        derivative_metadata[name] = {
            "path": str(path.relative_to(ROOT)),
            "units": units,
            "statistics": raster_stats(derivatives[name]),
            "sha256": sha256(path),
        }

    run_seed = json.dumps(
        {
            "sources": checksum_records,
            "aoi_bounds": [round(value, 8) for value in aoi_bounds],
            "resolution_m": args.resolution_m,
            "target_crs": args.target_crs,
        },
        sort_keys=True,
    ).encode("utf-8")
    run_id = f"terrain-v31-{hashlib.sha256(run_seed).hexdigest()[:12]}"
    target_count = sample_targets(raster_paths, run_id)

    RUN_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": "1.0",
        "run_id": run_id,
        "pipeline": "scripts/build_terrain_derivatives.py",
        "source_dataset": "ASTER Global Digital Elevation Model V003",
        "checksum_verification": "SKIPPED_DIAGNOSTIC_ONLY" if args.skip_checksum_verification else "PASS",
        "source_tiles": checksum_records,
        "tiles_selected_for_aoi": [str(path.relative_to(ROOT)) for path in source_paths],
        "aoi": {
            "source": aoi_source,
            "bounds_wgs84": [round(value, 8) for value in aoi_bounds],
            "path": str(aoi_path.relative_to(ROOT)),
            "note": "A provisional evidence envelope is not a legal, cadastral, or permit boundary.",
        },
        "processing": {
            "target_crs": args.target_crs,
            "resolution_m": args.resolution_m,
            "resampling": "bilinear",
            "nodata": NODATA,
            "roughness_window": "3x3 cells",
            "hillshade": "azimuth 315°, altitude 45°",
        },
        "derivatives": derivative_metadata,
        "manganese_target_terrain_rows": target_count,
        "model_integration": "NOT_APPLIED",
        "scientific_guardrail_fa": "مشتقات DEM فقط ویژگی‌های توپوگرافی هستند و بدون داده و آزمون مستقل، امتیاز، احتمال، ذخیره، عیار یا وضعیت حقوقی را تغییر نمی‌دهند.",
    }
    RUN_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"PASS — wrote {len(raster_paths)} terrain rasters to {OUTPUT_DIR.relative_to(ROOT)}")
    print(f"PASS — wrote run manifest {RUN_MANIFEST.relative_to(ROOT)}")
    if target_count:
        print(f"PASS — sampled terrain at {target_count} existing manganese targets")


if __name__ == "__main__":
    try:
        main()
    except TerrainPipelineError as exc:
        print(f"FAIL — {exc}")
        raise SystemExit(2)
