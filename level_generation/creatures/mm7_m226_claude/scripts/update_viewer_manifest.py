#!/usr/bin/env python3
"""Review viewer manifest from the tier GLBs (viewer_tiers.py): clip durations read from the GLB, native reference
frames per clip (the validated m226 restorations), cache-busting hash on the model URLs."""
import json, hashlib, struct
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m226' / 'aligned_2x'
REL = '../../../mm7_m226/aligned_2x'
clips = {
 'Standing': ('loop', 'Mixamo Standard Idle; falchion held low like m226sa0', ['m226sa0', 'm226sa1', 'm226sa2']),
 'Walking': ('loop', 'Mixamo Walk; feet levelled (constant tilt), floor lift', [f'm226w{c}0' for c in 'abcdefgh']),
 'Running': ('loop', 'Mixamo Standard Run, high-pelvis run fit, 1.8 m stride', [f'm226w{c}0' for c in 'abcdefgh']),
 'Attack': ('once', 'Mixamo Sword And Shield Slash (2), planted + 20 % legs, stepped feet; 0.3 s ready pause; overhead raise and downward chop; blow at 0.983 s', [f'm226a{c}0' for c in 'abcdefgh']),
 'Hit': ('once', 'Humanoid set Unarmed get-hit F1, eased from/to Standing, floor pass', [f'm226n{c}0' for c in 'abcde']),
 'Death': ('once', 'Mixamo Falling Back Death (travel halved): falls backward with the legs up like m226d', ['m226na0', 'm226nb0'] + [f'm226d{c}0' for c in 'abcd']),
 'Dead': ('loop', 'Last Death pose held', ['m226xa0']),
 'Fidget': ('once', 'Mixamo Sword And Shield Power Up (planted, stepped feet)', [f'm226f{c}0' for c in 'abcde']),
}
first = sorted(V.glob('mm7_m226_a.glb'))[0]
raw = first.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
m = {'revision': 'mm7_m226_claude_v1', 'model': 'mm7_m226_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm226_a', 'models': [], 'clips': {}}
for vid, lab in (('m226_a', 'Robber - A (green cloth)'), ('m226_b', 'Raider - B (blue cloth)'),
                 ('m226_c', 'Bandit - C (red cloth)')):
    h = hashlib.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m226_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m226sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
