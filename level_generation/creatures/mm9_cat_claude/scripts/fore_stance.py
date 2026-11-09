"""Foreleg stance correction on the delivered clips (Blender module used by build_export.py).

MM9's clips key the foreleg joints at MM9's own stance: in `stand1` the shoulders sit about 2.4 cm and the ankles 1.5 cm off
the midline. MM9's chest is that narrow; ours is not, and our rest legs are straight at 3 cm, so the keyed stance bends each
leg inward under the chest and the wrists meet (gap 0.8 mm in Standing, 40 mm at rest).

This moves the shoulder and ankle sideways in the chest frame (Xfrontleg) by one constant per side, measured once on
Standing's first frame, so Standing lands on the target stance and every other clip keeps MM9's motion on top of the same
offset, with the shoulder aimed down the leg's rest segment. It is the same offset on every frame, not a per-frame solve, so it adds no motion of its own: paws keep their height
and their fore-aft path, ankle and paw keep their world orientation, and loop ends stay equal. A paw raised to the mouth or
in the swipe fades back to MM9's line with its height (LIFT), a smooth function of the smooth curves, and only in RAISED clips:
in the walk and run a fade would make the paws swing in and out with every step."""
import bpy
from mathutils import Matrix, Quaternion, Vector

LEGS = ((-1.0, 'Xflegpiv', 'Xfankle', 'Xffoot'), (1.0, 'Xflegpiv01', 'Xfankle01', 'Xffoot01'))
SHOULDER_X = 0.030
ANKLE_X = 0.027
LIFT = (0.03, 0.08)
RAISED = {'Fidget', 'AttackMelee'}
WIDE = {'Walking', 'Running'}        # MM9's gaits already stand wide: no sideways shift, the shoulder aim only


def smooth(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def chest_x(rig, rest_q):
    pb = rig.pose.bones['Xfrontleg']
    q = pb.matrix.to_quaternion() @ rest_q.inverted()
    return pb.matrix.translation.copy(), q @ Vector((1, 0, 0))


def solve(rig, actions):
    vl = bpy.context.view_layer
    sc = bpy.context.scene
    rest_q = rig.data.bones['Xfrontleg'].matrix_local.to_quaternion()
    rig.animation_data.action = bpy.data.actions['Standing']
    sc.frame_set(int(bpy.data.actions['Standing'].frame_range[0]))
    vl.update()
    origin, lateral = chest_x(rig, rest_q)
    ref = {}
    for side, sh, an, ft in LEGS:
        xs = (rig.pose.bones[sh].matrix.translation - origin).dot(lateral)
        xa = (rig.pose.bones[an].matrix.translation - origin).dot(lateral)
        ref[side] = (side * SHOULDER_X - xs, side * ANKLE_X - xa, rig.pose.bones[an].matrix.translation.z)
    rest_s = {sh: rig.data.bones[sh].matrix_local.to_quaternion() for _, sh, _, _ in LEGS}
    rest_seg = {sh: rig.data.bones[an].matrix_local.translation - rig.data.bones[sh].matrix_local.translation
                for _, sh, an, _ in LEGS}
    report = {'offsets': {str(k): [round(v[0], 4), round(v[1], 4)] for k, v in ref.items()}}
    for act in actions:
        rig.animation_data.action = act
        f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
        pending = []
        for f in range(f0, f1 + 1):
            sc.frame_set(f)
            vl.update()
            _, lateral = chest_x(rig, rest_q)
            keys = {}
            for side, sh, an, ft in LEGS:
                ds, da, z_rest = ref[side]
                if act.name in WIDE:
                    ds, da = 0.0, 0.0
                S, A, F = (rig.pose.bones[n] for n in (sh, an, ft))
                ms, ma, mf = S.matrix.copy(), A.matrix.copy(), F.matrix.copy()
                if act.name in RAISED:
                    da = da * (1 - smooth(LIFT[0], LIFT[1], ma.translation.z - z_rest))
                new_s = ms.translation + lateral * ds
                new_a = ma.translation + lateral * da
                # MM9's shoulder turn does not point our rest leg at the keyed ankle, and the mesh under that bone would
                # head inward before the ankle pulled it back: the rest segment is aimed at the corrected ankle
                seg = ms.to_quaternion() @ rest_s[sh].inverted() @ rest_seg[sh]
                turn = seg.rotation_difference(new_a - new_s)
                S.matrix = Matrix.Translation(new_s) @ (turn @ ms.to_quaternion()).to_matrix().to_4x4()
                vl.update()
                A.matrix = Matrix.Translation(new_a) @ ma.to_quaternion().to_matrix().to_4x4()
                vl.update()
                F.matrix = Matrix.Translation(mf.translation + lateral * da) @ mf.to_quaternion().to_matrix().to_4x4()
                vl.update()
                for pb in (S, A, F):
                    keys[pb.name] = (pb.rotation_quaternion.copy(), pb.location.copy())
            pending.append((f, keys))
        for f, keys in pending:
            for b, (q, l) in keys.items():
                pb = rig.pose.bones[b]
                pb.rotation_quaternion, pb.location = q, l
                pb.keyframe_insert('rotation_quaternion', frame=f)
                pb.keyframe_insert('location', frame=f)
    return report
