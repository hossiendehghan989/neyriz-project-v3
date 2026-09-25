#!/usr/bin/env python3
"""Validate the reproducible terrain outputs made by build_terrain_derivatives.py."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
import rasterio

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "outputs/validation/terrain_run_manifest_v31.json"
TARGET_SOURCE = ROOT / "outputs/tables/manganese_targets.csv"
TARGET_TERRAIN = ROOT / "outputs/tables/manganese_targets_terrain_v31.csv"
EXPECTED_DERIVATIVES = {
    "dem_elevation_m",
    "slope_degrees",
    "aspect_degrees",
    "profile_curvature_per_m",
    "roughness_stddev_m_3x3",
    "hillshade_315az_45alt",
}


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
    require(MANIFEST_PATH.exists(), f"terrain manifest exists: {MANIFEST_PATH.relative_to(ROOT)}", failures)
    if not MANIFEST_PATH.exists():
        print("Terrain outputs have not been built; run `make terrain` before validation.")
        return 1

    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"FAIL — invalid terrain manifest JSON: {exc}")
        return 1

    require(manifest.get("schema_version") == "1.0", "terrain manifest schema is supported", failures)
    require(manifest.get("checksum_verification") == "PASS", "source checksum verification passed", failures)
    require(manifest.get("model_integration") == "NOT_APPLIED", "terrain features are not silently added to the prospectivity model", failures)
    require(bool(manifest.get("run_id")), "terrain run has an immutable identifier", failures)
    require(manifest.get("processing", {}).get("target_crs") == "EPSG:32640", "terrain processing uses UTM zone 40N", failures)
    require(manifest.get("processing", {}).get("resolution_m") == 30.0, "terrain output resolution is 30 metres", failures)

    sources = manifest.get("source_tiles", [])
    require(len(sources) == 9, "all nine checksum-listed ASTER tiles are represented in the manifest", failures)
    for source in sources:
        path = ROOT / source.get("path", "")
        require(path.exists(), f"source tile exists: {source.get('path', '<missing>')}", failures)
        if path.exists() and source.get("status") == "VERIFIED":
            require(sha256(path) == source.get("sha256"), f"source tile checksum matches: {path.name}", failures)

    derivatives = manifest.get("derivatives", {})
    require(set(derivatives) == EXPECTED_DERIVATIVES, "all six required terrain derivatives are documented", failures)
    first_shape: tuple[int, int] | None = None
    for name in sorted(EXPECTED_DERIVATIVES):
        item = derivatives.get(name, {})
        path = ROOT / item.get("path", "")
        require(path.exists(), f"terrain raster exists: {name}", failures)
        if not path.exists():
            continue
        require(sha256(path) == item.get("sha256"), f"terrain raster checksum matches manifest: {path.name}", failures)
        with rasterio.open(path) as dataset:
            require(dataset.count == 1, f"{name} has one raster band", failures)
            require(dataset.crs and dataset.crs.to_epsg() == 32640, f"{name} uses EPSG:32640", failures)
            require(dataset.nodata == -9999.0, f"{name} declares nodata=-9999", failures)
            require(dataset.dtypes[0] == "float32", f"{name} is float32", failures)
            require(abs(dataset.res[0] - 30.0) < 1e-6 and abs(dataset.res[1] - 30.0) < 1e-6, f"{name} has 30m cells", failures)
            require(dataset.width > 0 and dataset.height > 0, f"{name} has non-empty dimensions", failures)
            data = dataset.read(1, masked=True)
            require(data.count() >= 100, f"{name} contains at least 100 valid cells", failures)
            shape = (dataset.height, dataset.width)
            if first_shape is None:
                first_shape = shape
            else:
                require(shape == first_shape, f"{name} grid matches other terrain derivatives", failures)

    require(TARGET_SOURCE.exists(), "base manganese target table exists", failures)
    require(TARGET_TERRAIN.exists(), "terrain target attribute table exists", failures)
    if TARGET_SOURCE.exists() and TARGET_TERRAIN.exists():
        base = pd.read_csv(TARGET_SOURCE)
        terrain = pd.read_csv(TARGET_TERRAIN)
        require(len(terrain) == len(base) == 10, "terrain table covers the ten current manganese targets", failures)
        require(terrain["target_id"].is_unique, "terrain target identifiers are unique", failures)
        require(set(terrain["target_id"]) == set(base["target_id"]), "terrain table preserves the base target set", failures)
        require((terrain["terrain_model_integration"] == "NOT_APPLIED").all(), "target terrain values remain unmodelled", failures)
        require((terrain["terrain_feature_status"] == "DERIVED_NOT_MODELLED").all(), "target terrain values are correctly labelled", failures)
        require(set(terrain["terrain_run_id"]) == {manifest.get("run_id")}, "target terrain values point to the current run", failures)
        terrain_columns = [column for column in terrain.columns if column.startswith("terrain_") and column not in {"terrain_run_id", "terrain_feature_status", "terrain_model_integration"}]
        require(len(terrain_columns) == 6, "terrain target table has six sampled derivative columns", failures)

    print("ALL TERRAIN VALIDATION CHECKS PASSED" if not failures else f"FAILED: {len(failures)} terrain validation check(s)")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
