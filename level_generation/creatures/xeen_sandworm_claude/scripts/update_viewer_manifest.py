#!/usr/bin/env python3
"""Review viewer manifest from review/viewer/xeen_sandworm_a.glb and _c.glb: clip durations read from the GLB, native
reference frames per clip, cache-busting hashes on the model URLs."""
import json, hashlib, struct
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
V = ROOT / 'review' / 'viewer'
REL = '../../native'
info = json.load(open(ROOT / 'work' / 'anim_info.json'))['clips']
imp = info['Attack']['impact_s']
clips = {
 'Standing': ('loop', 'upright out of its sand mound, slow sway travelling up the rings, maw slowly opening and closing (native 056.mon 4-5)', ['mon_0004', 'mon_0005']),
 'Walking': ('loop', 'sunk into a travelling mound (lower rings shrunk inside it), upper rings and maw above, the hump rippling (native mon 1-3: the worm in the sand)', ['mon_0001', 'mon_0002', 'mon_0003']),
 'Running': ('loop', 'sunk deeper, leaning forward, faster ripple', ['mon_0001', 'mon_0002']),
 'Attack': ('once', f'rears back with the maw opening, lunges forward-down bent over toward the party, maw wide open facing forward (impact {imp} s, att 1-2), snaps shut, recovers', ['att_0000', 'att_0001', 'att_0002']),
 'Hit': ('once', 'recoils back and aside, maw clenched (no native frame)', ['mon_0005']),
 'Death': ('once', 'writhes with the maw gaping, sinks partly into the mound and topples aside onto the floor', ['mon_0006', 'mon_0007']),
 'Dead': ('loop', 'Death last pose held: slumped half out of the mound on the floor', ['mon_0007']),
 'Fidget': ('once', 'sinks partly into the mound and rises again, maw flexing wide (native mon 0-7 cycle)', ['mon_0002', 'mon_0005']),
}
models = []
for tier, label in (('sandworm_a', 'Sand Worm - Xeen Sand Worm A (native orange-ochre, grey spikes, red maw)'),
                    ('sandworm_c', 'Great Worm - Xeen Sand Worm C (rust-red / umber, near-black spikes, crimson maw)')):
    raw = (V / f'xeen_{tier}.glb').read_bytes()
    h = hashlib.sha256(raw).hexdigest()
    models.append({'id': tier, 'label': label, 'revision': 'xeen_sandworm_claude_v1', 'url': f'xeen_{tier}.glb?v={h[:12]}',
                   'sha256': h})
raw = (V / 'xeen_sandworm_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
m = {'revision': 'xeen_sandworm_claude_v1', 'model': 'xeen_sandworm_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'sandworm_a', 'model_sha256': models[0]['sha256'],
     'models': models, 'clips': {}}
for k, (mode, prov, imgs) in clips.items():
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov,
                                  'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
