#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m322' / 'aligned_2x'
REL = '../../../mm7_m322/aligned_2x'
clips = {
 'Standing': ('loop', 'Humanoid set Relax Idle; the staff carried upright in the left fist like a walking stick (author_carry.py, world-upright) as native m322sa', ['m322sa0', 'm322sa1', 'm322sa2']),
 'Walking': ('loop', 'Humanoid set Relax Walk Female; the staff stays upright in the left fist (native walk; attack/shoot alias it)', [f'm322w{c}0' for c in 'abcdefgh']),
 'Hit': ('once', 'Humanoid set Unarmed Get Hit F2: recoils back, right arm out, the staff kept upright (20 % of the source wrist motion); blends 0.2 s (native m322na..ne)', [f'm322n{c}0' for c in 'abcde']),
 'Death': ('once', 'Mixamo Standing React Death Backward: steps back and falls onto the back with the staff in hand, cleared of the floor (native m322da..dd)', ['m322na0', 'm322nb0'] + [f'm322d{c}0' for c in 'abcd']),
 'Dead': ('loop', 'Last Death pose held', ['m322xa0']),
 'Fidget': ('once', 'Mixamo Weight Shift (the native fidget barely moves); staff carried upright', [f'm322f{c}0' for c in 'abcd']),
}
raw = (V / 'mm7_m322_a1.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm7_m322_claude_v1', 'model': 'mm7_m322_a1.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm322_a1', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
LOOKS = [('m322_a1', '331 Peasant Elf FemaleA A (palette 323: green trousers, red hair)'),
         ('m322_a2', '332 A/B (324: blue, black hair)'), ('m322_a3', '333 A/C (325: red, auburn hair)'),
         ('m322_b1', '334 B/A (326: pale green, blonde)'), ('m322_b2', '335 B/B (327: black, white hair)'),
         ('m322_b3', '336 B/C (328: brown, strawberry blonde)'), ('m322_c1', '337 C/A (329: sky blue, red hair)'),
         ('m322_c2', '338 C/B (330: green, black hair)'), ('m322_c3', '339 C/C (331: coral, blonde)')]
for vid, lab in LOOKS:
    h = _h.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m322_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m322sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
