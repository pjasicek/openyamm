#!/usr/bin/env python3
"""Review viewer manifest from the tier GLBs (viewer_tiers.py): clip durations read from the GLB, native reference
frames per clip (the validated m246 restorations), cache-busting hash on the model URLs."""
import json, hashlib, struct
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m246' / 'aligned_2x'
REL = '../../../mm7_m246/aligned_2x'
clips = {
 'Standing': ('loop', 'Mixamo Standard Idle; broadsword carried diagonally up across the body like m246sa0 (author_carry.py)', ['m246sa0', 'm246sa1', 'm246sa2']),
 'Walking': ('loop', 'Mixamo Walk; feet levelled (constant tilt/roll), floor lift, walk bob smoothed', [f'm246w{c}0' for c in 'abcdefgh']),
 'Running': ('loop', 'Mixamo Standard Run, high-pelvis run fit, 1.8 m stride', [f'm246w{c}0' for c in 'abcdefgh']),
 'Attack': ('once', 'Mixamo Standing Melee Attack Downward (the ogre chop; user review 2026-10-20), planted + 20 % legs, stepped feet; 0.13 s ready pause eased from the carry; sword raised over the head and chopped down at the target; blow at 1.017 s, edge first; authored lower body: pelvis sinks/draws back then drives forward, hip lead, left-foot lunge step, rear heel peel', [f'm246a{c}0' for c in 'abcdefgh']),
 'Hit': ('once', 'Humanoid set Unarmed get-hit F1, eased from/to Standing, floor pass', [f'm246n{c}0' for c in 'abcdef']),
 'Death': ('once', 'Mixamo Falling Back Death (travel halved): falls backward like m246d', ['m246na0', 'm246nb0'] + [f'm246d{c}0' for c in 'abc']),
 'Dead': ('loop', 'Last Death pose held', ['m246xa0']),
 'Fidget': ('once', 'Mixamo Sword And Shield Power Up (planted, stepped feet); the descriptor fidget plays the standing group in game', [f'm246f{c}0' for c in 'abcde']),
}
first = sorted(V.glob('mm7_m246_a.glb'))[0]
raw = first.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
m = {'revision': 'mm7_m246_claude_v3', 'model': 'mm7_m246_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm246_a', 'models': [], 'clips': {}}
for vid, lab in (('m246_a', 'Goblin - A (palette 247, olive)'), ('m246_b', 'Hobgoblin - B (palette 248, blue)'),
                 ('m246_c', 'Goblin Lord - C (palette 249, red)')):
    h = hashlib.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m246_claude_v3', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m246sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
