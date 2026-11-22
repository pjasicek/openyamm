#!/usr/bin/env python3
"""Review viewer manifest from review/viewer/xeen_hand_a.glb: clip durations read from the GLB, native reference
frames per clip, cache-busting hash on the model URL."""
import json, hashlib, struct
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
V = ROOT / 'review' / 'viewer'
REL = '../../native'
clips = {
 'Standing': ('loop', 'hover bob; two open-close cycles fist -> half -> spread -> half (native idle 049.mon 0-7), the lip lids bare the fang ring whenever the hand opens', ['mon_0000', 'mon_0001', 'mon_0002']),
 'Walking': ('loop', 'flying forward: leaned 14 deg, half open, crawling finger wave, lips parted a little', ['mon_0001']),
 'Running': ('loop', 'leaned 22 deg, faster wave', ['mon_0003']),
 'Attack': ('once', 'draws back spreading and gaping (att 1), lunges 9 cm (att 2) and bites: lids snap shut, fingers clamp at 0.45 s, claws back into the fist (att 3)', ['att_0001', 'att_0002', 'att_0003']),
 'Hit': ('once', 'knocked back with a twist, fingers spasm open, the mouth gasps', ['mon_0001']),
 'Death': ('once', 'spasm (spread, gaping), clench, rolls palm down and drops: lies on its curled fingertips', ['att_0003']),
 'Dead': ('loop', 'Death last pose held', ['att_0003']),
 'Fidget': ('once', 'opens to half, drums the fingers pinky to index twice, back into the fist', ['mon_0001', 'mon_0005']),
}
raw = (V / 'xeen_hand_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
h = hashlib.sha256(raw).hexdigest()
m = {'revision': 'xeen_hand_claude_v1', 'model': 'xeen_hand_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'hand_a', 'model_sha256': h,
     'models': [{'id': 'hand_a', 'label': 'Carnage Hand - C (native tan skin, red maw, grey fangs)',
                 'revision': 'xeen_hand_claude_v1', 'url': f'xeen_hand_a.glb?v={h[:12]}', 'sha256': h}],
     'clips': {}}
for k, (mode, prov, imgs) in clips.items():
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov,
                                  'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
