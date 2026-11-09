#!/usr/bin/env python3
"""Review viewers for tools/run_creature_review.py (the wrapper wants one direct child of creatures/ per viewer, and the
clip lengths differ per model): ../mm6_<m>_sprint_claude/review/viewer with the export, its sword baked in flat grey
(review_glb.py), clips Standing, Walking, Running (installed) and Jog, Sprint (new). Page and script are the pirate gait
viewer's (mm8_m412_gait_claude). Usage: build_viewers.py"""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE / 'scripts'))
from gaitlib import glb_pose  # noqa: E402

SRC = HERE.parent / 'mm8_m412_gait_claude/review/viewer'
TITLES = {'ogr': 'MM6 Ogre', 'kni': 'MM6 KnightPlate'}
NEW = ('Jog', 'Sprint')
for m, title in TITLES.items():
    v = HERE.parent / f'mm6_{m}_sprint_claude/review/viewer'
    v.mkdir(parents=True, exist_ok=True)
    shutil.copy(SRC / 'index.html', v / 'index.html')
    js = (SRC / 'review.js').read_text().replace('MM8 Pirate Warrior', title).replace('mm8:m412', f'mm6:{m}') \
        .replace('mm8-m412-reduce-claude', f'mm6-{m}-sprint-claude').replace('mm8_m412_gait', f'mm6_{m}_sprint')
    (v / 'review.js').write_text(js)
    glb = v / f'mm6_{m}_sprint.glb'
    subprocess.run([sys.executable, str(HERE / 'scripts/review_glb.py'), str(HERE / f'export/mm6_{m}.glb'), str(glb),
                    f'Sword={ROOT}/assets_source/worlds/mm6/models/mm6_{m}_sword.glb:0.62,0.62,0.68'], check=True)
    model = glb_pose.Model(glb_pose.Glb(glb))
    clips = {}
    for name in ('Standing', 'Walking', 'Running') + NEW:
        clips[name] = {'label': name + (' (new)' if name in NEW else ''),
                       'duration': round(model.clip_times(name)[-1], 6), 'mode': 'loop',
                       'provenance': 'new clip' if name in NEW else 'installed clip (unchanged)', 'anchors': []}
    h = hashlib.sha256(glb.read_bytes()).hexdigest()
    manifest = {'revision': 'sprint-1', 'model': f'{title} — installed Walking/Running vs new Jog/Sprint',
                'default_clip': 'Sprint', 'default_model': f'{m}_sprint', 'feedback': '../feedback/user_feedback.json',
                'clips': clips, 'models': [{'id': f'{m}_sprint', 'label': f'{title} · tier A texture, sword flat',
                                           'url': f'{glb.name}?v={h[:12]}', 'revision': 'sprint-1', 'sha256': h}]}
    (v / 'manifest.json').write_text(json.dumps(manifest, indent=1))
    feedback = v.parent / 'feedback/user_feedback.json'
    feedback.parent.mkdir(exist_ok=True)
    if not feedback.exists():
        feedback.write_text('{"findings": []}')
    print('VIEWER', v.relative_to(ROOT))
