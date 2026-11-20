"""Face shell clean-up on the cleaned body (the head stays Meshy's: no head graft). Meshy's mouth is a recessed pocket with jagged lip
edges (the lip strips that covered it are dropped in clean_pm2.py) and the lids are crumpled where its eyeball cups sat.
1. mouth zone: faces facing into the head (normal y > NY) are deleted, the hole filled, the patch triangulated;
2. Taubin smoothing (lambda 0.5, mu -0.53) in the mouth and eye zones with a smooth falloff, the midline kept on x = 0.
Args: <in blend> <out blend>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
MOUTH = np.array([0.0, -0.075, 0.723]); MR = np.array([0.034, 0.03, 0.02])
EYES = [np.array([s * 0.021, -0.066, 0.792]) for s in (-1, 1)]; ER = np.array([0.02, 0.02, 0.014])
NY = 0.25
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
lay = bm.faces.layers.int['part']
def inside(c, cen, r): return float(np.sum(((np.array(c) - cen) / r) ** 2))
pocket = [f for f in bm.faces if f[lay] == 20 and inside(f.calc_center_median(), MOUTH, MR) < 1 and f.normal.y > NY]
print('FACEFIX pocket faces', len(pocket))
bmesh.ops.delete(bm, geom=pocket, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
# non-manifold leftovers on the midline in the mouth zone: drop faces until every edge has <= 2 faces
for _ in range(5):
    bad = [e for e in bm.edges if len(e.link_faces) > 2]
    if not bad: break
    rm = set()
    for e in bad:
        fs = sorted(e.link_faces, key=lambda f: f.normal.y)
        rm.update(fs[2:])
    bmesh.ops.delete(bm, geom=list(rm), context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
loops = []
seen = set()
for e0 in [e for e in bm.edges if e.is_boundary and e.link_faces[0][lay] == 20]:
    if e0 in seen: continue
    st = [e0]; seen.add(e0); cur = []
    while st:
        x = st.pop(); cur.append(x)
        for v in x.verts:
            for y in v.link_edges:
                if y.is_boundary and y not in seen: seen.add(y); st.append(y)
    c = np.mean([v.co[:] for e in cur for v in e.verts], 0)
    if inside(c, MOUTH, MR * 1.5) < 1 or len(cur) <= 6:
        r = bmesh.ops.holes_fill(bm, edges=cur, sides=len(cur))
        nf = r['faces']
        bmesh.ops.triangulate(bm, faces=nf)
        for f in bm.faces:
            if f[lay] == 0: f[lay] = 20
        loops.append(len(cur))
print('FACEFIX filled', loops)
bm.verts.ensure_lookup_table()
face_v = [v for v in bm.verts if any(f[lay] == 20 for f in v.link_faces)]
w = {}
for v in face_v:
    d = min([inside(v.co, MOUTH, MR * 1.4)] + [inside(v.co, e, ER * 1.4) for e in EYES])
    k = float(np.clip(1.6 - d, 0, 1))
    if k > 0: w[v] = k * k * (3 - 2 * k)
for it in range(30):
    for lam in (0.5, -0.53):
        mv = {}
        for v, k in w.items():
            nb = [e.other_vert(v).co for e in v.link_edges]
            if not nb or v.is_boundary: continue
            c = sum(nb, Vector()) / len(nb)
            mv[v] = v.co + (c - v.co) * lam * k
        for v, c in mv.items():
            if abs(v.co.x) < 1e-6: c.x = 0.0
            v.co = c
# midline repairs: faces on edges with > 2 faces go, then every small face-shell loop (not the neck opening) is closed
for _ in range(4):
    bad = [e for e in bm.edges if len(e.link_faces) > 2]
    if not bad: break
    rm = {f for e in bad for f in e.link_faces}
    bmesh.ops.delete(bm, geom=list(rm), context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    for _ in range(3):
        seen = set()
        for e0 in [e for e in bm.edges if e.is_boundary and e.link_faces and e.link_faces[0][lay] == 20]:
            if e0 in seen or not e0.is_valid: continue
            st = [e0]; seen.add(e0); cur = []
            while st:
                x = st.pop(); cur.append(x)
                for v in x.verts:
                    for y in v.link_edges:
                        if y.is_boundary and y not in seen: seen.add(y); st.append(y)
            if len(cur) >= 30: continue
            r = bmesh.ops.holes_fill(bm, edges=cur, sides=len(cur))
            bmesh.ops.triangulate(bm, faces=r['faces'])
            for f in bm.faces:
                if f[lay] == 0: f[lay] = 20
for _ in range(2):
    seen = set()
    for e0 in [e for e in bm.edges if e.is_boundary and e.link_faces and e.link_faces[0][lay] == 20]:
        if e0 in seen or not e0.is_valid: continue
        st = [e0]; seen.add(e0); cur = []
        while st:
            x = st.pop(); cur.append(x)
            for v in x.verts:
                for y in v.link_edges:
                    if y.is_boundary and y not in seen: seen.add(y); st.append(y)
        vs = list({v for e in cur for v in e.verts})
        if len(cur) < 12 and np.ptp(np.array([v.co[:] for v in vs]), 0).max() < 0.006:
            bmesh.ops.pointmerge(bm, verts=vs, merge_co=sum((v.co for v in vs), Vector()) / len(vs))
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_area() < 1e-10], context='FACES')
# two midline sheets touching on one edge (4 faces): split it so each sheet is manifold (coincident rims, nothing visible)
bad = [e for e in bm.edges if len(e.link_faces) > 2]
if bad: bmesh.ops.split_edges(bm, edges=bad)
bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f[lay] == 20])
print('FACEFIX smoothed verts', len(w), 'nonmanifold', sum(1 for e in bm.edges if len(e.link_faces) > 2), 'face boundary', sum(1 for e in bm.edges if e.is_boundary and e.link_faces[0][lay] == 20))
bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
bpy.ops.wm.save_as_mainfile(filepath=OUT)
