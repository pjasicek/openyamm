#!/usr/bin/env python3
"""review/viewer/manifest.json for the texture pass: every review/viewer/<skin>_<tag>.glb of the given tags, in tag
order per skin. Clip durations come from the installed GLB (three.js: the longest track); labels, provenance and
native anchors from the production viewer (../mm7_m322_claude) where it has the clip.
Usage: viewer_manifest.py <default model id> <tag>[=label] ..."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb import Glb  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
V = HERE / 'review/viewer'
SKINS = {'m322_a1': '331 A/A (green trousers, red hair)', 'm322_a2': '332 A/B (blue, black hair)',
         'm322_a3': '333 A/C (red, auburn hair)', 'm322_b1': '334 B/A (pale green, blonde)',
         'm322_b2': '335 B/B (black, white hair)', 'm322_b3': '336 B/C (brown, strawberry blonde)',
         'm322_c1': '337 C/A (sky blue, red hair)', 'm322_c2': '338 C/B (green, black hair)',
         'm322_c3': '339 C/C (coral, blonde)'}
default = sys.argv[1]
tags = [a.split('=', 1) if '=' in a else (a, a) for a in sys.argv[2:]]
prod = json.loads((HERE.parent / 'mm7_m322_claude/review/viewer/manifest.json').read_text())['clips']
g = Glb(HERE / 'work' / 'before_texpass' / 'mm7_m322.glb')
clips = {}
for anim in g.doc['animations']:
    duration = max(float(g.accessor(s['input']).max()) for s in anim['samplers'])
    name = anim['name']
    base = prod.get(name, {'label': name, 'mode': 'loop', 'provenance': 'installed clip (gait rollout h13)',
                           'anchors': []})
    clips[name] = {**base, 'duration': duration}
models = []
for skin, label in SKINS.items():
    for tag, tag_label in tags:
        f = V / f'{skin}_{tag}.glb'
        if not f.exists():
            continue
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        models.append({'id': f'{skin}_{tag}', 'label': f'{label} · {tag_label}', 'url': f'{f.name}?v={h[:12]}',
                       'sha256': h, 'revision': 'texpass-20261101'})
pick = next(m for m in models if m['id'] == default)
manifest = {'revision': 'texpass-20261101', 'default_model': default, 'default_clip': 'Standing', 'models': models,
            'clips': clips, 'issues': [], 'feedback': 'feedback/user_feedback.json', 'model': pick['url'],
            'model_sha256': pick['sha256']}
(V / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
print('MANIFEST', len(models), 'models', {k: round(v['duration'], 4) for k, v in clips.items()})
