#!/usr/bin/env python3
"""Review viewer of the reduced school (review/viewer/): per tier, the installed viewer file of the creature project
(mm8_m636_claude/review/viewer/m636_<tier>.glb, tier colours baked for Three.js; its geometry equals the installed
model's) and the same file with the reduced LOD0-3 fish swapped in (fish_build.py on the same templates as the export).
The viewer page, clips and native anchors are the creature project's. Usage: viewer_build.py <lod0..3 npz>"""
import hashlib
import json
import shutil
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(Path(__file__).resolve().parent))
from fish_build import template, school, write_school  # noqa: E402
SRC = HERE.parent / 'mm8_m636_claude' / 'review' / 'viewer'; OUT = HERE / 'review' / 'viewer'
OUT.mkdir(parents=True, exist_ok=True); (OUT / 'feedback').mkdir(exist_ok=True)
for f in ('index.html', 'review.js'):
    shutil.copy(SRC / f, OUT / f)
fb = OUT / 'feedback' / 'user_feedback.json'
if not fb.exists():
    fb.write_text('{"findings": []}\n')
fish = np.load(HERE / 'work' / 'fish.npz'); ref0 = {k: fish[k] for k in ('P', 'N', 'UV', 'J', 'W', 'I')}
t0 = template(np.load(sys.argv[1]), ref0); temps = [t0] + [template(np.load(n), t0) for n in sys.argv[2:5]]
lods = [school(t, fish) for t in temps]
man = json.loads((SRC / 'manifest.json').read_text()); models = []
tris = [len(s['I']) for s in lods]; tag = f'r{round(100 * tris[0] / 7800)}'
for m in man['models']:
    tier = m['id'][-1]; inst = OUT / f'mm8_m636_{tier}_r100.glb'; red = OUT / f'mm8_m636_{tier}_{tag}.glb'
    shutil.copy(SRC / f'm636_{tier}.glb', inst); write_school(SRC / f'm636_{tier}.glb', red, lods)
    for path, rid, lab, rev in ((inst, f'm636_{tier}_r100', 'installed · 7,800 (12 x 650)', 'reduce-0'),
                                (red, f'm636_{tier}_{tag}', f'reduced · {tris[0]:,} (12 x {tris[0] // 12})', 'reduce-1')):
        h = hashlib.sha256(path.read_bytes()).hexdigest()
        models.append({'id': rid, 'label': f"{m['label']} — {lab}", 'url': f'{path.name}?v={h[:12]}', 'sha256': h, 'revision': rev})
manifest = {'revision': 'reduce-1', 'default_model': f'm636_a_{tag}', 'default_clip': man.get('default_clip', 'Swim'),
            'models': models, 'clips': man['clips'], 'feedback': 'feedback/user_feedback.json'}
(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
print('VIEWER', [m['id'] for m in models])
