#!/usr/bin/env python3
"""Refresh review/viewer/manifest.json after viewer_tiers.py: per-tier sha256, and a ?v=<hash> suffix on each model
URL so browsers fetch the new GLB instead of a cached one; clip durations are read from the GLB (the viewer checks them
to 1e-5)."""
import hashlib, json, struct
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
m = json.load(open(V / 'manifest.json'))
for x in m['models']:
    name = x['url'].split('?')[0]
    x['sha256'] = hashlib.sha256((V / name).read_bytes()).hexdigest()
    x['url'] = f"{name}?v={x['sha256'][:12]}"
m['model_sha256'] = m['models'][0]['sha256']
raw = (V / m['models'][0]['url'].split('?')[0]).read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + n])
for a in doc['animations']:
    if a['name'] in m['clips']:
        m['clips'][a['name']]['duration'] = max(doc['accessors'][s_['input']]['max'][0] for s_ in a['samplers'])
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', [x['url'] for x in m['models']])
