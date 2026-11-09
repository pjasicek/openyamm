#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m418' / 'aligned_2x'
REL = '../../../mm7_m418/aligned_2x'
clips = {
 'Standing': ('loop', 'Mixamo Mutant Breathing Idle (spine keeps the hunch: KEEP_REST), arms out 8 deg, tail sway', ['m418sa0', 'm418sa1', 'm418sa2']),
 'Walking': ('loop', 'Mixamo Mutant Walking in place (2.38 m per cycle), arms out 22 deg, floor pass', [f'm418w{c}0' for c in 'abcdefg']),
 'Running': ('loop', 'Mixamo Mutant Run (never reached at the tier speeds)', [f'm418w{c}0' for c in 'abcdefg']),
 'Attack': ('once', 'Mixamo Mutant Swiping planted, from its second swipe: rears up with the arm raised, slashes down (blow 0.45 s), cut and eased back', [f'm418a{c}0' for c in 'abcdefgh']),
 'Hit': ('once', 'Mixamo Zombie Reaction Hit, arms out 22 deg', [f'm418n{c}0' for c in 'abcde']),
 'Death': ('once', 'Authored: rears back, rolls onto its back (118 deg), bounces and lies belly up like m418d', ['m418da0', 'm418db0', 'm418dc0', 'm418dd0', 'm418de0']),
 'Dead': ('loop', 'Last Death pose held', ['m418xa0']),
 'Fidget': ('once', 'Mixamo Mutant Roaring, arms out 22 deg', ['m418fa0', 'm418fb0', 'm418fc0', 'm418fd0', 'm418fe0']),
}
raw = (V / 'mm7_m418_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm7_m418_claude_v1', 'model': 'mm7_m418_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm418_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('m418_a', 'Troglodyte Drone - A (palette 95, green markings)'), ('m418_b', 'Troglodyte Soldier - B (96, grey)'), ('m418_c', 'Troglodyte Queen - C (97, cyan)')):
    h = _h.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m418_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m418sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
