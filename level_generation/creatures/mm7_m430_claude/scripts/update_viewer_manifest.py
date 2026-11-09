#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m430' / 'aligned_2x'
REL = '../../../mm7_m430/aligned_2x'
clips = {
 'Standing': ('loop', 'Mixamo Standard Idle; dagger in the solved fist', ['m430sa0', 'm430sa1', 'm430sa2']),
 'Walking': ('loop', 'Mixamo Walk under a dress-weighted robe (pelvis -> 45 % legs at the hem)', [f'm430w{c}0' for c in 'abcdefgh']),
 'Running': ('loop', 'Mixamo Standard Run, high pelvis fit (never reached at the tiers speeds)', [f'm430w{c}0' for c in 'abcdefgh']),
 'Attack': ('once', 'Mixamo Sword And Shield Slash planted (20 % of its leg motion, IK steps): raise over the right shoulder, cut down and across; blow 0.75 s', [f'm430a{c}0' for c in 'abcdef']),
 'Hit': ('once', 'Unarmed get-hit front 1 (humanoid set), floor pass on the hem', [f'm430n{c}0' for c in 'abcdef']),
 'Death': ('once', 'Mixamo Standing React Death Backward (travel halved); skirt bones fold the hem along the legs as it falls', ['m430na0', 'm430nb0', 'm430da0', 'm430db0', 'm430dc0', 'm430dd0']),
 'Dead': ('loop', 'Last Death pose held', ['m430xa0']),
 'Fidget': ('once', 'Mixamo Annoyed Head Shake planted', ['m430fa0', 'm430fb0', 'm430fc0', 'm430fd0']),
}
raw = (V / 'mm7_m430_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm7_m430_claude_v1', 'model': 'mm7_m430_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm430_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('m430_a', 'Wight - A (palette 111, brown robe)'), ('m430_b', 'Wraith - B (112, white)'), ('m430_c', 'Barrow Wight - C (113, red)')):
    h = _h.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m430_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m430sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
