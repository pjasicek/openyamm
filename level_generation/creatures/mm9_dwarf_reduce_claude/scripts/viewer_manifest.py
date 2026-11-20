#!/usr/bin/env python3
"""review/viewer/manifest.json: the installed model (r100, 13,643) and the reduction (REV, LOD0 count) for the three tiers
(GLBs from viewer_tiers.py); clips copied from the creature project's viewer manifest (read only).
Usage: viewer_manifest.py <rev tag, e.g. r70> <LOD0 triangles>"""
import hashlib, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; V = ROOT / 'review' / 'viewer'
rev, tris = sys.argv[1], int(sys.argv[2])
o = json.load(open(ROOT.parent / 'mm9_dwarf_claude' / 'review' / 'viewer' / 'manifest.json'))
clips = o['clips']
if isinstance(clips, dict):
    for c in clips.values():   # anchor images live in the source project
        for a in c.get('anchors', []):
            a['source_images'] = [x.replace('../../', '../../../mm9_dwarf_claude/', 1) for x in a.get('source_images', [])]
names = {'a': 'Dwarven Guard', 'b': 'Dwarven Soldier', 'c': 'Dwarven Commander'}
labs = {'r100': 'installed · 13,643', rev: f'reduced · {tris:,}'}
models = []
for lab in labs:
    for t in 'abc':
        f = f'dwarf_{t}_{lab}.glb'; h = hashlib.sha256((V / f).read_bytes()).hexdigest()
        models.append({'id': f'{t}_{lab}', 'label': f'{names[t]} · {labs[lab]}', 'revision': f'reduce-{rev}',
                       'url': f'{f}?v={h[:12]}', 'sha256': h})
json.dump({'revision': f'reduce-{rev}', 'model': f'dwarf_a_{rev}.glb', 'default_clip': 'Standing', 'default_model': f'a_{rev}',
           'feedback': 'feedback/user_feedback.json', 'models': models, 'clips': clips}, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', len(models))
