"""Dropped MM9 clips (run2-clips-groupC, 2026-10-31): build the MM9 clips the accepted export leaves out with this
project's clips_mm9.py (via claude_shared/mm9_extra_clips_blend.py) from the source blend build_export.py opens
(work/shards_v2.blend), and export the armature with them. Ctl_* are controls rebuilt from accepted clips' sources (compared with the
installed clips, never grafted); holds are temporary corpses for the floor pass. Written by
claude_shared/make_extra_clips.py from scripts/extra_clips.json; run by scripts/extra_clips.sh.
Floor as build_runtime.sh: raise for the fidget, hit and jump, Death2 grounded on a temporary Dead2.
Death2 is MM9 diewater1 with build_export.py's Death treatment (convulsion to 0.45 s, then limp into the swim
sprawl rolled 30 deg): diewater1 too is a sinking death that ends hanging head-up, standing on its tail on a floor.
diewater2 is the accepted Death's source (the same treatment): not added again."""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'claude_shared'))
import mm9_extra_clips_blend as X

ROLES = {
    'Fidget2': (['fidgetwater2'], False),
    'Hit2': (['wincewater2'], False),
    'Death2': (['diewater1'], False),
    'Jump': (['Jump'], False),
    'Ctl_Fidget': (['fidgetwater1'], False),
    'Ctl_Hit': (['wincewater1'], False),
    'Ctl_Walking': (['swim'], True),
}
def post(rig, report, C):
    # build_export.py's Death treatment on Death2: diewater1 is also a sinking death (it rises and ends hanging head-up,
    # standing on its tail on a floor), so it keeps MM9's convulsion up to CUT_S, then goes limp into the swim sprawl
    # rolled ROLL_DEG onto its side; Dead2 (temporary, for the floor pass) is then its last frame.
    import bpy, math
    from mathutils import Matrix
    CUT_S, LIMP_S, ROLL_DEG = 0.45, 0.9, 30
    sc = bpy.context.scene
    fps_import = sc.render.fps / sc.render.fps_base
    swim = bpy.data.actions['swim']
    rig.animation_data.action = swim
    try:
        rig.animation_data.action_slot = swim.slots[0]
    except Exception:
        pass
    sc.frame_set(0)
    limp = {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy(), pb.scale.copy()) for pb in rig.pose.bones}
    act = next(a for a in bpy.data.actions if a.name.rsplit('.', 1)[0] == 'Death2' and a.name != 'diewater2')
    rig.animation_data.action = act
    try:
        rig.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    cut = int(round(CUT_S * C.FPS))
    for fc in C.fcurves(act):
        for kp in [k for k in fc.keyframe_points if k.co.x > cut + 1e-3][::-1]:
            fc.keyframe_points.remove(kp)
    sc.frame_set(cut)
    start = {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy(), pb.scale.copy()) for pb in rig.pose.bones}
    n = int(round(LIMP_S * C.FPS))
    for k in range(1, n + 1):
        x = k / n
        a_ = x * x * (3 - 2 * x)
        th = math.radians(ROLL_DEG) * x * x
        for pb in rig.pose.bones:
            q0, l0, s0 = start[pb.name]
            q1, l1, s1 = limp[pb.name]
            if q0.dot(q1) < 0:
                q1 = -q1
            pb.rotation_mode = 'QUATERNION'
            pb.rotation_quaternion = q0.slerp(q1, a_)
            pb.location = l0.lerp(l1, a_)
            pb.scale = s0.lerp(s1, a_)
        bpy.context.view_layer.update()
        pb = rig.pose.bones['Bone01']
        h = (rig.matrix_world @ pb.matrix).translation
        R = Matrix.Translation(h) @ Matrix.Rotation(th, 4, 'Y') @ Matrix.Translation(-h)
        pb.matrix = rig.matrix_world.inverted() @ R @ rig.matrix_world @ pb.matrix
        bpy.context.view_layer.update()
        for pb in rig.pose.bones:
            pb.keyframe_insert('rotation_quaternion', frame=cut + k)
            pb.keyframe_insert('location', frame=cut + k)
            pb.keyframe_insert('scale', frame=cut + k)
    for fc in C.fcurves(act):
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
    report['clips']['Death2'].update({'sources': ['diewater1 (0 - %.2f s)' % CUT_S, 'limp into swim@0, roll %d deg' % ROLL_DEG],
                                      'duration': (cut + n) / C.FPS, 'frames': cut + n})
    old = next(a for a in bpy.data.actions if a.name.rsplit('.', 1)[0] == 'Dead2')
    bpy.data.actions.remove(old)
    X.hold_evaluated(rig, 'Dead2', act.name, C)
X.main(HERE, ROLES, rig_name='MM9_Rig', holds={'Dead2': 'Death2'}, post=post, hold_mode='eval')
