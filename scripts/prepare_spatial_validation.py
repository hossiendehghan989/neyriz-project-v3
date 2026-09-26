#!/usr/bin/env python3
"""Validate the independent spatial-test input contract without fabricating labels."""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'data/validation/independent_labels.csv'
OUT = ROOT / 'outputs/validation/spatial_validation_input_status.json'
REQUIRED = ['label_id','commodity','record_type','geometry','source','independent_group_id','spatial_split','label','model_score']


def main():
    result = {'source': str(PATH.relative_to(ROOT)), 'required_columns': REQUIRED}
    if not PATH.exists():
        result.update({'status':'BLOCKED_MISSING_FILE','rows':0,'missing_columns':REQUIRED})
    else:
        df = pd.read_csv(PATH)
        missing = [c for c in REQUIRED if c not in df.columns]
        test = df[df['spatial_split'].astype(str).str.lower().eq('independent_test')] if 'spatial_split' in df else df.iloc[0:0]
        positives = int((test['label'].astype(str).str.lower().isin(['1','true','positive'])).sum()) if 'label' in test else 0
        negatives = int((test['label'].astype(str).str.lower().isin(['0','false','negative'])).sum()) if 'label' in test else 0
        result.update({'status':'READY_SCHEMA_ONLY' if not missing else 'BLOCKED_SCHEMA','rows':int(len(df)),'missing_columns':missing,'independent_test_rows':int(len(test)),'independent_test_positive_rows':positives,'independent_test_negative_rows':negatives,'metrics_allowed':bool(len(test)>=20 and positives>=10 and negatives>=10)})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
