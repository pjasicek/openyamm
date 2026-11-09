#!/usr/bin/env python3
"""Review viewer for the sprint pass (revision sprint-1): tiers A/B/C of export/mm6_rat_sprint.glb (region ramps baked
by viewer_variants.py), every clip, Run2 and Sprint first. The page and script are the MM6 PeasantF reduction viewer's
(mm6_fmp_reduce_claude). The previous manifest is kept as review/viewer/manifest_gait-1.json.
Usage: viewer_sprint.py"""
import hashlib, json, shutil, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
V = HERE / 'review/viewer'
SRC = HERE.parent / 'mm6_fmp_reduce_claude/review/viewer'
sys.path.insert(0, str(HERE.parent / 'claude_shared/floor'))
import glb_pose  # noqa: E402

TAG = 'sprint'
GLB = HERE / 'export/mm6_rat_sprint.glb'
V.mkdir(parents=True, exist_ok=True)
(HERE / 'review/feedback').mkdir(parents=True, exist_ok=True)
if not (HERE / 'review/feedback/user_feedback.json').exists():
    (HERE / 'review/feedback/user_feedback.json').write_text('{"findings": []}\n')
old = V / 'manifest.json'
if old.exists() and json.loads(old.read_text()).get('revision') == 'gait-1':
    shutil.copy(old, V / 'manifest_gait-1.json')
shutil.copy(SRC / 'index.html', V / 'index.html')
(V / 'index.html').write_text((V / 'index.html').read_text().replace('MM6 PeasantF', 'MM6 Rat'))
(V / 'review.js').write_text((SRC / 'review.js').read_text().replace('MM6 PeasantF', 'MM6 Rat')
                             .replace('mm6:fmp', 'mm6:rat').replace('mm6_fmp_reduce_frame_feedback',
                                                                    'mm6_rat_sprint_frame_feedback'))
subprocess.run([sys.executable, str(HERE / 'scripts/viewer_variants.py'), str(GLB), TAG], check=True)
model = glb_pose.Model(glb_pose.Glb(GLB))
order = ['Run2', 'Sprint', 'Walk2', 'Standing', 'Walking', 'Running', 'Fidget', 'Attack', 'Hit', 'Death', 'Dead']
NEW = {'Walk2': 'procedural trot at the game speed (gait2_rat.py, 2026-10-21)',
       'Run2': 'procedural half-bound at the game speed (gait2_rat.py, 2026-10-21)',
       'Sprint': 'procedural bounding gallop for the MAW chase (sprint_rat.py, 2026-10-31)'}
clips = {}
for name in order:
    clips[name] = {'label': name + (' (new)' if name == 'Sprint' else ''),
                   'duration': round(float(model.clip_times(name)[-1]), 6),
                   'mode': 'loop' if name in ('Standing', 'Walking', 'Running', 'Fidget', 'Walk2', 'Run2', 'Sprint')
                   else 'once', 'provenance': NEW.get(name, 'installed clip (unchanged)'), 'anchors': []}
models = []
for variant in ('rat_a', 'rat_b', 'rat_c'):
    g = V / f'mm6_{variant}_{TAG}.glb'; h = hashlib.sha256(g.read_bytes()).hexdigest()
    models.append({'id': f'{variant}_{TAG}', 'label': f'{variant} · installed clips + Sprint', 'url': f'{g.name}?v={h[:12]}',
                   'revision': 'sprint-1', 'sha256': h})
manifest = {'revision': 'sprint-1', 'model': 'MM6 Rat — sprint pass (Sprint next to Run2)', 'default_clip': 'Sprint',
            'default_model': models[0]['id'], 'feedback': '../feedback/user_feedback.json', 'clips': clips,
            'models': models}
(V / 'manifest.json').write_text(json.dumps(manifest, indent=1))
print('MANIFEST', V / 'manifest.json', list(clips))
