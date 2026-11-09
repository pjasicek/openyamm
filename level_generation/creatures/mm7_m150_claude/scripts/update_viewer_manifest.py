#!/usr/bin/env python3
"""Review viewer manifest from the tier GLBs (viewer_tiers.py): clip durations read from the GLB, native reference
frames per clip (the validated m150 restorations), cache-busting hash on the model URLs."""
import json, hashlib, struct
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m150' / 'aligned_2x'
REL = '../../../mm7_m150/aligned_2x'
clips = {
 'Standing': ('loop', 'Mixamo Standard Idle; sword held diagonally across the body (carry) as m150sa0; wings spread, breathing', ['m150sa0', 'm150sa1', 'm150sa2']),
 'Walking': ('loop', 'Authored flight over Standing frame 0 (trunk 45 deg forward, legs trailing, sword forward); wing beat on the native 1.0 s cycle', [f'm150w{c}2' for c in 'abcdefgh']),
 'Attack': ('once', 'Mixamo Sword And Shield Slash (2), planted + 20 % legs; 0.3 s ready pause; overhead raise and a cut down and across; one wing beat; blow at 0.983 s', [f'm150a{c}0' for c in 'abcdefgh']),
 'Hit': ('once', 'Humanoid set Unarmed get-hit F1, eased from/to Standing; wings thrown up', [f'm150n{c}0' for c in 'abcdef']),
 'Death': ('once', 'Mixamo Sword And Shield Death (travel halved): falls backward; wings rise, then lie flat at both sides (floor search)', [f'm150d{c}0' for c in 'abcd']),
 'Dead': ('loop', 'Last Death pose held', ['m150xa0']),
 'Fidget': ('once', 'Mixamo Sword And Shield Power Up (planted, stepped feet); wings spread forward', [f'm150f{c}0' for c in 'abcd']),
}
first = sorted(V.glob('mm7_m150_a.glb'))[0]
raw = first.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
m = {'revision': 'mm7_m150_claude_v1', 'model': 'mm7_m150_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm150_a', 'models': [], 'clips': {}}
for vid, lab in (('m150_a', 'Angel - A (green skirt)'), ('m150_b', 'Angel Lord - B (blue skirt)'),
                 ('m150_c', 'Archangel - C (magenta skirt)')):
    h = hashlib.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m150_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m150sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
