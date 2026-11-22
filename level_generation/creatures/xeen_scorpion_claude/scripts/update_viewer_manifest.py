#!/usr/bin/env python3
"""Review viewer manifest from review/viewer/xeen_scorpion_a.glb: clip durations read from the GLB, native reference
frames per clip, cache-busting hash on the model URL."""
import json, hashlib, struct
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
V = ROOT / 'review' / 'viewer'
REL = '../../native'
clips = {
 'Standing': ('loop', 'breathing, the tail sways, the claws shift and twitch open (native idle 019.mon 0-7)', ['mon_0000', 'mon_0003', 'mon_0006']),
 'Walking': ('loop', 'alternating tetrapod (L1 R2 L3 R4 / R1 L2 R3 L4), 0.50 m per cycle', ['mon_0000']),
 'Running': ('loop', 'the same, lower, 0.80 m per cycle', ['mon_0000']),
 'Attack': ('once', 'rears, claws open, tail cocked back (0.32 s); the right claw lunges and snaps while the tail strikes forward over the head (impact 0.467 s, native att 1-2); recovers', ['att_0001', 'att_0002', 'att_0003']),
 'Hit': ('once', 'jolts back, claws flinch up and open, tail flinches back (no native frame)', ['mon_0000']),
 'Death': ('once', 'rears in pain, the tail lashes up, collapses on its belly, the tail falls onto the floor behind (no native frame)', ['mon_0000']),
 'Dead': ('loop', 'Death last pose held: on its belly, legs splayed, the tail on the floor', ['mon_0000']),
 'Fidget': ('once', 'the tail curls and sways, the left then the right claw snaps twice', ['mon_0004', 'mon_0007']),
}
raw = (V / 'xeen_scorpion_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
h = hashlib.sha256(raw).hexdigest()
models = [{'id': 'scorpion_a', 'label': 'Scorpion - A (native dark glossy brown)', 'revision': 'xeen_scorpion_claude_v1',
           'url': f'xeen_scorpion_a.glb?v={h[:12]}', 'sha256': h}]
m = {'revision': 'xeen_scorpion_claude_v1', 'model': 'xeen_scorpion_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'scorpion_a', 'model_sha256': h,
     'models': models, 'clips': {}}
for k, (mode, prov, imgs) in clips.items():
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov,
                                  'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
