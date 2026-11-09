#!/usr/bin/env python3
"""review/viewer/manifest.json from the viewer GLBs (clip durations read from the GLB samplers)."""
import hashlib, json, struct
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
V = ROOT / 'review/viewer'
LABELS = {'a': 'A: Glassback Pup (10080) - grey hide, short stubby crest, pale teal glow',
          'b': 'B: Glassback (10081) - darker hide, full crest, strong teal glow',
          'c': 'C: Glassback Bull (10082) - near-black hide, rust streaks, tall jagged crest, green-white glow'}
PROV = {'Standing': 'procedural: breathing, slow head sway, tail drift (3 s loop)',
        'Walking': 'procedural alternating tripod (FL MR HL / FR ML HR), duty 0.5, stride 0.875 m',
        'Running': 'procedural lumbering charge, duty 0.4, stride 1.458 m, body low, head down',
        'Attack': 'rears up on the hind legs, holds, slams down with beak and front feet; impact 1.083 s',
        'Bite': 'secondary: draws back, lunges and crushes down with the beak; impact 0.583 s',
        'Hit': 'flinch back and aside', 'Death': 'legs buckle outward, belly drops onto the floor, head sinks aside',
        'Dead': 'last Death pose held', 'Fidget': 'grazing: lowers the head, crops at the ground twice'}


def durations(path):
    raw = path.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; d = json.loads(raw[20:20 + n])
    return {a['name']: max(d['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in d['animations']}


models = []
for t in 'abc':
    p = V / f'hes_glassback_{t}.glb'
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    models.append({'id': f'hgb_{t}', 'label': LABELS[t], 'revision': 'hes_glassback_claude_v1',
                   'url': f'{p.name}?v={sha[:12]}', 'sha256': sha})
dur = durations(V / 'hes_glassback_b.glb')
clips = {}
for name in ['Standing', 'Walking', 'Running', 'Attack', 'Bite', 'Hit', 'Death', 'Dead', 'Fidget']:
    clips[name] = {'label': name, 'duration': round(dur[name], 6), 'mode': 'loop' if name in ('Standing', 'Walking', 'Running', 'Fidget') else 'once',
                   'provenance': PROV[name], 'anchors': [{'time': 0.0, 'label': name, 'phase': PROV[name],
                   'source_images': ['../../references_hd/03_left.png']}]}
man = {'revision': 'hes_glassback_claude_v1', 'model': 'hes_glassback_b.glb', 'default_clip': 'Walking',
       'feedback': 'feedback/user_feedback.json', 'default_model': 'hgb_b', 'model_sha256': models[1]['sha256'],
       'models': models, 'clips': clips}
json.dump(man, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: v['duration'] for k, v in clips.items()})
