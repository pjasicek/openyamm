#!/usr/bin/env python3
"""review/viewer/manifest.json: installed (r100) and reduced (TAG) GLBs per tier, the clips and native anchors of the
production viewer (mm8_m480_claude/review/viewer/manifest.json) with paths rebased; sha256 and ?v= from the files.
Usage: viewer_manifest.py <tag> <reduced triangle count>"""
import hashlib, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; V = HERE / 'review/viewer'
tag, tris = sys.argv[1], int(sys.argv[2])
prod = json.loads((HERE.parent / 'mm8_m480_claude/review/viewer/manifest.json').read_text())
tiers = {'m480_a': 'A · green cloth / brown crest', 'm480_b': 'B · grey cloth / grey crest', 'm480_c': 'C · red cloth / black crest'}
models = []
for tier, name in tiers.items():
    for t, what in (('r100', 'installed · 9,744 + club 1,668'), (tag, f'reduced · {tris:,} + club 1,668')):
        f = V / f'mm8_{tier}_{t}.glb'; h = hashlib.sha256(f.read_bytes()).hexdigest()
        models.append({'id': f'{tier}_{t}', 'label': f'Troll peasant {name} · {what}', 'url': f'{f.name}?v={h[:12]}',
                       'sha256': h, 'revision': f'reduce-{tag}'})
s = json.dumps(prod['clips']).replace('"../../references_native/', '"../../../mm8_m480_claude/references_native/')
pick = next(m for m in models if m['id'] == f'm480_a_{tag}')
m = {'revision': f'reduce-{tag}', 'default_model': pick['id'], 'default_clip': 'Standing', 'models': models,
     'clips': json.loads(s), 'issues': [], 'feedback': '../feedback/user_feedback.json',
     'model': pick['url'], 'model_sha256': pick['sha256']}
(V / 'manifest.json').write_text(json.dumps(m, indent=1) + '\n'); print('MANIFEST', len(models), 'models')
