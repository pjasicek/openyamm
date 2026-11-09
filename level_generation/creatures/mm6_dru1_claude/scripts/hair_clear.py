"""Hair off the skin (review 2: dark/light triangles on the neck were the hair shell's inner faces cutting through the
neck surface). Rest pose: every hair vertex (piece 1) inside the face/neck/torso skin (piece 0) or within CLEAR of it is
moved to CLEAR along the nearest skin face's normal; the displacement is diffused over the hair's own edges (3 passes)
so the shell stays smooth. Topology, UVs and weights are unchanged. In place on <blend>. Args: -- <blend>"""
import bpy, bmesh, sys, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
CLEAR = float(os.environ.get("HAIR_CLEAR", "0.004"))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index('--') + 1]))
rig = bpy.data.objects['Rig']; rig.animation_data_create(); rig.animation_data.action = None
me = bpy.data.objects['Body'].data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
co = [v.co.copy() for v in me.vertices]
skin_faces = [tuple(p.vertices) for p in me.polygons if all(pv[i] == 0 for i in p.vertices)]
tree = BVHTree.FromPolygons(co, skin_faces)
hair = np.where(pv == 1)[0]
disp = {}
for i in hair:
    loc, n, idx, d = tree.find_nearest(co[i], 0.05)
    if loc is None:
        continue
    s = (co[i] - loc).dot(n)
    if s < CLEAR:
        disp[int(i)] = n * (CLEAR - s)
nbr = {int(i): [] for i in hair}
for e in me.edges:
    a, b = e.vertices
    if a in nbr and b in nbr:
        nbr[a].append(b); nbr[b].append(a)
D = {i: disp.get(i, Vector()) for i in nbr}
for _ in range(3):
    D = {i: (D[i] if i in disp else Vector()) * 0.5 + (sum((D[j] for j in nbr[i]), Vector()) / max(len(nbr[i]), 1)) * 0.5
         if nbr[i] else D[i] for i in nbr}
    for i in disp:                                          # the offending vertices keep at least their own push
        if D[i].length < disp[i].length:
            D[i] = disp[i].copy()
moved = 0
for i, d in D.items():
    if d.length > 1e-5:
        me.vertices[i].co += d; moved += 1
me.update(); bpy.ops.wm.save_mainfile()
print('HAIRCLEAR inside/near skin', len(disp), 'moved', moved, 'max push mm', round(max((d.length for d in D.values()), default=0) * 1000, 1))
