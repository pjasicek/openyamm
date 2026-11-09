#!/usr/bin/env python3
"""Review viewer manifest from the tier GLBs (viewer_tiers.py): clip durations read from the GLB, native reference
frames per clip (the validated m154 restorations), cache-busting hash on the model URLs."""
import json, hashlib, struct
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m154' / 'aligned_2x'
REL = '../../../mm7_m154/aligned_2x'
clips = {
 'Standing': ('loop', 'Mixamo Standard Idle; bow held low in the right hand like m154sa0', ['m154sa0', 'm154sa1', 'm154sa2']),
 'Walking': ('loop', 'Mixamo Walk; feet levelled (constant tilt), floor lift', [f'm154w{c}0' for c in 'abcdefgh']),
 'Running': ('loop', 'Mixamo Standard Run, high-pelvis run fit', [f'm154w{c}0' for c in 'abcdefgh']),
 'Attack': ('once', 'Mixamo Standing Draw Arrow + Standing Aim Recoil, mirrored and planted: arrow from the quiver over the left shoulder (0.43 s), nocked (0.67 s), drawn to the cheek, released at 1.167 s (string snaps back, arrow hidden), lowered', [f'm154a{c}0' for c in 'abcdefgh']),
 'Hit': ('once', 'Humanoid set Unarmed get-hit F1, eased from/to Standing, floor pass', [f'm154n{c}0' for c in 'abcdef']),
 'Death': ('once', 'Mixamo Falling Back Death (travel halved): falls backward with the legs up like m154d', ['m154na0', 'm154nb0'] + [f'm154d{c}0' for c in 'abcd']),
 'Dead': ('loop', 'Last Death pose held', ['m154xa0']),
 'Fidget': ('once', 'Mixamo Sword And Shield Power Up (planted, stepped feet), the bow carried in the right fist', [f'm154f{c}0' for c in 'abcde']),
}
first = sorted(V.glob('mm7_m154_a.glb'))[0]
raw = first.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
m = {'revision': 'mm7_m154_claude_v1', 'model': 'mm7_m154_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm154_a', 'models': [], 'clips': {}}
for vid, lab in (('m154_a', 'Archer - A (green)'), ('m154_b', 'Bowman - B (blue)'),
                 ('m154_c', 'Elite Archer - C (red)')):
    h = hashlib.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m154_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m154sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
