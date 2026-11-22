#!/usr/bin/env python3
"""Review viewer manifest from review/viewer/xeen_guard_a.glb (one skin): clip durations read from the GLB, native reference
frames per clip, cache-busting hash on the model URL."""
import json, hashlib, struct
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
V = ROOT / 'review' / 'viewer'
REL = '../../native'
clips = {
 'Standing': ('loop', 'stand-in mm8_m592 Standing on our hunched posture: heavy breathing sway, claws open (native idle 062.mon 0, 3)', ['mon_0000', 'mon_0003']),
 'Walking': ('loop', 'stand-in Walk2 retargeted: bowed knees, heavy steps, 0.71 m per cycle', ['mon_0000']),
 'Running': ('loop', 'stand-in Jog retargeted, 1.18 m per cycle', ['mon_0000']),
 'Attack': ('once', 'both claws raised over the dome (att 0-1), slammed down at the party (impact 1.033 s); the green beam charges at the gem socket (att 2)', ['att_0000', 'att_0001', 'att_0002', 'att_0003']),
 'Hit': ('once', 'stand-in Hit: recoil (no native frame)', ['mon_0000']),
 'Death': ('once', 'stand-in Death: staggers and falls on its back, the hunch eases out, legs to plain FK (no native frame)', ['mon_0000']),
 'Dead': ('loop', 'Death last pose held: on its back on the floor', ['mon_0000']),
 'Fidget': ('once', 'stand-in Fidget: a short shrug', ['mon_0003']),
}
raw = (V / 'xeen_guard_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
h = hashlib.sha256(raw).hexdigest()
LABELS = {'a': "Xeen's Guard - Xeen Construct D (native chrome, Clouds image 62)"}
models = []
for t, label in LABELS.items():
    hh = hashlib.sha256((V / f'xeen_guard_{t}.glb').read_bytes()).hexdigest()
    models.append({'id': f'guard_{t}', 'label': label, 'revision': 'xeen_guard_claude_v1',
                   'url': f'xeen_guard_{t}.glb?v={hh[:12]}', 'sha256': hh})
m = {'revision': 'xeen_guard_claude_v1', 'model': 'xeen_guard_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'guard_a', 'model_sha256': h,
     'models': models, 'clips': {}}
for k, (mode, prov, imgs) in clips.items():
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov,
                                  'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
