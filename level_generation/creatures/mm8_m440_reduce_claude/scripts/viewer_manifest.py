#!/usr/bin/env python3
"""review/viewer/manifest.json: installed (r100) and reduced (r67) GLB per tier (body only; the club is unchanged),
with the m440 project's clips and native anchors (their relative image paths resolve from this viewer as well)."""
import hashlib, json
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; V = HERE / 'review/viewer'
clips = json.loads((HERE.parent / 'mm8_m440_claude/review/viewer/manifest.json').read_text())['clips']
TIERS = {'a': 'Ogre Brawler, green', 'b': 'Ogre Warrior, blue', 'c': 'Ogre Warleader, red'}
models = []
for t, name in TIERS.items():
    for tag, label in (('r100', 'installed · 18,752 tris'), ('r67', 'reduced · 12,678 tris')):
        f = V / f'mm8_m440_{t}_{tag}.glb'; h = hashlib.sha256(f.read_bytes()).hexdigest()
        models.append({'id': f'm440_{t}_{tag}', 'label': f'{name} · {label}', 'url': f'{f.name}?v={h[:12]}',
                       'sha256': h, 'revision': 'reduce-1'})
first = models[1]
(V / 'manifest.json').write_text(json.dumps({'revision': 'reduce-1', 'model': first['url'], 'model_sha256': first['sha256'],
    'default_clip': 'Standing', 'default_model': first['id'], 'feedback': '../feedback/user_feedback.json',
    'models': models, 'clips': clips}, indent=1) + '\n')
print('MANIFEST', len(models), 'models', list(clips))
