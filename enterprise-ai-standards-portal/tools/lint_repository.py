#!/usr/bin/env python3
"""Repository integrity checks for control IDs, artifact paths, and required metadata."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
items = json.loads((ROOT/'data/artifacts.json').read_text())
errors=[]
seen=set()
for a in items:
    for key in ['id','title','domain','type','requirement','summary','phases','riskTiers','framework','checks','evidence','artifactPath']:
        if key not in a or a[key] in (None,'',[]): errors.append(f"{a.get('id','?')}: missing {key}")
    if a['id'] in seen: errors.append(f"duplicate control ID: {a['id']}")
    seen.add(a['id'])
    if not (ROOT/a['artifactPath']).exists(): errors.append(f"{a['id']}: artifact path missing: {a['artifactPath']}")
    if a['requirement'] not in {'MUST','SHOULD','MAY'}: errors.append(f"{a['id']}: unsupported requirement {a['requirement']}")
if errors:
    print('\n'.join('ERROR: '+e for e in errors))
    raise SystemExit(1)
print(f"OK: {len(items)} control artifacts validated")
