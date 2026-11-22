#!/usr/bin/env python3
"""Review viewer manifest from review/viewer/xeen_octopod_a/b/c.glb: clip durations read from the GLB, native
reference frames per clip, cache-busting hashes on the model URLs."""
import json, hashlib, struct
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
V = ROOT / 'review' / 'viewer'
REL = '../../native'
info = json.load(open(ROOT / 'work' / 'anim_info.json'))['clips']
imp = info['Attack']['impact_s']
clips = {
 'Standing': ('loop', 'head bobbing on the water, every tentacle arching out of the water and weaving with its own phase, tips curling (native 041.mon 0-7)', ['mon_0000', 'mon_0004', 'mon_0005']),
 'Walking': ('loop', 'swimming on the surface: the tentacles swept back in low arches, a stroke pulse per cycle, head pitched forward', ['mon_0001', 'mon_0002']),
 'Running': ('loop', 'the same, swept further back, lower and faster', ['mon_0001']),
 'Attack': ('once', f'the front tentacles rear up tall, then lash forward and down onto the party, the head lunging (impact {imp} s); the purple ink spray is the binding glow at Socket_Siphon (native att 1-2)', ['att_0000', 'att_0001', 'att_0002', 'att_0003']),
 'Hit': ('once', 'the head jerks back and ducks, tentacles flinch up and curl (no native frame)', ['mon_0003']),
 'Death': ('once', 'tentacles flail, the head tips back, the whole body sinks under the waterline, the foam ring shrinks away (no native corpse)', ['att_0003']),
 'Dead': ('loop', 'sunk below the waterline (nothing above z 0)', ['mon_0007']),
 'Fidget': ('once', 'the left side tentacle rises tall and curls and uncurls its tip twice, the head turning toward it', ['mon_0006', 'mon_0007']),
}
models = []
for tier, label in (('octopod_a', 'Octopod - Xeen Octopod A and D (native red, yellow-olive suckers, blue eyes)'),
                    ('octopod_b', 'Great Octopod - Xeen Octopod B (violet-purple, pale gold suckers, amber eyes)'),
                    ('octopod_c', 'Kraken - Xeen Octopod C (dark sea-green slate, bone suckers, red-orange eyes)')):
    raw = (V / f'xeen_{tier}.glb').read_bytes()
    h = hashlib.sha256(raw).hexdigest()
    models.append({'id': tier, 'label': label, 'revision': 'xeen_octopod_claude_v1', 'url': f'xeen_{tier}.glb?v={h[:12]}',
                   'sha256': h})
raw = (V / 'xeen_octopod_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
m = {'revision': 'xeen_octopod_claude_v1', 'model': 'xeen_octopod_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'octopod_a', 'model_sha256': models[0]['sha256'],
     'models': models, 'clips': {}}
for k, (mode, prov, imgs) in clips.items():
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov,
                                  'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
