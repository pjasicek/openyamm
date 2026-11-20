"""Loop seam for a cyclic clip whose arm was re-solved per frame (author_carry.py's global path is not cyclic): reports
the per-frame world-rotation steps of the listed bones near the ends and, with FIX=1, spreads the seam (last frame vs
first frame) over the last K frames of the local rotations (slerp toward frame f0's keys), so the cycle closes.
Args: -- <in blend> <out blend> <Action> <bone> [...]"""
import bpy, sys, os, math
a = sys.argv[sys.argv.index('--') + 1:]
src, out, an, bones = a[0], a[1], a[2], a[3:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
act = bpy.data.actions[an]; rig.animation_data_create(); rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
K = int(os.environ.get('K', '5'))


def world(b, f):
    sc.frame_set(f); return (rig.matrix_world @ rig.pose.bones[b].matrix).to_quaternion()


for b in bones:
    st = [round(math.degrees(world(b, f).rotation_difference(world(b, f + 1)).angle), 1) for f in range(f1 - 6, f1)]
    print('LOOPSEAM', an, b, 'steps over the last frames', st, 'end vs start', round(math.degrees(world(b, f1).rotation_difference(world(b, f0)).angle), 1))
if os.environ.get('FIX') == '1':
    keys = {}
    for b in bones:
        pb = rig.pose.bones[b]
        sc.frame_set(f0); q0 = pb.rotation_quaternion.copy()
        for f in range(f1 - K, f1 + 1):
            sc.frame_set(f); q = pb.rotation_quaternion.copy()
            if q.dot(q0) < 0:
                q0 = -q0
            t = (f - (f1 - K)) / K
            keys[(b, f)] = q.slerp(q0, t * t * (3 - 2 * t))
    for (b, f), q in keys.items():
        pb = rig.pose.bones[b]; pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=f)
    for b in bones:
        st = [round(math.degrees(world(b, f).rotation_difference(world(b, f + 1)).angle), 1) for f in range(f1 - 6, f1)]
        print('LOOPSEAM fixed', an, b, st)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
