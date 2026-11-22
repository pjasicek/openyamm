#!/usr/bin/env python3
"""Review viewer manifest from review/viewer/xeen_saber_a.glb: clip durations read from the GLB, native reference
frames per clip, cache-busting hash on the model URL."""
import json, hashlib, struct
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
V = ROOT / 'review' / 'viewer'
REL = '../../native'
clips = {
 'Standing': ('loop', 'breathing, slow look round, tail-tip swish (native idle 044.mon 0-2)', ['mon_0000', 'mon_0001', 'mon_0002']),
 'Walking': ('loop', 'lateral-sequence walk, slightly crouched, shoulder blades rolling, 1.45 m per cycle', ['mon_0004', 'mon_0005']),
 'Running': ('loop', 'rotary gallop, the spine flexing, 2.30 m per cycle (chase)', ['mon_0004']),
 'Sprint': ('loop', 'the gallop stretched, 3.00 m per cycle (MAW chase)', ['mon_0004']),
 'Attack': ('once', 'crouch and snarl (att 0), lunge with both forepaws thrown forward and the jaws wide (att 1-2, impact 0.5 s), jaws snap shut, recover (att 3)', ['att_0000', 'att_0001', 'att_0002', 'att_0003']),
 'Hit': ('once', 'flinches back, head jerks up and aside, snarls (no native frame)', ['mon_0000']),
 'Death': ('once', 'rears in pain, the hind legs buckle, falls onto its right side (no native frame)', ['mon_0000']),
 'Dead': ('loop', 'Death last pose held: on its right side, legs out', ['mon_0000']),
 'Fidget': ('once', 'a great yawn baring the sabres, a head shake, a tail flick', ['att_0001', 'mon_0006']),
}
raw = (V / 'xeen_saber_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
h = hashlib.sha256(raw).hexdigest()
LABELS = {'a': 'Sabertooth / Kennel Sabertooth - saber_a (native tawny ochre)'}
models = []
for t, label in LABELS.items():
    hh = hashlib.sha256((V / f'xeen_saber_{t}.glb').read_bytes()).hexdigest()
    models.append({'id': f'saber_{t}', 'label': label, 'revision': 'xeen_saber_claude_v1',
                   'url': f'xeen_saber_{t}.glb?v={hh[:12]}', 'sha256': hh})
m = {'revision': 'xeen_saber_claude_v1', 'model': 'xeen_saber_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'saber_a', 'model_sha256': h,
     'models': models, 'clips': {}}
for k, (mode, prov, imgs) in clips.items():
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov,
                                  'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
