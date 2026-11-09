#!/usr/bin/env python3
"""Review viewer manifest from the tier GLBs (viewer_tiers.py): clip durations read from the GLB, native reference
frames per clip (the validated m406 restorations), cache-busting hash on the model URLs."""
import json, hashlib, struct
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m406' / 'aligned_2x'
REL = '../../../mm7_m406/aligned_2x'
clips = {
 'Standing': ('loop', 'Mixamo Standard Idle; sword held low like m406sa0', ['m406sa0', 'm406sa1', 'm406sa2']),
 'Walking': ('loop', 'Mixamo Walk; feet levelled (constant tilt), floor lift', [f'm406w{c}0' for c in 'abcdefgh']),
 'Running': ('loop', 'Mixamo Standard Run, high-pelvis run fit, 1.8 m stride', [f'm406w{c}0' for c in 'abcdefgh']),
 'Attack': ('once', 'Mixamo Sword And Shield Slash (2), planted + 20 % legs, stepped feet; 0.3 s ready pause; overhead raise and downward chop; blow at 0.983 s', [f'm406a{c}0' for c in 'abcdef']),
 'Hit': ('once', 'Humanoid set Unarmed get-hit F1, eased from/to Standing, floor pass', [f'm406n{c}0' for c in 'abcdef']),
 'Death': ('once', 'Mixamo Falling Back Death (travel halved): falls backward with the legs up like m406d', ['m406na0', 'm406nb0'] + [f'm406d{c}0' for c in 'abcd']),
 'Dead': ('loop', 'Last Death pose held', ['m406xa0']),
 'Fidget': ('once', 'Mixamo Sword And Shield Power Up (planted, stepped feet)', [f'm406f{c}0' for c in 'abcde']),
}
first = sorted(V.glob('mm7_m406_a.glb'))[0]
raw = first.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
m = {'revision': 'mm7_m406_claude_v1', 'model': 'mm7_m406_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm406_a', 'models': [], 'clips': {}}
for vid, lab in (('m406_a', 'Swordsman - A (green)'), ('m406_b', 'Guard - B (blue)'),
                 ('m406_c', 'Adventurer - C (red)')):
    h = hashlib.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m406_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m406sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
