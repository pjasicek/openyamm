#!/usr/bin/env python3
"""Review viewer manifest from review/viewer/xeen_mole_a/b/c.glb: clip durations read from the GLB, native reference
frames per clip, cache-busting hash on the model URL."""
import json, hashlib, struct
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
V = ROOT / 'review' / 'viewer'
REL = '../../native'
clips = {
 'Standing': ('loop', 'breathing heave, snout twitches, tail sway (native idle 011.mon 0-7)', ['mon_0000', 'mon_0003', 'mon_0006']),
 'Walking': ('loop', 'paddle gait: the spade hands stroke back and out like a swimmer, 0.60 m per cycle', ['mon_0000']),
 'Running': ('loop', 'the same, longer, lower and faster, 0.95 m per cycle', ['mon_0000']),
 'Attack': ('once', 'rears, both claws raised and splayed (att 1), thrown forward and down at the party (att 2, impact 0.47 s), dig in (att 3)', ['att_0001', 'att_0002', 'att_0003']),
 'Hit': ('once', 'jolts back, head up, hands flinch (no native frame)', ['mon_0000']),
 'Death': ('once', 'rears in pain, rolls onto its right side, claws curl (no native frame)', ['mon_0000']),
 'Dead': ('loop', 'Death last pose held: on its right side on the floor', ['mon_0000']),
 'Fidget': ('once', 'digs: left then right hand scrape the ground, snout sniffs', ['mon_0004', 'att_0003']),
}
raw = (V / 'xeen_mole_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
h = hashlib.sha256(raw).hexdigest()
LABELS = {'a': 'Tiger Mole - A (native teal-blue)', 'b': 'Rock Mole - B (stone grey-brown)',
          'c': 'Tunnel Mole - C (dark earth-brown)'}
models = []
for t, label in LABELS.items():
    hh = hashlib.sha256((V / f'xeen_mole_{t}.glb').read_bytes()).hexdigest()
    models.append({'id': f'mole_{t}', 'label': label, 'revision': 'xeen_mole_claude_v1',
                   'url': f'xeen_mole_{t}.glb?v={hh[:12]}', 'sha256': hh})
m = {'revision': 'xeen_mole_claude_v1', 'model': 'xeen_mole_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'mole_a', 'model_sha256': h,
     'models': models, 'clips': {}}
for k, (mode, prov, imgs) in clips.items():
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov,
                                  'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
