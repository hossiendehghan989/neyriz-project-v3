#!/usr/bin/env python3
"""Create a conservative, model-ready quality view of Step 09A labels.

The source CSV remains unchanged. This derivative makes record type, spatial
uncertainty, study clustering, and model eligibility explicit without inventing
missing coordinates or accuracy values.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/labels/labels_step09.csv"
OUT = ROOT / "data/labels/labels_step09_normalized.csv"
SUMMARY = ROOT / "outputs/validation/labels_step09_quality_summary.json"


def classify(row: dict[str, str]) -> dict[str, str]:
    label_id = row["label_id"]
    if label_id == "MN-09A-001":
        return {
            "record_type": "occurrence",
            "deposit_model": "unknown_manganese",
            "independent_group_id": "AB_BAND_MRDS",
            "coordinate_accuracy_m": "10000",
            "coordinate_accuracy_class": "LOW_REPORTED_10KM",
            "crs_status": "WGS84_EXPLICIT",
            "model_eligibility": "REFERENCE_ONLY",
            "validation_role": "NOT_INDEPENDENT_TEST",
            "quality_reason": "MRDS prints WGS84 but reports 10000 m location accuracy; not a precise training point.",
        }
    if label_id == "MN-09A-002":
        return {
            "record_type": "occurrence",
            "deposit_model": "radiolarite_associated_manganese",
            "independent_group_id": "KUH_KHAM_STUDY",
            "coordinate_accuracy_m": "",
            "coordinate_accuracy_class": "UNKNOWN_DATUM_APPROXIMATE",
            "crs_status": "UNVERIFIED",
            "model_eligibility": "REFERENCE_ONLY",
            "validation_role": "NOT_INDEPENDENT_TEST",
            "quality_reason": "DMS locality coordinate; datum and point accuracy are not stated.",
        }
    if label_id == "CR-09A-001":
        return {
            "record_type": "occurrence",
            "deposit_model": "podiform_chromite",
            "independent_group_id": "KHAJEH_JAMALI_LOCALITY",
            "coordinate_accuracy_m": "",
            "coordinate_accuracy_class": "UNKNOWN_DATUM_APPROXIMATE",
            "crs_status": "UNVERIFIED",
            "model_eligibility": "REFERENCE_ONLY",
            "validation_role": "NOT_INDEPENDENT_TEST",
            "quality_reason": "Mine locality is named in a type-locality source; datum and operating status are not stated.",
        }
    if label_id.startswith("IR-09A-"):
        return {
            "record_type": "sample",
            "deposit_model": "qatruyeh_hydrothermal_metasomatic_iron",
            "independent_group_id": "QATRUYEH_2014_STUDY",
            "coordinate_accuracy_m": "",
            "coordinate_accuracy_class": "UNKNOWN_DATUM_SAMPLE_COORDINATE",
            "crs_status": "UNVERIFIED",
            "model_eligibility": "REFERENCE_ONLY",
            "validation_role": "CLUSTERED_NOT_INDEPENDENT",
            "quality_reason": "Ore-sample location from one study; not an independent deposit or validation label.",
        }
    raise ValueError(f"Unclassified label: {label_id}")


def main() -> None:
    with SRC.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SystemExit("No source rows found")

    extra = [
        "record_type",
        "deposit_model",
        "independent_group_id",
        "coordinate_accuracy_m",
        "coordinate_accuracy_class",
        "crs_status",
        "model_eligibility",
        "validation_role",
        "quality_reason",
    ]
    fieldnames = list(rows[0].keys()) + extra
    normalized = []
    for row in rows:
        meta = classify(row)
        normalized.append({**row, **meta})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(normalized)

    counts = {}
    for row in normalized:
        for key in ("commodity", "record_type", "model_eligibility", "validation_role", "independent_group_id"):
            counts.setdefault(key, {})
            value = row[key]
            counts[key][value] = counts[key].get(value, 0) + 1
    summary = {
        "source": str(SRC.relative_to(ROOT)),
        "output": str(OUT.relative_to(ROOT)),
        "row_count": len(normalized),
        "model_ready_rows": sum(r["model_eligibility"] == "MODEL_READY" for r in normalized),
        "validation_ready_rows": sum(r["validation_role"] == "INDEPENDENT_TEST" for r in normalized),
        "counts": counts,
        "status": "REFERENCE_ONLY_NO_INDEPENDENT_TEST",
    }
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
