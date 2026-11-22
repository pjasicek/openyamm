#!/usr/bin/env python3
"""Review viewer manifest from review/viewer/xeen_mantis_a/b/c/lava.glb: clip durations read from the GLB, native reference
frames per clip, cache-busting hash on the model URL."""
import json, hashlib, struct
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
V = ROOT / 'review' / 'viewer'
REL = '../../native'
clips = {
 'Standing': ('loop', 'breathing, the raised hooks bob, antennae sway, the radial mouth pulses (native idle 010.mon 0-7)', ['mon_0000', 'mon_0003', 'mon_0006']),
 'Walking': ('loop', 'diagonal trot (L1+R2 / R1+L2), hooks held up, 0.50 m per cycle', ['mon_0000']),
 'Running': ('loop', 'the same, lower and leaning, 0.80 m per cycle', ['mon_0000']),
 'Attack': ('once', 'rears and throws both arms out wide (att 1), snaps the scythes together forward and down at the party (att 2, impact 0.50 s), folds back (att 3)', ['att_0001', 'att_0002', 'att_0003']),
 'Hit': ('once', 'jolts back, arms flinch up, head back (no native frame)', ['mon_0000']),
 'Death': ('once', 'rears, topples backward onto its back, legs curl up, arms fold (no native frame)', ['mon_0000']),
 'Dead': ('loop', 'Death last pose held: on its back, legs curled', ['mon_0000']),
 'Fidget': ('once', 'head tilts, the left hook wipes the mouth, antennae twitch', ['mon_0004', 'mon_0007']),
}
raw = (V / 'xeen_mantis_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
h = hashlib.sha256(raw).hexdigest()
LABELS = {'a': 'Mantis Ant - A (native violet)', 'b': 'Mantis Warrior - B (bronze-green, bronze joints)',
          'c': 'Mantis Queen - C (black-violet, gold joints; 1.2x in game)',
          'lava': 'Lava Roach - Crawler C (grey, glowing joints)'}
models = []
for t, label in LABELS.items():
    hh = hashlib.sha256((V / f'xeen_mantis_{t}.glb').read_bytes()).hexdigest()
    models.append({'id': f'mantis_{t}', 'label': label, 'revision': 'xeen_mantis_claude_v1',
                   'url': f'xeen_mantis_{t}.glb?v={hh[:12]}', 'sha256': hh})
m = {'revision': 'xeen_mantis_claude_v1', 'model': 'xeen_mantis_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'mantis_a', 'model_sha256': h,
     'models': models, 'clips': {}}
for k, (mode, prov, imgs) in clips.items():
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov,
                                  'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
