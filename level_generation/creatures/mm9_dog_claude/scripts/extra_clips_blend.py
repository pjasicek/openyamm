"""Dropped MM9 clips (run2-clips-groupC, 2026-10-31): build the MM9 clips the accepted export leaves out with this
project's clips_mm9.py (via claude_shared/mm9_extra_clips_blend.py) from the source blend build_export.py opens
(work/uv_v2.blend), and export the armature with them. Ctl_* are controls rebuilt from accepted clips' sources (compared with the
installed clips, never grafted); holds are temporary corpses for the floor pass. Written by
claude_shared/make_extra_clips.py from scripts/extra_clips.json; run by scripts/extra_clips.sh.
The dog's build_export.py steps run on the new clips too (rest offsets, neck_spread). Floor as build_runtime.sh:
the gaits ground-looped (sniffing and barking walks low-passed 0.02 s as Walking), the run away raised and low-passed
0.03 s as Running, the sitting loop ground-looped."""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'claude_shared'))
import mm9_extra_clips_blend as X

ROLES = {
    'WalkSniff': (['walksniff'], True),
    'WalkBark': (['walkbark'], True),
    'RunAway': (['run(away)'], True),
    'Sit': (['sitting'], True),
    'Ctl_Fidget': (['fidget1'], False),
    'Ctl_Walking': (['walk'], True),
    'Ctl_Running': (['run'], True),
}
def post(rig, report, C):
    # build_export.py: the neck bend is spread over three joints on every role action (neck_spread.py)
    import bpy
    import neck_spread
    acts = [a for a in bpy.data.actions if a.name.rsplit('.', 1)[0] in report['clips']
            and a.name not in {'walksniff', 'walkbark', 'run(away)', 'sitting', 'fidget1', 'walk', 'run'}]
    report['neck_spread'] = neck_spread.spread(rig, acts)
def prep(rig):
    # build_export.py: the rest offsets stored on the rig feed the clip build
    import json
    from mathutils import Matrix
    sys.path.insert(0, HERE)
    import clips_mm9 as C
    if rig.get('rest_offset_json'):
        C.REST_OFFSET.update({b: Matrix(m) for b, m in json.loads(rig['rest_offset_json']).items()})

X.main(HERE, ROLES, rig_name='MM9_Rig', holds={}, post=post, hold_mode='rec', prep=prep, post_first=True)
