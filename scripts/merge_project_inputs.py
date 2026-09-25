#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
result={'schema_version':'1.0','project_root':'.','merged_reference_root':'data/reference/supplied_steps','completed_steps_root':'data/raw/completed_steps','step_06_present':False,'note':'Step 06 was absent from the supplied archive and remains an explicit gap.'}
(ROOT/'outputs/tables/merge_manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(result,ensure_ascii=False,indent=2))
