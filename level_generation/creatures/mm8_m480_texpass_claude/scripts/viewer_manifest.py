#!/usr/bin/env python3
"""review/viewer/manifest.json for the texture pass: every review/viewer/<variant>_<tag>.glb of the given tags, in
tag order per tier, with the clips and native anchors of the production viewer (mm8_m480_claude) rebased.
Usage: viewer_manifest.py <default model id> <tag>[=label] ..."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
V = HERE / 'review/viewer'
TIERS = {'m480_a': 'MM8 A (green wrap, brown crest)', 'm480_b': 'MM8 B (grey wrap, grey crest)',
         'm480_c': 'MM8 C (red wrap, black crest)', 'm461_a': 'MM7 Swamp Troll (499)',
         'm461_b': 'MM7 River Troll (505)', 'm461_c': 'MM7 Mountain Troll (509)'}
default = sys.argv[1]
tags = [a.split('=', 1) if '=' in a else (a, a) for a in sys.argv[2:]]
prod = json.loads((HERE.parent / 'mm8_m480_claude/review/viewer/manifest.json').read_text())
models = []
for tier, name in TIERS.items():
    for tag, label in tags:
        f = V / f'{tier}_{tag}.glb'
        if not f.exists():
            continue
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        models.append({'id': f'{tier}_{tag}', 'label': f'{name} · {label}', 'url': f'{f.name}?v={h[:12]}',
                       'sha256': h, 'revision': 'texpass-20261031'})
clips = json.loads(json.dumps(prod['clips']).replace('"../../references_native/',
                                                     '"../../../mm8_m480_claude/references_native/'))
pick = next(m for m in models if m['id'] == default)
manifest = {'revision': 'texpass-20261031', 'default_model': default, 'default_clip': 'Standing', 'models': models,
            'clips': clips, 'issues': [], 'feedback': 'feedback/user_feedback.json', 'model': pick['url'],
            'model_sha256': pick['sha256']}
(V / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
print('MANIFEST', len(models), 'models')
