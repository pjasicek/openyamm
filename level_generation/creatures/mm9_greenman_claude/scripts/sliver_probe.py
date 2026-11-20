"""Long thin triangles (max edge > L, area/maxedge = altitude < A) of 'Body' in a blend within a box; prints their
loose part, head/hand flags and position. Args: <blend> [L 0.06] [A 0.004] [zmin zmax]"""
import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
L = float(a[1]) if len(a) > 1 else 0.06; A = float(a[2]) if len(a) > 2 else 0.004
z0 = float(a[3]) if len(a) > 3 else 0.85; z1 = float(a[4]) if len(a) > 4 else 1.2
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
hl = bm.faces.layers.int.get('head')
comp = {}; cid = 0
for v in bm.verts:
    if v in comp: continue
    st = [v]; comp[v] = cid
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in comp: comp[y] = cid; st.append(y)
    cid += 1
n = 0
for f in bm.faces:
    c = f.calc_center_median()
    if not (z0 < c.z < z1 and abs(c.x) < 0.15 and c.y < -0.05):
        continue
    es = [e.calc_length() for e in f.edges]; me_ = max(es); alt = 2 * f.calc_area() / me_
    if me_ > L and alt < A:
        n += 1
        print('SLIVER face', f.index, 'part', comp[f.verts[0]], 'head', f[hl] if hl else None, 'maxedge %.3f alt %.4f' % (me_, alt), 'c', tuple(round(x, 3) for x in c))
print('SLIVER count', n)
