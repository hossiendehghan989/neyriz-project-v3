#!/usr/bin/env python3
from pathlib import Path
import json, pandas as pd
ROOT=Path(__file__).resolve().parents[1]; p=ROOT/'data/validation/independent_labels.csv'; out=ROOT/'outputs/validation/independent_validation.json'; out.parent.mkdir(parents=True,exist_ok=True)
if not p.exists(): r={'status':'BLOCKED','reason':'independent_labels.csv is missing; no metric calculated.'}
else:
 d=pd.read_csv(p); test=d[d.spatial_split.astype(str).str.lower().eq('independent_test')]
 if len(test)<20 or test.label.nunique()<2: r={'status':'BLOCKED','reason':f'Need at least 20 independent labels and both classes; found {len(test)} rows.'}
 else:
  top=test.sort_values('model_score',ascending=False).head(20); pr=float(top.label.astype(int).mean()); r={'status':'EVALUATED','k':20,'independent_test_n':len(test),'positives_in_top_k':int(top.label.astype(int).sum()),'precision_at_20':pr,'claim_over_80_percent':pr>=.8,'interpretation':'این معیار فقط عملکرد آزمون مستقل را می‌سنجد و وضعیت حقوقی یا ذخیره را تعیین نمی‌کند.'}
out.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(r,ensure_ascii=False,indent=2))
