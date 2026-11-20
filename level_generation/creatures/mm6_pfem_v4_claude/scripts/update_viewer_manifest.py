#!/usr/bin/env python3
"""Review viewer manifest from the tier GLBs (viewer_tiers.py) for a New Sorpigal peasant: clip durations read from the
GLB, the native standing sprite and the HD masters as reference images, cache-busting hash on the model URLs.
Clip notes and tier labels: creature.json "viewer"."""
import json, hashlib, struct
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
V = ROOT / 'review' / 'viewer'
CJ = json.load(open(ROOT / 'creature.json')); OUT = CJ['out']; VW = CJ['viewer']
REF = VW['references']
variants = json.load(open(ROOT / 'textures' / f"{CJ['prefix']}_ramps.json"))['variants']
first = V / f'{OUT}_{variants[0]}.glb'
raw = first.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
rev = ROOT.name + '_' + VW.get('revision', 'v1')
m = {'revision': rev, 'model': first.name, 'default_clip': 'Standing', 'feedback': 'feedback/user_feedback.json',
     'default_model': variants[0], 'models': [], 'clips': {}}
for vid in variants:
    h = hashlib.sha256((V / f'{OUT}_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': VW['tiers'][vid], 'revision': rev, 'url': f'{OUT}_{vid}.glb?v={h[:12]}',
                        'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov) in VW['clips'].items():
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': REF}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
