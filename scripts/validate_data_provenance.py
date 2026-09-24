#!/usr/bin/env python3
from pathlib import Path
import json, hashlib
import geopandas as gpd
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
fail=[]
def check(c,m): print(('PASS' if c else 'FAIL')+' — '+m); fail.extend([] if c else [m])
for p in [ROOT/'outputs/tables/data_inventory.csv',ROOT/'outputs/tables/input_audit_v3.csv',ROOT/'data/processed/manganese_prospectivity.geojson',ROOT/'data/processed/chromite_prospectivity.geojson',ROOT/'data/processed/iron_prospectivity.geojson']:
    check(p.exists() and p.stat().st_size>0,f'exists: {p.relative_to(ROOT)}')
for p in [ROOT/'data/processed/manganese_prospectivity.geojson',ROOT/'data/processed/chromite_prospectivity.geojson',ROOT/'data/processed/iron_prospectivity.geojson']:
    if p.exists():
        g=gpd.read_file(p); check(g.crs and g.crs.to_epsg()==4326,f'WGS84 CRS: {p.name}'); check(g.geometry.is_valid.all(),f'valid geometry: {p.name}')
# Guard against model-ineligible occurrence misuse.
occ=ROOT/'data/raw/completed_steps/step_04_chromite_neyriz/chromite_occurrences_step04.csv'
if occ.exists():
    d=pd.read_csv(occ); check((d.loc[d.model_eligible.astype(str).str.lower()=='false'].shape[0])>=1,'ineligible chromite representatives are flagged')
print('ALL PROVENANCE CHECKS PASSED' if not fail else f'FAILED: {len(fail)} checks')
raise SystemExit(1 if fail else 0)

if __name__=='__main__': pass


def _sha256(path):
    h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()

# kept for future inventory extensions
_unused=json.dumps({'root':str(ROOT)})
