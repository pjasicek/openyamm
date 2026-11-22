#!/usr/bin/env python3
"""Review viewer manifest from review/viewer/xeen_electrapede_a.glb: clip durations read from the GLB, native
reference frames per clip, cache-busting hash on the model URL."""
import json, hashlib, struct
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
V = ROOT / 'review' / 'viewer'
REL = '../../native'
info = json.load(open(ROOT / 'work' / 'anim_info.json'))['clips']
imp = info['Attack']['impact_s']
clips = {
 'Standing': ('loop', 'breathing ripple, head drift, antennae sway, mandibles chew (native idle 007.mon 0-7)', ['mon_0000', 'mon_0003', 'mon_0005']),
 'Walking': ('loop', 'S-wave head to tail, metachronal leg waves (each pair 0.11 cycle behind the one in front, left/right in antiphase), 0.45 m per cycle', ['mon_0000']),
 'Running': ('loop', 'larger S-wave, faster legs, 0.70 m per cycle', ['mon_0000']),
 'Attack': ('once', f'the front rears, mouth opening and antennae up (att 0-1: lightning charges, engine melee glow at mouth and antenna tips), lunges and bites (impact {imp} s)', ['att_0000', 'att_0001', 'att_0002']),
 'Hit': ('once', 'recoils: front jerks up and back, body kinks (no native frame)', ['mon_0000']),
 'Death': ('once', 'thrashes, then curls into a C on the floor, legs folding in (att 3 shows the curled body)', ['att_0003']),
 'Dead': ('loop', 'Death last pose held: curled on the floor', ['att_0003']),
 'Fidget': ('once', 'head turns left and right, antennae flick, the front pair lifts and cleans the mouth', ['mon_0004', 'mon_0006']),
}
raw = (V / 'xeen_electrapede_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
h = hashlib.sha256(raw).hexdigest()
models = [{'id': 'electrapede_a', 'label': 'Electrapede - B tier of Xeen Crawler (native green, magenta eyes and legs)',
           'revision': 'xeen_electrapede_claude_v1', 'url': f'xeen_electrapede_a.glb?v={h[:12]}', 'sha256': h}]
m = {'revision': 'xeen_electrapede_claude_v1', 'model': 'xeen_electrapede_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'electrapede_a', 'model_sha256': h,
     'models': models, 'clips': {}}
for k, (mode, prov, imgs) in clips.items():
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov,
                                  'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
