#!/usr/bin/env python3
from pathlib import Path
import json, geopandas as gpd, pandas as pd
ROOT=Path(__file__).resolve().parents[1]; fail=[]
def req(c,m): print(('PASS' if c else 'FAIL')+' — '+m); fail.extend([] if c else [m])
meta=json.loads((ROOT/'outputs/tables/run_metadata_v3.json').read_text())
for p in [ROOT/'outputs/tables/manganese_targets.csv',ROOT/'outputs/tables/chromite_targets.csv',ROOT/'outputs/tables/iron_targets.csv',ROOT/'outputs/tables/data_inventory.csv',ROOT/'outputs/tables/input_audit_v3.csv']:
 req(p.exists() and p.stat().st_size>0,f'exists: {p.name}')
mg=pd.read_csv(ROOT/'outputs/tables/manganese_targets.csv'); req(len(mg)==10,'ten spaced manganese targets'); req(mg.target_id.is_unique,'unique manganese target IDs'); req(mg.model_score.between(0,100).all(),'scores within 0-100'); req((mg.data_confidence_score<=30).all(),'confidence cap <=30'); req((mg.legal_status=='NOT_VERIFIED').all(),'legal status remains unverified')
for n in ['chromite','iron']:
 d=pd.read_csv(ROOT/f'outputs/tables/{n}_targets.csv'); req(len(d)==0,f'{n} targets are not fabricated while evidence is blocked')
for n in ['manganese','chromite','iron']:
 g=gpd.read_file(ROOT/f'data/processed/{n}_prospectivity.geojson'); req(g.crs and g.crs.to_epsg()==4326,f'{n} GeoJSON is WGS84'); req(g.geometry.is_valid.all(),f'{n} geometries valid')
v4=ROOT/'data/processed/manganese_targets_v4.geojson'
if v4.exists():
 g=gpd.read_file(v4); req(len(g)==10,'v4 has ten target polygons'); req(g.crs and g.crs.to_epsg()==4326,'v4 target polygons are WGS84'); req(g.geometry.is_valid.all(),'v4 target polygons valid'); req(g.candidate_id.is_unique,'v4 target IDs unique')
req(meta['accuracy_claim']=='CLAIM_NOT_ALLOWED','unsupported accuracy claim blocked'); req(meta['legal_claim']=='NOT_VERIFIED','legal claim blocked'); print('ALL PROJECT VALIDATION CHECKS PASSED' if not fail else f'FAILED: {len(fail)} checks'); raise SystemExit(1 if fail else 0)
