#!/usr/bin/env python3
"""Review viewer manifest: clip durations read from the viewer GLB, native reference frames per clip, cache-busting
hash on the model URL."""
import json, hashlib, struct
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[1] / 'native'
REL = '../../native'
clips = {
 'Standing': ('loop', 'Procedural hover: the feet bob in turn (1 s), wings beat 2.5 Hz, slight sway', ['mon_0000', 'mon_0002', 'mon_0004', 'mon_0006']),
 'Walking': ('loop', 'Standing leaned 10 deg toes-down, wings 3.5 Hz, deeper bob', ['mon_0001', 'mon_0003']),
 'Running': ('loop', 'Leaned 18 deg, wings 4.5 Hz', ['mon_0005', 'mon_0007']),
 'Attack': ('once', 'The left (near) foot draws back and up with its sole turned to the party, then stamps forward; impact 0.45 s', ['att_0000', 'att_0001', 'att_0002']),
 'Hit': ('once', 'Both feet jolt back and roll, wings flare', ['att_0003']),
 'Death': ('once', 'Wings flare and stop, the feet tumble onto their sides, wings fitted to the floor', ['att_0003']),
 'Dead': ('loop', 'Last Death pose held', ['att_0003']),
 'Fidget': ('once', 'Toe wiggle on the left foot, two heel taps on the right one', ['mon_0000']),
}
raw = (V / 'xeen_feet_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
h = hashlib.sha256(raw).hexdigest()
m = {'revision': 'xeen_feet_claude_v1', 'model': 'xeen_feet_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'feet_a', 'model_sha256': h,
     'models': [{'id': 'feet_a', 'label': 'Flying Feet - A (native warm skin, white wings)', 'revision': 'xeen_feet_claude_v1',
                 'url': f'xeen_feet_a.glb?v={h[:12]}', 'sha256': h}], 'clips': {}}
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()]
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
