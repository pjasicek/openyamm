"""Arm clearance (sword_clear.py's idea for the limbs; m406's bulky thigh plates and tabard take hands that the source
swung past a slimmer body): per frame of each listed action and side, if forearm/hand vertices lie inside the rest of
the body (garment 0 without that arm; inside = behind the nearest face within a 45 deg cone, 6 cm search, as
g6_contacts.py), the upper arm swings outward about the chest's forward axis at the shoulder by the smallest angle
(2..24 deg) that clears them by MARGIN. Angles are dilated by 2 frames and Gaussian-smoothed (sigma 1.5 frames).
The twist bones are re-baked afterwards (rebake_twist.py). Args: -- <in blend> <out blend> <Action>[:L|:R] ..."""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector, Quaternion, Matrix
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
src, out, items = a[0], a[1], a[2:]
MARGIN = float(os.environ.get('MARGIN', '0.01'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; sc = bpy.context.scene
gv = np.zeros(len(me.vertices), np.int32); me.attributes['garment'].data.foreach_get('value', gv)
names = [g.name for g in body.vertex_groups]
W = np.zeros((len(me.vertices), len(names)))
for v in me.vertices:
    for e in v.groups:
        W[v.index, e.group] = e.weight
part = lambda s, keys: W[:, [i for i, n in enumerate(names) if n.startswith(f'B_{s}_') and any(k in n for k in keys)]].sum(1)


def set_act(x):
    rig.animation_data_create(); rig.animation_data.action = x
    if x is not None and len(x.slots):
        rig.animation_data.action_slot = x.slots[0]


def posed():
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    P = [body.matrix_world @ v.co for v in m.vertices]; ev.to_mesh_clear(); return P


for item in items:
    an, *sides = item.split(':'); sides = sides or ['L', 'R']
    act = bpy.data.actions[an]; f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    for s in sides:
        arm_all = part(s, ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger')) > 0.2
        samp = np.where(part(s, ('Forearm', 'Hand', 'Finger')) > 0.5)[0]
        faces = [tuple(p.vertices) for p in me.polygons if gv[p.vertices[0]] in (0, 2) and not any(arm_all[i] for i in p.vertices)]
        ua = f'B_{s}_UpperArm'; out_sign = 1 if s == 'L' else -1
        angles = []
        for f in range(f0, f1 + 1):
            set_act(act); sc.frame_set(f)
            snap = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
            set_act(None)
            for pb in rig.pose.bones:
                pb.matrix_basis = snap[pb.name]
            bpy.context.view_layer.update()
            P = posed(); tree = BVHTree.FromPolygons(P, faces)

            def depth(PP):
                d = 0.0
                for i in samp:
                    loc, nrm, idx, dist = tree.find_nearest(PP[i], 0.06)
                    if loc is not None and (PP[i] - loc).dot(nrm) < -0.7 * dist:
                        d = max(d, dist + MARGIN)
                return d
            d0 = depth(P); best = 0.0
            if d0 > 0:
                chest = (rig.matrix_world @ rig.pose.bones['B_Spine2'].matrix).to_3x3()
                fwd = (chest @ (rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted() @ Vector((0, -1, 0)))).normalized()
                pb = rig.pose.bones[ua]; M0 = (rig.matrix_world @ pb.matrix).copy()
                best = 24.0
                for ang in range(2, 25, 2):
                    R = Quaternion(fwd, math.radians(out_sign * ang)).to_matrix().to_4x4()
                    M = R @ M0.to_3x3().to_4x4(); M.translation = M0.translation
                    pb.matrix = rig.matrix_world.inverted() @ M; bpy.context.view_layer.update()
                    if depth(posed()) == 0.0:
                        best = float(ang); break
                pb.matrix_basis = snap[ua]; bpy.context.view_layer.update()
            angles.append((d0, best))
        ang = np.array([b for _, b in angles]); n = len(ang)
        dil = np.array([ang[max(0, i - 2):i + 3].max() for i in range(n)])
        gk = np.exp(-0.5 * (np.arange(-4, 5) / 1.5) ** 2); gk /= gk.sum()
        pad = np.concatenate([np.repeat(dil[:1], 4), dil, np.repeat(dil[-1:], 4)])
        sm = np.convolve(pad, gk, 'valid')
        for i, f in enumerate(range(f0, f1 + 1)):
            if sm[i] < 0.05:
                continue
            set_act(act); sc.frame_set(f)
            snap = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
            set_act(None)
            for pb in rig.pose.bones:
                pb.matrix_basis = snap[pb.name]
            bpy.context.view_layer.update()
            chest = (rig.matrix_world @ rig.pose.bones['B_Spine2'].matrix).to_3x3()
            fwd = (chest @ (rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted() @ Vector((0, -1, 0)))).normalized()
            pb = rig.pose.bones[ua]; M0 = (rig.matrix_world @ pb.matrix).copy()
            R = Quaternion(fwd, math.radians(out_sign * sm[i])).to_matrix().to_4x4()
            M = R @ M0.to_3x3().to_4x4(); M.translation = M0.translation
            pb.matrix = rig.matrix_world.inverted() @ M; bpy.context.view_layer.update()
            q = pb.rotation_quaternion.copy()
            set_act(act); pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=f)
        set_act(None)
        hit = [i for i, (d0, _) in enumerate(angles) if d0 > 0]
        print(f'ARMCLEAR {an} {s}: frames with contact {len(hit)} of {n}, worst {max([d for d, _ in angles] + [0]) * 100:.1f} cm, '
              f'max swing {sm.max():.0f} deg, unresolved {sum(1 for d0, b in angles if d0 > 0 and b >= 24)}')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
