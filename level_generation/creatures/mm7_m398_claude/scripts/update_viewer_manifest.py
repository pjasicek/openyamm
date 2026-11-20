#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m398' / 'aligned_2x'
REL = '../../../mm7_m398/aligned_2x'
clips = {
 'Standing': ('loop', 'Mixamo Standard Idle; sword in the solved fist (bar1 route)', ['m398sa0', 'm398sa1', 'm398sa2']),
 'Walking': ('loop', 'Mixamo Walk (1.69 m stride)', [f'm398w{c}0' for c in 'abcdefgh']),
 'Running': ('loop', 'Mixamo Standard Run, high pelvis fit, 1.8 m stride (never reached at the tiers speeds)', [f'm398w{c}0' for c in 'abcdefgh']),
 'Attack': ('once', 'Mixamo Sword And Shield Slash planted (20 % of its leg motion, IK steps): raise over the right shoulder, chop across; blow 0.75 s', [f'm398a{c}0' for c in 'abcdef']),
 'Hit': ('once', 'Unarmed get-hit front 1 (humanoid set), floor pass', [f'm398n{c}0' for c in 'abcdef']),
 'Death': ('once', 'Mixamo Standing React Death Backward (travel halved): knocked back onto the back like m398d', ['m398na0', 'm398nb0', 'm398da0', 'm398db0', 'm398dc0', 'm398dd0']),
 'Dead': ('loop', 'Last Death pose held', ['m398xa0']),
 'Fidget': ('once', 'Mixamo Annoyed Head Shake planted: the skull rattles, sword kept low (native m398f is a calm shift)', ['m398fa0', 'm398fb0', 'm398fc0', 'm398fd0']),
}
raw = (V / 'mm7_m398_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm7_m398_claude_v1', 'model': 'mm7_m398_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm398_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('m398_a', 'Skeleton - A (palette 399, green)'), ('m398_b', 'Skeleton Warrior - B (63, blue)'), ('m398_c', 'Skeleton Lord - C (64, brown)')):
    h = _h.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m398_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m398sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
