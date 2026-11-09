#!/usr/bin/env python3
"""Review viewer manifest: production (r100, one look per outfit) vs reduced (r86, all nine looks); clip durations from
the GLBs; clip descriptions, native reference frames and look labels from the production viewer
(../mm7_m342_claude/review/viewer/manifest.json)."""
import json, hashlib, struct
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; V = ROOT / 'review' / 'viewer'
P = json.load(open(ROOT.parent / 'mm7_m342_claude' / 'review' / 'viewer' / 'manifest.json'))
labels = {x['id']: x['label'] for x in P['models']}
m = {'revision': 'reduce-1', 'model': 'MM7 Peasant Human1 Female - production vs reduced', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm342_aa_r86', 'models': [], 'clips': {}}
for vid in labels:
    for tag, text in (('r100', 'production - 9,920'), ('r86', 'reduced - 8,683')):
        f = V / f'mm7_{vid}_{tag}.glb'
        if not f.exists():
            continue
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        m['models'].append({'id': f'{vid}_{tag}', 'label': f'{labels[vid]} - {text}', 'revision': 'reduce-1', 'url': f'{f.name}?v={h[:12]}', 'sha256': h})
raw = (V / 'mm7_m342_aa_r86.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
for k, c in P['clips'].items():
    if k in dur:
        m['clips'][k] = dict(c, duration=dur[k])
m['model_sha256'] = m['models'][0]['sha256']
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', len(m['models']), 'models', {k: round(v, 3) for k, v in dur.items()})
