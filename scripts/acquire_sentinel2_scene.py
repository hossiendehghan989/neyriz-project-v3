#!/usr/bin/env python3
"""Acquire one pinned, public Sentinel-2 L2A scene and clip it to a project AOI.

SAS credentials are requested at runtime and never written to disk. Spectral
assets remain quantized source digital numbers; this script does not rescale,
cloud-fill, derive indices, or add imagery to the prospectivity model.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import geopandas as gpd
import numpy as np
import rasterio
import requests
from rasterio.features import geometry_mask
from rasterio.windows import Window, from_bounds
from shapely.geometry import shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
STAC_ROOT = "https://planetarycomputer.microsoft.com/api/stac/v1"
SAS_ROOT = "https://planetarycomputer.microsoft.com/api/sas/v1"
COLLECTION = "sentinel-2-l2a"
DEFAULT_ITEM = "S2C_MSIL2A_20260917T065621_R063_T40RBT_20260917T121802"
DEFAULT_AOI = ROOT / "data/processed/terrain/aoi_used_v31.geojson"
DEFAULT_OUTPUT_ROOT = ROOT / "data/remote_sensing/sentinel2"
DEFAULT_ITEM_ARCHIVE = ROOT / "data/acquired/sentinel2"
DEFAULT_QC_MANIFEST = ROOT / "outputs/validation/sentinel2_scene_manifest.json"
REMOTE_SENSING_CSV = ROOT / "data/remote_sensing/remote_sensing_manifest.csv"
TILE_CLOUD_MAX_PERCENT = 5.0
AOI_CLOUD_SHADOW_MAX_PERCENT = 5.0
MIN_CLEAR_AOI_PERCENT = 90.0
NODATA = 0
BANDS_10M = ["B02", "B03", "B04", "B08"]
BANDS_20M = ["B05", "B06", "B07", "B8A", "B11", "B12"]
CLOUD_SHADOW_CLASSES = {3, 8, 9, 10}
CLEAR_SURFACE_CLASSES = {4, 5, 6}
CSV_FIELDS = [
    "scene_id",
    "acquisition_datetime_utc",
    "platform",
    "collection",
    "scene_cloud_cover_pct",
    "aoi_cloud_shadow_cirrus_pct",
    "aoi_clear_surface_pct",
    "aoi_status",
    "aoi_geojson",
    "aoi_sha256",
    "spectral_10m_path",
    "spectral_10m_sha256",
    "spectral_20m_path",
    "spectral_20m_sha256",
    "scene_classification_path",
    "scene_classification_sha256",
    "clear_mask_path",
    "clear_mask_sha256",
    "item_metadata_path",
    "item_metadata_sha256",
    "quality_status",
    "model_integration",
    "source_catalog",
    "source_license",
]


class AcquisitionError(RuntimeError):
    """Raised when imagery fails the acquisition or quality contract."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_item(item_id: str) -> dict[str, Any]:
    url = f"{STAC_ROOT}/collections/{COLLECTION}/items/{item_id}"
    response = requests.get(url, timeout=90)
    response.raise_for_status()
    item = response.json()
    if item.get("id") != item_id or item.get("collection") != COLLECTION:
        raise AcquisitionError("STAC response did not match the requested Sentinel-2 L2A item")
    return item


def signed_assets(item: dict[str, Any], asset_names: list[str]) -> dict[str, str]:
    """Sign requested public-archive asset URLs without persisting the SAS token."""
    token_response = requests.get(f"{SAS_ROOT}/token/{COLLECTION}", timeout=90)
    token_response.raise_for_status()
    token_data = token_response.json()
    token = token_data.get("token")
    if not token:
        raise AcquisitionError("Planetary Computer did not return an access token")
    signed: dict[str, str] = {}
    for name in asset_names:
        asset = item.get("assets", {}).get(name)
        if not asset or not asset.get("href"):
            raise AcquisitionError(f"Required STAC asset is missing: {name}")
        href = asset["href"]
        host = urlparse(href).hostname
        if not host or not host.endswith("blob.core.windows.net"):
            raise AcquisitionError(f"Unexpected Sentinel asset host for {name}: {host}")
        signed[name] = f"{href}{'&' if '?' in href else '?'}{token}"
    # Deliberately do not log or save the token, expiry token, or signed asset hrefs.
    return signed


def clipped_window(dataset: rasterio.io.DatasetReader, bounds: tuple[float, float, float, float]) -> Window:
    raw = from_bounds(*bounds, transform=dataset.transform)
    col0 = max(0, math.floor(raw.col_off))
    row0 = max(0, math.floor(raw.row_off))
    col1 = min(dataset.width, math.ceil(raw.col_off + raw.width))
    row1 = min(dataset.height, math.ceil(raw.row_off + raw.height))
    if col1 <= col0 or row1 <= row0:
        raise AcquisitionError("AOI does not overlap a required Sentinel-2 asset")
    return Window(col0, row0, col1 - col0, row1 - row0)


def write_multiband(
    path: Path,
    arrays: list[np.ndarray],
    band_names: list[str],
    transform: rasterio.Affine,
    crs: Any,
    resolution_m: int,
    aoi_mask: np.ndarray,
    item_id: str,
) -> None:
    if len(arrays) != len(band_names) or not arrays:
        raise AcquisitionError("Band arrays and band names do not match")
    shape_hw = arrays[0].shape
    if any(array.shape != shape_hw for array in arrays) or aoi_mask.shape != shape_hw:
        raise AcquisitionError(f"Inconsistent arrays in the {resolution_m}m spectral stack")
    data = np.stack(arrays).astype("uint16", copy=False)
    data[:, ~aoi_mask] = NODATA
    profile = {
        "driver": "GTiff",
        "width": shape_hw[1],
        "height": shape_hw[0],
        "count": len(arrays),
        "dtype": "uint16",
        "crs": crs,
        "transform": transform,
        "nodata": NODATA,
        "compress": "deflate",
        "predictor": 2,
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
        "BIGTIFF": "IF_SAFER",
    }
    with rasterio.open(path, "w", **profile) as output:
        output.write(data)
        output.update_tags(
            PRODUCT="Sentinel-2 Level-2A clipped project input",
            SCENE_ID=item_id,
            COLLECTION=COLLECTION,
            SPATIAL_RESOLUTION_M=str(resolution_m),
            PIXEL_VALUES="Source L2A quantized values; no scaling, offset, or atmospheric reprocessing applied",
            AOI_MASK="Pixels outside the project polygon are set to NoData",
            MODEL_INTEGRATION="NOT_APPLIED",
        )
        for index, band in enumerate(band_names, start=1):
            output.set_band_description(index, band)


def write_singleband(
    path: Path,
    array: np.ndarray,
    description: str,
    transform: rasterio.Affine,
    crs: Any,
    dtype: str,
    nodata: int,
    item_id: str,
    tags: dict[str, str],
) -> None:
    encoded = array.astype(dtype, copy=False)
    profile = {
        "driver": "GTiff",
        "width": encoded.shape[1],
        "height": encoded.shape[0],
        "count": 1,
        "dtype": dtype,
        "crs": crs,
        "transform": transform,
        "nodata": nodata,
        "compress": "deflate",
        "predictor": 2 if dtype in ("uint16", "int16") else 1,
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
        "BIGTIFF": "IF_SAFER",
    }
    with rasterio.open(path, "w", **profile) as output:
        output.write(encoded, 1)
        output.set_band_description(1, description)
        output.update_tags(SCENE_ID=item_id, MODEL_INTEGRATION="NOT_APPLIED", **tags)


def read_asset_window(href: str, expected_resolution: float, bounds: tuple[float, float, float, float]):
    dataset = rasterio.open(href)
    if dataset.crs is None or dataset.crs.to_epsg() != 32640:
        dataset.close()
        raise AcquisitionError(f"Expected an EPSG:32640 asset, received {dataset.crs}")
    if not (math.isclose(abs(dataset.transform.a), expected_resolution, abs_tol=1e-6)
            and math.isclose(abs(dataset.transform.e), expected_resolution, abs_tol=1e-6)):
        dataset.close()
        raise AcquisitionError(
            f"Expected {expected_resolution}m asset, received pixel size {dataset.res}"
        )
    window = clipped_window(dataset, bounds)
    array = dataset.read(1, window=window)
    transform = dataset.window_transform(window)
    nodata = dataset.nodata
    return dataset, array, transform, nodata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--item-id", default=DEFAULT_ITEM, help="Pinned STAC item ID")
    parser.add_argument("--aoi-file", type=Path, default=DEFAULT_AOI, help="AOI GeoJSON/vector with CRS")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--item-archive", type=Path, default=DEFAULT_ITEM_ARCHIVE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_QC_MANIFEST)
    parser.add_argument("--max-scene-cloud-percent", type=float, default=TILE_CLOUD_MAX_PERCENT)
    parser.add_argument("--max-aoi-cloud-shadow-percent", type=float, default=AOI_CLOUD_SHADOW_MAX_PERCENT)
    parser.add_argument("--min-clear-aoi-percent", type=float, default=MIN_CLEAR_AOI_PERCENT)
    args = parser.parse_args()

    if not args.aoi_file.exists():
        raise AcquisitionError(f"AOI file does not exist: {args.aoi_file}")
    aoi = gpd.read_file(args.aoi_file)
    if aoi.empty or aoi.crs is None:
        raise AcquisitionError("AOI must have at least one geometry and an explicit CRS")
    aoi = aoi.to_crs("EPSG:32640")
    aoi_geometry = unary_union([geometry for geometry in aoi.geometry if geometry is not None])
    if aoi_geometry.is_empty or not aoi_geometry.is_valid:
        raise AcquisitionError("AOI geometry must be non-empty and valid")

    item = fetch_item(args.item_id)
    properties = item.get("properties", {})
    scene_cloud = properties.get("eo:cloud_cover")
    if scene_cloud is None or float(scene_cloud) > args.max_scene_cloud_percent:
        raise AcquisitionError(
            f"Scene-level cloud cover ({scene_cloud}) does not meet the "
            f"{args.max_scene_cloud_percent}% threshold"
        )
    footprint = shape(item["geometry"])
    aoi_wgs84 = unary_union([geometry for geometry in aoi.to_crs("EPSG:4326").geometry if geometry is not None])
    if not footprint.intersects(aoi_wgs84):
        raise AcquisitionError("STAC scene footprint does not intersect the requested AOI")

    band_names = BANDS_10M + BANDS_20M + ["SCL"]
    hrefs = signed_assets(item, band_names)
    output_dir = args.output_root / properties["datetime"][:10]
    output_dir.mkdir(parents=True, exist_ok=True)
    args.item_archive.mkdir(parents=True, exist_ok=True)

    # Preserve unsigned STAC metadata only; SAS query tokens are never archived.
    item_path = args.item_archive / f"{args.item_id}.json"
    item_path.write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
    item_metadata_sha256 = sha256(item_path)

    bounds = tuple(float(value) for value in aoi_geometry.bounds)
    opened: list[rasterio.io.DatasetReader] = []
    try:
        arrays_10m: list[np.ndarray] = []
        transform_10m = None
        crs = None
        mask_10m = None
        for name in BANDS_10M:
            dataset, values, transform, nodata = read_asset_window(hrefs[name], 10, bounds)
            opened.append(dataset)
            if transform_10m is None:
                transform_10m, crs = transform, dataset.crs
                mask_10m = geometry_mask(
                    [aoi_geometry.__geo_interface__],
                    out_shape=values.shape,
                    transform=transform_10m,
                    invert=True,
                )
            elif transform != transform_10m or values.shape != arrays_10m[0].shape:
                raise AcquisitionError("10m spectral assets are not aligned to a common grid")
            if nodata is not None and nodata != NODATA:
                values = values.copy()
                values[values == nodata] = NODATA
            arrays_10m.append(values)
        assert transform_10m is not None and crs is not None and mask_10m is not None
        spectral_10m_path = output_dir / "sentinel2_spectral_10m.tif"
        write_multiband(
            spectral_10m_path, arrays_10m, BANDS_10M, transform_10m, crs, 10,
            mask_10m, args.item_id,
        )
        for dataset in opened:
            dataset.close()
        opened.clear()

        arrays_20m: list[np.ndarray] = []
        transform_20m = None
        mask_20m = None
        for name in BANDS_20M:
            dataset, values, transform, nodata = read_asset_window(hrefs[name], 20, bounds)
            opened.append(dataset)
            if transform_20m is None:
                transform_20m = transform
                mask_20m = geometry_mask(
                    [aoi_geometry.__geo_interface__],
                    out_shape=values.shape,
                    transform=transform_20m,
                    invert=True,
                )
            elif transform != transform_20m or values.shape != arrays_20m[0].shape:
                raise AcquisitionError("20m spectral assets are not aligned to a common grid")
            if nodata is not None and nodata != NODATA:
                values = values.copy()
                values[values == nodata] = NODATA
            arrays_20m.append(values)
        dataset, scl, scl_transform, scl_nodata = read_asset_window(hrefs["SCL"], 20, bounds)
        opened.append(dataset)
        if scl_transform != transform_20m or scl.shape != arrays_20m[0].shape:
            raise AcquisitionError("SCL and 20m spectral assets are not aligned")
        assert transform_20m is not None and mask_20m is not None

        # AOI-only statistics use the native 20m scene-classification product.
        scl_inside = scl[mask_20m]
        classes, counts = np.unique(scl_inside, return_counts=True)
        class_counts = {str(int(code)): int(count) for code, count in zip(classes, counts)}
        total_pixels = int(scl_inside.size)
        if total_pixels == 0:
            raise AcquisitionError("No SCL pixels fall inside the AOI")
        cloud_codes = CLOUD_SHADOW_CLASSES
        clear_codes = CLEAR_SURFACE_CLASSES
        cloud_pixels = sum(class_counts.get(str(code), 0) for code in cloud_codes)
        clear_pixels = sum(class_counts.get(str(code), 0) for code in clear_codes)
        aoi_cloud_shadow_pct = 100.0 * cloud_pixels / total_pixels
        aoi_clear_pct = 100.0 * clear_pixels / total_pixels
        if aoi_cloud_shadow_pct > args.max_aoi_cloud_shadow_percent:
            raise AcquisitionError(
                f"AOI cloud/shadow/cirrus is {aoi_cloud_shadow_pct:.4f}% "
                f"(threshold {args.max_aoi_cloud_shadow_percent}%)"
            )
        if aoi_clear_pct < args.min_clear_aoi_percent:
            raise AcquisitionError(
                f"AOI clear surface is {aoi_clear_pct:.4f}% "
                f"(minimum {args.min_clear_aoi_percent}%)"
            )

        spectral_20m_path = output_dir / "sentinel2_spectral_20m.tif"
        write_multiband(
            spectral_20m_path, arrays_20m, BANDS_20M, transform_20m, crs, 20,
            mask_20m, args.item_id,
        )
        scl_path = output_dir / "sentinel2_scl_20m.tif"
        scl_out = scl.copy()
        scl_out[~mask_20m] = NODATA
        write_singleband(
            scl_path, scl_out, "Sentinel-2 Scene Classification Layer (SCL)",
            transform_20m, crs, "uint8", NODATA, args.item_id,
            {"CLASS_CODES_SOURCE": "Sentinel-2 Level-2A Scene Classification Layer", "PIXEL_SIZE_M": "20"},
        )
        clear_mask = np.isin(scl, list(clear_codes)).astype("uint8")
        clear_mask[~mask_20m] = 255
        clear_mask_path = output_dir / "sentinel2_clear_surface_mask_20m.tif"
        write_singleband(
            clear_mask_path, clear_mask, "1=clear vegetation/bare soil/water; 0=other or obscured",
            transform_20m, crs, "uint8", 255, args.item_id,
            {
                "PIXEL_SIZE_M": "20",
                "CLEAR_SCL_CLASSES": "4,5,6",
                "CLOUD_SHADOW_CIRRUS_SCL_CLASSES": "3,8,9,10",
                "NOTE": "Only classes 4,5,6 are set to 1; other inside-AOI classes are 0; outside-AOI pixels are NoData=255.",
            },
        )
    finally:
        for dataset in opened:
            dataset.close()

    aoi_sha256 = sha256(args.aoi_file)
    aoi_status_values = aoi.get("aoi_status", [])
    aoi_status = ";".join(sorted({str(value) for value in aoi_status_values})) or "USER_PROVIDED"
    outputs = {
        "spectral_10m": {"path": str(spectral_10m_path.relative_to(ROOT)), "sha256": sha256(spectral_10m_path), "bands": BANDS_10M, "resolution_m": 10},
        "spectral_20m": {"path": str(spectral_20m_path.relative_to(ROOT)), "sha256": sha256(spectral_20m_path), "bands": BANDS_20M, "resolution_m": 20},
        "scene_classification_20m": {"path": str(scl_path.relative_to(ROOT)), "sha256": sha256(scl_path), "resolution_m": 20},
        "clear_mask_20m": {"path": str(clear_mask_path.relative_to(ROOT)), "sha256": sha256(clear_mask_path), "resolution_m": 20},
    }
    manifest = {
        "schema_version": "1.0",
        "scene_id": args.item_id,
        "collection": COLLECTION,
        "source_catalog": "Microsoft Planetary Computer STAC; source mission/product: Copernicus Sentinel-2 Level-2A",
        "source_item_url": f"{STAC_ROOT}/collections/{COLLECTION}/items/{args.item_id}",
        "source_license_url": next((link["href"] for link in item.get("links", []) if link.get("rel") == "license"), "https://sentinel.esa.int/documents/247904/690755/Sentinel_Data_Legal_Notice"),
        "acquisition_datetime_utc": properties.get("datetime"),
        "platform": properties.get("platform"),
        "tile": "T40RBT",
        "scene_cloud_cover_pct": float(scene_cloud),
        "aoi": {
            "path": str(args.aoi_file.relative_to(ROOT)) if args.aoi_file.is_relative_to(ROOT) else str(args.aoi_file),
            "sha256": aoi_sha256,
            "status": aoi_status,
            "crs_for_analysis": "EPSG:32640",
            "bounds_epsg32640_m": [round(float(value), 3) for value in bounds],
            "note": "The current project AOI is a provisional evidence envelope, not a legal, cadastral, or permit boundary.",
        },
        "quality_control": {
            "status": "PASS",
            "scene_cloud_cover_max_pct": args.max_scene_cloud_percent,
            "aoi_cloud_shadow_cirrus_pct": round(aoi_cloud_shadow_pct, 6),
            "aoi_clear_surface_pct": round(aoi_clear_pct, 6),
            "aoi_scl_pixel_count": total_pixels,
            "aoi_scl_class_counts": class_counts,
            "cloud_shadow_cirrus_scl_classes": sorted(cloud_codes),
            "clear_surface_scl_classes": sorted(clear_codes),
        },
        "processing": {
            "download_method": "Range reads from cloud-optimized GeoTIFF assets with temporary SAS authorization",
            "bands_10m": BANDS_10M,
            "bands_20m": BANDS_20M,
            "reflectance_values": "Original quantized Level-2A source values (DN); no scale/offset applied",
            "aoi_clip": "Exact AOI geometry mask; outside pixels set to NoData=0",
            "cloud_handling": "Original band pixels preserved; explicit 20m SCL and clear-surface mask are supplied",
            "derived_indices": "NOT_GENERATED",
            "model_integration": "NOT_APPLIED",
        },
        "stac_item_metadata": {
            "path": str(item_path.relative_to(ROOT)),
            "sha256": item_metadata_sha256,
            "note": "Unsigned public STAC metadata only; no SAS token or signed URL is stored.",
        },
        "outputs": outputs,
        "scientific_guardrail_fa": "تصویر و ماسک کیفیت وارد ریپو شده است؛ هنوز شاخص طیفی، ویژگی مدل، احتمال، ذخیره، عیار یا دقت استخراج/ادعا نشده است.",
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    csv_row = {
        "scene_id": args.item_id,
        "acquisition_datetime_utc": properties.get("datetime"),
        "platform": properties.get("platform"),
        "collection": COLLECTION,
        "scene_cloud_cover_pct": f"{float(scene_cloud):.6f}",
        "aoi_cloud_shadow_cirrus_pct": f"{aoi_cloud_shadow_pct:.6f}",
        "aoi_clear_surface_pct": f"{aoi_clear_pct:.6f}",
        "aoi_status": aoi_status,
        "aoi_geojson": manifest["aoi"]["path"],
        "aoi_sha256": aoi_sha256,
        "spectral_10m_path": outputs["spectral_10m"]["path"],
        "spectral_10m_sha256": outputs["spectral_10m"]["sha256"],
        "spectral_20m_path": outputs["spectral_20m"]["path"],
        "spectral_20m_sha256": outputs["spectral_20m"]["sha256"],
        "scene_classification_path": outputs["scene_classification_20m"]["path"],
        "scene_classification_sha256": outputs["scene_classification_20m"]["sha256"],
        "clear_mask_path": outputs["clear_mask_20m"]["path"],
        "clear_mask_sha256": outputs["clear_mask_20m"]["sha256"],
        "item_metadata_path": str(item_path.relative_to(ROOT)),
        "item_metadata_sha256": item_metadata_sha256,
        "quality_status": "PASS",
        "model_integration": "NOT_APPLIED",
        "source_catalog": "https://planetarycomputer.microsoft.com/api/stac/v1",
        "source_license": "https://sentinel.esa.int/documents/247904/690755/Sentinel_Data_Legal_Notice",
    }
    REMOTE_SENSING_CSV.parent.mkdir(parents=True, exist_ok=True)
    existing: dict[str, dict[str, str]] = {}
    if REMOTE_SENSING_CSV.exists():
        with REMOTE_SENSING_CSV.open(encoding="utf-8-sig", newline="") as stream:
            for row in csv.DictReader(stream):
                if row.get("scene_id"):
                    existing[row["scene_id"]] = row
    existing[args.item_id] = csv_row
    with REMOTE_SENSING_CSV.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        for scene_id in sorted(existing):
            writer.writerow({key: existing[scene_id].get(key, "") for key in CSV_FIELDS})

    print(f"PASS — acquired {args.item_id} ({properties.get('datetime')})")
    print(f"PASS — scene cloud cover: {float(scene_cloud):.6f}%")
    print(f"PASS — AOI cloud/shadow/cirrus: {aoi_cloud_shadow_pct:.6f}%")
    print(f"PASS — AOI clear surface classes: {aoi_clear_pct:.6f}%")
    print(f"PASS — wrote 10 spectral bands plus SCL and clear mask under {output_dir.relative_to(ROOT)}")
    print(f"PASS — manifest: {args.manifest.relative_to(ROOT) if args.manifest.is_relative_to(ROOT) else args.manifest}")
    print("INFO — imagery is checksum-tracked input only; no spectral index or model integration was performed")


if __name__ == "__main__":
    try:
        main()
    except (AcquisitionError, requests.RequestException, rasterio.errors.RasterioError) as error:
        print(f"FAIL — Sentinel-2 acquisition: {error}")
        raise SystemExit(2)
