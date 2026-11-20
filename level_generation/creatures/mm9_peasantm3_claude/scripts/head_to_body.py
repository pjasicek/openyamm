"""Collar faces to the body (orchestrator review of r7: the gold painted into the head texture below the neckline read as a
blotchy gold bib). Head faces lying on or below neck_line.py's curve (every vertex within 0.5 mm above it or lower) become BODY
faces (attribute head = 0, so the export gives them the body material), and every corner of them takes the body UV
('UVMap') of the closest point on the body's own collar/tunic surface, interpolated barycentrically, so the body's brocade
continues across them. Faces straddling the curve stay head (skin). Geometry unchanged (neck_line.py already put them 4 mm
behind the body collar where they overlap). Reference surface: body faces (no head/hand) within 16 cm of the neck axis above
z 0.52. Args (Blender): <in blend> <out blend> [zfront 0.668]"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]
ZFRONT = float(a[2]) if len(a) > 2 else 0.668
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data; rig = body.parent
nb = rig.data.bones['Bip01 Neck']; C = np.array((rig.matrix_world @ nb.head_local)[:2])
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
lh = bm.faces.layers.int['head']; lhn = bm.faces.layers.int['hand']
uv = bm.loops.layers.uv['UVMap']
P = np.array([v.co[:] for v in bm.verts])
d = P[:, :2] - C; r = np.hypot(d[:, 0], d[:, 1]); ang = np.degrees(np.arctan2(d[:, 0], -d[:, 1]))
bodyf = [f for f in bm.faces if not f[lh] and not f[lhn]]
bodyv = np.zeros(len(P), bool)
for f in bodyf:
    for v in f.verts:
        bodyv[v.index] = True
# the neckline curve, as neck_line.py
bins = np.arange(-180, 181, 10)
neckb = bodyv & (P[:, 2] > 0.55) & (r < 0.13)
top = np.array([P[neckb & (ang >= b) & (ang < b + 10), 2].max() if (neckb & (ang >= b) & (ang < b + 10)).any() else np.nan
                for b in bins[:-1]])
top = np.maximum(np.where(np.isnan(top), np.nanmin(top), top), ZFRONT)
top = np.maximum(np.convolve(np.r_[top[-3:], top, top[:3]], np.ones(7) / 7, 'valid'), ZFRONT)
zv = np.interp(ang, bins[:-1] + 5, top, period=360)
# reference: body faces of the collar/tunic near the neck (triangulated copies for the BVH)
ref = [f for f in bodyf if np.all(r[[v.index for v in f.verts]] < 0.16) and min(v.co.z for v in f.verts) > 0.52]
tris, tri_uv = [], []
for f in ref:
    ls = f.loops
    for k in range(1, len(ls) - 1):
        tris.append((ls[0].vert.co.copy(), ls[k].vert.co.copy(), ls[k + 1].vert.co.copy()))
        tri_uv.append((ls[0][uv].uv.copy(), ls[k][uv].uv.copy(), ls[k + 1][uv].uv.copy()))
verts = [p for t in tris for p in t]
tree = BVHTree.FromPolygons(verts, [(3 * i, 3 * i + 1, 3 * i + 2) for i in range(len(tris))])
moved = []
for f in bm.faces:
    if not f[lh] or f[lhn]:
        continue
    vs = [v.index for v in f.verts]
    if r[vs].max() > 0.16:
        continue
    if (P[vs, 2] - zv[vs]).max() > 0.0005:
        continue
    moved.append(f)
import os
MODE = os.environ.get('MODE', 'nearest')
if MODE == 'panel':
    # r8b: a closed shirt front of the tunic's own velvet: the moved faces' (x, z) mapped affinely into one large front tunic
    # island around ANCHOR (left chest, clear of the centre placket's brocade), the affine fitted on that island's own
    # vertices within 8 cm, so the weave continues at the island's own scale with no stretch
    AX, AZ = float(os.environ.get('ANCHOR_X', '0.075')), float(os.environ.get('ANCHOR_Z', '0.40'))
    front = [f for f in bodyf if f.calc_center_median().y < -0.05]
    f0 = min(front, key=lambda f: (f.calc_center_median() - Vector((AX, -0.15, AZ))).length * (1 + 10 * (abs(f.calc_center_median().x - AX) > 0.05)))
    # UV island of f0 (faces sharing UV-continuous edges)
    def key(l):
        return (round(l[uv].uv.x, 6), round(l[uv].uv.y, 6))
    isl = {f0}; stack = [f0]
    while stack:
        f = stack.pop()
        for l in f.loops:
            e = l.edge
            for g in e.link_faces:
                if g in isl or g[lh] or g[lhn]:
                    continue
                lg = [m for m in g.loops if m.vert in e.verts]
                lf = [m for m in f.loops if m.vert in e.verts]
                if {key(m) for m in lg} == {key(m) for m in lf}:
                    isl.add(g); stack.append(g)
    p0 = f0.calc_center_median()
    pts = [(l.vert.co.x, l.vert.co.z, l[uv].uv.x, l[uv].uv.y) for f in isl for l in f.loops if (l.vert.co - p0).length < 0.08]
    A = np.array([[1, x, z] for x, z, _, _ in pts]); U = np.array([[u, v] for _, _, u, v in pts])
    coef, *_ = np.linalg.lstsq(A, U, rcond=None)
    cm = np.mean([[l.vert.co.x, l.vert.co.z] for f in moved for l in f.loops], 0)
    for f in moved:
        f[lh] = 0
        for l in f.loops:
            x = l.vert.co.x - cm[0] + p0.x; z = l.vert.co.z - cm[1] + p0.z
            l[uv].uv = tuple(np.array([1, x, z]) @ coef)
        f.material_index = f0.material_index
    print('PANEL island faces', len(isl), 'anchor', [round(c, 3) for c in p0], 'fit points', len(pts))
    moved_panel = True
else:
    moved_panel = False
maxd = 0.0
for f in ([] if moved_panel else moved):
    f[lh] = 0
    for l in f.loops:
        loc, nrm, ti, dist = tree.find_nearest(l.vert.co, 0.08)
        if loc is None:
            continue
        maxd = max(maxd, dist)
        a_, b_, c_ = tris[ti]
        ua, ub, uc = tri_uv[ti]
        q = barycentric_transform(loc, a_, b_, c_, Vector((ua.x, ua.y, 0)), Vector((ub.x, ub.y, 0)), Vector((uc.x, uc.y, 0)))
        l[uv].uv = (q.x, q.y)
    if ref:
        f.material_index = ref[0].material_index
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('HEADTOBODY ' + json.dumps({'faces_to_body': len(moved), 'ref_tris': len(tris), 'max_dist_mm': round(maxd * 1000, 1)}))
