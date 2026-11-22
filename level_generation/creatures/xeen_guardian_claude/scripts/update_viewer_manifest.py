#!/usr/bin/env python3
"""Review viewer manifest from review/viewer/xeen_guardian_a.glb: clip durations read from the GLB, native reference
frames per clip, cache-busting hash on the model URL."""
import json, hashlib, struct
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
V = ROOT / 'review' / 'viewer'
REL = '../../native'
clips = {
 'Standing': ('loop', 'hover bob and sway; the jaw chatters (native idle 083.mon 0-7)', ['mon_0000', 'mon_0001', 'mon_0006']),
 'Walking': ('loop', 'Standing leaned 8 deg nose-down, faster bob, jaw nearly shut', ['mon_0002']),
 'Running': ('loop', 'leaned 14 deg, stronger bob', ['mon_0004']),
 'Attack': ('once', 'melee: draws back, jaw gapes, eyes flare, lunges and bites shut (impact 0.45 s)', ['att_0000', 'att_0001']),
 'AttackRanged': ('once', 'rises, jaw gapes, eyes and gem flare; release from Socket_Gem at 0.50 s (native: lightning from the eyes)', ['att_0001', 'att_0002']),
 'Hit': ('once', 'knocked back with a small spin, jaw snaps open', ['mon_0003']),
 'Death': ('once', 'shudders, eyes go out, drops and rolls onto its left side on the floor (native att 3: spent eyes)', ['att_0003']),
 'Dead': ('loop', 'Death last pose held', ['att_0003']),
 'Fidget': ('once', 'jaw-chattering cackle, turning side to side', ['mon_0005', 'mon_0006']),
}
raw = (V / 'xeen_guardian_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
h = hashlib.sha256(raw).hexdigest()
m = {'revision': 'xeen_guardian_claude_v1', 'model': 'xeen_guardian_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'guardian_a', 'model_sha256': h,
     'models': [{'id': 'guardian_a', 'label': 'Guardian - B (native chrome, red gem, green eyes)',
                 'revision': 'xeen_guardian_claude_v1', 'url': f'xeen_guardian_a.glb?v={h[:12]}', 'sha256': h}],
     'clips': {}}
for k, (mode, prov, imgs) in clips.items():
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov,
                                  'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
