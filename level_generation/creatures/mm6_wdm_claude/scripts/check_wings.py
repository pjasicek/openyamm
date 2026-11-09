"""Wing crossing check on work/anim_v1.blend: per clip frame, the deformed wing vertices in the Spine2 frame. Reports
left-wing vertices that cross the body midline (and vice versa) and the closest left-right wing gap."""
import bpy, os
import numpy as np
from mathutils import kdtree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rig = bpy.data.objects['Demon_Rig']; mesh = bpy.data.objects['Demon']; sc = bpy.context.scene
att = mesh.data.attributes.get('wing')
if att:
    wing = np.zeros(len(mesh.data.vertices), bool); att.data.foreach_get('value', wing)
else:
    wing = np.load(os.path.join(HERE, 'work', 'wing_mask.npy'))
rest = np.array([tuple(v.co) for v in mesh.data.vertices])
left, right = wing & (rest[:, 0] > 0), wing & (rest[:, 0] < 0)
worst = {}
for act in ('Flight', 'Attack', 'Cast', 'Hit', 'Death'):
    A = bpy.data.actions[act]; rig.animation_data.action = A
    f0, f1 = map(int, A.frame_range)
    for f in range(f0, f1 + 1):
        if act == 'Death' and f > 10:      # the body shrinks into the disintegration burst from 0.45 s
            break
        sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        me = mesh.evaluated_get(dg).to_mesh()
        co = np.array([tuple(v.co) for v in me.vertices]); mesh.evaluated_get(dg).to_mesh_clear()
        m = np.array((rig.matrix_world @ rig.pose.bones['mixamorig:Spine2'].matrix).inverted())
        loc = co @ m[:3, :3].T + m[:3, 3]
        # Spine2 local x is the body's side axis; its sign is taken from the hips so either bone-roll convention works
        side = np.sign(np.median(loc[left, 0]) - np.median(loc[right, 0]))
        cross = int((loc[left, 0] * side < 0).sum() + (loc[right, 0] * side > 0).sum())
        kd = kdtree.KDTree(int(right.sum()))
        for i, p in enumerate(co[right]):
            kd.insert(p, i)
        kd.balance()
        gap = min(kd.find(p)[2] for p in co[left][::4])
        w = worst.setdefault(act, [0, 9.0, 0])
        if cross > w[0]:
            w[0] = cross; w[2] = f
        w[1] = min(w[1], gap)
for act, (cross, gap, f) in worst.items():
    print(f'WINGS {act:7s} crossing verts max {cross:4d} (frame {f})  min L-R gap {gap * 100:.1f} cm')
