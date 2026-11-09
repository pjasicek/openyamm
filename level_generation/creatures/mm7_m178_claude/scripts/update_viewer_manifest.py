#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m178' / 'aligned_2x'
REL = '../../../mm7_m178/aligned_2x'
clips = {
 'Standing': ('loop', 'Mixamo Standard Idle (trunk keeps the mesh rest: KEEP_REST), arms out 22 deg, feet planted, tail carriage and sway', ['m178sa0', 'm178sa1', 'm178sa2']),
 'Walking': ('loop', 'Mixamo Mutant Walking in place (1.88 m per 1.43 s cycle), arms out 14 deg, floor pass', [f'm178w{c}0' for c in 'abcdefgh']),
 'Running': ('loop', 'Mixamo Mutant Run in place, arms out 10 deg (tier C 300 reaches the run threshold)', [f'm178w{c}0' for c in 'abcdefgh']),
 'Attack': ('once', 'Mixamo Standing Melee Attack Downward (arms and trunk), 1.1x, lower body authored (attack_legs.py): weight back, left-foot lunge step and deep crouch into the downward swipe (blow 0.75 s), rear heel peels, step back', [f'm178a{c}0' for c in 'abcdefgh']),
 'Hit': ('once', 'Mixamo Zombie Reaction Hit cut at the flinch (0.87 s), arms out 12 deg', [f'm178n{c}0' for c in 'abcde']),
 'Death': ('once', 'Mixamo Standing React Death Forward, travel halved, floor pass; the tail lies down', ['m178na0', 'm178nb0', 'm178da0', 'm178db0', 'm178dc0', 'm178dd0']),
 'Dead': ('loop', 'Last Death pose held', ['m178xa0']),
 'Fidget': ('once', 'Mixamo Roar planted, arms out 20 deg', ['m178fa0', 'm178fb0', 'm178fc0', 'm178fd0', 'm178fe0']),
}
raw = (V / 'mm7_m178_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm7_m178_claude_v1', 'model': 'mm7_m178_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm178_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('m178_a', 'Devil Worker - A (palette 44, ochre-brown hide)'), ('m178_b', 'Devil Warrior - B (45, teal-green hide)'), ('m178_c', 'Devil Captain - C (46, red hide)')):
    h = _h.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m178_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m178sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
