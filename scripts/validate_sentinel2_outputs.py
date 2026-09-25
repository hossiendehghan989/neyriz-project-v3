#!/usr/bin/env python3
"""Validate Sentinel-2 scene files, AOI cloud QC, and source/output hashes."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "outputs/validation/sentinel2_scene_manifest.json"
REMOTE_SENSING = ROOT / "data/remote_sensing/remote_sensing_manifest.csv"
CLOUD_LIMIT_PERCENT = 5.0
MIN_CLEAR_PERCENT = 90.0
EXPECTED_10M_BANDS = ["B02", "B03", "B04", "B08"]
EXPECTED_20M_BANDS = ["B05", "B06", "B07", "B8A", "B11", "B12"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str, failures: list[str]) -> None:
    print(f"{'PASS' if condition else 'FAIL'} — {message}")
    if not condition:
        failures.append(message)


def main() -> int:
    failures: list[str] = []
    require(MANIFEST.exists(), "Sentinel-2 scene manifest exists", failures)
    if not MANIFEST.exists():
        return 1
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        print(f"FAIL — invalid Sentinel-2 manifest JSON: {error}")
        return 1

    quality = manifest.get("quality_control", {})
    require(manifest.get("schema_version") == "1.0", "manifest schema is supported", failures)
    require(quality.get("status") == "PASS", "scene quality gate passed", failures)
    require(float(manifest.get("scene_cloud_cover_pct", 999)) <= CLOUD_LIMIT_PERCENT, "scene cloud cover is <= 5%", failures)
    require(float(quality.get("aoi_cloud_shadow_cirrus_pct", 999)) <= CLOUD_LIMIT_PERCENT, "AOI cloud/shadow/cirrus is <= 5%", failures)
    require(float(quality.get("aoi_clear_surface_pct", 0)) >= MIN_CLEAR_PERCENT, "AOI clear surface is >= 90%", failures)
    require(manifest.get("processing", {}).get("model_integration") == "NOT_APPLIED", "scene has not been integrated into prospectivity scores", failures)
    require(manifest.get("processing", {}).get("derived_indices") == "NOT_GENERATED", "spectral indices have not been fabricated or inferred", failures)

    item_metadata = manifest.get("stac_item_metadata", {})
    item_path = ROOT / item_metadata.get("path", "")
    require(item_path.exists(), "unsigned STAC item metadata exists", failures)
    if item_path.exists():
        require(sha256(item_path) == item_metadata.get("sha256"), "STAC item metadata checksum matches", failures)
        raw_metadata = item_path.read_text(encoding="utf-8")
        require("?se=" not in raw_metadata and "&sig=" not in raw_metadata, "no temporary SAS signatures are persisted", failures)

    outputs = manifest.get("outputs", {})
    expected = {"spectral_10m", "spectral_20m", "scene_classification_20m", "clear_mask_20m"}
    require(set(outputs) == expected, "all expected spectral and quality-control products are listed", failures)
    first_shapes: dict[int, tuple[int, int]] = {}
    for key, item in sorted(outputs.items()):
        path = ROOT / item.get("path", "")
        require(path.exists(), f"output exists: {item.get('path', key)}", failures)
        if not path.exists():
            continue
        require(sha256(path) == item.get("sha256"), f"output checksum matches: {path.name}", failures)
        resolution = int(item.get("resolution_m", 0))
        with rasterio.open(path) as dataset:
            require(dataset.crs and dataset.crs.to_epsg() == 32640, f"{path.name} uses EPSG:32640", failures)
            require(dataset.res[0] == resolution and dataset.res[1] == resolution, f"{path.name} uses {resolution}m pixels", failures)
            require(dataset.nodata == (255 if key == "clear_mask_20m" else 0), f"{path.name} declares the expected NoData value", failures)
            require(dataset.width > 0 and dataset.height > 0, f"{path.name} has non-empty dimensions", failures)
            data = dataset.read(masked=True)
            require(data.count() > 0, f"{path.name} contains valid pixels", failures)
            if resolution in first_shapes:
                require((dataset.height, dataset.width) == first_shapes[resolution], f"{path.name} grid aligns within {resolution}m products", failures)
            else:
                first_shapes[resolution] = (dataset.height, dataset.width)
            if key == "spectral_10m":
                require(dataset.count == 4, "10m stack has four bands", failures)
                require([dataset.descriptions[index] for index in range(dataset.count)] == EXPECTED_10M_BANDS, "10m bands are in documented order", failures)
            elif key == "spectral_20m":
                require(dataset.count == 6, "20m stack has six spectral bands", failures)
                require([dataset.descriptions[index] for index in range(dataset.count)] == EXPECTED_20M_BANDS, "20m bands are in documented order", failures)
            elif key == "scene_classification_20m":
                require(dataset.count == 1, "SCL has one class band", failures)
            elif key == "clear_mask_20m":
                require(dataset.count == 1, "clear-surface mask has one band", failures)
                valid_values = set(int(value) for value in np.unique(data.compressed()))
                require(valid_values.issubset({0, 1}), "clear-surface mask only contains 0/1 valid cells", failures)
                require(1 in valid_values, "clear-surface mask includes clear pixels", failures)

    require(REMOTE_SENSING.exists(), "remote-sensing input manifest exists", failures)
    if REMOTE_SENSING.exists():
        try:
            frame = pd.read_csv(REMOTE_SENSING, encoding="utf-8-sig")
            match = frame[frame["scene_id"] == manifest.get("scene_id")]
            require(len(match) == 1, "scene is recorded exactly once in remote-sensing manifest", failures)
            if len(match) == 1:
                require(match.iloc[0]["quality_status"] == "PASS", "remote-sensing manifest records PASS", failures)
                require(match.iloc[0]["model_integration"] == "NOT_APPLIED", "remote-sensing manifest blocks silent model integration", failures)
        except (KeyError, pd.errors.ParserError) as error:
            require(False, f"remote-sensing manifest schema is valid: {error}", failures)

    print("ALL SENTINEL-2 VALIDATION CHECKS PASSED" if not failures else f"FAILED: {len(failures)} Sentinel-2 validation check(s)")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
