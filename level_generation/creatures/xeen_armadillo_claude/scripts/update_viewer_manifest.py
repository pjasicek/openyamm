#!/usr/bin/env python3
"""Review viewer manifest from review/viewer/xeen_armadillo_a.glb (one skin): clip durations read from the GLB, native reference
frames per clip, cache-busting hash on the model URL."""
import json, hashlib, struct
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
V = ROOT / 'review' / 'viewer'
REL = '../../native'
clips = {
 'Standing': ('loop', 'breathing heave, two tongue flicks, head drift, slow tail sway (native idle 005.mon 0-7)', ['mon_0000', 'mon_0004']),
 'Walking': ('loop', 'heavy waddle on short sprawled legs (LF+RH / RF+LH), 0.45 m per cycle', ['mon_0000']),
 'Running': ('loop', 'the same, longer, faster and lower, 0.80 m per cycle', ['mon_0000']),
 'Attack': ('once', 'forelegs up, tail over the back as the spikes pop out of the ball (att 0-1), the mace comes down over the head with both claws thrown forward (att 2, impact 0.733 s), hunch (att 3)', ['att_0000', 'att_0001', 'att_0002', 'att_0003']),
 'Hit': ('once', 'flinches into the shell: head ducked, body dropped, tail tucked (no native frame)', ['mon_0000']),
 'Death': ('once', 'rears in pain, rolls onto its right side, legs curl, tail falls limp (no native frame)', ['mon_0000']),
 'Dead': ('loop', 'Death last pose held: on its right side on the floor', ['mon_0000']),
 'Fidget': ('once', 'curls partly into a ball and uncurls; long tongue flick', ['mon_0004', 'att_0003']),
}
raw = (V / 'xeen_armadillo_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
h = hashlib.sha256(raw).hexdigest()
LABELS = {'a': 'Armadillo - Xeen Sand Worm B (native red, Darkside image 5)'}
models = []
for t, label in LABELS.items():
    hh = hashlib.sha256((V / f'xeen_armadillo_{t}.glb').read_bytes()).hexdigest()
    models.append({'id': f'armadillo_{t}', 'label': label, 'revision': 'xeen_armadillo_claude_v1',
                   'url': f'xeen_armadillo_{t}.glb?v={hh[:12]}', 'sha256': hh})
m = {'revision': 'xeen_armadillo_claude_v1', 'model': 'xeen_armadillo_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'armadillo_a', 'model_sha256': h,
     'models': models, 'clips': {}}
for k, (mode, prov, imgs) in clips.items():
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov,
                                  'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
