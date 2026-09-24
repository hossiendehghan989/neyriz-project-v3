#!/usr/bin/env python3
from pathlib import Path
import json, shutil, hashlib, csv
from datetime import datetime, timezone
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import box

SRC_OP = Path('/home/ubuntu/work/neyriz_project/operational_project')
SRC_STEPS = Path('/home/ubuntu/work/neyriz_completed/neyriz_completed_steps')
ROOT = Path('/home/ubuntu/work/neyriz_project_v3')
WGS='EPSG:4326'; METRIC='EPSG:32640'; GRID=500

def sha256(p):
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()

def copytree(src,dst):
    if src.exists(): shutil.copytree(src,dst,dirs_exist_ok=True)

def make_dirs():
    for x in ['data/raw','data/reference','data/processed','data/remote_sensing','data/geochemistry','data/geophysics','data/cadastre','data/validation','outputs/maps','outputs/tables','outputs/validation','docs','scripts','tests']:
        (ROOT/x).mkdir(parents=True,exist_ok=True)

def build_grid(area):
    minx,miny,maxx,maxy=area.bounds; cells=[]
    for x in np.arange(minx,maxx,GRID):
        for y in np.arange(miny,maxy,GRID):
            c=box(x,y,x+GRID,y+GRID).intersection(area)
            if not c.is_empty and c.area >= GRID*GRID*.25: cells.append(c)
    return gpd.GeoDataFrame({'grid_id':[f'GRID-{i:03d}' for i in range(1,len(cells)+1)]},geometry=cells,crs=METRIC)

def fault_score(d): return 25 if d<=1000 else 17 if d<=2000 else 8 if d<=3000 else 0
def analogue_score(d): return 15 if d<=1000 else 10 if d<=2500 else 5 if d<=4000 else 0

def main():
    make_dirs(); copytree(SRC_OP/'data/raw/supplied_steps',ROOT/'data/reference/supplied_steps'); copytree(SRC_STEPS,ROOT/'data/raw/completed_steps')
    hosts=gpd.read_file(SRC_OP/'data/raw/supplied_steps/step_02_geology_neyriz/host_lithology_units.geojson').to_crs(METRIC)
    faults=gpd.read_file(SRC_OP/'data/raw/supplied_steps/step_03_faults_targets_neyriz/faults_step03.geojson').to_crs(METRIC)
    known=gpd.read_file(SRC_OP/'data/raw/supplied_steps/step_01_manganese_nasirabad_neyriz/manganese_confirmed_step01.geojson').to_crs(METRIC)
    host1=hosts.loc[hosts.unit_id=='HOST-01'].geometry.iloc[0]; host2=hosts.loc[hosts.unit_id=='HOST-02'].geometry.iloc[0]; kp=known.geometry.iloc[0]
    grid=build_grid(host2); rows=[]
    for _,r in grid.iterrows():
        c=r.geometry.centroid; ds=[c.distance(g) for g in faults.geometry]; nd=min(ds); dk=c.distance(kp); in1=r.geometry.intersects(host1); both=sum(d<=2000 for d in ds)==len(ds)
        rows.append({'grid_id':r.grid_id,'host_score':35 if in1 else 15,'fault_score':fault_score(nd),'analogue_score':analogue_score(dk),'structural_intersection_score':10 if both else 0,'distance_to_nearest_fault_m':round(nd,1),'distance_to_known_m':round(dk,1),'excluded_known_occurrence':bool(r.geometry.intersects(kp.buffer(500))),'data_confidence_score':30})
    attrs=pd.DataFrame(rows); grid=grid.merge(attrs,on='grid_id'); grid['manganese_score']=grid.host_score+grid.fault_score+grid.analogue_score+grid.structural_intersection_score
    cand=grid.loc[~grid.excluded_known_occurrence].sort_values(['manganese_score','distance_to_known_m'],ascending=[False,False]).copy(); sel=[]; pts=[]
    for i,r in cand.iterrows():
        p=r.geometry.centroid
        if all(p.distance(q)>=900 for q in pts): sel.append(i); pts.append(p)
        if len(sel)==10: break
    manganese=grid.loc[sel].copy().reset_index(drop=True); manganese['candidate_id']=[f'MN-V3-{i:02d}' for i in range(1,len(manganese)+1)]; manganese['rank']=range(1,len(manganese)+1); manganese['commodity']='manganese'; manganese['model_status']='SCREENING_ONLY'; manganese['interpretation_fa']='امتیاز غربالگری منگنز است؛ احتمال، ذخیره یا عیار نیست.'
    # Blocked models retain a spatial context grid but deliberately have no numeric prospectivity score.
    chromite=grid[['grid_id','geometry']].copy(); chromite['commodity']='chromite'; chromite['model_status']='BLOCKED_INSUFFICIENT_DATA'; chromite['prospectivity_score']=pd.NA; chromite['blocking_reason_fa']='بدون نقشه رسمی اولترامافیک/دونیت/هارزبورژیت با مختصات کنترل‌شده، داده ژئوشیمی محلی و آزمون مستقل.'
    iron=grid[['grid_id','geometry']].copy(); iron['commodity']='iron'; iron['model_status']='BLOCKED_INSUFFICIENT_DATA'; iron['prospectivity_score']=pd.NA; iron['blocking_reason_fa']='رکوردهای آهن موجود مختصات معدن منفرد و لایه میزبان قابل مدل‌سازی ندارند.'
    for frame,name in [(hosts.to_crs(WGS),'host_lithology_units_v3.geojson'),(faults.to_crs(WGS),'faults_approximate_v3.geojson'),(known.to_crs(WGS),'known_manganese_occurrence_v3.geojson'),(grid.to_crs(WGS),'manganese_scored_grid_v3.geojson'),(manganese.to_crs(WGS),'manganese_prospectivity.geojson'),(chromite.to_crs(WGS),'chromite_prospectivity.geojson'),(iron.to_crs(WGS),'iron_prospectivity.geojson')]: frame.to_file(ROOT/'data/processed'/name,driver='GeoJSON')
    grid.to_crs(WGS).assign(commodity='manganese',model_status='SCREENING_ONLY').to_file(ROOT/'data/processed/scored_grid_by_commodity.geojson',driver='GeoJSON')
    # tables
    mg=manganese.to_crs(WGS); cent=manganese.geometry.centroid.to_crs(WGS)
    tab=pd.DataFrame({'target_id':mg.candidate_id,'commodity':'manganese','rank':mg['rank'],'latitude':cent.y,'longitude':cent.x,'model_score':mg.manganese_score,'data_confidence_score':30,'model_status':'SCREENING_ONLY','legal_status':'NOT_VERIFIED','interpretation_fa':'هدف اکتشافی؛ وضعیت حقوقی نامشخص؛ نیازمند کنترل رسمی و میدانی مجاز'})
    tab.to_csv(ROOT/'outputs/tables/manganese_targets.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame({'target_id':[],'commodity':[],'rank':[],'model_score':[],'model_status':[],'blocking_reason_fa':[]}).to_csv(ROOT/'outputs/tables/chromite_targets.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame({'target_id':[],'commodity':[],'rank':[],'model_score':[],'model_status':[],'blocking_reason_fa':[]}).to_csv(ROOT/'outputs/tables/iron_targets.csv',index=False,encoding='utf-8-sig')
    # inventory
    inv=[]
    for p in sorted(ROOT.rglob('*')):
        if p.is_file() and ('data/raw' in str(p) or 'data/reference' in str(p)):
            inv.append({'path':str(p.relative_to(ROOT)),'size_bytes':p.stat().st_size,'sha256':sha256(p),'role':'reference/raw input','status':'AVAILABLE'})
    pd.DataFrame(inv).to_csv(ROOT/'outputs/tables/data_inventory.csv',index=False,encoding='utf-8-sig')
    audit=[
      {'dataset':'manganese occurrence','features':1,'coordinate_quality':'A','model_role':'positive analogue / exclusion','status':'USED_FOR_SCREENING','limitation':'one known occurrence; no supervised training'},
      {'dataset':'host lithology','features':2,'coordinate_quality':'B','model_role':'manganese host screening','status':'USED_FOR_SCREENING','limitation':'generalized polygons; not official sheet GIS'},
      {'dataset':'fault structures','features':2,'coordinate_quality':'B','model_role':'structural screening','status':'USED_FOR_SCREENING','limitation':'approximate reconstructed traces'},
      {'dataset':'chromite occurrences/literature','features':9,'coordinate_quality':'A/B/N/A','model_role':'reference only','status':'BLOCKED_FOR_MODEL','limitation':'mostly outside AOI or representative coordinates; no local independent labels'},
      {'dataset':'iron/other occurrences','features':5,'coordinate_quality':'B/N/A','model_role':'reference only','status':'BLOCKED_FOR_MODEL','limitation':'no mine-level coordinates or host GIS'},
      {'dataset':'remote sensing','features':0,'coordinate_quality':'N/A','model_role':'not used','status':'BLOCKED','limitation':'no checksum-tracked scenes'},
      {'dataset':'geochemistry','features':0,'coordinate_quality':'N/A','model_role':'not used','status':'BLOCKED','limitation':'no field samples with QA/QC'},
      {'dataset':'geophysics','features':0,'coordinate_quality':'N/A','model_role':'not used','status':'BLOCKED','limitation':'no auditable local survey'},
      {'dataset':'cadastre','features':0,'coordinate_quality':'N/A','model_role':'legal gate','status':'BLOCKED','limitation':'no dated official output or written response'},
      {'dataset':'independent labels','features':0,'coordinate_quality':'N/A','model_role':'validation','status':'BLOCKED','limitation':'no independent spatial test set'}]
    pd.DataFrame(audit).to_csv(ROOT/'outputs/tables/input_audit_v3.csv',index=False,encoding='utf-8-sig')
    (ROOT/'outputs/tables/run_metadata_v3.json').write_text(json.dumps({'run_utc':datetime.now(timezone.utc).isoformat(),'grid_size_m':500,'models':{'manganese':{'status':'SCREENING_ONLY','candidates':len(tab),'max_score':85},'chromite':{'status':'BLOCKED_INSUFFICIENT_DATA','candidates':0},'iron':{'status':'BLOCKED_INSUFFICIENT_DATA','candidates':0}},'accuracy_claim':'CLAIM_NOT_ALLOWED','legal_claim':'NOT_VERIFIED','critical_rule':'scores are priorities, never probabilities, reserves, grades, or legal status'},ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Built {ROOT}; manganese targets={len(tab)}, chromite/iron blocked')
if __name__=='__main__': main()
