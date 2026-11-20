#!/usr/bin/env python3
"""Viewer manifest for m262 (review/viewer/manifest.json): three tier GLBs (viewer_tiers.py), the clips with their
native reference frames (the validated mm7_m262 restorations), cache-busting hash on the model URLs."""
import json, hashlib, struct
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m262' / 'aligned_2x'
REL = '../../../mm7_m262/aligned_2x'
CLIPS = {
 'Walking': ('loop', 'Flight loop (also standing and fidget, as the native): authored hover over Standard Idle frame 0, tucked bird legs, knife before the body, wing beat on the native 1.0 s cycle', [f'm262w{c}0' for c in 'abcdefgh']),
 'Attack': ('once', 'Mixamo Sword And Shield Slash (2) arms and trunk (planted), talon kick and a wing beat; blow at 0.983 s', [f'm262a{c}0' for c in 'abcdefgh']),
 'Hit': ('once', 'Humanoid set Unarmed get-hit F1 trunk and arms, hover legs flinch, wings flare', [f'm262n{c}0' for c in 'abcdefgh']),
 'Death': ('once', 'Mixamo Falling Back Death; legs drawn up, tail folded, wings laid flat at both sides', ['m262na0', 'm262nb0', 'm262nc0'] + [f'm262d{c}0' for c in 'abcdefg']),
 'Dead': ('loop', 'Last Death pose held', ['m262xa0']),
}
first = V / 'mm7_m262_a.glb'
raw = first.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
m = {'revision': 'mm7_m262_claude_v1', 'model': 'mm7_m262_a.glb', 'default_clip': 'Walking',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm262_a', 'models': [], 'clips': {}}
for vid, lab in (('m262_a', 'Harpy - A (green)'), ('m262_b', 'Harpy Hag - B (violet)'), ('m262_c', 'Harpy Queen - C (magenta)')):
    h = hashlib.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m262_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in CLIPS.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m262wa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
