"""HOF1 hair crown fitted to MM9's silhouette (coordinator review 2026-11-02: "a smooth leather helmet"): MM9's head narrows to
+-9 cm at 0.95 m (ours +-11-12 cm, a balloon crown). Every head-material vertex above Z0 (the ears and braids excluded:
loose parts under 200 vertices or reaching below 0.6 m) moves horizontally toward the head axis by a factor easing from 1
at Z0 to K at the top (smoothstep), the face is below Z0. Positions only (UVs, weights unchanged).
Args: <in blend> <out blend> [z0 0.875] [k 0.84] [cx,cy -0.005,0.06]"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
Z0 = float(a[2]) if len(a) > 2 else 0.875
K = float(a[3]) if len(a) > 3 else 0.84
cx, cy = [float(t) for t in (a[4] if len(a) > 4 else '-0.005,0.06').split(',')]
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; mw = ob.matrix_world; mwi = mw.inverted()
bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
lk = bm.faces.layers.int['head']
comp = -np.ones(len(bm.verts), int); parts = []
for v in bm.verts:
    if comp[v.index] >= 0: continue
    st = [v]; comp[v.index] = len(parts); cur = []
    while st:
        x = st.pop(); cur.append(x.index)
        for e in x.link_edges:
            o = e.other_vert(x)
            if comp[o.index] < 0: comp[o.index] = len(parts); st.append(o)
    parts.append(cur)
CO = np.array([tuple(mw @ v.co) for v in bm.verts])
ok_part = {k for k, p in enumerate(parts) if len(p) >= 200 and CO[p, 2].min() > 0.6}
ztop = max(CO[p, 2].max() for k, p in enumerate(parts) if k in ok_part)
n = 0
for v in bm.verts:
    if comp[v.index] not in ok_part or not any(f[lk] for f in v.link_faces): continue
    p = CO[v.index]
    if p[2] <= Z0: continue
    t = min(1.0, (p[2] - Z0) / (ztop - Z0)); t = t * t * (3 - 2 * t)
    f = 1 - (1 - K) * t
    q = np.array([cx + (p[0] - cx) * f, cy + (p[1] - cy) * f, p[2]])
    v.co = mwi @ Vector(q.tolist()); n += 1
bm.to_mesh(ob.data); ob.data.update()
print('HAIR_TAPER moved', n, 'parts', sorted(ok_part), 'ztop', round(float(ztop), 3))
bpy.ops.wm.save_as_mainfile(filepath=a[1])
