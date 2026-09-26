#!/usr/bin/env python3
from pathlib import Path
import json
from collections import Counter
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/validation/evidence_gate_status.json"
OUT.parent.mkdir(parents=True, exist_ok=True)


def rows(path):
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


field = rows(ROOT / "data/geochemistry/field_samples.csv")
rs = rows(ROOT / "data/remote_sensing/remote_sensing_manifest.csv")
geo = rows(ROOT / "data/geophysics/geophysics_surveys.csv")
cad = rows(ROOT / "data/cadastre/cadastre_status.csv")
lab = rows(ROOT / "data/validation/independent_labels.csv")
catalog = rows(ROOT / "data/labels/labels_step09.csv")

gates = [
    {"gate": "field_geochemistry", "status": "PASS" if len(field) >= 20 else "BLOCKED", "requirement": "20 real samples with standard, blank and duplicate QA/QC"},
    {"gate": "remote_sensing", "status": "PASS" if len(rs) >= 1 else "BLOCKED", "requirement": "checksum-tracked quality-passed scene"},
    {"gate": "geophysics", "status": "PASS" if len(geo) >= 1 else "BLOCKED", "requirement": "auditable local survey"},
    {"gate": "cadastre", "status": "PASS" if len(cad) >= 1 else "BLOCKED", "requirement": "dated official output and legal response"},
    {"gate": "independent_labels", "status": "PASS" if len(lab) >= 20 and (lab.get("spatial_split", pd.Series(dtype=str)).astype(str).str.lower() == "independent_test").sum() >= 10 else "BLOCKED", "requirement": "20 labels with at least 10 independent spatial-test labels"},
]
allpass = all(item["status"] == "PASS" for item in gates)
catalog_by_commodity = Counter(catalog["commodity"].fillna("unknown").astype(str)) if not catalog.empty and "commodity" in catalog.columns else Counter()
result = {
    "status": "READY_FOR_INDEPENDENT_VALIDATION" if allpass else "BLOCKED_INSUFFICIENT_DATA",
    "claim_allowed": False,
    "metric_required": "precision@k on an independent spatial test set with confidence interval",
    "gates": gates,
    "counts": {"field": len(field), "remote_sensing": len(rs), "geophysics": len(geo), "cadastre": len(cad), "independent_labels": len(lab)},
    "reference_label_catalog": {"rows": len(catalog), "by_commodity": dict(catalog_by_commodity), "model_use": "REFERENCE_ONLY_NOT_INDEPENDENT_TEST"},
    "warning_fa": "تا زمانی که همه دروازه‌ها و آزمون مستقل مکانی تکمیل نشده‌اند، ادعای دقت ۸۰٪ مجاز نیست.",
}
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
