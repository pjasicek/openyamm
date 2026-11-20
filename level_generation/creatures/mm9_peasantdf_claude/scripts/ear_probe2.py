"""Job 7 probe: the head shell around the ears (positions, HeadUV bounds) and the hair/hood shell edge at ear height,
on a master blend. Args: <blend>"""
import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; me = ob.data
print('MATS', [m.name for m in me.materials], 'layers', [l.name for l in me.attributes])
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
lh = bm.faces.layers.int.get('head'); uvh = bm.loops.layers.uv.get('HeadUV'); uvb = bm.loops.layers.uv.get('UVMap')
comp = -np.ones(len(bm.verts), int); k = 0
for v in bm.verts:
    if comp[v.index] >= 0: continue
    st = [v]; comp[v.index] = k
    while st:
        x = st.pop()
        for e in x.link_edges:
            o = e.other_vert(x)
            if comp[o.index] < 0: comp[o.index] = k; st.append(o)
    k += 1
co = np.array([tuple(v.co) for v in bm.verts])
head_v = set()
for f in bm.faces:
    if f[lh]:
        for v in f.verts: head_v.add(v.index)
hv = np.array(sorted(head_v))
print('head verts', len(hv), 'bounds', np.round(co[hv].min(0), 3), np.round(co[hv].max(0), 3))
cnt = np.bincount(comp[hv], minlength=k)
for c in np.argsort(-cnt)[:8]:
    if cnt[c] == 0: continue
    q = co[comp == c]
    print('COMP', c, cnt[c], len(q), np.round(q.min(0), 3), np.round(q.max(0), 3))
