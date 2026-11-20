#!/usr/bin/env python3
"""Per-pirate review viewers (../mm8_<model>_gait_claude/review/viewer: the review wrapper wants a creatures/ child) for tools/run_creature_review.py: the export with its
props baked in flat colours (review_glb.py output in work/), clips Standing, Walking, Walk2, Running, Jog.
The page and script are the m412 reduction viewer's. Usage: build_viewers.py"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
from gaitlib import glb_pose  # noqa: E402

SRC = HERE.parent / 'mm8_m412_reduce_claude/review/viewer'
TITLES = {'m412': 'MM8 Pirate Warrior', 'm416': 'MM8 Pirate Crossbowman', 'm420': 'MM8 Pirate Mage'}
for m, title in TITLES.items():
    v = HERE.parent / f'mm8_{m}_gait_claude/review/viewer'
    v.mkdir(parents=True, exist_ok=True)
    shutil.copy(SRC / 'index.html', v / 'index.html')
    js = (SRC / 'review.js').read_text().replace('MM8 Pirate Warrior', title).replace('mm8:m412', f'mm8:{m}') \
        .replace('mm8_m412_reduce_frame_feedback', f'mm8_{m}_gait_frame_feedback')
    (v / 'review.js').write_text(js)
    glb = v / f'mm8_{m}_gait.glb'
    shutil.copy(HERE / f'work/{m}_final_review.glb', glb)
    model = glb_pose.Model(glb_pose.Glb(glb))
    clips = {}
    for name in ('Standing', 'Walking', 'Walk2', 'Running', 'Jog'):
        clips[name] = {'label': name + (' (new)' if name in ('Walk2', 'Jog') else ''),
                       'duration': round(model.clip_times(name)[-1], 6), 'mode': 'loop',
                       'provenance': 'new clip' if name in ('Walk2', 'Jog') else 'installed clip (unchanged)',
                       'anchors': []}
    h = hashlib.sha256(glb.read_bytes()).hexdigest()
    manifest = {'revision': 'gait-1', 'model': f'{title} — installed Walking/Running vs new Walk2/Jog',
                'default_clip': 'Jog', 'default_model': f'{m}_gait', 'feedback': '../feedback/user_feedback.json',
                'clips': clips, 'models': [{'id': f'{m}_gait', 'label': f'{title} · tier A texture, props flat',
                                           'url': f'{glb.name}?v={h[:12]}', 'revision': 'gait-1', 'sha256': h}]}
    (v / 'manifest.json').write_text(json.dumps(manifest, indent=1))
    print('VIEWER', v.relative_to(HERE.parents[2]))
