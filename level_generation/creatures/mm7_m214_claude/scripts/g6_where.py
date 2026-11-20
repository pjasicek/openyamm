"""Which bow/string vertices are inside the skin at one action frame: their bow-frame coordinates (y along the bow,
x toward the belly; string at x -0.15) and the piece hit. Args: -- <blend> <action> <frame>"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
blend, an, fr = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
act = bpy.data.actions[an]; rig.animation_data_create(); rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
bpy.context.scene.frame_set(int(float(fr)), subframe=float(fr) % 1)
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
gv = np.zeros(len(me.vertices), np.int32); me.attributes['garment'].data.foreach_get('value', gv)
ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
P = np.array([tuple(body.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear()
fl = [tuple(p.vertices) for p in me.polygons if gv[p.vertices[0]] == 0 and pv[p.vertices[0]] < 100]
tree = BVHTree.FromPolygons([tuple(p) for p in P], fl)
Bw = rig.matrix_world @ rig.pose.bones['Bow'].matrix; Bi = Bw.inverted()
for k, idx in (('bow', 100), ('string', 102)):
    hits = []
    for i in np.where(pv == idx)[0]:
        loc, nrm, fi, d = tree.find_nearest(Vector(P[i]), 0.05)
        if loc is not None and (Vector(P[i]) - loc).dot(nrm) < -0.7 * d:
            b = Bi @ Vector(P[i]); hits.append((round(b.y, 2), round(b.x, 2), round(d * 100, 1), int(pv[fl[fi][0]])))
    hits.sort()
    print('WHERE', an, fr, k, len(hits), 'inside; (bow y, bow x, depth cm, piece):', hits[:3], '...', hits[-3:])
