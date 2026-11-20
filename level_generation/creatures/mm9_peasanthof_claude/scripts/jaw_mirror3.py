"""Symmetric lower face, third pass (user review r10, 2026-11-04, review/user_20261104/jaw_asymmetry_r9.png: her right lower face
runs as a straight diagonal from the cheek to the chin). Measured cause: the head shell's lower edge (the neck seam to the body,
shared vertices) sits up to 13-27 mm higher on the narrow side at the jaw corner (55-80 deg from the front), so the body neck takes
over where the fuller side still has its jaw corner, and the narrow side's few large triangles span straight from cheek to chin.

Steps, all on the narrow side (master +x for HOF1; the fuller side is given as a sign), topology kept apart from one subdivision:
1. the narrow side's lower-face head faces are subdivided once (bmesh subdivide_edges, cuts 1, grid fill; UVs, weights and face
   layers interpolate), so the jaw corner has vertices to hold its shape;
2. the seam: every narrow-side seam vertex gets the fuller side's seam height at its angle (linear in angle through the fuller
   side's seam vertices); the same vertical shift reaches the head and body vertices near it with a smooth falloff over SEAM_FALL
   (3 cm) above and below, so no face folds;
3. every narrow-side vertex in the region (head shell and the body neck within 4 cm below the seam) is projected radially onto
   the mirror image of the fuller side's surface (head shell + body neck faces): a ray from C = (nose-tip x, mid depth, export
   height ZC) in the mirrored direction, the crossing nearest the vertex's own radius (none within 25 mm = left as is), and the
   vertex moves along its own direction from C to that radius; missed rays take their neighbours' mean displacement and the
   displacement field is relaxed twice (half to the neighbour mean), so no single ray leaves a dent.
Weights: 1 in the region, eased to 0 (smooth) over the upper edge Y1-0.02..Y1 (cheekbone), near the midline T0..T0+15 deg (the
midline itself does not move, so it stays welded), toward the back T1-20..T1 deg, the body neck from the seam down to 4 cm, and
the mouth (a sphere of R_MOUTH round the lips, 1 cm ease), so the nose, lips, tusks and eyes stay.
Args: <in blend> <out blend> [y1 1.748] [t0 12] [t1 135] [r_mouth 0.02] [mouth_dy -0.043] [export head y 1.697]
      [fuller side -|+ (master x sign)] [zc 1.715] [cuts 1]"""
import bpy, bmesh, sys, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
a = sys.argv[sys.argv.index('--') + 1:]
f = lambda i, d: float(a[i]) if len(a) > i else d
Y1, T0, T1, RM, MDY, HEADY = f(2, 1.748), f(3, 12.0), f(4, 135.0), f(5, 0.02), f(6, -0.043), f(7, 1.697)
full = -1 if (a[8] if len(a) > 8 else '-') == '-' else 1
ZC, CUTS = f(9, 1.715), int(f(10, 1))
SEAM_FALL, NECK = 0.03, 0.04
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; rig = ob.parent; mw = ob.matrix_world; mwi = mw.inverted()
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
hb = next(b for b in rig.pose.bones if b.name.endswith('Head')); off = HEADY - (rig.matrix_world @ hb.head).z
bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
lh, lk = bm.faces.layers.int['head'], bm.faces.layers.int['hand']
ishead = lambda f_: f_[lh] and not f_[lk]
hv = {v.index for f_ in bm.faces if ishead(f_) for v in f_.verts}
W0 = [mw @ v.co for v in bm.verts]
fr = [i for i in hv if 1.70 - off < W0[i].z < 1.78 - off]
nose = min(fr, key=lambda i: W0[i].y)                     # faces -y
comp = {nose}; st = [bm.verts[nose]]
while st:
    v = st.pop()
    for e in v.link_edges:
        o = e.other_vert(v)
        if o.index in hv and o.index not in comp: comp.add(o.index); st.append(o)
cx = W0[nose].x
band = [i for i in comp if 1.60 - off < W0[i].z < Y1 - off]
cy = 0.5 * (min(W0[i].y for i in band) + max(W0[i].y for i in band))
def ang(p): return math.degrees(math.atan2(abs(p.x - cx), -(p.y - cy)))
def ss(x): x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)
def angw(t): return ss((t - T0) / 15.0) * ss((T1 - t) / 20.0)
seam = [i for i in comp if any(not ishead(f_) for f_ in bm.verts[i].link_faces) and W0[i].z + off < 1.71 and ang(W0[i]) < T1 + 5]
kd = KDTree(len(seam))
for k, i in enumerate(seam): kd.insert(W0[i], k)
kd.balance()
# the body neck: non-head faces whose vertices all lie within NECK of the seam and below the cheekbone
neckf = [f_ for f_ in bm.faces if not f_[lh] and all(kd.find(W0[v.index])[2] < NECK + 0.01 and W0[v.index].z + off < 1.71
                                                     for v in f_.verts)]
neckv = {v.index for f_ in neckf for v in f_.verts}
# BVH of the fuller side's surface (head shell + body neck), original positions
surf = [f_ for f_ in bm.faces if (ishead(f_) and all(v.index in comp for v in f_.verts)) or f_ in set(neckf)]
surf = [f_ for f_ in surf if sum((W0[v.index].x - cx) * full for v in f_.verts) > 0]
vmap = {}; verts = []; polys = []
for f_ in surf:
    pl = []
    for v in f_.verts:
        if v.index not in vmap: vmap[v.index] = len(verts); verts.append(W0[v.index])
        pl.append(vmap[v.index])
    polys.append(pl)
bvh = BVHTree.FromPolygons(verts, polys)
# the fuller side's seam profile: height by angle
fs = sorted((ang(W0[i]), W0[i].z) for i in seam if (W0[i].x - cx) * full > 0)
fsa, fsz = np.array([t for t, _ in fs]), np.array([z for _, z in fs])
mouth = Vector((cx, W0[nose].y + 0.02, W0[nose].z + MDY))
def weight(p, body):
    t = ang(p); z = p.z + off
    w = ss((Y1 - z) / 0.02) * angw(t) * ss(((p - mouth).length - RM) / 0.01)
    if body: w *= ss(1.0 - kd.find(p)[2] / NECK)
    return w
# 1. subdivide the narrow side's lower-face head faces
nf0 = len(bm.faces)
sub = [f_ for f_ in bm.faces if ishead(f_) and all(v.index in comp for v in f_.verts)
       and all((W0[v.index].x - cx) * full < 0.002 for v in f_.verts)
       and any((W0[v.index].x - cx) * full < 0 and weight(W0[v.index], False) > 0 and W0[v.index].z + off > 1.60 for v in f_.verts)]
if CUTS > 0:
    bmesh.ops.subdivide_edges(bm, edges=list({e for f_ in sub for e in f_.edges}), cuts=CUTS, use_grid_fill=True, smooth=0.0)
    bmesh.ops.triangulate(bm, faces=[f_ for f_ in bm.faces if len(f_.verts) > 3], quad_method="BEAUTY", ngon_method="BEAUTY")
bm.verts.ensure_lookup_table(); bm.verts.index_update()
P = [mw @ v.co for v in bm.verts]
narrow = lambda p: (p.x - cx) * full < 0
# narrow-side seam after the subdivision (new vertices on the seam edges are shared with body faces too)
nseam = [v.index for v in bm.verts if narrow(P[v.index]) and any(ishead(f_) for f_ in v.link_faces)
         and any(not f_[lh] for f_ in v.link_faces) and P[v.index].z + off < 1.71 and ang(P[v.index]) < T1 + 5]
ns = sorted((ang(P[i]), P[i].z, i) for i in nseam)
nsa = np.array([t for t, _, _ in ns]); nsz = np.array([z for _, z, _ in ns])
dzs = np.array([(np.interp(t, fsa, fsz) - z) * angw(t) for t, z, _ in ns])
print('JAWMIRROR3 narrow seam (deg:mm height -> shift):', ' '.join(f'{t:.0f}:{(z+off)*1000:.0f}->{d*1000:+.0f}' for (t, z, _), d in zip(ns, dzs)))
# 2. seam shift with a vertical falloff
mx2 = 0.0
# the skin shell after the subdivision: the old shell vertices plus the new ones on its faces (hair, braids, ears stay out)
headv = set(comp) | {v.index for v in bm.verts if v.index >= len(W0) and any(ishead(f_) for f_ in v.link_faces)}
for v in bm.verts:
    p = P[v.index]
    if not narrow(p) or not (v.index in headv or v.index in neckv): continue
    t = ang(p)
    zs = np.interp(t, nsa, nsz); dz = float(np.interp(t, nsa, dzs))
    fall = ss(1.0 - abs(p.z - zs) / SEAM_FALL)
    if fall <= 0 or abs(dz) < 1e-6: continue
    P[v.index] = p + Vector((0, 0, dz * fall)); mx2 = max(mx2, abs(dz * fall))
# 3. radial projection onto the mirrored fuller side
C = Vector((cx, cy, ZC - off))
moved = 0; mx = 0.0; misses = []
D = {}                                                     # radial displacement per region vertex (missed rays filled below)
for v in bm.verts:
    p = P[v.index]
    if not narrow(p) or not (1.585 - off < p.z < Y1 - off) or not (T0 < ang(p) < T1): continue
    if v.index not in headv and v.index not in neckv: continue
    body = v.index not in headv
    if body and kd.find(p)[2] > NECK: continue
    w = weight(p, body)
    if w <= 0: continue
    u = (p - C).normalized(); um = Vector((-u.x, u.y, u.z))
    o = C.copy(); hits = []
    for _ in range(8):
        h, _n, _i, d = bvh.ray_cast(o, um)
        if h is None: break
        hits.append((h - C).length); o = h + um * 1e-4
    r0 = (p - C).length
    r = min(hits, key=lambda x: abs(x - r0)) if hits else None
    if r is None or abs(r - r0) > 0.025:
        misses.append(v.index); D[v.index] = None; continue
    D[v.index] = (C + u * r - p) * w; moved += 1
# missed rays take the mean of their region neighbours' displacements (repeated so chains fill), then the displacement field is
# relaxed twice (half towards the neighbour mean, region vertices only) so a single odd ray cannot leave a dent or a fold
for _ in range(6):
    for i in [i for i in D if D[i] is None]:
        nb = [D.get(e.other_vert(bm.verts[i]).index) for e in bm.verts[i].link_edges]
        nb = [d for d in nb if d is not None]
        if nb: D[i] = sum(nb, Vector()) / len(nb)
for i in D:
    if D[i] is None: D[i] = Vector()
for _ in range(2):
    E = {}
    for i in D:
        nb = [D.get(e.other_vert(bm.verts[i]).index, Vector()) for e in bm.verts[i].link_edges]
        E[i] = 0.5 * D[i] + 0.5 * sum(nb, Vector()) / max(len(nb), 1)
    D = E
for i, d in D.items():
    P[i] = P[i] + d; mx = max(mx, d.length)
miss = len(misses)
print('JAWMIRROR3 missed rays at (export x, height, z mm):', ' '.join(f'({-(P[i].x)*1000:.0f},{(P[i].z+off)*1000:.0f},{-P[i].y*1000:.0f})' for i in misses))
for v in bm.verts: v.co = mwi @ P[v.index]
bm.to_mesh(ob.data); bm.free(); ob.data.update()
bpy.ops.wm.save_as_mainfile(filepath=a[1])
print('JAWMIRROR3 fuller side', '+x' if full > 0 else '-x', 'subdivided', len(sub), 'faces (', nf0, '->', len(ob.data.polygons),
      '); seam shift max', round(mx2 * 1000, 1), 'mm; projected', moved, 'max', round(mx * 1000, 1), 'mm; rays missed', miss)
