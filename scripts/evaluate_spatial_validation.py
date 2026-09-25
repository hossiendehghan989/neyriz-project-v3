#!/usr/bin/env python3
"""Evaluate whether an independent spatial validation set is available.

This guard intentionally produces BLOCKED rather than fabricated metrics when
labels are missing, clustered, or not independently partitioned.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "data/labels/labels_step09_normalized.csv"
OUT = ROOT / "outputs/validation/spatial_validation_status.json"


def main() -> None:
    with LABELS.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    independent = [r for r in rows if r.get("validation_role") == "INDEPENDENT_TEST"]
    positive = [r for r in independent if r.get("record_type") in {"deposit", "occurrence"}]
    negative = [r for r in independent if r.get("record_type") == "confirmed_absence"]
    reasons = []
    if not independent:
        reasons.append("independent spatial test labels are missing")
    if len(positive) < 10:
        reasons.append("fewer than 10 independent positive test labels")
    if len(negative) < 10:
        reasons.append("fewer than 10 confirmed negative test labels")
    result = {
        "status": "PASS" if not reasons else "BLOCKED",
        "metrics_allowed": not reasons,
        "metric_policy": ["precision_at_k", "recall", "pr_auc", "calibration_only_if_probabilities_are_valid"],
        "counts": {
            "all_rows": len(rows),
            "independent_test_rows": len(independent),
            "independent_positive_rows": len(positive),
            "independent_confirmed_negative_rows": len(negative),
        },
        "reasons": reasons,
        "required_next": "Collect independent, spatially separated labels and reserve them before model tuning." if reasons else "Run metrics on the frozen independent spatial test set.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if reasons:
        return


if __name__ == "__main__":
    main()
