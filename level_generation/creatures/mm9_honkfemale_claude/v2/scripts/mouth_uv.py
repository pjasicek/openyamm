"""UV triangles (HeadUV) of the head shell behind the lip plates: Meshy's lips are two separate open cups, and the shell
between them carries the reference's pale teeth as a jagged strip. Args: <blend> <out json> <x0 x1 y0 y1 z0 z1 zline rim> (rest metres; plate faces within rim of zline are the inner lip edge)"""
import bpy, bmesh, json, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
b = bpy.data.objects['Body']; me = b.data; M = b.matrix_world
box = [float(x) for x in a[2:8]]
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
lh = bm.faces.layers.int['head']; uv = bm.loops.layers.uv['HeadUV']
comp = {}
big, bigk = 0, None
for v in bm.verts:
    if v.index in comp: continue
    st = [v]; comp[v.index] = v.index; n = 1
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in comp:
                comp[y.index] = v.index; st.append(y); n += 1
    if n > big and any(f[lh] == 1 for f in v.link_faces):
        big, bigk = n, v.index
out = {'shell': [], 'plate': [], 'rim': []}
from mathutils import Vector
from mathutils.bvhtree import BVHTree
pf = [f for f in bm.faces if f[lh] == 1 and comp[f.verts[0].index] != bigk
      and box[0] < (M @ f.calc_center_median()).x < box[1] and box[2] < (M @ f.calc_center_median()).y < box[3]
      and box[4] < (M @ f.calc_center_median()).z < box[5]]
vid = {}
vco = []
for f in pf:
    for v in f.verts:
        if v.index not in vid:
            vid[v.index] = len(vco); vco.append(M @ v.co)
bvh = BVHTree.FromPolygons(vco, [[vid[v.index] for v in f.verts] for f in pf])
zline = float(a[8]); rimh = float(a[9])
for f in bm.faces:
    if f[lh] != 1: continue
    c = M @ f.calc_center_median()
    if not (box[0] < c.x < box[1] and box[2] < c.y < box[3] and box[4] < c.z < box[5]): continue
    t = [tuple(l[uv].uv) for l in f.loops]
    if comp[f.verts[0].index] == bigk:
        if bvh.ray_cast(c, Vector((0, -1, 0)), 0.04)[0] is not None:     # only shell hidden behind the lips
            out['shell'].append(t)
    else:
        out['plate'].append(t)
        if abs(c.z - zline) < rimh:
            out['rim'].append(t)
json.dump(out, open(a[1], 'w'))
print('MOUTHUV', {k: len(v) for k, v in out.items()})
