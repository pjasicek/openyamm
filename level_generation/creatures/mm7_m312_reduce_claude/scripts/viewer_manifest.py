#!/usr/bin/env python3
"""Review viewer manifest: production (r100, one look per outfit) vs reduced (r81, all nine looks), clip durations
from the GLBs, native reference frames and labels from ../mm7_m312_claude/work/viewer_clips.json."""
import json, hashlib, struct
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; V = ROOT / 'review' / 'viewer'
C = json.load(open(ROOT.parent / 'mm7_m312_claude' / 'work' / 'viewer_clips.json'))
labels = dict(C['tiers']); REL = '../../../mm7_m312/aligned_2x'; NAT = ROOT.parent / 'mm7_m312' / 'aligned_2x'
m = {'revision': 'reduce-1', 'model': 'MM7 Peasant Dwarf Female - production vs reduced', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm312_a1_r81', 'models': [], 'clips': {}}
for vid, _ in C['tiers']:
    for tag, text in (('r100', 'production - 10,591'), ('r81', 'reduced 80 % - 8,517')):
        f = V / f'mm7_{vid}_{tag}.glb'
        if not f.exists():
            continue
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        m['models'].append({'id': f'{vid}_{tag}', 'label': f'{labels[vid]} - {text}', 'revision': 'reduce-1', 'url': f'{f.name}?v={h[:12]}', 'sha256': h})
raw = (V / 'mm7_m312_a1_r81.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
for k, (mode, prov, imgs) in C['clips'].items():
    if k in dur:
        imgs = [i for i in imgs if (NAT / f'{i}.png').exists()]
        m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                         'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
m['model_sha256'] = m['models'][0]['sha256']
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', len(m['models']), 'models', {k: round(v, 3) for k, v in dur.items()})
