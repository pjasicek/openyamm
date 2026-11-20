"""Dropped MM9 clips (run2-clips-groupC, 2026-10-31): build the MM9 clips the accepted export leaves out with this
project's clips_mm9.py (via claude_shared/mm9_extra_clips_blend.py) from the source blend build_export.py opens
(work/uv_v5.blend), and export the armature with them. Ctl_* are controls rebuilt from accepted clips' sources (compared with the
installed clips, never grafted); holds are temporary corpses for the floor pass. Written by
claude_shared/make_extra_clips.py from scripts/extra_clips.json; run by scripts/extra_clips.sh.
Fidget2 is MM9's Fidget1 (the accepted Fidget plays MM9 Fidget2). Floor as build_runtime.sh: ground-loop for idles,
lying down, rolling, resting and standing up; raise for the hit; Death2 grounded on a temporary Dead2; low-passed like Fidget (0.12 s) and Hit (0.06 s)."""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'claude_shared'))
import mm9_extra_clips_blend as X

ROLES = {
    'Fidget2': (['Fidget1'], False),
    'LieDown': (['Standdown'], False),
    'Roll': (['Roll'], False),
    'Rest': (['Rest'], True),
    'StandUp': (['Standup'], False),
    'Hit2': (['Wince2'], False),
    'Death2': (['Die2'], False),
    'Ctl_Fidget': (['Fidget2'], False),
    'Ctl_Hit': (['Wince1'], False),
    'Ctl_Death': (['Die1'], False),
}
def post(rig, report, C):
    # build_export.py: the ear helper bones (refine_pig.py) turn exactly as MM9's Xearpiv, every frame
    import bpy
    sc = bpy.context.scene
    HELPERS = {'EarRoot': 'Xearpiv', 'EarRoot01': 'Xearpiv01'}
    for act in [a for a in bpy.data.actions if a.name in report['clips']]:
        rig.animation_data.action = act
        try:
            rig.animation_data.action_slot = act.slots[0]
        except Exception:
            pass
        f0, f1 = (int(round(x)) for x in act.frame_range)
        for f in range(f0, f1 + 1):
            sc.frame_set(f)
            for h, s_ in HELPERS.items():
                if h not in rig.pose.bones:
                    continue
                ph = rig.pose.bones[h]
                ph.rotation_mode = 'QUATERNION'
                ph.rotation_quaternion = rig.pose.bones[s_].rotation_quaternion.copy()
                ph.keyframe_insert('rotation_quaternion', frame=f)
                ph.keyframe_insert('location', frame=f)
                ph.keyframe_insert('scale', frame=f)
        for fc in C.fcurves(act):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'
X.main(HERE, ROLES, rig_name='MM9_Rig', holds={'Dead2': 'Death2', 'Ctl_Dead': 'Ctl_Death'}, post=post)
