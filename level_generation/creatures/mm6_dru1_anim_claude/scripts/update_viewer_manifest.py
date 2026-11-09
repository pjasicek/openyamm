#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm6_dru1' / 'native'
REL = '../../../mm6_dru1/native'
clips = {
 'Standing': ('loop', 'Relax idle (humanoid set), world-rotation copy; open hands', ['dru1sta0', 'dru1sta1', 'dru1sta2']),
 'Walking': ('loop', 'Relax walk female; cloak baked (15 verlet chains)', [f'dru1wk{c}0' for c in 'abcdef']),
 'Attack': ('once', 'Unarmed cast R buff 2, stance planted: gather, right hand raised diagonally overhead (25 deg tilt), fling; release 0.817 s', [f'dru1at{c}0' for c in 'abcdef']),
 'Cast': ('once', 'Ready hold 0.25 s + unarmed cast dual attack 2, stance planted: arms spread, palms clap forward; release 0.717 s', [f'dru1at{c}0' for c in 'abcdef']),
 'Hit': ('once', 'Unarmed get-hit front 1, stance planted, blended from Standing', [f'dru1wi{c}0' for c in 'abcdef']),
 'Death': ('once', 'Relax lay down: kneels, lies face down; cloak drapes over her', [f'dru1dy{c}0' for c in 'abcdef']),
 'Dead': ('loop', 'Last Death pose held', ['dru1dyf0']),
 'Fidget': ('once', 'Relax drink 1 with open fingers: right hand to the hood and down', [f'dru1fi{c}0' for c in 'abcdef']),
}
raw = (V / 'mm6_dru1_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm6_dru1_claude_v1', 'model': 'mm6_dru1_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'dru1_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('dru1_a', 'Druid - A (green)'), ('dru1_b', 'Great Druid - B (rose)'), ('dru1_c', 'Grand Druid - C (blue)')):
    h = _h.sha256((V / f'mm6_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm6_dru1_claude_v1', 'url': f'mm6_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['dru1sta0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
