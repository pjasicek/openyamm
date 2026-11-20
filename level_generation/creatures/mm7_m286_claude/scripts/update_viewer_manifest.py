#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m286' / 'aligned_2x'
REL = '../../../mm7_m286/aligned_2x'
clips = {
 'Standing': ('loop', 'v2 native-proportion body; Mixamo Orc Idle, stance narrowed to the native, free elbow bent (fist at the hip); authored carry, the axe held forward at the right hip, head toward the midline and up (native m286sa)', ['m286sa0', 'm286sa1', 'm286sa2']),
 'Walking': ('loop', 'Mixamo Orc Walk (heavy steps) + the forward carry; floor pass', [f'm286w{c}0' for c in 'abcdefgh']),
 'Running': ('loop', 'Mixamo Standard Run fitted + the carry, axe raised 35 deg; loop seam blended (no native run)', [f'm286w{c}0' for c in 'abcdefgh']),
 'Attack': ('once', 'Mixamo Sword And Shield Slash (2): overhead raise, downward axe chop (native m286aa..af); planted + 20 % legs, 0.13 s ready pause, blow 0.817 s (native action 0.75 s); axe and left hand cleared of the legs', [f'm286a{c}0' for c in 'abcdef']),
 'Hit': ('once', 'Humanoid set Unarmed get-hit front 1 + the carry; blends 0.2 s; axe cleared', [f'm286n{c}0' for c in 'abcdef']),
 'Death': ('once', 'Mixamo Standing React Death Backward: steps back and falls onto the back (native m286da..de); the axe kept in hand, cleared of the floor', [f'm286d{c}0' for c in 'abcde']),
 'Dead': ('loop', 'Last Death pose held', ['m286xa0']),
 'Fidget': ('once', 'Mixamo Sword And Shield Power Up (planted): axe brandished up, chest out (native m286fa..fe)', [f'm286f{c}0' for c in 'abcde']),
}
raw = (V / 'mm7_m286_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm7_m286_claude_v2c', 'model': 'mm7_m286_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm286_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('m286_a', 'Minotaur - A (olive, 287)'), ('m286_b', 'Minotaur Headsman - B (teal, 288)'), ('m286_c', 'Minotaur Lord - C (red, 289)')):
    h = _h.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m286_claude_v2c', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m286sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
