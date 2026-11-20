#!/usr/bin/env python3
"""Package h05 copy of h02's build_viewers.py (models changed). Review viewers for tools/run_creature_review.py (the wrapper wants one direct child of creatures/ per viewer):
../../mm6_<m>_gait_h05_claude/review/viewer with this package's export, its prop baked in flat grey (review_glb.py),
the installed locomotion clips and the new ones. Page and script are the sprint pilot's viewer
(../../mm6_ogr_sprint_claude). Usage: build_viewers.py <m> [<m> ...]   (m: natm, mer1, mfp, natf, nobl)"""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
CREATURES = HERE.parents[1]
ROOT = CREATURES.parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
from gaitlib import glb_pose  # noqa: E402

SRC = CREATURES / 'mm6_ogr_sprint_claude/review/viewer'
MODELS = {          # title, props (node, file), installed clips, new clips
    'natm': ('MM6 PeasantM4', (('Spear', 'mm6_natm_spear.glb'), ('Buckler', 'mm6_natm_buckler.glb')),
             ('Walking', 'Running'), ('Walk2', 'Jog', 'Sprint')),
    'mer1': ('MM6 Merchant', (('Club', 'mm6_mer1_club.glb'),), ('Walking', 'Running'), ('Jog',)),
    'mfp': ('MM6 PeasantF3', (('Knife', 'mm6_mfp_knife.glb'),), ('Walking', 'Running'), ('Walk2', 'Jog', 'Sprint')),
    'natf': ('MM6 PeasantF4', (('ForearmBlade', 'mm6_natf_blade.glb'), ('LeafShield', 'mm6_natf_shield.glb')),
             ('Walking', 'Running'), ('Walk2', 'Jog', 'Sprint')),
    'nobl': ('MM6 Nobleman', (('Sword', 'mm6_nobl_sword.glb'),), ('Walking', 'Running'), ('Walk2', 'Jog', 'Sprint')),
}
for m in sys.argv[1:]:
    title, props_of, old, new = MODELS[m]
    v = CREATURES / f'mm6_{m}_gait_h05_claude/review/viewer'
    v.mkdir(parents=True, exist_ok=True)
    shutil.copy(SRC / 'index.html', v / 'index.html')
    js = (SRC / 'review.js').read_text().replace('MM6 Ogre', title).replace('mm6:ogr', f'mm6:{m}') \
        .replace('mm6-ogr-sprint-claude', f'mm6-{m}-gait-h05-claude').replace('mm6_ogr_sprint', f'mm6_{m}_gait')
    (v / 'review.js').write_text(js)
    glb = v / f'mm6_{m}_gait.glb'
    props = [f'{node}={ROOT}/assets_source/worlds/mm6/models/{f}:0.62,0.62,0.68' for node, f in props_of]
    subprocess.run([sys.executable, str(HERE / 'scripts/review_glb.py'), str(HERE / f'export/mm6_{m}.glb'), str(glb)]
                   + props, check=True)
    model = glb_pose.Model(glb_pose.Glb(glb))
    clips = {}
    for name in ('Standing',) + old + new:
        clips[name] = {'label': name + (' (new)' if name in new else ''),
                       'duration': round(model.clip_times(name)[-1], 6), 'mode': 'loop',
                       'provenance': 'new clip' if name in new else 'installed clip (unchanged)', 'anchors': []}
    h = hashlib.sha256(glb.read_bytes()).hexdigest()
    manifest = {'revision': 'gait-h05-1', 'model': f'{title} — installed {"/".join(old)} vs new {"/".join(new)}',
                'default_clip': new[-1], 'default_model': f'{m}_gait', 'feedback': '../feedback/user_feedback.json',
                'clips': clips, 'models': [{'id': f'{m}_gait', 'label': f'{title} · tier A texture'
                                           + (', props flat grey' if props_of else ''),
                                           'url': f'{glb.name}?v={h[:12]}', 'revision': 'gait-h05-1', 'sha256': h}]}
    (v / 'manifest.json').write_text(json.dumps(manifest, indent=1))
    feedback = v.parent / 'feedback/user_feedback.json'
    feedback.parent.mkdir(exist_ok=True)
    if not feedback.exists():
        feedback.write_text('{"findings": []}')
    print('VIEWER', v.relative_to(ROOT))
