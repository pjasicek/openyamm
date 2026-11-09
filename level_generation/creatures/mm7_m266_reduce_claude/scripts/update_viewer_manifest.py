#!/usr/bin/env python3
"""Viewer manifest for the reduction review: the batch I tiers (r100) beside the reduced ones (<tag>), the batch I
viewer's clip list, provenance and native reference frames unchanged. Usage: update_viewer_manifest.py <tag> <tris>"""
import hashlib, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; V = HERE / 'review/viewer'
tag, tris = sys.argv[1], int(sys.argv[2])
src = json.loads((HERE.parent / 'mm7_m266_claude/review/viewer/manifest.json').read_text())
names = {'m266_a': 'Fire Hydra A (olive)', 'm266_b': 'Air Hydra B (blue-grey)', 'm266_c': 'Chaos Hydra C (red)'}
models = []
for t, label in (('r100', 'batch I · 17,866'), (tag, f'reduced · {tris:,}')):
    for v, n in names.items():
        g = V / f'mm7_{v}_{t}.glb'; h = hashlib.sha256(g.read_bytes()).hexdigest()
        models.append({'id': f'{v[-1]}_{t}', 'label': f'{n} · {label}', 'revision': 'reduce-1', 'url': f'{g.name}?v={h[:12]}',
                       'sha256': h})
manifest = {'revision': 'reduce-1', 'model': f'MM7 Hydra — batch I vs reduced ({tris:,})', 'default_clip': 'Standing',
            'feedback': 'feedback/user_feedback.json', 'default_model': f'a_{tag}', 'models': models, 'clips': src['clips']}
(V / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
print('MANIFEST', len(models), 'models', list(src['clips']))
