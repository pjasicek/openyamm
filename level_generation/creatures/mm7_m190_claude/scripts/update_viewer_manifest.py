#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m190' / 'aligned_2x'
REL = '../../../mm7_m190/aligned_2x'
clips = {
 'Standing': ('loop', 'Mixamo Dwarf Idle (3): wide burly stance; the axe hangs head-down by the knee (native m190sa)', ['m190sa0', 'm190sa1', 'm190sa2']),
 'Walking': ('loop', 'Mixamo Dwarf Walk (short heavy steps), axe swinging with the arm; floor pass', [f'm190w{c}0' for c in 'abcdefgh']),
 'Running': ('loop', 'Mixamo Standard Run fitted + authored carry: the axe held up and forward at the side; loop seam blended', [f'm190w{c}0' for c in 'abcdefgh']),
 'Attack': ('once', 'Mixamo Sword And Shield Slash (2): overhead raise, downward axe chop into a crouch (native m190aa..ah); planted + 20 % legs, 0.3 s ready pause, blow 0.983 s (native action 1.0 s); left hand and axe cleared of the legs', [f'm190a{c}0' for c in 'abcdefgh']),
 'Hit': ('once', 'Humanoid set Unarmed get-hit front 1; blends 0.2 s; axe cleared', [f'm190n{c}0' for c in 'abcdef']),
 'Death': ('once', 'Mixamo Standing React Death Backward: steps back and falls onto the back (native m190da..dd); the axe kept in hand, cleared of the floor', ['m190na0', 'm190nb0'] + [f'm190d{c}0' for c in 'abcd']),
 'Dead': ('loop', 'Last Death pose held', ['m190xa0']),
 'Fidget': ('once', 'Mixamo Sword And Shield Power Up (planted): axe swept up, chest out (native m190fa..fd)', [f'm190f{c}0' for c in 'abcd']),
}
raw = (V / 'mm7_m190_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm7_m190_claude_v1', 'model': 'mm7_m190_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm190_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('m190_a', 'Dwarven Soldier - A (green)'), ('m190_b', 'Dwarven Lieutenant - B (blue-violet)'), ('m190_c', 'Dwarven Commander - C (red)')):
    h = _h.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m190_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m190sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
