#!/usr/bin/env python3
"""review/viewer/manifest.json: installed (r100) and reduced (r72) GLB per tier, with the m436 project's clips and
native anchors (image paths rebased to this viewer)."""
import hashlib, json
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; V = HERE / 'review/viewer'
src = json.loads((HERE.parent / 'mm8_m436_claude/review/viewer/manifest.json').read_text())
clips = json.loads(json.dumps(src['clips']).replace('"../../references_native/', '"../../../mm8_m436_claude/references_native/'))
TIERS = {'a': 'A, green', 'b': 'B, blue', 'c': 'C, red'}
models = []
for t, name in TIERS.items():
    for tag, label in (('r100', 'installed · 14,488 tris'), ('r72', 'reduced · 10,527 tris')):
        f = V / f'mm8_m436_{t}_{tag}.glb'; h = hashlib.sha256(f.read_bytes()).hexdigest()
        models.append({'id': f'm436_{t}_{tag}', 'label': f'Ogre Peasant {name} · {label}', 'url': f'{f.name}?v={h[:12]}',
                       'sha256': h, 'revision': 'reduce-1'})
first = models[1]
(V / 'manifest.json').write_text(json.dumps({'revision': 'reduce-1', 'model': first['url'], 'model_sha256': first['sha256'],
    'default_clip': 'Standing', 'default_model': first['id'], 'feedback': '../feedback/user_feedback.json',
    'models': models, 'clips': clips}, indent=1) + '\n')
print('MANIFEST', len(models), 'models', list(clips))
