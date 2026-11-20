#!/usr/bin/env python3
"""Review viewer manifest (adapted from mm6_natm_claude): clip durations read from the tier GLB, native reference
frames (the restored aligned_2x frames of the native project, front view) per clip, cache-busting hashes.
Clip provenance and tier labels: work/viewer_clips.json {"tiers": [[id, label], ...], "clips": {name: [mode, text,
[native frame names]]}}. Env OUT (export name), NATIVE (native project folder)."""
import json, hashlib, struct, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
V = ROOT / 'review' / 'viewer'
import sys; sys.path.insert(0, str(ROOT / 'scripts')); import cfg
OUT, NATIVE = cfg.C['out'], cfg.C['native']
NAT = ROOT.parent / NATIVE / 'aligned_2x'; REL = f'../../../{NATIVE}/aligned_2x'
cfg = json.load(open(ROOT / 'work' / 'viewer_clips.json'))
tiers = cfg['tiers']
raw = (V / f'{OUT}_{tiers[0][0][-1]}.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
m = {'revision': cfg.get('revision', f'{OUT}_claude_v1'), 'model': f'{OUT}_{tiers[0][0][-1]}.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': tiers[0][0], 'models': [], 'clips': {}}
for vid, lab in tiers:
    h = hashlib.sha256((V / f'{OUT}_{vid[-1]}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': m['revision'], 'url': f'{OUT}_{vid[-1]}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in cfg['clips'].items():
    if k not in dur:
        continue
    imgs = [f'{REL}/{i}.png' for i in imgs if (NAT / f'{i}.png').exists()]
    if not imgs:                                     # hgd: no native sprite: the approved concept's HD front master
        imgs = ['../../references_hd/01_front.png']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': imgs}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
