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
 'Standing': ('loop', 'Mixamo Floating, legs damped to 40 % round a dangling pose (knees bent, toes pointed); wings beat 6.1 Hz', ['killer_mon_0000', 'killer_mon_0001']),
 'Walking': ('loop', 'Standing leaned 14 deg forward, thighs trailing, gaze levelled; wings 6.4 Hz', ['killer_mon_0002', 'killer_mon_0003']),
 'Running': ('loop', 'Standing leaned 26 deg forward, legs trailing; wings 7.5 Hz', ['killer_mon_0004', 'killer_mon_0005']),
 'Attack': ('once', 'Mixamo Mutant Swiping window (upper body) on the hovering legs: right claw raised, slashed down across; blow at the peak fingertip speed', ['killer_att_0000', 'killer_att_0001']),
 'Cast': ('once', 'Mixamo Standing 2H Magic Attack 01 window: both hands overhead, then pushed forward together; release when the palms are furthest forward', ['killer_att_0002', 'killer_att_0003']),
 'Hit': ('once', 'Humanoid set Unarmed get-hit F1 on the hovering legs', ['killer_mon_0006']),
 'Death': ('once', 'Mixamo Standing Death Forward 01 (turned): staggers, knees, falls face down; wings stop and fold shut; lowest point kept on the floor', ['killer_mon_0007']),
 'Dead': ('loop', 'Last Death pose held', ['killer_mon_0007']),
 'Fidget': ('once', 'Mixamo Taunt Gesture on the hovering legs (left arm 12 deg out over the hip)', ['killer_mon_0000']),
}
raw = (V / 'xeen_sprite_b.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'xeen_sprite_claude_v1', 'model': 'xeen_sprite_b.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'sprite_b', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('sprite_b', 'Killer Sprite - B (native: blue, magenta)'), ('sprite_a', 'Medusa Sprite - A (olive, green)'), ('sprite_c', 'Sprite Queen - C (violet, gold, purple)')):
    h = _h.sha256((V / f'xeen_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'xeen_sprite_claude_v1', 'url': f'xeen_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['killer_mon_0000']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
