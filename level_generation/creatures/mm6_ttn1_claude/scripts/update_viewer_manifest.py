#!/usr/bin/env python3
"""Refresh review/viewer/manifest.json after viewer_tiers.py: per-tier sha256, and a ?v=<hash> suffix on each model
URL so browsers fetch the new GLB instead of a cached one."""
import hashlib, json
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
m = json.load(open(V / 'manifest.json'))
for x in m['models']:
    name = x['url'].split('?')[0]
    x['sha256'] = hashlib.sha256((V / name).read_bytes()).hexdigest()
    x['url'] = f"{name}?v={x['sha256'][:12]}"
m['model_sha256'] = m['models'][0]['sha256']
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', [x['url'] for x in m['models']])
