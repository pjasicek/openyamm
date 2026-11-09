#!/usr/bin/env python3
"""Review viewer for tools/run_creature_review.py (it wants a direct child of creatures/ per viewer):
../../mm7_<m>_gait_h08_claude/review/viewer with this package's export (attachments baked flat by review_glb.py) and the
locomotion clips, old and new. Page and script are the pirate gait viewer's (mm8_m412_gait_claude).

    build_viewer.py <m> "<title>" <clip,clip,...> <new,new,...> [node=attachment.glb ...]
"""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
CREATURES = HERE.parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
from gaitlib import glb_pose  # noqa: E402

SRC = CREATURES / 'mm8_m412_gait_claude/review/viewer'
m, title, clip_list, new_list = sys.argv[1:5]
attachments = sys.argv[5:]
NEW = tuple(new_list.split(','))
name = f'mm7_{m}_gait_h08'
v = CREATURES / f'{name}_claude/review/viewer'
v.mkdir(parents=True, exist_ok=True)
shutil.copy(SRC / 'index.html', v / 'index.html')
js = (SRC / 'review.js').read_text().replace('MM8 Pirate Warrior', title).replace('mm8:m412', f'mm7:{m}') \
    .replace('mm8-m412-reduce-claude', f'mm7-{m}-gait-h08-claude').replace('mm8_m412_gait', name)
(v / 'review.js').write_text(js)
glb = v / f'{name}.glb'
src = HERE / f'export/mm7_{m}.glb'
if attachments:
    subprocess.run([sys.executable, str(HERE / 'scripts/review_glb.py'), str(src), str(glb)] + attachments, check=True)
else:
    shutil.copy(src, glb)
model = glb_pose.Model(glb_pose.Glb(glb))
clips = {}
for clip in clip_list.split(','):
    clips[clip] = {'label': clip + (' (new)' if clip in NEW else ''), 'duration': round(model.clip_times(clip)[-1], 6),
                   'mode': 'loop', 'provenance': 'new clip' if clip in NEW else 'installed clip (unchanged)',
                   'anchors': []}
h = hashlib.sha256(glb.read_bytes()).hexdigest()
manifest = {'revision': 'gait-h08-1', 'model': f'{title}: installed locomotion vs new clips',
            'default_clip': NEW[-1], 'default_model': name, 'feedback': '../feedback/user_feedback.json',
            'clips': clips, 'models': [{'id': name, 'label': f'{title} · tier A texture',
                                       'url': f'{glb.name}?v={h[:12]}', 'revision': 'gait-h08-1', 'sha256': h}]}
(v / 'manifest.json').write_text(json.dumps(manifest, indent=1))
feedback = v.parent / 'feedback/user_feedback.json'
feedback.parent.mkdir(exist_ok=True)
if not feedback.exists():
    feedback.write_text('{"findings": []}')
print('VIEWER', v)
