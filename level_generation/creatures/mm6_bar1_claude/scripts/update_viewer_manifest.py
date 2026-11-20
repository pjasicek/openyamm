#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm6_bar1' / 'native'
clips = {
 'Standing': ('loop', 'Mixamo Standard Idle (upright), retarget_mixamo.py; solved sword fist', ['bar1sta0', 'bar1sta1', 'bar1sta2']),
 'Walking': ('loop', 'Armed walk', [f'bar1wa{c}0' for c in 'abcdef']),
 'Running': ('loop', 'Relax run forward (RPG set): upright run', [f'bar1wa{c}0' for c in 'abcdef']),
 'Attack': ('once', 'Mixamo Sword And Shield Slash, planted: 0.15 s ready pause, raise over the right shoulder, slice across at 0.75 s, recovery', [f'bar1at{c}0' for c in 'abcdef']),
 'Hit': ('once', 'Unarmed get-hit front 1 (RPG set), eased from/to Standing', [f'bar1wi{c}0' for c in 'bcdef']),
 'Death': ('once', 'Armed death 1 (falls forward), eased in from Standing', [f'bar1de{c}0' for c in 'abcdef']),
 'Dead': ('loop', 'Last Death pose held', ['bar1def0']),
 'Fidget': ('once', 'Mixamo Standing Taunt Battlecry, eased from/to Standing', [f'bar1fi{c}0' for c in 'bcdef']),
}
raw = (V / 'mm6_bar1_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm6_bar1_claude_clay', 'model': 'mm6_bar1_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'bar1_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('bar1_a', 'Magyar - A (bronze / brown)'), ('bar1_b', 'Magyar Soldier - B (blue / burgundy)'), ('bar1_c', 'Magyar Matron - C (copper / green)')):
    h = _h.sha256((V / f'mm6_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm6_bar1_claude_v1', 'url': f'mm6_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['bar1sta0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'../../../mm6_bar1/native/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
