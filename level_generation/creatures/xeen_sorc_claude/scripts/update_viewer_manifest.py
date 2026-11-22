#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
import os as _os; _os.chdir(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))  # project-relative paths
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[1] / 'native'
REL = '../../native'
clips = {
 'Standing': ('loop', 'Mixamo Standard Idle; arms moved clear of the wide hips (elbow_clear.py)', ['xeen_mon_0000', 'xeen_mon_0001']),
 'Walking': ('loop', 'Mixamo Walk (in place, 1.70 m stride), floor pass; panels swing with the thighs (panel_bones.py)', ['xeen_mon_0002', 'xeen_mon_0003']),
 'Running': ('loop', 'Mixamo Standard Run fitted (pelvis 92 % of Standing + bob, 2.05 m stride, 13 deg lean)', ['xeen_mon_0004', 'xeen_mon_0005']),
 'Attack': ('once', 'Mixamo Zombie Attack (1), first right open-hand swipe (planted), a slap; blow at 95 % of the forward reach', ['xeen_att_0000', 'xeen_att_0001']),
 'Cast': ('once', 'Mixamo Standing 2H Magic Attack 01 (planted): both palms raised overhead (the native attack), then thrust forward together; release at 95 % of the right palm thrust', ['xeen_att_0002', 'xeen_att_0003']),
 'Hit': ('once', 'Humanoid set Unarmed get-hit F1; blends 0.12/0.20 s', ['xeen_mon_0006']),
 'Death': ('once', 'Mixamo Standing React Death Backward (travel halved)', ['xeen_mon_0007']),
 'Dead': ('loop', 'Last Death pose held', ['xeen_mon_0007']),
 'Fidget': ('once', 'Mixamo Standing Idle 03 "playing with magic" (planted), first 5 s', ['xeen_mon_0000']),
}
raw = (V / 'xeen_sorc_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'xeen_sorc_claude_v1', 'model': 'xeen_sorc_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'sorc_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('sorc_a', 'Sorceress - A (native white)'), ('sorc_b', 'Enchantress - B (pale violet, design)'), ('sorc_c', 'Grand Sorceress - C (emerald, design)'), ('sorc_m', 'Morgana - M (crimson, black folds, D-32)')):
    h = _h.sha256((V / f'xeen_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'xeen_sorc_claude_v1', 'url': f'xeen_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['mon_0000']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
