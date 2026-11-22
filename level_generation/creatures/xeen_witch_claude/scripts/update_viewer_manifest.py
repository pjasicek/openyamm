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
 'Standing': ('loop', 'Mixamo Standard Idle; staff carried upright in the gloved left hand (author_carry); bare right palm raised beside the head as in the sprite (right arm from the cast stance)', ['mon_0000', 'mon_0001']),
 'Walking': ('loop', 'Mixamo Walk (in place, 1.69 m natural stride), floor pass; staff carried, 30 % of the walk arm swing', ['mon_0002', 'mon_0003']),
 'Running': ('loop', 'Mixamo Standard Run fitted (pelvis 92 % of Standing + bob, 1.8 m stride, 13 deg lean); staff carried', ['mon_0004', 'mon_0005']),
 'Attack': ('once', 'Mixamo Zombie Attack (1), first right-claw swipe (planted): claw drawn back to the hip, slashed forward; follow-through pushed clear of the hips; blow at 95 % of the forward reach', ['att_0000', 'att_0001']),
 'Cast': ('once', 'Mixamo Standing 1H Magic Attack 02 (planted): wind-up beside the head, open right palm thrust forward; release at 95 % of the thrust', ['att_0002', 'att_0003']),
 'Hit': ('once', 'Humanoid set Unarmed get-hit F1 + staff carry; blends 0.12/0.20 s', ['mon_0006']),
 'Death': ('once', 'Mixamo Standing React Death Backward (travel halved), staff kept in hand', ['mon_0007']),
 'Dead': ('loop', 'Last Death pose held', ['mon_0007']),
 'Fidget': ('once', 'Mixamo Laughing, first 5 s (a cackle), staff carried', ['mon_0000']),
}
raw = (V / 'xeen_witch_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'xeen_witch_claude_v1', 'model': 'xeen_witch_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'witch_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('witch_a', 'Wicked Witch - A (native red robe)'), ('witch_b', 'Witch - B (violet robe, design)'), ('witch_c', 'Head Witch - C (black robe, design)')):
    h = _h.sha256((V / f'xeen_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'xeen_witch_claude_v1', 'url': f'xeen_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['mon_0000']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
