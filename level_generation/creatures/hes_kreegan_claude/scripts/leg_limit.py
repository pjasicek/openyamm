"""hkr Trooper caste (v4 shell): a soft limit on the hip flexion of the listed clips (Running): the source run drives
the knee to 88 deg of hip flexion, where the thigh's front rises above the belt and no tasset or thigh plate can clear
it. Per frame and thigh: flexion t relative to the pelvis (as helper_bones.py measures it); above MAX it continues at
SOFT of the source's rate (t' = MAX + (t - MAX) * SOFT); the thigh turns back by t - t' about the pelvis X axis at the
hip joint, the knee and foot follow (their local rotations unchanged), the reduction smoothed over the loop (Gaussian,
cyclic, never below the per-frame need). Run before helper_bones.py; foot_floor.py later keeps the soles on the floor.
Args: -- <in blend> <out blend> <Action> [...]   (env MAX deg, default 60; SOFT 0.3)"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Quaternion, Matrix, Vector
a = sys.argv[sys.argv.index('--') + 1:]
src, out, acts = a[0], a[1], a[2:]
MAX, SOFT = float(os.environ.get('MAX', '60')), float(os.environ.get('SOFT', '0.3'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene; AW = rig.matrix_world
REST = lambda n: rig.data.bones[n].matrix_local.to_3x3()


def flex(s):
    pel = rig.pose.bones['B_Pelvis']; Pm = pel.matrix.to_3x3(); Pr = REST('B_Pelvis'); th = rig.pose.bones[f'B_{s}_Thigh']
    d0 = Pr.inverted() @ REST(th.name).col[1]; d1 = Pm.inverted() @ th.matrix.to_3x3().col[1]
    w0, w1 = Pr @ d0, Pr @ d1
    return math.degrees(math.atan2(-w1.y, -w1.z) - math.atan2(-w0.y, -w0.z))


rep = {}
for name in acts:
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range); fr = list(range(f0, f1 + 1))
    rep[name] = {}
    for s in 'LR':
        th = np.array([(sc.frame_set(f), flex(s))[1] for f in fr])
        red = np.where(th > MAX, (th - MAX) * (1 - SOFT), 0.0)
        g = np.exp(-0.5 * (np.arange(-4, 5) / 1.5) ** 2); g /= g.sum()
        red = np.maximum(np.convolve(np.pad(red, 4, mode='wrap'), g, mode='valid'), red)
        keys = {}
        for f, d in zip(fr, red):
            if d < 0.05: continue
            sc.frame_set(f)
            pb = rig.pose.bones[f'B_{s}_Thigh']; pel = rig.pose.bones['B_Pelvis']
            axis = pel.matrix.to_3x3() @ (REST('B_Pelvis').inverted() @ Vector((1, 0, 0)))   # the pelvis's X, posed
            M = pb.matrix.copy(); J = M.translation.copy()
            R = Quaternion(axis.normalized(), math.radians(d)).to_matrix().to_4x4()   # back: +X undoes forward flexion
            N = Matrix.Translation(J) @ R @ Matrix.Translation(-J) @ M
            pb.rotation_mode = 'QUATERNION'; pb.matrix = N; bpy.context.view_layer.update()
            keys[f] = pb.rotation_quaternion.copy()
        prev = None
        for f in fr:
            if f not in keys: continue
            q = keys[f]
            if prev is not None and q.dot(prev) < 0: q = -q
            prev = q; pb = rig.pose.bones[f'B_{s}_Thigh']; pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=f)
        after = [(sc.frame_set(f), flex(s))[1] for f in fr]
        rep[name][s] = {'max_before': round(float(th.max()), 1), 'max_after': round(float(max(after)), 1),
                        'frames': len(keys)}
    print('LEGLIMIT', name, json.dumps(rep[name]))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
