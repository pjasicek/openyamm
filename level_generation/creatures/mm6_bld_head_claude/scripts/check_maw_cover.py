"""Gate: in every frame of Attack, Hit, Death and Dead, no head vertex inside the open disc's footprint may sit in front
of the disc's front surface (along the maw axis). Prints the worst margin per clip (positive = covered)."""
import bpy, os
import numpy as np
from mathutils import kdtree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'master.blend'))
mesh = bpy.data.objects['Bld']; rig = bpy.data.objects['Bld_Rig']; sc = bpy.context.scene
kind = np.array([d.value for d in mesh.data.attributes['maw_kind'].data])
gi = {g.name: g.index for g in mesh.vertex_groups}
inner_v = sorted({v for p in mesh.data.polygons if kind[p.index] == 1 for v in p.vertices})
maw_v = {v for p in mesh.data.polygons if kind[p.index] > 0 for v in p.vertices}
head_v = [v.index for v in mesh.data.vertices if v.index not in maw_v
          and sum(g.weight for g in v.groups if g.group in (gi['Head'], gi['Mouth'])) > 0.5]
worst_all = {}
for name in ('Attack', 'Hit', 'Death', 'Dead'):
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if act.slots: rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    worst = 1.0
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get(); ev = mesh.evaluated_get(dg); m = ev.to_mesh()
        co = np.array([v.co[:] for v in m.vertices]); ev.to_mesh_clear()
        bone = rig.pose.bones['Maw']; M = rig.matrix_world @ bone.matrix
        origin = np.array(M.translation); axis = np.array(M.col[1][:3]); axis /= np.linalg.norm(axis)
        def split(p):
            d = p - origin; a = d @ axis; return a, d - np.outer(a, axis)
        ia, ir = split(co[inner_v]); ha, hr = split(co[head_v])
        radius = np.linalg.norm(ir, axis=1).max()
        if radius < 0.03:
            continue                                   # disc (nearly) closed: nothing to cover
        inside = np.linalg.norm(hr, axis=1) < radius * 0.95
        if not inside.any():
            continue
        tree = kdtree.KDTree(len(ir))
        for i, p in enumerate(ir):
            tree.insert(p, i)
        tree.balance()
        idx = np.array([tree.find(p)[1] for p in hr[inside]])
        margin = (ia[idx] - ha[inside]).min()          # disc surface ahead of the vertex (m)
        worst = min(worst, margin)
    worst_all[name] = round(float(worst), 4)
print('COVER', worst_all)
