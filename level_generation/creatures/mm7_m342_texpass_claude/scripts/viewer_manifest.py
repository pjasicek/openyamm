#!/usr/bin/env python3
"""review/viewer/manifest.json for the m342 texture pass: every review/viewer/<variant>_<tag>.glb of the given tags, in
tag order per skin. Clips and durations come from the installed GLB (all eight, including Walk2 and Jog); anchors of
the production viewer (mm7_m342_claude) are kept where it has them, rebased.
Usage: viewer_manifest.py <revision> <default model id> <tag>[=label] ...
CLOSEUPS=1 maps the capture wrapper's focus names arms/skirt/feet/shoulders to eyes/mouth/nose/face (close-up shots
only; rewrite the manifest without it afterwards)."""
import hashlib
import os
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb import Glb  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
V = HERE / 'review/viewer'
SKINS = {'m342_aa': 'A A (343) green / chestnut', 'm342_ab': 'A B (344) yellow-olive / ginger',
         'm342_ac': 'A C (345) brown / blonde', 'm342_ba': 'B A (346) red / black', 'm342_bb': 'B B (347) blue / blonde',
         'm342_bc': 'B C (348) purple / white', 'm342_ca': 'C A (349) khaki / red-brown',
         'm342_cb': 'C B (350) white / grey', 'm342_cc': 'C C (351) black / brown'}
revision, default = sys.argv[1], sys.argv[2]
tags = [a.split('=', 1) if '=' in a else (a, a) for a in sys.argv[3:]]
prod = json.loads((HERE.parent / 'mm7_m342_claude/review/viewer/manifest.json').read_text())['clips']
g = Glb(HERE / 'work/before_texpass/mm7_m342.glb')
clips = {}
for anim in g.doc['animations']:
    duration = max(float(g.accessor(s['input']).max()) for s in anim['samplers'])
    old = prod.get(anim['name'], {})
    anchors = old.get('anchors', [])          # same folder depth as the production viewer: paths stay valid
    clips[anim['name']] = {'label': anim['name'], 'duration': duration,
                           'mode': old.get('mode', 'once' if anim['name'] in ('Death', 'Hit') else 'loop'),
                           'provenance': old.get('provenance', 'installed clip'), 'anchors': anchors}
models = []
for skin, name in SKINS.items():
    for tag, label in tags:
        f = V / f'{skin}_{tag}.glb'
        if not f.exists():
            continue
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        models.append({'id': f'{skin}_{tag}', 'label': f'{name} · {label}', 'url': f'{f.name}?v={h[:12]}',
                       'sha256': h, 'revision': revision})
pick = next(m for m in models if m['id'] == default)
manifest = {'revision': revision, 'default_model': default, 'default_clip': 'Standing', 'models': models,
            'clips': clips, 'issues': [], 'feedback': 'feedback/user_feedback.json', 'model': pick['url'],
            'model_sha256': pick['sha256']}
if os.environ.get('CLOSEUPS'):
    manifest['focus_overrides'] = {'arms': 'eyes', 'skirt': 'mouth', 'feet': 'nose', 'shoulders': 'face'}
(V / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
print('MANIFEST', len(models), 'models', {k: round(v['duration'], 3) for k, v in clips.items()})
