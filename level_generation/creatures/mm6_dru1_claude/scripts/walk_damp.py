"""Calmer walk for the druidess (user reviews 1 and 2, 2026-10-11: "the hips sway WAY too much", then "the sway
left->right->left is still too big"). The Relax female walk is a catwalk: pelvis roll +-34.5 deg, 12.6 cm lateral sway,
and the spine bends against it (motion_probe.py). Per frame each trunk bone (pelvis, spine, spine1, spine2) keeps only
ROT_K of its world-rotation deviation from its cycle mean (slerp from the mean), the pelvis only X_K of its lateral
offset; the trunk is rebuilt top-down from the bones' rest offsets. The neck, both clavicles and both thighs keep their
world rotations (head, arms and the leg swing as before) and the pelvis height is corrected so the lower foot stays
where it was. Args: -- <in> <out>"""
import bpy, sys, os
import numpy as np
from mathutils import Matrix, Vector, Quaternion
src, out = sys.argv[sys.argv.index('--') + 1:]
ROT_K = float(os.environ.get('WALK_ROT_K', '0.12'))
X_K = float(os.environ.get('WALK_X_K', '0.25'))
CLIP = 'Walking'
TRUNK = ['B_Pelvis', 'B_Spine', 'B_Spine1', 'B_Spine2']
KEEP = ['B_Neck', 'B_L_Clavicle', 'B_R_Clavicle', 'B_L_Thigh', 'B_R_Thigh']
FEET = ['B_L_Foot', 'B_R_Foot', 'B_L_Toe0', 'B_R_Toe0']
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene
rig = bpy.data.objects['Rig']
act = bpy.data.actions[CLIP]; rig.animation_data_create(); rig.animation_data.action = act
if len(act.slots):
    rig.animation_data.action_slot = act.slots[0]
f0, f1 = (int(x) for x in act.frame_range)
B = rig.data.bones


def basis(bn, P_pose, B_pose):
    b = B[bn]
    rest_rel = b.parent.matrix_local.inverted() @ b.matrix_local
    return rest_rel.inverted() @ (P_pose.inverted() @ B_pose)


S = []
for f in range(f0, f1 + 1):
    scene.frame_set(f)
    pb = rig.pose.bones
    S.append({n: pb[n].matrix.copy() for n in TRUNK + KEEP + FEET})


def mean_rot(qs):
    q_mean = qs[0].copy()
    for _ in range(4):
        acc = Vector()
        for q in qs:
            d = q_mean.inverted() @ q
            if d.w < 0:
                d.negate()
            ax, an = d.to_axis_angle(); acc += ax * an
        acc /= len(qs)
        if acc.length > 1e-9:
            q_mean = q_mean @ Quaternion(acc.normalized(), acc.length)
    return q_mean


means = {n: mean_rot([s[n].to_quaternion() for s in S]) for n in TRUNK}
x_mean = float(np.mean([s['B_Pelvis'].translation.x for s in S]))
keys = []
for f, s in zip(range(f0, f1 + 1), S):
    new = {}
    for n in TRUNK:
        q = s[n].to_quaternion(); d = means[n].inverted() @ q
        if d.w < 0:
            d.negate()
        R = (means[n] @ Quaternion().slerp(d, ROT_K)).to_matrix()
        if n == 'B_Pelvis':
            t = s[n].translation.copy(); t.x = x_mean + (t.x - x_mean) * X_K
        else:                                              # head at the rest offset in the new parent
            par = B[n].parent.name
            t = new[par] @ (B[par].matrix_local.inverted() @ B[n].head_local)
        M = R.to_4x4(); M.translation = t; new[n] = M
    for n in KEEP:                                         # world rotation kept, head carried by the new parent
        par = B[n].parent.name
        M = s[n].to_3x3().normalized().to_4x4(); M.translation = new[par] @ (B[par].matrix_local.inverted() @ B[n].head_local)
        new[n] = M
    # feet move with their thigh head's displacement (the leg chain below the thighs is unchanged)
    lo_old = min(s[n].translation.z for n in FEET)
    lo_new = min((s[n].translation + (new[f'B_{n[2]}_Thigh'].translation - s[f'B_{n[2]}_Thigh'].translation)).z for n in FEET)
    dz = Vector((0, 0, lo_old - lo_new))
    for n in new:
        new[n] = Matrix.Translation(dz) @ new[n]
    keys.append((f, new))
for f, new in keys:
    p = rig.pose.bones['B_Pelvis']; p.rotation_mode = 'QUATERNION'
    Mb = B['B_Pelvis'].matrix_local.inverted() @ new['B_Pelvis']
    p.rotation_quaternion = Mb.to_quaternion(); p.location = Mb.translation
    p.keyframe_insert('rotation_quaternion', frame=f); p.keyframe_insert('location', frame=f)
    for n in TRUNK[1:] + KEEP:
        p = rig.pose.bones[n]; p.rotation_mode = 'QUATERNION'
        p.rotation_quaternion = basis(n, new[B[n].parent.name], new[n]).to_quaternion()
        p.keyframe_insert('rotation_quaternion', frame=f)
rig.animation_data.action = None
print('WALKDAMP trunk rotation x', ROT_K, 'pelvis lateral x', X_K, 'frames', len(keys))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
