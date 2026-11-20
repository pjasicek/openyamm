"""Dropped MM9 clips (run2-clips-groupC, 2026-10-31): build the MM9 clips the accepted export leaves out with this
project's clips_mm9.py (via claude_shared/mm9_extra_clips_blend.py) from the source blend build_export.py opens
(work/uv_v1.blend), and export the armature with them. Ctl_* are controls rebuilt from accepted clips' sources (compared with the
installed clips, never grafted); holds are temporary corpses for the floor pass. Written by
claude_shared/make_extra_clips.py from scripts/extra_clips.json; run by scripts/extra_clips.sh.
The cat's build_export.py steps run on the new clips too (rest offsets, hind_ik, fore_stance, knee helpers, the
3.12 cm rest shift). The MM9 cat's idle is a sit; down lies down (LieDown), up sits back up (GetUp), standdown is
the lying idle (Lie) and fidgetdown1/2 its fidgets. Floor as build_runtime.sh: ground-loop, low-passed 0.05 s with smooth-hold 0.5 as the accepted Fidget.
clips_mm9.py has no joint-offset cut (its 0.004 values are key data), so the soft line does not apply."""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'claude_shared'))
import mm9_extra_clips_blend as X

ROLES = {
    'Fidget2': (['fidget2'], False),
    'LieDown': (['down'], False),
    'GetUp': (['up'], False),
    'Lie': (['standdown'], True),
    'LieFidget': (['fidgetdown1'], False),
    'LieFidget2': (['fidgetdown2'], False),
    'Ctl_Fidget': (['fidget1'], False),
    'Standing': (['stand1'], True),
}
def post(rig, report, C):
    # build_export.py's steps on every role action: hind legs solved onto MM9's paw motion, the fore stance offset,
    # then the hip/knee/hock half-rotation helpers (bones added and keyed)
    import bpy
    import hind_ik, fore_stance, knee_helpers
    acts = [a for a in bpy.data.actions if a.name.rsplit('.', 1)[0] in report['clips'] and a.name not in
            {'fidget2', 'down', 'up', 'standdown', 'fidgetdown1', 'fidgetdown2', 'fidget1', 'stand1'}]
    hind_ik.LOOPS |= {'Lie'}   # the sitting idle loops: its leg low-pass wraps, as Standing's
    src_rig = hind_ik.load_src(os.path.join(HERE, '..', 'work', 'mm9_cat_rig.blend'))
    report['hind_ik_short'] = hind_ik.solve(rig, src_rig, C.REST_OFFSET, acts, C.FPS)
    # a paw raised in an idle fades back to MM9's line, as in the accepted Fidget (fore_stance.RAISED)
    fore_stance.RAISED |= {'Ctl_Fidget', 'Fidget2', 'LieDown', 'GetUp', 'Lie', 'LieFidget', 'LieFidget2'}
    report['fore_stance'] = fore_stance.solve(rig, acts)
    bpy.data.objects.remove(src_rig)
    body = bpy.data.objects['Body']
    report['knee_helpers'] = knee_helpers.add(rig, body)
    knee_helpers.key(rig, acts)
def prep(rig):
    # build_export.py: the rest offsets stored on the rig feed the clip build
    import json
    from mathutils import Matrix
    sys.path.insert(0, HERE)
    import clips_mm9 as C
    if rig.get('rest_offset_json'):
        C.REST_OFFSET.update({b: Matrix(m) for b, m in json.loads(rig['rest_offset_json']).items()})
def pre_export(rig):
    import bpy
    # build_export.py: MM9's clips stand 3.1 cm above its bind floor, one constant rest shift of the skeleton
    # the control Standing (fore_stance.py and hind_ik.py read it by that name) leaves as Ctl_Standing
    bpy.data.actions['Standing'].name = 'Ctl_Standing'
    SHIFT = float(os.environ.get('FLOOR_SHIFT', '0.0312'))
    for o in bpy.data.objects:
        o.select_set(o == rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    for eb in rig.data.edit_bones:
        eb.head.z -= SHIFT
        eb.tail.z -= SHIFT
    bpy.ops.object.mode_set(mode='OBJECT')
X.main(HERE, ROLES, rig_name='MM9_Rig', holds={}, post=post, hold_mode='rec', prep=prep, pre_export=pre_export, post_first=True)
