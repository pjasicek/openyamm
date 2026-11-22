"""G6 for the cloth panels (sorceress): per action and frame, how far thigh/hip skin comes out IN FRONT of the front
panel (P04) or BEHIND the back panel (P06), measured along the actor's forward axis (-Y, she animates in place):
a ray from the skin vertex toward the body's back (+Y; -Y for the back panel): if it meets the panel within 20 cm,
the vertex lies on the viewer's side of the panel and shows through it by that distance. Skin = P00 vertices with thigh weight > 0.3
between 0.45 and 1.0 m at rest. Prints per action and panel the worst depth (cm) and its frame and the number of
frames over 1 cm. Args: -- <blend> action [...]"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
gi = {g.name: g.index for g in body.vertex_groups}
thw = np.array([sum(e.weight for e in v.groups if e.group in (gi['B_L_Thigh'], gi['B_R_Thigh'], gi['B_L_Calf'], gi['B_R_Calf']))
                for v in me.vertices])
rest = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
skin = np.where((pv == 0) & (thw > 0.3) & (rest[:, 2] > 0.45) & (rest[:, 2] < 1.0))[0]
PANELS = {'front': (4, 1.0), 'back': (6, -1.0)}
pf = {k: [tuple(p.vertices) for p in me.polygons if pv[p.vertices[0]] == pc] for k, (pc, _) in PANELS.items()}
for an in a[1:]:
    act = bpy.data.actions[an]; rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    res = {}
    for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
        bpy.context.scene.frame_set(f)
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        P = np.array([tuple(body.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear()
        for k, (pc, sgn) in PANELS.items():
            t = BVHTree.FromPolygons([tuple(p) for p in P], pf[k])
            d = Vector((0, sgn, 0))          # front: +Y, from the skin toward the body's back
            worst = 0.0
            for i in skin:
                hit = t.ray_cast(Vector(P[i]), d, 0.2)
                if hit[0] is not None:
                    worst = max(worst, hit[3])
            w, wf, n = res.get(k, (0.0, None, 0))
            res[k] = (max(w, worst), f if worst > w else wf, n + (worst > 0.01))
    print('PANELPOKE', an, {k: (round(v[0] * 100, 1), v[1], v[2]) for k, v in res.items()})
