#!/usr/bin/env python3
"""Append current Step 9A and ASTER provenance to project inventories.

The script preserves existing inventory rows, adds only missing file records,
and records missing-input checksums as blank rather than inventing values.
"""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "outputs/tables/data_inventory.csv"
AUDIT = ROOT / "outputs/tables/input_audit_v3.csv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def add_inventory_records() -> None:
    with INVENTORY.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or ["path", "size_bytes", "sha256", "role", "status"]
        rows = list(reader)
    by_path = {row.get("path", ""): row for row in rows}

    candidates = [
        *sorted((ROOT / "data/remote_sensing/aster_gdem_v003").glob("*.tif")),
        ROOT / "data/remote_sensing/aster_gdem_v003/metadata.json",
        ROOT / "data/remote_sensing/aster_gdem_v003/README.md",
        ROOT / "data/acquired/aster_gdem_v003_sha256.txt",
        ROOT / "data/labels/labels_step09.csv",
        ROOT / "data/labels/labels_step09.geojson",
        ROOT / "data/labels/labels_step09_normalized.csv",
        ROOT / "outputs/validation/labels_step09_quality_summary.json",
        ROOT / "data/acquired/research_step_04_label_supplement/step09a_supplemental_search.json",
    ]
    for path in candidates:
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        by_path[rel] = {
            "path": rel,
            "size_bytes": str(path.stat().st_size),
            "sha256": sha256(path),
            "role": "ASTER GDEM source raster" if path.suffix.lower() == ".tif" else "Step 9A source/derived evidence",
            "status": "AVAILABLE_CHECKSUMMED",
        }
    rows = [by_path[key] for key in sorted(by_path)]
    with INVENTORY.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def update_input_audit() -> None:
    with AUDIT.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        old_fields = reader.fieldnames or []
        rows = list(reader)
    fields = list(old_fields)
    for field in ("source_path", "sha256"):
        if field not in fields:
            fields.append(field)
    mapping = {
        "manganese occurrence": "data/processed/known_manganese_occurrence_v3.geojson",
        "host lithology": "data/processed/host_lithology_units_v3.geojson",
        "fault structures": "data/processed/faults_approximate_v3.geojson",
        "chromite occurrences/literature": "data/raw/completed_steps/step_04_chromite_neyriz/chromite_occurrences_step04.geojson",
        "iron/other occurrences": "data/raw/completed_steps/step_05_iron_other_minerals_neyriz/iron_other_minerals_step05.geojson",
        "remote sensing": "data/acquired/aster_gdem_v003_sha256.txt",
        "independent labels": "data/labels/labels_step09_normalized.csv",
    }
    for row in rows:
        name = row.get("dataset", "")
        if name == "remote sensing":
            row["features"] = "9"
            row["coordinate_quality"] = "A (ASTER GDEM tiles; checksums in manifest)"
            row["model_role"] = "topography only; not mineral evidence"
            row["status"] = "AVAILABLE_TERRAIN_ONLY"
            row["limitation"] = "9 ASTER GDEM V3 tiles cover the approximate AOI; no new terrain derivatives were calculated in Step 9A. Sentinel-2 remains blocked."
        elif name == "independent labels":
            row["features"] = "0"
            row["coordinate_quality"] = "N/A"
            row["model_role"] = "independent validation only"
            row["status"] = "BLOCKED"
            row["limitation"] = "25 Step 9A catalog rows exist but are reference-only; 0 rows meet the independent spatial-test definition."
        path_value = mapping.get(name, "")
        path = ROOT / path_value if path_value else None
        row["source_path"] = path_value if path and path.is_file() else ""
        row["sha256"] = sha256(path) if path and path.is_file() else ""

    existing_names = {row.get("dataset", "") for row in rows}
    added = [
        {
            "dataset": "Step 9A positive-label catalog",
            "features": "25",
            "coordinate_quality": "A (source prints numeric coordinate; not an accuracy claim)",
            "model_role": "reference only; no training or score update",
            "status": "AVAILABLE_REFERENCE_ONLY",
            "limitation": "2 manganese occurrences, 1 chromite locality, and 22 clustered Qatruyeh iron samples; 0 independent-test labels.",
            "source_path": "data/labels/labels_step09.csv",
            "sha256": sha256(ROOT / "data/labels/labels_step09.csv"),
        },
        {
            "dataset": "Step 9A supplemental candidate audit",
            "features": "4 reviewed candidates",
            "coordinate_quality": "Source coordinates reviewed; rejected as duplicate, town-reference or uncertain alias",
            "model_role": "provenance audit only",
            "status": "AVAILABLE_WITH_EXCLUSIONS",
            "limitation": "No reviewed candidate met the feature-level location requirements for a new label.",
            "source_path": "data/acquired/research_step_04_label_supplement/step09a_supplemental_search.json",
            "sha256": sha256(ROOT / "data/acquired/research_step_04_label_supplement/step09a_supplemental_search.json"),
        },
    ]
    for row in added:
        if row["dataset"] not in existing_names:
            rows.append(row)
    with AUDIT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    add_inventory_records()
    update_input_audit()
    print(f"Updated {INVENTORY.relative_to(ROOT)} and {AUDIT.relative_to(ROOT)} with checksums.")


if __name__ == "__main__":
    main()
