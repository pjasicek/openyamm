#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m470' / 'aligned_2x'
REL = '../../../mm7_m470/aligned_2x'
clips = {
 'Standing': ('loop', 'Mixamo Standard Idle, arms turned out 16 deg (the claws sank into the thighs)', ['m470sa0', 'm470sa1', 'm470sa2']),
 'Walking': ('loop', 'Mixamo Walk, arms out 12 deg', [f'm470w{c}0' for c in 'abcdefgh']),
 'Running': ('loop', 'Mixamo Standard Run, high pelvis fit (never reached at the tiers speeds)', [f'm470w{c}0' for c in 'abcdefgh']),
 'Attack': ('once', 'Mixamo Zombie Attack (1) planted (20 % legs, IK steps) at 1.4x: wind back, lunge and reach with the claws; cut 0.1 s after the reach and eased back (the source then pulls a victim to the belly)', [f'm470a{c}0' for c in 'abcdef']),
 'Hit': ('once', 'Unarmed get-hit front 1 (humanoid set), arms out 8 deg', [f'm470n{c}0' for c in 'abcdef']),
 'Death': ('once', 'Mixamo Standing React Death Backward (travel halved): falls back like m470d', ['m470na0', 'm470nb0', 'm470da0', 'm470db0', 'm470dc0', 'm470dd0']),
 'Dead': ('loop', 'Last Death pose held', ['m470xa0']),
 'Fidget': ('once', 'Mixamo Annoyed Head Shake planted, arms out 16 deg', ['m470fa0', 'm470fb0', 'm470fc0', 'm470fd0']),
}
raw = (V / 'mm7_m470_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm7_m470_claude_v1', 'model': 'mm7_m470_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm470_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('m470_a', 'Ghast - A (palette 511, ash-blond hair)'), ('m470_b', 'Ghoul - B (517, black)'), ('m470_c', 'Revenant - C (525, orange-brown)')):
    h = _h.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m470_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m470sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
