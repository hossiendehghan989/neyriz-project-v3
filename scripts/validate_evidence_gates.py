#!/usr/bin/env python3
"""Report project evidence gates; passing inputs never implies model accuracy."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/validation/evidence_gate_status.json"
OUT.parent.mkdir(parents=True, exist_ok=True)


def rows(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig") if path.exists() else pd.DataFrame()


def checksum_matches(relative_path: str, expected: str) -> bool:
    path = ROOT / relative_path
    if not path.is_file() or not expected:
        return False
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest() == expected


def validated_remote_sensing_count(frame: pd.DataFrame) -> int:
    required = {
        "scene_id",
        "quality_status",
        "spectral_10m_path",
        "spectral_10m_sha256",
        "spectral_20m_path",
        "spectral_20m_sha256",
        "scene_classification_path",
        "scene_classification_sha256",
        "clear_mask_path",
        "clear_mask_sha256",
    }
    if frame.empty or not required.issubset(frame.columns):
        return 0
    valid = 0
    for record in frame.to_dict(orient="records"):
        if str(record.get("quality_status", "")).upper() != "PASS":
            continue
        if all(
            checksum_matches(str(record.get(path_key, "")), str(record.get(hash_key, "")))
            for path_key, hash_key in [
                ("spectral_10m_path", "spectral_10m_sha256"),
                ("spectral_20m_path", "spectral_20m_sha256"),
                ("scene_classification_path", "scene_classification_sha256"),
                ("clear_mask_path", "clear_mask_sha256"),
            ]
        ):
            valid += 1
    return valid


field = rows(ROOT / "data/geochemistry/field_samples.csv")
remote_sensing = rows(ROOT / "data/remote_sensing/remote_sensing_manifest.csv")
geophysics = rows(ROOT / "data/geophysics/geophysics_surveys.csv")
cadastre = rows(ROOT / "data/cadastre/cadastre_status.csv")
labels = rows(ROOT / "data/validation/independent_labels.csv")
valid_remote_sensing = validated_remote_sensing_count(remote_sensing)
independent_test_count = int(
    (labels.get("spatial_split", pd.Series(dtype=str)).astype(str).str.lower() == "independent_test").sum()
)

GATES = [
    {
        "gate": "field_geochemistry",
        "status": "PASS" if len(field) >= 20 else "BLOCKED",
        "requirement": "20 real samples with standard, blank and duplicate QA/QC",
    },
    {
        "gate": "remote_sensing",
        "status": "PASS" if valid_remote_sensing >= 1 else "BLOCKED",
        "requirement": "quality-passed scene with checksum-verified spectral assets and SCL cloud mask",
        "validated_scene_count": valid_remote_sensing,
    },
    {
        "gate": "geophysics",
        "status": "PASS" if len(geophysics) >= 1 else "BLOCKED",
        "requirement": "auditable local survey",
    },
    {
        "gate": "cadastre",
        "status": "PASS" if len(cadastre) >= 1 else "BLOCKED",
        "requirement": "dated official output and legal response",
    },
    {
        "gate": "independent_labels",
        "status": "PASS" if len(labels) >= 20 and independent_test_count >= 10 else "BLOCKED",
        "requirement": "20 labels with at least 10 independent spatial-test labels",
    },
]
all_pass = all(gate["status"] == "PASS" for gate in GATES)
result = {
    "status": "READY_FOR_INDEPENDENT_VALIDATION" if all_pass else "BLOCKED_INSUFFICIENT_DATA",
    "claim_allowed": False,
    "metric_required": "precision@k on an independent spatial test set with confidence interval",
    "gates": GATES,
    "counts": {
        "field": len(field),
        "remote_sensing_records": len(remote_sensing),
        "remote_sensing_checksum_verified": valid_remote_sensing,
        "geophysics": len(geophysics),
        "cadastre": len(cadastre),
        "independent_labels": len(labels),
        "independent_test_labels": independent_test_count,
    },
    "warning_fa": "وجود تصویر سنجش‌ازدور به‌تنهایی اعتبار مدل را اثبات نمی‌کند؛ تا تکمیل همه دروازه‌ها و آزمون مستقل مکانی، ادعای دقت مجاز نیست.",
}
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
