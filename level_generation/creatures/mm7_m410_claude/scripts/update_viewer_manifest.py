#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m410' / 'aligned_2x'
REL = '../../../mm7_m410/aligned_2x'
clips = {
 'Standing': ('loop', 'Mixamo Standard Idle, hands empty, the dagger in its left-hip sheath (native m410sa); arms cleared of the thighs', ['m410sa0', 'm410sa1', 'm410sa2']),
 'Walking': ('loop', 'Mixamo Walk; floor pass', [f'm410w{c}0' for c in 'abcdefgh']),
 'Running': ('loop', 'Mixamo Standard Run fitted; the sheath follows pelvis and left thigh', [f'm410w{c}0' for c in 'abcdefgh']),
 'Attack': ('once', 'Authored: the right hand draws the dagger from the left-hip sheath (cross-draw, solved arm), humanoid set Dagger-Attack R3 raises it and lunges into a forward thrust (native m410aa..ah), blow 0.86 s, then the dagger is sheathed again (native ah..aa)', [f'm410a{c}0' for c in 'abcdefgh']),
 'Hit': ('once', 'Humanoid set Unarmed get-hit front 1; blends 0.2 s', [f'm410n{c}0' for c in 'abcdef']),
 'Death': ('once', 'Mixamo Falling Back Death (travel halved): thrown back, legs up (native m410da..dd)', ['m410na0', 'm410nb0'] + [f'm410d{c}0' for c in 'abcd']),
 'Dead': ('loop', 'Last Death pose held', ['m410xa0']),
 'Fidget': ('once', 'Mixamo Shrugging (planted): arms out to the sides (native m410fa..fd)', [f'm410f{c}0' for c in 'abcd']),
}
raw = (V / 'mm7_m410_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm7_m410_claude_v1', 'model': 'mm7_m410_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm410_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('m410_a', 'Thief - A (purple, green)'), ('m410_b', 'Rogue - B (green, brown)'), ('m410_c', 'Master Thief - C (red, red)')):
    h = _h.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m410_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m410sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
