#!/usr/bin/env python3
"""Review viewer for tools/run_creature_review.py (it wants a direct child of creatures/ per viewer):
../../<m>_gait_h15_claude/review/viewer (m: mm7_7m452, mm8_m504, ...) with the export, its held prop baked in flat grey (review_glb.py), the
model's installed locomotion clips and the new ones. Page and script are the pirate gait viewer's
(mm8_m412_gait_claude).

    build_viewers.py <m> <export.glb> <title> <installed,clips> <new,clips> [node=prop.glb ...]
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
m, export, title, installed, new = sys.argv[1:6]
props = [f'{p}:0.62,0.62,0.68' for p in sys.argv[6:]]
installed, new = installed.split(','), new.split(',')
v = CREATURES / f'{m}_gait_h15_claude/review/viewer'
world, short = m.split('_', 1)
v.mkdir(parents=True, exist_ok=True)
shutil.copy(SRC / 'index.html', v / 'index.html')
js = (SRC / 'review.js').read_text().replace('MM8 Pirate Warrior', title).replace('mm8:m412', f'{world}:{short}') \
    .replace('mm8-m412-reduce-claude', f"{m.replace('_', '-')}-gait-h15-claude").replace('mm8_m412_gait', f'{m}_gait')
(v / 'review.js').write_text(js)
glb = v / f'{m}_gait.glb'
subprocess.run([sys.executable, str(HERE / 'scripts/review_glb.py'), export, str(glb), *props], check=True)
model = glb_pose.Model(glb_pose.Glb(glb))
clips = {}
for name in ['Standing'] + installed + new:
    clips[name] = {'label': name + (' (new)' if name in new else ''),
                   'duration': round(model.clip_times(name)[-1], 6), 'mode': 'loop',
                   'provenance': 'new clip' if name in new else 'installed clip (unchanged)', 'anchors': []}
h = hashlib.sha256(glb.read_bytes()).hexdigest()
manifest = {'revision': 'gait-h15-1', 'model': f'{title}: installed {"/".join(installed)} vs new {"/".join(new)}',
            'default_clip': new[-1], 'default_model': f'{m}_gait', 'feedback': '../feedback/user_feedback.json',
            'clips': clips, 'models': [{'id': f'{m}_gait', 'label': f'{title} · tier A texture, prop flat',
                                       'url': f'{glb.name}?v={h[:12]}', 'revision': 'gait-h15-1', 'sha256': h}]}
(v / 'manifest.json').write_text(json.dumps(manifest, indent=1))
feedback = v.parent / 'feedback/user_feedback.json'
feedback.parent.mkdir(exist_ok=True)
if not feedback.exists():
    feedback.write_text('{"findings": []}')
print('VIEWER', v)
