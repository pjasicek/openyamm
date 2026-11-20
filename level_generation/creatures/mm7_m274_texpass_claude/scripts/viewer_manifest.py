#!/usr/bin/env python3
"""review/viewer/manifest.json for the Mage texture pass: every review/viewer/<tier>_<tag>.glb of the given tags, in
tag order per tier. Clips and durations come from the installed GLB (the review page checks every clip against each
model); provenance and native anchors from the reduction's viewer (mm7_m274_reduce_claude).
Usage: viewer_manifest.py <default model id> <tag>[=label] ..."""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb import Glb  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
V = HERE / 'review/viewer'
REVISION = 'texpass-20261101'
TIERS = {'m274_a': 'Sorcerer A (green robe, ginger hair)', 'm274_b': 'Wizard B (violet robe, dark grey hair)',
         'm274_c': 'Archmage C (red robe, white hair)'}
default = sys.argv[1]
tags = [a.split('=', 1) if '=' in a else (a, a) for a in sys.argv[2:]]
prod = json.loads((HERE.parent / 'mm7_m274_reduce_claude/review/viewer/manifest.json').read_text())['clips']
g = Glb(HERE / 'work/before_texpass/mm7_m274.glb')
clips = {}
for anim in g.doc['animations']:
    name = anim['name']
    duration = max(float(g.accessor(s['input']).max()) for s in anim['samplers'])
    old = prod.get(name, {})      # same depth under level_generation/creatures/: anchor paths stay valid
    clips[name] = {'label': name, 'duration': duration,
                   'mode': old.get('mode', 'once' if name in ('Attack', 'Cast', 'Hit', 'Death') else 'loop'),
                   'provenance': old.get('provenance', 'installed (gait rollout 2026-10-31)'),
                   'anchors': old.get('anchors', [])}
models = []
for tier, name in TIERS.items():
    for tag, label in tags:
        f = V / f'{tier}_{tag}.glb'
        if not f.exists():
            continue
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        models.append({'id': f'{tier}_{tag}', 'label': f'{name} · {label}', 'url': f'{f.name}?v={h[:12]}',
                       'sha256': h, 'revision': REVISION})
pick = next(m for m in models if m['id'] == default)
manifest = {'revision': REVISION, 'default_model': default, 'default_clip': 'Standing', 'models': models,
            'clips': clips, 'issues': [], 'feedback': 'feedback/user_feedback.json', 'model': pick['url'],
            'model_sha256': pick['sha256']}
(V / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
print('MANIFEST', len(models), 'models', {k: round(v['duration'], 4) for k, v in clips.items()})
