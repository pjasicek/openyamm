#!/usr/bin/env python3
"""Review viewer manifest from the tier GLBs (viewer_tiers.py): clip durations read from the GLB, native reference
frames per clip (the validated m234 restorations), cache-busting hash on the model URLs."""
import json, hashlib, struct
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m234' / 'aligned_2x'
REL = '../../../mm7_m234/aligned_2x'
clips = {
 'Standing': ('loop', 'Mixamo Mutant Breathing Idle (hunched, claws forward); wings folded beside the body, tail on the ground', ['m234sa0', 'm234sa1', 'm234sa2']),
 'Walking': ('loop', 'Authored upright hovering flight over Standing frame 0, legs dangling; wing beat on the native 1.0 s cycle', [f'm234w{c}0' for c in 'abcdefgh']),
 'Attack': ('once', 'Mixamo Mutant Punch, planted; wings spread for the swipe, tail lash; blow at 0.95 s', [f'm234a{c}0' for c in 'abcdefgh']),
 'Hit': ('once', 'Humanoid set Unarmed get-hit F1; wings flung up and out', [f'm234n{c}0' for c in 'abcdef']),
 'Death': ('once', 'Mixamo Falling Back Death (travel halved); wings spread, then laid flat on the floor; tail settles', ['m234na0', 'm234nb0', 'm234nc0'] + [f'm234d{c}0' for c in 'abcd']),
 'Dead': ('loop', 'Last Death pose held', ['m234xa0']),
 'Fidget': ('once', 'Mixamo Mutant Flexing Muscles, planted; wings spread and folded again', [f'm234f{c}0' for c in 'abcd']),
}
first = sorted(V.glob('mm7_m234_a.glb'))[0]
raw = first.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
m = {'revision': 'mm7_m234_claude_v1', 'model': 'mm7_m234_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm234_a', 'models': [], 'clips': {}}
for vid, lab in (('m234_a', 'Stone Gargoyle - A (green membranes)'), ('m234_b', 'Marble Gargoyle - B (blue)'),
                 ('m234_c', 'Obsidian Gargoyle - C (red)')):
    h = hashlib.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m234_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m234sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
