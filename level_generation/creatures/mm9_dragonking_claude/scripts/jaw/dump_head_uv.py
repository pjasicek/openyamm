"""Dump the head set's UV triangles and tags from head_v1.blend for compose_head_dk.py.
tag: 0 skin, 1 palate, 2 floor, 3 tooth, 4 eye; seam: (HeadUV, UVMap) pairs at vertices shared by head and body faces.
Args: -- <blend> <out npz>"""
import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; me = body.data
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.triangulate(bm, faces=bm.faces[:])
hl = bm.faces.layers.int['head']; ml = bm.faces.layers.int['mouth']; tl = bm.faces.layers.int['tooth']
hu = bm.loops.layers.uv['HeadUV']; bu = bm.loops.layers.uv['UVMap']
bm.verts.ensure_lookup_table()
comp = -np.ones(len(bm.verts), int); cid = 0
for v in bm.verts:
    if comp[v.index] >= 0: continue
    st = [v]; comp[v.index] = cid
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0: comp[y.index] = cid; st.append(y)
    cid += 1
n = np.bincount(comp); shell = n.argmax()
uv, tag, xyz = [], [], []
for f in bm.faces:
    if not f[hl]: continue
    c = f.calc_center_median(); k = comp[f.verts[0].index]
    t = 1 if f[ml] == 1 else 2 if f[ml] == 2 else 3 if f[tl] else (4 if (k != shell and n[k] < 80 and abs(c.x) > 0.35 and c.z > 15.2) else 0)
    uv.append([tuple(l[hu].uv) for l in f.loops]); tag.append(t); xyz.append(tuple(c))
seam = []
for v in bm.verts:
    hs = [l for l in v.link_loops if l.face[hl]]; bs = [l for l in v.link_loops if not l.face[hl]]
    if hs and bs and comp[v.index] == shell:
        seam.append(tuple(hs[0][hu].uv) + tuple(bs[0][bu].uv))
np.savez(a[1], uv=np.array(uv), tag=np.array(tag), xyz=np.array(xyz), seam=np.array(seam))
print('DUMP', len(uv), 'tri', np.bincount(np.array(tag)).tolist(), 'seam', len(seam))
